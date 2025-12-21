import React from "react";
import { FatalErrorScreen } from "@/components/common/FatalErrorScreen";

interface AppErrorBoundaryProps {
  children: React.ReactNode;
}

interface AppErrorBoundaryState {
  error: unknown | null;
}

export class AppErrorBoundary extends React.Component<
  AppErrorBoundaryProps,
  AppErrorBoundaryState
> {
  state: AppErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: unknown): AppErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: unknown) {
    void error;
  }

  render() {
    if (this.state.error) {
      return <FatalErrorScreen error={this.state.error} />;
    }
    return this.props.children;
  }
}

