import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  createForm,
  getForm,
  googleExport,
  googleStatus,
  updateForm,
} from "../api/client";
import { CHOICE_TYPES, QUESTION_TYPE_LABELS, type Form, type Question, type QuestionType } from "../types";

const blankQuestion = (): Question => ({
  type: "single_choice",
  title: "",
  required: false,
  options: ["Seçenek 1", "Seçenek 2"],
  scale_min: 1,
  scale_max: 5,
});

export default function FormBuilder() {
  const { id } = useParams();
  const formId = id ? Number(id) : null;
  const nav = useNavigate();

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [questions, setQuestions] = useState<Question[]>([blankQuestion()]);
  const [form, setForm] = useState<Form | null>(null);
  const [loading, setLoading] = useState(!!formId);
  const [saving, setSaving] = useState(false);
  const [googleConnected, setGoogleConnected] = useState(false);
  const [googleBusy, setGoogleBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  useEffect(() => {
    googleStatus().then((s) => setGoogleConnected(s.connected)).catch(() => {});
    if (formId) {
      getForm(formId)
        .then((f) => {
          setForm(f);
          setTitle(f.title);
          setDescription(f.description);
          setQuestions(f.questions.length ? f.questions : [blankQuestion()]);
        })
        .finally(() => setLoading(false));
    }
  }, [formId]);

  const patchQuestion = (idx: number, patch: Partial<Question>) =>
    setQuestions((qs) => qs.map((q, i) => (i === idx ? { ...q, ...patch } : q)));

  const move = (idx: number, dir: -1 | 1) => {
    const j = idx + dir;
    if (j < 0 || j >= questions.length) return;
    setQuestions((qs) => {
      const copy = [...qs];
      [copy[idx], copy[j]] = [copy[j], copy[idx]];
      return copy;
    });
  };

  const save = async (): Promise<number | null> => {
    if (!title.trim()) {
      setMsg("Form başlığı gerekli.");
      return null;
    }
    setSaving(true);
    setMsg(null);
    const payload = {
      title,
      description,
      questions: questions.map((q, i) => ({ ...q, order: i })),
    };
    try {
      if (formId) {
        const f = await updateForm(formId, payload);
        setForm(f);
        setMsg("Kaydedildi ✓");
        return formId;
      }
      const f = await createForm(payload);
      nav(`/forms/${f.id}/edit`, { replace: true });
      return f.id;
    } catch (e: any) {
      setMsg(e?.response?.data?.detail || "Kaydetme hatası.");
      return null;
    } finally {
      setSaving(false);
    }
  };

  const exportToGoogle = async () => {
    const savedId = await save();
    if (!savedId) return;
    setGoogleBusy(true);
    setMsg(null);
    try {
      const res = await googleExport(savedId);
      const f = await getForm(savedId);
      setForm(f);
      setMsg(res.published ? "Google Forms'a aktarıldı ve yayınlandı ✓" : "Google'a aktarıldı (yayınlama atlandı).");
    } catch (e: any) {
      setMsg(e?.response?.data?.detail || "Google'a aktarma hatası.");
    } finally {
      setGoogleBusy(false);
    }
  };

  if (loading) return <div className="spinner">Yükleniyor…</div>;

  return (
    <div className="stack">
      <button className="btn sm ghost muted" onClick={() => nav("/")}>
        ← Tüm formlar
      </button>

      <div className="card stack">
        <div>
          <label>Form başlığı</label>
          <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Örn. Müşteri Memnuniyet Anketi" />
        </div>
        <div>
          <label>Açıklama (opsiyonel)</label>
          <textarea rows={2} value={description} onChange={(e) => setDescription(e.target.value)} />
        </div>
      </div>

      <div className="stack">
        {questions.map((q, idx) => (
          <QuestionCard
            key={idx}
            index={idx}
            total={questions.length}
            q={q}
            onChange={(patch) => patchQuestion(idx, patch)}
            onMove={(dir) => move(idx, dir)}
            onRemove={() => setQuestions((qs) => qs.filter((_, i) => i !== idx))}
          />
        ))}
      </div>

      <div className="row">
        <button className="btn" onClick={() => setQuestions((qs) => [...qs, blankQuestion()])}>
          + Soru ekle
        </button>
      </div>

      <div className="divider" />

      <div className="spread">
        <div className="row">
          <button className="btn primary" onClick={save} disabled={saving}>
            {saving ? "Kaydediliyor…" : "Kaydet"}
          </button>
          {formId && (
            <button className="btn" onClick={() => nav(`/forms/${formId}/responses`)}>
              Cevaplar →
            </button>
          )}
        </div>
        {msg && <span className={msg.includes("✓") ? "badge green" : "badge amber"}>{msg}</span>}
      </div>

      {/* Google Forms bölümü */}
      <div className="card stack">
        <h3>Google Forms</h3>
        {!googleConnected ? (
          <p className="muted" style={{ margin: 0 }}>
            Google Forms'a aktarmak için önce sağ üstten <b>Google'a Bağlan</b>.
          </p>
        ) : (
          <>
            <div className="row">
              <button className="btn primary" onClick={exportToGoogle} disabled={googleBusy}>
                {googleBusy ? "Aktarılıyor…" : form?.google_form_id ? "Google'a yeniden aktar" : "Google Forms'a aktar"}
              </button>
              {form?.google_form_id && (
                <a className="btn" href={`https://docs.google.com/forms/d/${form.google_form_id}/edit`} target="_blank" rel="noreferrer">
                  Google'da düzenle ↗
                </a>
              )}
            </div>
            {form?.google_responder_uri && (
              <div className="callout">
                <div className="muted" style={{ fontSize: 12, marginBottom: 4 }}>Yanıt bağlantısı (paylaş):</div>
                <a className="mono" href={form.google_responder_uri} target="_blank" rel="noreferrer">
                  {form.google_responder_uri}
                </a>
                {form.published ? (
                  <span className="badge green" style={{ marginLeft: 8 }}>Yayında</span>
                ) : (
                  <span className="badge amber" style={{ marginLeft: 8 }}>Yayınlanmadı</span>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

// ---------- Soru kartı ----------
function QuestionCard({
  index,
  total,
  q,
  onChange,
  onMove,
  onRemove,
}: {
  index: number;
  total: number;
  q: Question;
  onChange: (patch: Partial<Question>) => void;
  onMove: (dir: -1 | 1) => void;
  onRemove: () => void;
}) {
  const isChoice = CHOICE_TYPES.includes(q.type);
  const isScale = q.type === "linear_scale";
  const options = q.options ?? [];

  return (
    <div className="card stack">
      <div className="spread">
        <div className="row">
          <span className="badge gray">{index + 1}</span>
          <select
            style={{ width: 160 }}
            value={q.type}
            onChange={(e) => {
              const type = e.target.value as QuestionType;
              const patch: Partial<Question> = { type };
              if (CHOICE_TYPES.includes(type) && (!q.options || q.options.length === 0)) {
                patch.options = ["Seçenek 1", "Seçenek 2"];
              }
              onChange(patch);
            }}
          >
            {Object.entries(QUESTION_TYPE_LABELS).map(([val, label]) => (
              <option key={val} value={val}>
                {label}
              </option>
            ))}
          </select>
        </div>
        <div className="row">
          <button className="btn sm ghost" onClick={() => onMove(-1)} disabled={index === 0}>↑</button>
          <button className="btn sm ghost" onClick={() => onMove(1)} disabled={index === total - 1}>↓</button>
          <button className="btn sm danger" onClick={onRemove}>Sil</button>
        </div>
      </div>

      <input placeholder="Soru metni" value={q.title} onChange={(e) => onChange({ title: e.target.value })} />

      {isChoice && (
        <div className="stack" style={{ gap: 6 }}>
          <label>Seçenekler</label>
          {options.map((opt, i) => (
            <div key={i} className="row">
              <input
                value={opt}
                onChange={(e) => {
                  const next = [...options];
                  next[i] = e.target.value;
                  onChange({ options: next });
                }}
              />
              <button
                className="btn sm ghost danger"
                onClick={() => onChange({ options: options.filter((_, j) => j !== i) })}
                disabled={options.length <= 1}
              >
                ✕
              </button>
            </div>
          ))}
          <button
            className="btn sm"
            onClick={() => onChange({ options: [...options, `Seçenek ${options.length + 1}`] })}
          >
            + Seçenek ekle
          </button>
        </div>
      )}

      {isScale && (
        <div className="row">
          <div>
            <label>Min</label>
            <input
              type="number"
              style={{ width: 80 }}
              value={q.scale_min ?? 1}
              onChange={(e) => onChange({ scale_min: Number(e.target.value) })}
            />
          </div>
          <div>
            <label>Max</label>
            <input
              type="number"
              style={{ width: 80 }}
              value={q.scale_max ?? 5}
              onChange={(e) => onChange({ scale_max: Number(e.target.value) })}
            />
          </div>
        </div>
      )}

      <label className="row" style={{ cursor: "pointer", fontWeight: 400 }}>
        <input
          type="checkbox"
          style={{ width: "auto" }}
          checked={!!q.required}
          onChange={(e) => onChange({ required: e.target.checked })}
        />
        Zorunlu soru
      </label>
    </div>
  );
}
