import type { Question, QuestionType } from "../types";

export type Role = "numeric" | "categorical" | "multi" | "text";

export function roleOf(type: QuestionType): Role {
  if (type === "number" || type === "linear_scale") return "numeric";
  if (type === "single_choice" || type === "dropdown") return "categorical";
  if (type === "multi_choice") return "multi";
  return "text";
}

export const byRole = (questions: Question[], ...roles: Role[]) =>
  questions.filter((q) => roles.includes(roleOf(q.type)));
