import type { Question } from "../../types";
import { roleOf } from "../../lib/roles";

const ROLE_TAG: Record<string, string> = {
  numeric: "sayısal",
  categorical: "kategorik",
  multi: "çoklu",
  text: "metin",
};

export function QuestionSelect({
  questions,
  value,
  onChange,
  placeholder = "— soru seç —",
}: {
  questions: Question[];
  value: number | null;
  onChange: (v: number | null) => void;
  placeholder?: string;
}) {
  return (
    <select value={value ?? ""} onChange={(e) => onChange(e.target.value ? Number(e.target.value) : null)}>
      <option value="">{placeholder}</option>
      {questions.map((q) => (
        <option key={q.id} value={q.id}>
          {q.title} ({ROLE_TAG[roleOf(q.type)]})
        </option>
      ))}
    </select>
  );
}
