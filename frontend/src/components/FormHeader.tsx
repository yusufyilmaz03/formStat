import { Link, useNavigate } from "react-router-dom";

interface Props {
  formId: number;
  title: string;
  active: "edit" | "responses" | "analysis";
  responseCount?: number;
}

const TABS = [
  { key: "edit", label: "Düzenle", path: "edit" },
  { key: "responses", label: "Cevaplar", path: "responses" },
  { key: "analysis", label: "Analiz", path: "analysis" },
] as const;

export default function FormHeader({ formId, title, active, responseCount }: Props) {
  const nav = useNavigate();
  return (
    <div style={{ marginBottom: 20 }}>
      <button className="btn sm ghost muted" onClick={() => nav("/")} style={{ marginBottom: 8 }}>
        ← Tüm formlar
      </button>
      <div className="spread">
        <h1>{title || "(Başlıksız form)"}</h1>
        {responseCount !== undefined && <span className="badge gray">{responseCount} cevap</span>}
      </div>
      <div className="tabs" style={{ marginTop: 12 }}>
        {TABS.map((t) => (
          <Link
            key={t.key}
            to={`/forms/${formId}/${t.path}`}
            className={`tab ${active === t.key ? "active" : ""}`}
            style={{ textDecoration: "none" }}
          >
            {t.label}
          </Link>
        ))}
      </div>
    </div>
  );
}
