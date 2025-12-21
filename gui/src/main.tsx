import React from "react";
import ReactDOM from "react-dom/client";
import "@/styles/globals.css";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { FatalErrorScreen } from "@/components/common/FatalErrorScreen";
import { AppErrorBoundary } from "@/components/common/AppErrorBoundary";

const queryClient = new QueryClient();

const rootEl = document.getElementById("root");
if (!rootEl) {
  throw new Error("Root element #root not found");
}

const root = ReactDOM.createRoot(rootEl);

function renderApp(node: React.ReactNode) {
  document.getElementById("boot-splash")?.remove();
  root.render(
    <React.StrictMode>
      <QueryClientProvider client={queryClient}>{node}</QueryClientProvider>
    </React.StrictMode>
  );
}

renderApp(
  <div className="flex h-full w-full items-center justify-center bg-background text-sm text-foreground-muted">
    Loading…
  </div>
);

window.addEventListener("error", (e) => {
  renderApp(<FatalErrorScreen error={e.error || e.message} />);
});

window.addEventListener("unhandledrejection", (e) => {
  renderApp(<FatalErrorScreen error={e.reason} />);
});

import("./router")
  .then(async ({ router }) => {
    const { RouterProvider } = await import("@tanstack/react-router");
    renderApp(
      <AppErrorBoundary>
        <RouterProvider router={router} />
      </AppErrorBoundary>
    );
  })
  .catch((err) => {
    renderApp(<FatalErrorScreen error={err} />);
  });
