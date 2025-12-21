import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

type MarkdownBlock =
  | { type: "heading"; level: 1 | 2 | 3 | 4 | 5 | 6; text: string }
  | { type: "paragraph"; text: string }
  | { type: "ul"; items: Array<{ text: string; checked?: boolean; done?: boolean }> }
  | { type: "ol"; items: Array<{ text: string }> }
  | { type: "code"; language?: string; code: string }
  | { type: "hr" };

function normalizeNewlines(input: string): string {
  return String(input ?? "").replace(/\r\n/g, "\n");
}

function isHr(line: string): boolean {
  const trimmed = line.trim();
  return /^(-{3,}|_{3,}|\*{3,})$/.test(trimmed);
}

function parseMarkdownBlocks(content: string): MarkdownBlock[] {
  const lines = normalizeNewlines(content).split("\n");
  const blocks: MarkdownBlock[] = [];

  let i = 0;
  while (i < lines.length) {
    const line = lines[i];

    if (!line.trim()) {
      i += 1;
      continue;
    }

    if (line.startsWith("```")) {
      const language = line.slice(3).trim() || undefined;
      const codeLines: string[] = [];
      i += 1;
      while (i < lines.length && !lines[i].startsWith("```")) {
        codeLines.push(lines[i]);
        i += 1;
      }
      // Skip closing fence if present.
      if (i < lines.length && lines[i].startsWith("```")) i += 1;
      blocks.push({ type: "code", language, code: codeLines.join("\n") });
      continue;
    }

    if (isHr(line)) {
      blocks.push({ type: "hr" });
      i += 1;
      continue;
    }

    const headingMatch = line.match(/^(#{1,6})\s+(.*)$/);
    if (headingMatch) {
      const level = headingMatch[1].length as 1 | 2 | 3 | 4 | 5 | 6;
      const text = headingMatch[2].trim();
      blocks.push({ type: "heading", level, text });
      i += 1;
      continue;
    }

    const ulItemMatch = line.match(/^[-*]\s+(.*)$/);
    const olItemMatch = line.match(/^\d+\.\s+(.*)$/);

    if (ulItemMatch) {
      const items: Array<{ text: string; checked?: boolean; done?: boolean }> = [];
      while (i < lines.length) {
        const currentLine = lines[i];
        const match = currentLine.match(/^[-*]\s+(.*)$/);
        if (!match) break;
        const itemText = match[1];
        const checkboxMatch = itemText.match(/^\[([ xX])\]\s+(.*)$/);
        if (checkboxMatch) {
          const done = checkboxMatch[1].toLowerCase() === "x";
          items.push({ text: checkboxMatch[2], checked: true, done });
        } else {
          items.push({ text: itemText });
        }
        i += 1;
      }
      blocks.push({ type: "ul", items });
      continue;
    }

    if (olItemMatch) {
      const items: Array<{ text: string }> = [];
      while (i < lines.length) {
        const currentLine = lines[i];
        const match = currentLine.match(/^\d+\.\s+(.*)$/);
        if (!match) break;
        items.push({ text: match[1] });
        i += 1;
      }
      blocks.push({ type: "ol", items });
      continue;
    }

    const paragraphLines: string[] = [];
    while (i < lines.length) {
      const currentLine = lines[i];
      if (!currentLine.trim()) break;
      if (currentLine.startsWith("```")) break;
      if (isHr(currentLine)) break;
      if (/^(#{1,6})\s+/.test(currentLine)) break;
      if (/^[-*]\s+/.test(currentLine)) break;
      if (/^\d+\.\s+/.test(currentLine)) break;
      paragraphLines.push(currentLine);
      i += 1;
    }
    blocks.push({ type: "paragraph", text: paragraphLines.join("\n") });
  }

  return blocks;
}

function renderInline(text: string): ReactNode[] {
  const out: ReactNode[] = [];
  const parts = String(text ?? "").split("`");
  for (let idx = 0; idx < parts.length; idx += 1) {
    const part = parts[idx];
    if (idx % 2 === 1) {
      out.push(
        <code
          key={`code-${idx}`}
          className="rounded border border-border bg-background px-1 py-0.5 font-mono text-[12px] text-foreground"
        >
          {part}
        </code>
      );
    } else if (part) {
      out.push(<span key={`text-${idx}`}>{part}</span>);
    }
  }
  return out;
}

export function Markdown({ content, className }: { content: string; className?: string }) {
  const blocks = parseMarkdownBlocks(content);

  return (
    <div className={cn("text-sm leading-relaxed text-foreground", className)}>
      {blocks.map((block, idx) => {
        switch (block.type) {
          case "heading": {
            const Tag = (`h${Math.min(block.level + 1, 6)}` as unknown) as "h2";
            const size =
              block.level <= 2
                ? "text-sm font-semibold"
                : "text-xs font-semibold uppercase tracking-wide text-foreground-muted";
            return (
              <Tag key={idx} className={cn("mt-4 first:mt-0", size)}>
                {block.text}
              </Tag>
            );
          }
          case "paragraph":
            return (
              <p key={idx} className="mt-2 whitespace-pre-wrap first:mt-0">
                {renderInline(block.text)}
              </p>
            );
          case "ul":
            return (
              <ul key={idx} className="mt-2 space-y-1 pl-5 first:mt-0">
                {block.items.map((item, itemIdx) => (
                  <li key={itemIdx} className="text-sm">
                    <div className="flex items-start gap-2">
                      {item.checked ? (
                        <span
                          aria-hidden
                          className={cn(
                            "mt-[3px] inline-flex h-4 w-4 items-center justify-center rounded border",
                            item.done
                              ? "border-status-ok/40 bg-status-ok/10 text-status-ok"
                              : "border-border bg-background text-foreground-subtle"
                          )}
                        >
                          {item.done ? "✓" : ""}
                        </span>
                      ) : null}
                      <div className={cn("min-w-0", item.done && "text-foreground-muted")}>
                        {renderInline(item.text)}
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            );
          case "ol":
            return (
              <ol key={idx} className="mt-2 list-decimal space-y-1 pl-5 first:mt-0">
                {block.items.map((item, itemIdx) => (
                  <li key={itemIdx} className="text-sm">
                    {renderInline(item.text)}
                  </li>
                ))}
              </ol>
            );
          case "code":
            return (
              <pre
                key={idx}
                className="custom-scrollbar mt-2 overflow-x-auto rounded-lg border border-border bg-background p-3 text-xs leading-relaxed first:mt-0"
              >
                <code>{block.code}</code>
              </pre>
            );
          case "hr":
            return <hr key={idx} className="my-4 border-border" />;
          default:
            return null;
        }
      })}
    </div>
  );
}

