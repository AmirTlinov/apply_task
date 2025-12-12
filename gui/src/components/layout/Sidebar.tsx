import {
  LayoutList,
  LayoutGrid,
  Clock,
  BarChart3,
  Settings,
  FolderOpen,
  PanelLeftClose,
  PanelLeftOpen,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Link } from "@tanstack/react-router";

interface NavItem {
  to: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  shortcut?: string;
}

const navItems: NavItem[] = [
  { to: "/", label: "Tasks", icon: LayoutList, shortcut: "g l" },
  { to: "/board", label: "Board", icon: LayoutGrid, shortcut: "g b" },
  { to: "/timeline", label: "Timeline", icon: Clock, shortcut: "g t" },
  { to: "/dashboard", label: "Dashboard", icon: BarChart3, shortcut: "g d" },
];

interface SidebarProps {
  projectName?: string;
  collapsed?: boolean;
  onToggle?: () => void;
}

export function Sidebar({
  projectName,
  collapsed = false,
  onToggle,
}: SidebarProps) {
  return (
    <aside
      className={cn(
        "flex h-full flex-col shrink-0 border-r border-border bg-background-subtle transition-all duration-300 ease-[cubic-bezier(0.32,0.72,0,1)] overflow-hidden",
        collapsed ? "w-[64px]" : "w-[240px]"
      )}
    >
      {/* Header */}
      <div
        className={cn(
          "flex items-center gap-3 min-h-[64px] border-b border-border",
          collapsed ? "px-3 justify-center" : "px-4"
        )}
      >
        {/* Logo */}
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-blue-600 text-white shadow-sm shadow-blue-500/20">
          <span className="font-bold text-[13px] tracking-tight">AT</span>
        </div>

        {!collapsed && (
          <div className="flex flex-1 min-w-0 flex-col overflow-hidden">
            <span className="truncate font-semibold text-[15px] leading-tight text-foreground tracking-tight">
              Apply Task
            </span>
            {projectName && (
              <span className="truncate text-xs text-foreground-muted mt-0.5">
                {projectName}
              </span>
            )}
          </div>
        )}

        {!collapsed && onToggle && (
          <Button
            variant="ghost"
            size="icon"
            onClick={onToggle}
            className="h-8 w-8 text-foreground-muted hover:text-foreground"
            title="Collapse sidebar"
          >
            <PanelLeftClose className="h-[18px] w-[18px]" />
          </Button>
        )}

        {collapsed && onToggle && (
          <div className="absolute left-[60px] top-[22px] z-50">
            <Button
              variant="outline"
              size="icon"
              onClick={onToggle}
              className="h-6 w-6 rounded-md border-border bg-background shadow-sm hover:bg-background-hover"
              title="Expand sidebar"
            >
              <PanelLeftOpen className="h-3.5 w-3.5 text-foreground-muted" />
            </Button>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto p-2 space-y-0.5">
        {navItems.map((item) => (
          <NavButton
            key={item.to}
            item={item}
            collapsed={collapsed}
          />
        ))}
      </nav>

      {/* Footer */}
      <div className="p-2 border-t border-border space-y-0.5">
        <NavButton
          item={{ to: "/projects", label: "Projects", icon: FolderOpen }}
          collapsed={collapsed}
        />
        <NavButton
          item={{ to: "/settings", label: "Settings", icon: Settings }}
          collapsed={collapsed}
        />
      </div>
    </aside>
  );
}

interface NavButtonProps {
  item: NavItem;
  collapsed: boolean;
}

function NavButton({ item, collapsed }: NavButtonProps) {
  const Icon = item.icon;

  return (
    <Link
      to={item.to}
      title={collapsed ? item.label : undefined}
      activeProps={{
        className: "bg-primary-subtle text-primary"
      }}
      inactiveProps={{
        className: "text-foreground-muted hover:bg-background-hover hover:text-foreground"
      }}
      className={cn(
        "group relative flex w-full items-center gap-3 rounded-lg text-sm font-medium transition-colors outline-none focus-visible:ring-2 focus-visible:ring-primary",
        collapsed ? "justify-center px-2 py-2.5" : "px-3 py-2.5"
      )}
    >
      {({ isActive }) => (
        <>
          {/* Active Indicator */}
          {isActive && (
            <span className="absolute left-0 top-1/2 h-5 w-[3px] -translate-y-1/2 rounded-r-sm bg-primary" />
          )}

          <Icon
            className={cn(
              "shrink-0 transition-transform duration-200",
              isActive ? "text-primary" : "text-foreground-muted group-hover:text-foreground",
              collapsed ? "h-5 w-5" : "h-[18px] w-[18px]"
            )}
          />

          {!collapsed && (
            <>
              <span className="flex-1 truncate text-left">{item.label}</span>
              {item.shortcut && (
                <kbd className="inline-flex h-5 items-center rounded border border-border bg-background px-1.5 font-mono text-[10px] font-medium text-foreground-subtle opacity-100">
                  {item.shortcut}
                </kbd>
              )}
            </>
          )}
        </>
      )}
    </Link>
  );
}