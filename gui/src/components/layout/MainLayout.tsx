import { useState, type ReactNode } from "react";
import { Sidebar } from "./Sidebar";

interface MainLayoutProps {
  children: ReactNode;
  projectName?: string;
}

export function MainLayout({
  children,
  projectName,
}: MainLayoutProps) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background">
      {/* Sidebar */}
      <Sidebar
        projectName={projectName}
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
      />

      {/* Main Content Area */}
      <main className="flex flex-1 flex-col overflow-hidden min-w-0">
        {children}
      </main>
    </div>
  );
}

export { Sidebar } from "./Sidebar";
export { Header } from "./Header";