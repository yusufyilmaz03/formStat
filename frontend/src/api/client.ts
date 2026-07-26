import axios from "axios";
import type { Form, FormSummary, Question, ResponseOut } from "../types";

const api = axios.create({ baseURL: "/api" });

// ---- Forms ----
export const listForms = () => api.get<FormSummary[]>("/forms").then((r) => r.data);
export const getForm = (id: number) => api.get<Form>(`/forms/${id}`).then((r) => r.data);
export const createForm = (payload: { title: string; description: string; questions: Question[] }) =>
  api.post<Form>("/forms", payload).then((r) => r.data);
export const updateForm = (
  id: number,
  payload: { title?: string; description?: string; questions?: Question[] }
) => api.put<Form>(`/forms/${id}`, payload).then((r) => r.data);
export const deleteForm = (id: number) => api.delete(`/forms/${id}`);

// ---- Responses ----
export const listResponses = (formId: number) =>
  api.get<ResponseOut[]>(`/forms/${formId}/responses`).then((r) => r.data);
export const addResponse = (
  formId: number,
  answers: { question_id: number; value: unknown }[],
  source = "manual"
) => api.post(`/forms/${formId}/responses`, { source, answers }).then((r) => r.data);
export const deleteResponse = (formId: number, respId: number) =>
  api.delete(`/forms/${formId}/responses/${respId}`);
export const clearResponses = (formId: number) => api.delete(`/forms/${formId}/responses`);

export const importPreview = (formId: number, file: File) => {
  const fd = new FormData();
  fd.append("file", file);
  return api
    .post<{ import_id: string; columns: string[]; row_count: number; sample: Record<string, string>[] }>(
      `/forms/${formId}/responses/import/preview`,
      fd
    )
    .then((r) => r.data);
};
export const importApply = (
  formId: number,
  importId: string,
  mappings: { column: string; question_id: number }[]
) =>
  api
    .post<{ imported: number }>(`/forms/${formId}/responses/import`, {
      import_id: importId,
      mappings,
    })
    .then((r) => r.data);

// ---- Analysis ----
export const getOverview = (formId: number) =>
  api.get(`/forms/${formId}/analysis/overview`).then((r) => r.data);
export const runTest = (formId: number, a: number, b: number) =>
  api.post(`/forms/${formId}/analysis/test`, { question_a: a, question_b: b }).then((r) => r.data);
export const runCrosstab = (formId: number, a: number, b: number) =>
  api.post(`/forms/${formId}/analysis/crosstab`, { question_a: a, question_b: b }).then((r) => r.data);
export const runRegression = (formId: number, target: number, predictors: number[]) =>
  api.post(`/forms/${formId}/analysis/regression`, { target, predictors }).then((r) => r.data);
export const runSegmentation = (formId: number, questions: number[], nClusters: number | null) =>
  api
    .post(`/forms/${formId}/analysis/segmentation`, { questions, n_clusters: nClusters })
    .then((r) => r.data);
export const getInsights = (formId: number) =>
  api.get(`/forms/${formId}/analysis/insights`).then((r) => r.data);

// ---- Google ----
export const googleStatus = () =>
  api.get<{ client_configured: boolean; connected: boolean }>("/google/status").then((r) => r.data);
export const googleAuthUrl = () => api.get<{ url: string }>("/google/auth").then((r) => r.data);
export const googleDisconnect = () => api.post("/google/disconnect").then((r) => r.data);
export const googleExport = (formId: number) =>
  api.post(`/forms/${formId}/google/export`).then((r) => r.data);
export const googleSync = (formId: number) =>
  api.post(`/forms/${formId}/google/sync`).then((r) => r.data);

export const reportCsvUrl = (formId: number) => `/api/forms/${formId}/report/export.csv`;

export default api;
