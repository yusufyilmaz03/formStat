import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import {
  addResponse,
  clearResponses,
  deleteResponse,
  getForm,
  googleSync,
  importApply,
  importPreview,
  listResponses,
  reportCsvUrl,
} from "../api/client";
import FormHeader from "../components/FormHeader";
import type { AnswerOut, Form, ResponseOut } from "../types";

function displayAnswer(a?: AnswerOut): string {
  if (!a) return "";
  if (a.value_options && a.value_options.length) return a.value_options.join(", ");
  if (a.value_text != null && a.value_text !== "") return a.value_text;
  if (a.value_number != null) return String(a.value_number);
  return "";
}

export default function ResponsesPage() {
  const { id } = useParams();
  const formId = Number(id);
  const [form, setForm] = useState<Form | null>(null);
  const [responses, setResponses] = useState<ResponseOut[]>([]);
  const [msg, setMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [showManual, setShowManual] = useState(false);

  // CSV import state
  const [preview, setPreview] = useState<{ import_id: string; columns: string[]; row_count: number } | null>(null);
  const [mapping, setMapping] = useState<Record<string, number | 0>>({});

  const load = async () => {
    const [f, rs] = await Promise.all([getForm(formId), listResponses(formId)]);
    setForm(f);
    setResponses(rs);
  };
  useEffect(() => {
    load();
  }, [formId]);

  const answerMap = useMemo(() => {
    return responses.map((r) => {
      const m: Record<number, AnswerOut> = {};
      r.answers.forEach((a) => (m[a.question_id] = a));
      return m;
    });
  }, [responses]);

  const onFile = async (file: File) => {
    setMsg(null);
    try {
      const p = await importPreview(formId, file);
      setPreview(p);
      // otomatik eşleme: aynı isimli sütun -> soru
      const auto: Record<string, number> = {};
      p.columns.forEach((col) => {
        const q = form?.questions.find((qq) => qq.title.toLowerCase() === col.toLowerCase());
        if (q?.id) auto[col] = q.id;
      });
      setMapping(auto);
    } catch (e: any) {
      setMsg(e?.response?.data?.detail || "CSV okunamadı.");
    }
  };

  const applyImport = async () => {
    if (!preview) return;
    const mappings = Object.entries(mapping)
      .filter(([, qid]) => qid)
      .map(([column, question_id]) => ({ column, question_id: question_id as number }));
    if (!mappings.length) {
      setMsg("En az bir sütunu bir soruyla eşle.");
      return;
    }
    setBusy(true);
    try {
      const res = await importApply(formId, preview.import_id, mappings);
      setMsg(`${res.imported} cevap içe aktarıldı ✓`);
      setPreview(null);
      await load();
    } catch (e: any) {
      setMsg(e?.response?.data?.detail || "İçe aktarma hatası.");
    } finally {
      setBusy(false);
    }
  };

  const sync = async () => {
    setBusy(true);
    setMsg(null);
    try {
      const res = await googleSync(formId);
      setMsg(`Google'dan ${res.imported} yeni cevap alındı ✓`);
      await load();
    } catch (e: any) {
      setMsg(e?.response?.data?.detail || "Senkronizasyon hatası.");
    } finally {
      setBusy(false);
    }
  };

  const clearAll = async () => {
    if (!confirm("Tüm cevaplar silinsin mi?")) return;
    await clearResponses(formId);
    await load();
  };

  if (!form) return <div className="spinner">Yükleniyor…</div>;

  return (
    <div>
      <FormHeader formId={formId} title={form.title} active="responses" responseCount={responses.length} />

      <div className="card stack" style={{ marginBottom: 16 }}>
        <div className="spread">
          <div className="row">
            <label className="btn" style={{ marginBottom: 0 }}>
              📄 CSV içe aktar
              <input
                type="file"
                accept=".csv,text/csv"
                style={{ display: "none" }}
                onChange={(e) => e.target.files?.[0] && onFile(e.target.files[0])}
              />
            </label>
            <button className="btn" onClick={() => setShowManual((s) => !s)}>
              ✏️ Manuel cevap
            </button>
            {form.google_form_id && (
              <button className="btn primary" onClick={sync} disabled={busy}>
                🔄 Google'dan senkronize et
              </button>
            )}
          </div>
          <div className="row">
            <a className="btn sm" href={reportCsvUrl(formId)}>⬇ CSV indir</a>
            {responses.length > 0 && (
              <button className="btn sm danger" onClick={clearAll}>Tümünü sil</button>
            )}
          </div>
        </div>
        {msg && <div className={msg.includes("✓") ? "callout" : "callout warn"}>{msg}</div>}
      </div>

      {/* CSV eşleme sihirbazı */}
      {preview && (
        <div className="card stack" style={{ marginBottom: 16, borderColor: "var(--primary)" }}>
          <div className="spread">
            <h3 style={{ margin: 0 }}>Sütun eşleme ({preview.row_count} satır)</h3>
            <button className="btn sm ghost" onClick={() => setPreview(null)}>İptal</button>
          </div>
          <p className="muted" style={{ margin: 0 }}>Her CSV sütununu bir soruyla eşle (eşlemek istemediklerini "— atla" bırak).</p>
          <div className="grid cols-2">
            {preview.columns.map((col) => (
              <div key={col} className="row">
                <span className="mono" style={{ minWidth: 120, overflow: "hidden", textOverflow: "ellipsis" }}>{col}</span>
                <span className="muted">→</span>
                <select
                  value={mapping[col] || 0}
                  onChange={(e) => setMapping((m) => ({ ...m, [col]: Number(e.target.value) }))}
                >
                  <option value={0}>— atla —</option>
                  {form.questions.map((q) => (
                    <option key={q.id} value={q.id}>{q.title}</option>
                  ))}
                </select>
              </div>
            ))}
          </div>
          <div>
            <button className="btn primary" onClick={applyImport} disabled={busy}>
              {busy ? "İçe aktarılıyor…" : "İçe aktar"}
            </button>
          </div>
        </div>
      )}

      {/* Manuel cevap */}
      {showManual && (
        <ManualEntry
          form={form}
          onSaved={async () => {
            setShowManual(false);
            setMsg("Cevap eklendi ✓");
            await load();
          }}
        />
      )}

      {/* Cevap tablosu */}
      {responses.length === 0 ? (
        <div className="card" style={{ textAlign: "center", padding: 40 }}>
          <p className="muted">Henüz cevap yok. CSV içe aktar, manuel ekle veya Google'dan senkronize et.</p>
        </div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>#</th>
                {form.questions.map((q) => (
                  <th key={q.id}>{q.title}</th>
                ))}
                <th>Kaynak</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {responses.map((r, i) => (
                <tr key={r.id}>
                  <td className="muted">{i + 1}</td>
                  {form.questions.map((q) => (
                    <td key={q.id}>{displayAnswer(answerMap[i][q.id!])}</td>
                  ))}
                  <td><span className="pill-type">{r.source}</span></td>
                  <td>
                    <button
                      className="btn sm ghost danger"
                      onClick={async () => {
                        await deleteResponse(formId, r.id);
                        load();
                      }}
                    >
                      ✕
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ---------- Manuel cevap girişi ----------
function ManualEntry({ form, onSaved }: { form: Form; onSaved: () => void }) {
  const [values, setValues] = useState<Record<number, any>>({});
  const [saving, setSaving] = useState(false);

  const set = (qid: number, v: any) => setValues((s) => ({ ...s, [qid]: v }));

  const submit = async () => {
    setSaving(true);
    const answers = Object.entries(values)
      .filter(([, v]) => v !== undefined && v !== "" && !(Array.isArray(v) && v.length === 0))
      .map(([qid, v]) => ({ question_id: Number(qid), value: v }));
    await addResponse(form.id, answers, "inapp");
    setValues({});
    setSaving(false);
    onSaved();
  };

  return (
    <div className="card stack" style={{ marginBottom: 16 }}>
      <h3 style={{ margin: 0 }}>Manuel cevap ekle</h3>
      {form.questions.map((q) => {
        const qid = q.id!;
        return (
          <div key={qid}>
            <label>{q.title} {q.required && <span style={{ color: "var(--danger)" }}>*</span>}</label>
            {q.type === "single_choice" || q.type === "dropdown" ? (
              <select value={values[qid] ?? ""} onChange={(e) => set(qid, e.target.value)}>
                <option value="">— seç —</option>
                {(q.options ?? []).map((o) => <option key={o} value={o}>{o}</option>)}
              </select>
            ) : q.type === "multi_choice" ? (
              <div className="row">
                {(q.options ?? []).map((o) => {
                  const arr: string[] = values[qid] ?? [];
                  const checked = arr.includes(o);
                  return (
                    <label key={o} className="row" style={{ fontWeight: 400, cursor: "pointer", width: "auto" }}>
                      <input
                        type="checkbox"
                        style={{ width: "auto" }}
                        checked={checked}
                        onChange={(e) => {
                          const next = e.target.checked ? [...arr, o] : arr.filter((x) => x !== o);
                          set(qid, next);
                        }}
                      />
                      {o}
                    </label>
                  );
                })}
              </div>
            ) : q.type === "linear_scale" || q.type === "number" ? (
              <input type="number" value={values[qid] ?? ""} onChange={(e) => set(qid, e.target.value)} />
            ) : q.type === "date" ? (
              <input type="date" value={values[qid] ?? ""} onChange={(e) => set(qid, e.target.value)} />
            ) : q.type === "long_text" ? (
              <textarea rows={2} value={values[qid] ?? ""} onChange={(e) => set(qid, e.target.value)} />
            ) : (
              <input value={values[qid] ?? ""} onChange={(e) => set(qid, e.target.value)} />
            )}
          </div>
        );
      })}
      <div>
        <button className="btn primary" onClick={submit} disabled={saving}>
          {saving ? "Kaydediliyor…" : "Cevabı ekle"}
        </button>
      </div>
    </div>
  );
}
