import {
  LayoutList,
  LayoutGrid,
  ListTodo,
  Clock,
  BarChart3,
  Settings,
  FolderOpen,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Link } from "@tanstack/react-router";

interface NavItem {
  to: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  shortcut?: string;
}

const navItems: NavItem[] = [
  { to: "/plans", label: "Plans", icon: LayoutList, shortcut: "g l" },
  { to: "/", label: "Tasks", icon: ListTodo, shortcut: "g t" },
  { to: "/board", label: "Board", icon: LayoutGrid, shortcut: "g b" },
  { to: "/timeline", label: "Timeline", icon: Clock, shortcut: "g i" },
  { to: "/dashboard", label: "Dashboard", icon: BarChart3, shortcut: "g d" },
];

interface SidebarProps {
  className?: string;
  onNavigate?: () => void;
}

export function Sidebar({
  className,
  onNavigate,
}: SidebarProps) {
  const collapsed = true;
  return (
    <aside
      className={cn(
        "flex h-full flex-col shrink-0 border-r border-border bg-background-subtle transition-all duration-300 ease-sidebar overflow-hidden",
        "w-[var(--density-sidebar-collapsed-w)]",
        className
      )}
    >
      {/* Header */}
      <div
        className={cn(
          "flex items-center gap-3 min-h-[var(--density-sidebar-header-min-h)] border-b border-border",
          "px-3 justify-center"
        )}
      >
        {/* Logo */}
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-blue-600 text-white shadow-sm shadow-blue-500/20">
          <span className="font-bold text-[13px] tracking-tight">AT</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto p-2 space-y-0.5">
        {navItems.map((item) => (
          <NavButton
            key={item.to}
            item={item}
            collapsed={collapsed}
            onNavigate={onNavigate}
          />
        ))}
      </nav>

      {/* Footer */}
      <div className="p-2 border-t border-border space-y-0.5">
        <NavButton
          item={{ to: "/projects", label: "Projects", icon: FolderOpen, shortcut: "g p" }}
          collapsed={collapsed}
          onNavigate={onNavigate}
        />
        <NavButton
          item={{ to: "/settings", label: "Settings", icon: Settings, shortcut: "g s" }}
          collapsed={collapsed}
          onNavigate={onNavigate}
        />
      </div>
    </aside>
  );
}

interface NavButtonProps {
  item: NavItem;
  collapsed: boolean;
  onNavigate?: () => void;
}

function NavButton({ item, collapsed, onNavigate }: NavButtonProps) {
  const Icon = item.icon;

  return (
    <Link
      to={item.to}
      onClick={() => onNavigate?.()}
      title={collapsed ? item.label : undefined}
      activeProps={{
        className: "bg-primary-subtle text-primary"
      }}
      inactiveProps={{
        className: "text-foreground-muted hover:bg-background-hover hover:text-foreground"
      }}
      className={cn(
        "group relative flex w-full items-center gap-3 rounded-lg text-sm font-medium transition-colors outline-none focus-visible:ring-2 focus-visible:ring-primary",
        collapsed ? "justify-center px-2 py-2" : "px-3 py-2"
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
                <kbd className="inline-flex h-5 items-center rounded border border-border bg-background px-1.5 font-mono text-[10px] font-medium text-foreground-subtle opacity-0 transition-opacity duration-150 group-hover:opacity-100">
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
