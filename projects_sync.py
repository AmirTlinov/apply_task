import difflib
import hashlib
import hmac
import json
import logging
import os
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
import yaml

from config import get_user_token

GRAPHQL_URL = "https://api.github.com/graphql"
CONFIG_PATH = Path(".apply_task_projects.yaml")
logger = logging.getLogger("apply_task.projects")
_PROJECTS_SYNC: Optional["ProjectsSync"] = None


def _read_project_file(path: Optional[Path] = None) -> Dict[str, Any]:
    target = path or CONFIG_PATH
    if not target.exists():
        return {}
    try:
        return yaml.safe_load(target.read_text()) or {}
    except Exception:
        return {}


def _write_project_file(data: Dict[str, Any], path: Optional[Path] = None) -> None:
    target = path or CONFIG_PATH
    if not data:
        if target.exists():
            target.unlink()
        return
    target.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")


@dataclass
class FieldConfig:
    name: str
    options: Dict[str, str] = field(default_factory=dict)


@dataclass
class ProjectConfig:
    project_type: str
    owner: str
    number: int
    repo: Optional[str] = None
    fields: Dict[str, FieldConfig] = field(default_factory=dict)
    enabled: bool = True


class ProjectsSync:
    def __init__(self, config_path: Optional[Path] = None) -> None:
        self.config_path = config_path or CONFIG_PATH
        self.config: Optional[ProjectConfig] = self._load_config()
        self.token = os.getenv("APPLY_TASK_GITHUB_TOKEN") or os.getenv("GITHUB_TOKEN") or get_user_token()
        self.session = requests.Session()
        self.project_id: Optional[str] = None
        self.project_fields: Dict[str, Dict[str, Any]] = {}
        self.conflicts_dir = Path(".tasks") / ".projects_conflicts"
        self._pending_conflicts: List[Dict[str, Any]] = []
        self._seen_conflicts: Dict[Tuple[str, str], str] = {}
        self.last_pull: Optional[str] = None
        self.last_push: Optional[str] = None

    # ------------------------------------------------------------------
    # Helpers for conflict detection / reporting
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_timestamp(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        text = str(value).strip()
        if not text:
            return None
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            if "T" in text:
                return datetime.fromisoformat(text)
            return datetime.strptime(text, "%Y-%m-%d %H:%M")
        except ValueError:
            return None

    def _local_is_newer(self, local_value: Optional[str], remote_value: Optional[str]) -> bool:
        remote_dt = self._parse_timestamp(remote_value)
        local_dt = self._parse_timestamp(local_value)
        if not remote_dt or not local_dt:
            return False
        if remote_dt.tzinfo:
            remote_dt = remote_dt.astimezone(timezone.utc).replace(tzinfo=None)
        return local_dt > remote_dt

    def _conflict_key(self, task_id: str, remote_updated: Optional[str], new_text: str) -> Tuple[str, str]:
        if remote_updated:
            return task_id, remote_updated
        digest = hashlib.sha1(new_text.encode()).hexdigest()
        return task_id, digest

    def _record_conflict(self, task_id: str, file_path: Path, existing_text: str, new_text: str, reason: str, remote_updated: Optional[str], source: str) -> Dict[str, Any]:
        safe_task = task_id or file_path.stem
        key = self._conflict_key(safe_task, remote_updated, new_text)
        report_path = self._seen_conflicts.get(key)
        if not report_path:
            self.conflicts_dir.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            report_file = self.conflicts_dir / f"{safe_task}-{stamp}.diff"
            diff = "\n".join(
                difflib.unified_diff(
                    (existing_text or "").splitlines(),
                    new_text.splitlines(),
                    fromfile=str(file_path),
                    tofile=f"remote:{source}",
                    lineterm="",
                )
            )
            report_text = (
                f"Задача: {safe_task}\n"
                f"Источник: {source}\n"
                f"Причина: {reason}\n"
                f"Удалённое обновление: {remote_updated or '—'}\n"
                f"--- DIFF ---\n{diff or 'Нет различий'}\n"
            )
            report_file.write_text(report_text, encoding="utf-8")
            report_path = str(report_file)
            self._seen_conflicts[key] = report_path
        info = {
            "task": safe_task,
            "file": str(file_path),
            "diff_path": report_path,
            "remote_updated": remote_updated,
            "source": source,
            "reason": reason,
        }
        self._pending_conflicts.append(info)
        logger.warning("Projects sync conflict for %s (%s). Детали: %s", safe_task, reason, report_path)
        return info

    def consume_conflicts(self) -> List[Dict[str, Any]]:
        pending = list(self._pending_conflicts)
        self._pending_conflicts.clear()
        return pending

    @property
    def enabled(self) -> bool:
        return bool(self.config and self.config.enabled and self.token)

    def sync_task(self, task) -> bool:
        if not self.enabled:
            return False
        try:
            self._ensure_project_metadata()
        except Exception as exc:  # pragma: no cover - defensive log
            logger.warning("projects sync disabled: %s", exc)
            return False

        changed = False
        body = self._build_body(task)
        if not getattr(task, "project_item_id", None):
            item_id, draft_id = self._create_draft_issue(task, body)
            if item_id:
                task.project_item_id = item_id
                changed = True
            if draft_id:
                task.project_draft_id = draft_id
                changed = True
        else:
            self._update_draft_issue(task, body)

        if getattr(task, "project_item_id", None):
            self._update_fields(task)
        repo_changed = self._ensure_repo_issue(task, body)

        if changed or repo_changed:
            self._persist_metadata(task)
        if changed or repo_changed:
            self.last_push = datetime.now().strftime("%Y-%m-%d %H:%M")
        return changed or repo_changed

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_config(self) -> Optional[ProjectConfig]:
        data = _read_project_file(self.config_path)
        if not data:
            return None
        project = data.get("project") or {}
        fields_cfg = {}
        for alias, cfg in (data.get("fields") or {}).items():
            fields_cfg[alias] = FieldConfig(name=cfg.get("name", alias), options=cfg.get("options", {}))
        try:
            project_type = (project.get("type") or "repository").lower()
            owner = project["owner"]
            number = int(project.get("number", 1))
            repo = project.get("repo")
        except KeyError:
            return None
        enabled = project.get("enabled", True)
        return ProjectConfig(project_type=project_type, owner=owner, number=number, repo=repo, fields=fields_cfg, enabled=bool(enabled))

    def _graphql(self, query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        headers = {"Authorization": f"bearer {self.token}", "Accept": "application/vnd.github+json"}
        response = self.session.post(GRAPHQL_URL, json={"query": query, "variables": variables}, headers=headers, timeout=30)
        if response.status_code >= 400:
            raise RuntimeError(f"GitHub API error: {response.status_code} {response.text}")
        payload = response.json()
        if payload.get("errors"):
            raise RuntimeError(payload["errors"])
        return payload["data"]

    def _ensure_project_metadata(self) -> None:
        if self.project_id:
            return
        cfg = self.config
        if not cfg:
            raise RuntimeError("projects config missing")
        if cfg.project_type == "repository":
            if not cfg.repo:
                raise RuntimeError("repo is required for repository projects")
            query = self._repo_project_query()
            variables = {"owner": cfg.owner, "name": cfg.repo, "number": cfg.number}
            data = self._graphql(query, variables)
            node = (data.get("repository") or {}).get("projectV2")
        elif cfg.project_type == "organization":
            query = self._org_project_query()
            variables = {"login": cfg.owner, "number": cfg.number}
            data = self._graphql(query, variables)
            node = (data.get("organization") or {}).get("projectV2")
        else:  # user
            query = self._user_project_query()
            variables = {"login": cfg.owner, "number": cfg.number}
            data = self._graphql(query, variables)
            node = (data.get("user") or {}).get("projectV2")
        if not node:
            raise RuntimeError("project not found")
        self.project_id = node.get("id")
        field_nodes = ((node.get("fields") or {}).get("nodes") or [])
        self.project_fields = self._map_fields(field_nodes)

    def _repo_project_query(self) -> str:
        return (
            "query($owner:String!,$name:String!,$number:Int!){\n"
            "  repository(owner:$owner,name:$name){\n"
            "    projectV2(number:$number){\n"
            "      id title\n"
            "      fields(first:50){\n"
            "        nodes{\n"
            "          __typename\n"
            "          ... on ProjectV2FieldCommon { id name dataType }\n"
            "          ... on ProjectV2SingleSelectField { options { id name } }\n"
            "        }\n"
            "      }\n"
            "    }\n"
            "  }\n"
            "}"
        )

    def _org_project_query(self) -> str:
        return (
            "query($login:String!,$number:Int!){\n"
            "  organization(login:$login){\n"
            "    projectV2(number:$number){\n"
            "      id title\n"
            "      fields(first:50){\n"
            "        nodes{\n"
            "          __typename\n"
            "          ... on ProjectV2FieldCommon { id name dataType }\n"
            "          ... on ProjectV2SingleSelectField { options { id name } }\n"
            "        }\n"
            "      }\n"
            "    }\n"
            "  }\n"
            "}"
        )

    def _user_project_query(self) -> str:
        return (
            "query($login:String!,$number:Int!){\n"
            "  user(login:$login){\n"
            "    projectV2(number:$number){\n"
            "      id title\n"
            "      fields(first:50){\n"
            "        nodes{\n"
            "          __typename\n"
            "          ... on ProjectV2FieldCommon { id name dataType }\n"
            "          ... on ProjectV2SingleSelectField { options { id name } }\n"
            "        }\n"
            "      }\n"
            "    }\n"
            "  }\n"
            "}"
        )

    def _map_fields(self, nodes: Any) -> Dict[str, Dict[str, Any]]:
        result: Dict[str, Dict[str, Any]] = {}
        cfg_fields = self.config.fields if self.config else {}
        for alias, field_cfg in cfg_fields.items():
            match = next((n for n in nodes if n.get("name") == field_cfg.name), None)
            if not match:
                continue
            entry = {
                "id": match.get("id"),
                "typename": match.get("__typename"),
                "options": {},
                "reverse": {},
            }
            if match.get("__typename") == "ProjectV2SingleSelectField":
                entry["options" ] = {opt.get("name"): opt.get("id") for opt in (match.get("options") or [])}
                reverse = {}
                for status, option_name in field_cfg.options.items():
                    opt_id = entry["options"].get(option_name)
                    if opt_id:
                        reverse[opt_id] = status
                entry["reverse"] = reverse
            result[alias] = entry
        return result

    def _alias_by_field_id(self, field_id: str) -> Optional[str]:
        for alias, info in self.project_fields.items():
            if info.get("id") == field_id:
                return alias
        return None

    def _create_draft_issue(self, task, body: str) -> (Optional[str], Optional[str]):
        mutation = (
            "mutation($projectId:ID!,$title:String!,$body:String!){"
            "  addProjectV2DraftIssue(input:{projectId:$projectId,title:$title,body:$body}){"
            "    projectItem{ id content{ __typename ... on DraftIssue { id } } }"
            "  }"
            "}"
        )
        variables = {"projectId": self.project_id, "title": f"{task.id}: {task.title}", "body": body}
        try:
            data = self._graphql(mutation, variables)["addProjectV2DraftIssue"]
            item = (data or {}).get("projectItem") or {}
            draft = (item.get("content") or {}) if item else {}
            draft_id = draft.get("id") if draft.get("__typename") == "DraftIssue" else None
            return item.get("id"), draft_id
        except Exception as exc:  # pragma: no cover - network failure
            logger.warning("GitHub draft creation failed: %s", exc)
            return None, None

    def _ensure_draft_id(self, task) -> Optional[str]:
        if getattr(task, "project_draft_id", None):
            return task.project_draft_id
        query = (
            "query($item:ID!){ node(id:$item){ ... on ProjectV2Item { content { __typename ... on DraftIssue { id } } } } }"
        )
        try:
            data = self._graphql(query, {"item": task.project_item_id})
            node = (data.get("node") or {}).get("content") or {}
            if node.get("__typename") == "DraftIssue":
                task.project_draft_id = node.get("id")
        except Exception as exc:  # pragma: no cover - network failure
            logger.warning("Unable to fetch draft issue id: %s", exc)
        return task.project_draft_id

    def _update_draft_issue(self, task, body: str) -> None:
        draft_id = self._ensure_draft_id(task)
        if not draft_id:
            return
        mutation = (
            "mutation($projectId:ID!,$draftId:ID!,$title:String!,$body:String!){"
            "  updateProjectV2DraftIssue(input:{projectId:$projectId,draftIssueId:$draftId,title:$title,body:$body}){ draftIssue{ id } }"
            "}"
        )
        variables = {
            "projectId": self.project_id,
            "draftId": draft_id,
            "title": f"{task.id}: {task.title}",
            "body": body,
        }
        try:
            self._graphql(mutation, variables)
        except Exception as exc:  # pragma: no cover
            logger.warning("GitHub draft update failed: %s", exc)

    def _update_fields(self, task) -> None:
        for alias, field in self.project_fields.items():
            field_cfg = self.config.fields.get(alias) if self.config else None
            if not field_cfg:
                continue
            value = None
            if field["typename"] == "ProjectV2SingleSelectField":
                desired = field_cfg.options.get(task.status)
                option_id = field["options"].get(desired)
                if option_id:
                    value = {"singleSelectOptionId": option_id}
            elif field["typename"] == "ProjectV2NumberField":
                if alias == "progress":
                    value = {"number": task.calculate_progress()}
            else:  # text/datetime
                if alias == "domain":
                    value = {"text": task.domain or "-"}
                elif alias == "subtasks":
                    total = len(task.subtasks)
                    completed = sum(1 for st in task.subtasks if st.completed)
                    value = {"text": f"{completed}/{total}" if total else "-"}
            if value is None:
                continue
            mutation = (
                "mutation($projectId:ID!,$itemId:ID!,$fieldId:ID!,$value:ProjectV2FieldValue!){"
                "  updateProjectV2ItemFieldValue(input:{projectId:$projectId,itemId:$itemId,fieldId:$fieldId,value:$value}){ projectV2Item{ id } }"
                "}"
            )
            variables = {
                "projectId": self.project_id,
                "itemId": task.project_item_id,
                "fieldId": field["id"],
                "value": value,
            }
            try:
                self._graphql(mutation, variables)
            except Exception as exc:  # pragma: no cover
                logger.warning("Field update failed (%s): %s", alias, exc)

    def _persist_metadata(self, task, remote_updated: Optional[str] = None, source: str = "pull") -> bool:
        try:
            new_path = task.filepath
            old_path = getattr(task, "_source_path", new_path)
            old_mtime = getattr(task, "_source_mtime", None)
            existing_text = ""
            if Path(old_path).exists():
                existing_text = Path(old_path).read_text(encoding="utf-8")
            new_text = task.to_file_content()
            conflict_reason = None
            if remote_updated and self._local_is_newer(getattr(task, "updated", None), remote_updated):
                conflict_reason = "Локальные правки новее удалённых"
            elif existing_text and old_mtime is not None and Path(old_path).exists():
                current_mtime = Path(old_path).stat().st_mtime
                if current_mtime > old_mtime + 1e-6:
                    conflict_reason = "Файл обновлён локально после загрузки"
            if conflict_reason:
                self._record_conflict(getattr(task, "id", Path(old_path).stem), Path(old_path), existing_text, new_text, conflict_reason, remote_updated, source)
                return False
            new_path.parent.mkdir(parents=True, exist_ok=True)
            new_path.write_text(new_text, encoding="utf-8")
            if old_path != new_path and Path(old_path).exists():
                Path(old_path).unlink()
            task._source_path = new_path
            task._source_mtime = new_path.stat().st_mtime
            if remote_updated:
                task.project_remote_updated = remote_updated
            return True
        except Exception as exc:  # pragma: no cover
            logger.warning("Unable to persist project metadata: %s", exc)
        return False

    def _build_body(self, task) -> str:
        lines = [
            f"# {task.id}: {task.title}",
            "",
            f"- Status: {task.status}",
            f"- Domain: {task.domain or '—'}",
            f"- Progress: {task.calculate_progress()}%",
        ]
        if getattr(task, "description", ""):
            lines += ["", "## Description", task.description]
        if task.subtasks:
            lines += ["", "## Subtasks"]
            for sub in task.subtasks:
                mark = "x" if sub.completed else " "
                crit = "✓" if sub.criteria_confirmed else "·"
                tests = "✓" if sub.tests_confirmed else "·"
                blockers = "✓" if sub.blockers_resolved else "·"
                lines.append(f"- [{mark}] {sub.title} [criteria {crit} | tests {tests} | blockers {blockers}]")
        if getattr(task, "success_criteria", None):
            lines += ["", "## Success criteria", *[f"- {item}" for item in task.success_criteria]]
        if getattr(task, "risks", None):
            lines += ["", "## Risks", *[f"- {r}" for r in task.risks]]
        return "\n".join(lines).strip()

    def _ensure_repo_issue(self, task, body: str) -> bool:
        cfg = self.config
        if not cfg or cfg.project_type != "repository" or not cfg.repo:
            return False
        if not self.enabled:
            return False
        headers = {"Authorization": f"token {self.token}", "Accept": "application/vnd.github+json"}
        base_url = f"https://api.github.com/repos/{cfg.owner}/{cfg.repo}/issues"
        payload = {
            "title": f"{task.id}: {task.title}",
            "body": body,
        }
        changed = False
        if not getattr(task, "project_issue_number", None):
            resp = self._issue_request_with_retry("post", base_url, payload, headers)
            if resp.status_code >= 400:
                self._report_issue_error(task, resp)
                return False
            data = resp.json()
            task.project_issue_number = data.get("number")
            changed = True
        else:
            issue_url = f"{base_url}/{task.project_issue_number}"
            payload["state"] = "closed" if task.status == "OK" else "open"
            resp = self._issue_request_with_retry("patch", issue_url, payload, headers)
            if resp.status_code >= 400:
                self._report_issue_error(task, resp)
                return False
        return changed

    def _report_issue_error(self, task, response):
        message = f"GitHub issue error ({response.status_code}): {response.text[:120]}"
        logger.warning(message)
        setattr(task, "_sync_error", message)
        self._record_conflict(task.id, Path(task.filepath), task.to_file_content(), task.to_file_content(), message, None, "issues")

    def _issue_request_with_retry(self, method: str, url: str, payload: Dict[str, Any], headers: Dict[str, str]) -> requests.Response:
        attempt = 0
        delay = 1.0
        while True:
            attempt += 1
            resp = getattr(self.session, method)(url, json=payload, headers=headers, timeout=30)
            if resp.status_code < 500 or attempt >= 3:
                if resp.status_code >= 500:
                    logger.warning("issue sync retry #%s failed: %s %s", attempt, resp.status_code, resp.text)
                return resp
            logger.warning("issue sync retry #%s due to %s", attempt, resp.status_code)
            jitter = random.uniform(0, delay)
            time.sleep(delay + jitter)
            delay *= 2

    # ------------------------------------------------------------------
    # Pull from GitHub → local files
    # ------------------------------------------------------------------

    def pull_task_fields(self, task) -> bool:
        if not self.enabled or not getattr(task, "project_item_id", None):
            return False
        try:
            self._ensure_project_metadata()
        except Exception as exc:  # pragma: no cover
            logger.warning("projects metadata unavailable: %s", exc)
            return False
        data = self._fetch_remote_state(task.project_item_id)
        if not data:
            return False
        updates: Dict[str, Any] = {}
        if data.get("status") and data["status"] != task.status:
            updates["status"] = data["status"]
        if data.get("progress") is not None and data["progress"] != task.progress:
            updates["progress"] = data["progress"]
        if data.get("domain") and data["domain"] != task.domain:
            updates["domain"] = data["domain"]
        if not updates:
            return False
        remote_updated = data.get("remote_updated")
        snapshot = {
            "status": task.status,
            "progress": task.progress,
            "domain": task.domain,
            "project_remote_updated": getattr(task, "project_remote_updated", None),
        }
        for key, value in updates.items():
            setattr(task, key, value)
        task.project_remote_updated = remote_updated or snapshot["project_remote_updated"]
        persisted = self._persist_metadata(task, remote_updated, source="pull")
        if not persisted:
            for key, value in snapshot.items():
                setattr(task, key, value)
            return False
        self.last_pull = datetime.now().strftime("%Y-%m-%d %H:%M")
        return True

    def _fetch_remote_state(self, item_id: str) -> Dict[str, Any]:
        cfg_fields = self.config.fields if self.config else {}
        field_aliases = []
        variables: Dict[str, Any] = {"item": item_id}
        query_sections = []
        if "status" in cfg_fields:
            variables["statusName"] = cfg_fields["status"].name
            query_sections.append(
                "status: fieldValueByName(name:$statusName){ ... on ProjectV2ItemFieldSingleSelectValue { optionId } }"
            )
        if "progress" in cfg_fields:
            variables["progressName"] = cfg_fields["progress"].name
            query_sections.append(
                "progress: fieldValueByName(name:$progressName){ ... on ProjectV2ItemFieldNumberValue { number } }"
            )
        if "domain" in cfg_fields:
            variables["domainName"] = cfg_fields["domain"].name
            query_sections.append(
                "domain: fieldValueByName(name:$domainName){ ... on ProjectV2ItemFieldTextValue { text } }"
            )
        if not query_sections:
            return {}
        query = (
            "query($item:ID!,$statusName:String,$progressName:String,$domainName:String){"
            "  node(id:$item){"
            "    ... on ProjectV2Item {"
            f"      {' '.join(query_sections)} updatedAt"
            "    }"
            "  }"
            "}"
        )
        data = self._graphql(query, variables)
        node = data.get("node") or {}
        result: Dict[str, Any] = {}
        if node.get("updatedAt"):
            result["remote_updated"] = node.get("updatedAt")
        status_field = node.get("status")
        if status_field and cfg_fields.get("status"):
            option_id = status_field.get("optionId")
            status = (self.project_fields.get("status") or {}).get("reverse", {}).get(option_id)
            if status:
                result["status"] = status
        progress_field = node.get("progress")
        if progress_field and progress_field.get("number") is not None:
            result["progress"] = int(progress_field.get("number"))
        domain_field = node.get("domain")
        if domain_field and domain_field.get("text"):
            result["domain"] = domain_field.get("text").strip()
        return result

    def _lookup_item_timestamp(self, item_id: str) -> Optional[str]:
        query = "query($item:ID!){ node(id:$item){ ... on ProjectV2Item { updatedAt } } }"
        try:
            data = self._graphql(query, {"item": item_id})
            node = data.get("node") or {}
            return node.get("updatedAt")
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Webhook handling
    # ------------------------------------------------------------------

    def handle_webhook(self, body: str, signature: Optional[str], secret: Optional[str]) -> Optional[str]:
        if not self.enabled:
            return None
        payload_bytes = body.encode()
        if secret:
            if not signature or not signature.startswith("sha256="):
                raise ValueError("signature missing for webhook")
            expected = "sha256=" + hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(expected, signature):
                raise ValueError("invalid signature")
        try:
            payload = json.loads(body)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid payload: {exc}")

        item = payload.get("projects_v2_item") or {}
        item_id = item.get("node_id") or item.get("id")
        if not item_id:
            return None

        try:
            self._ensure_project_metadata()
        except Exception as exc:  # pragma: no cover
            logger.warning("projects metadata unavailable: %s", exc)
            return None

        if self.project_id and item.get("project_node_id") and item["project_node_id"] != self.project_id:
            return None

        change = (payload.get("changes") or {}).get("field_value")
        if not change:
            return None
        field_id = change.get("field_node_id")
        alias = self._alias_by_field_id(field_id) if field_id else None
        if not alias:
            return None

        updates: Dict[str, Any] = {}
        if alias == "status":
            option_id = change.get("single_select_option_id") or (change.get("value") or {}).get("singleSelectOptionId")
            status = None
            if option_id:
                status = (self.project_fields.get(alias) or {}).get("reverse", {}).get(option_id)
            if status:
                updates["status"] = status
        elif alias == "progress":
            number = change.get("number")
            if number is None:
                number = (change.get("value") or {}).get("number")
            if number is not None:
                updates["progress"] = int(number)
        elif alias == "domain":
            text = change.get("text") or (change.get("value") or {}).get("text")
            if text:
                updates["domain"] = text.strip()
        if not updates:
            return None
        remote_updated = item.get("updated_at") or payload.get("updated_at")
        if not remote_updated:
            remote_updated = self._lookup_item_timestamp(item_id)
        return self._update_local_metadata(item_id, updates, remote_updated)

    def _update_local_metadata(self, item_id: str, updates: Dict[str, Any], remote_updated: Optional[str] = None) -> Dict[str, Any]:
        tasks_dir = Path(".tasks")
        if not tasks_dir.exists():
            return {}
        for file in tasks_dir.rglob("TASK-*.task"):
            content = file.read_text(encoding="utf-8")
            parts = content.split("---", 2)
            if len(parts) < 3:
                continue
            metadata = yaml.safe_load(parts[1]) or {}
            if metadata.get("project_item_id") != item_id:
                continue
            changed = False
            if "status" in updates and metadata.get("status") != updates["status"]:
                metadata["status"] = updates["status"]
                changed = True
            if "progress" in updates and metadata.get("progress") != updates["progress"]:
                metadata["progress"] = updates["progress"]
                changed = True
            if "domain" in updates and updates["domain"]:
                metadata["domain"] = updates["domain"]
                changed = True
            if changed:
                metadata["project_remote_updated"] = remote_updated or metadata.get("project_remote_updated")
                header = yaml.dump(metadata, allow_unicode=True, default_flow_style=False).strip()
                body = parts[2].lstrip("\n")
                new_text = f"---\n{header}\n---\n{body}"
                if self._local_is_newer(metadata.get("updated"), remote_updated):
                    info = self._record_conflict(metadata.get("id", file.stem), file, content, new_text, "Локальные правки новее удалённых", remote_updated, "webhook")
                    return {"conflict": info}
                file.write_text(new_text, encoding="utf-8")
                return {"updated": str(file)}
            return {}
        return {}


def get_projects_sync() -> ProjectsSync:
    global _PROJECTS_SYNC
    if _PROJECTS_SYNC is None:
        _PROJECTS_SYNC = ProjectsSync()
    return _PROJECTS_SYNC


def reload_projects_sync() -> ProjectsSync:
    global _PROJECTS_SYNC
    _PROJECTS_SYNC = ProjectsSync()
    return _PROJECTS_SYNC


def update_projects_enabled(enabled: bool) -> bool:
    data = _read_project_file()
    project = data.get("project") or {}
    project["enabled"] = bool(enabled)
    data["project"] = project
    _write_project_file(data)
    reload_projects_sync()
    return bool(enabled)


def update_project_target(project_type: str, owner: str, repo: Optional[str], number: int) -> None:
    data = _read_project_file()
    project = data.get("project") or {}
    project["type"] = project_type
    project["owner"] = owner
    project["number"] = int(number)
    if project_type == "repository":
        project["repo"] = repo or ""
    else:
        project.pop("repo", None)
    data["project"] = project
    _write_project_file(data)
    reload_projects_sync()
