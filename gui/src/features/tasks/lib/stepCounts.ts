import type { Step, TaskNode } from "@/types/task";

export interface StepCounts {
  total: number;
  done: number;
}

type StepLike = Pick<Step, "completed"> & {
  plan?: {
    tasks?: TaskNode[];
  };
};

export function countStepTree(steps?: StepLike[] | null): StepCounts {
  const stack: StepLike[] = Array.isArray(steps) ? [...steps] : [];
  let total = 0;
  let done = 0;

  while (stack.length > 0) {
    const current = stack.pop();
    if (!current) continue;
    total += 1;
    if (current.completed) done += 1;
    const tasks = current.plan?.tasks ?? [];
    for (let tIdx = tasks.length - 1; tIdx >= 0; tIdx -= 1) {
      const task = tasks[tIdx];
      const childSteps = task?.steps ?? [];
      for (let sIdx = childSteps.length - 1; sIdx >= 0; sIdx -= 1) {
        stack.push(childSteps[sIdx]);
      }
    }
  }

  return { total, done };
}
