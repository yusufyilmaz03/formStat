export type QuestionType =
  | "short_text"
  | "long_text"
  | "single_choice"
  | "multi_choice"
  | "dropdown"
  | "linear_scale"
  | "number"
  | "date"
  | "email";

export interface Question {
  id?: number;
  type: QuestionType;
  title: string;
  required?: boolean;
  options?: string[] | null;
  scale_min?: number | null;
  scale_max?: number | null;
  order?: number;
}

export interface Form {
  id: number;
  title: string;
  description: string;
  created_at: string;
  google_form_id: string | null;
  google_responder_uri: string | null;
  published: boolean;
  questions: Question[];
}

export interface FormSummary {
  id: number;
  title: string;
  description: string;
  created_at: string;
  google_form_id: string | null;
  published: boolean;
  question_count: number;
  response_count: number;
}

export interface AnswerOut {
  question_id: number;
  value_text: string | null;
  value_number: number | null;
  value_options: string[] | null;
}

export interface ResponseOut {
  id: number;
  source: string;
  submitted_at: string | null;
  created_at: string;
  answers: AnswerOut[];
}

export const QUESTION_TYPE_LABELS: Record<QuestionType, string> = {
  short_text: "Kısa metin",
  long_text: "Uzun metin",
  single_choice: "Tek seçim",
  multi_choice: "Çoklu seçim",
  dropdown: "Açılır liste",
  linear_scale: "Ölçek (1–n)",
  number: "Sayı",
  date: "Tarih",
  email: "E-posta",
};

export const CHOICE_TYPES: QuestionType[] = ["single_choice", "multi_choice", "dropdown"];
