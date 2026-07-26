import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { deleteForm, listForms } from "../api/client";
import type { FormSummary } from "../types";

export default function FormsList() {
  const [forms, setForms] = useState<FormSummary[] | null>(null);
  const nav = useNavigate();

  const load = () => listForms().then(setForms);
  useEffect(() => {
    load();
  }, []);

  const remove = async (id: number, title: string) => {
    if (!confirm(`"${title}" formu ve tüm cevapları silinsin mi?`)) return;
    await deleteForm(id);
    load();
  };

  return (
    <div className="stack">
      <div className="spread">
        <div>
          <h1>Formlarım</h1>
          <p className="muted" style={{ margin: 0 }}>
            Anket oluştur, cevap topla, istatistiksel analiz yap.
          </p>
        </div>
        <button className="btn primary" onClick={() => nav("/new")}>
          + Yeni Form
        </button>
      </div>

      {forms === null ? (
        <div className="spinner">Yükleniyor…</div>
      ) : forms.length === 0 ? (
        <div className="card" style={{ textAlign: "center", padding: 48 }}>
          <p style={{ fontSize: 40, margin: 0 }}>📝</p>
          <h2>Henüz form yok</h2>
          <p className="muted">İlk anketini oluşturarak başla.</p>
          <button className="btn primary" onClick={() => nav("/new")}>
            + Yeni Form
          </button>
        </div>
      ) : (
        <div className="grid cols-2">
          {forms.map((f) => (
            <div key={f.id} className="card stack">
              <div className="spread">
                <h2 style={{ margin: 0 }}>{f.title}</h2>
                {f.google_form_id ? (
                  <span className="badge green">Google</span>
                ) : (
                  <span className="badge gray">Yerel</span>
                )}
              </div>
              {f.description && <p className="muted" style={{ margin: 0 }}>{f.description}</p>}
              <div className="row muted" style={{ fontSize: 13 }}>
                <span>{f.question_count} soru</span>
                <span>•</span>
                <span>{f.response_count} cevap</span>
              </div>
              <div className="row">
                <Link className="btn sm" to={`/forms/${f.id}/edit`}>
                  Düzenle
                </Link>
                <Link className="btn sm" to={`/forms/${f.id}/responses`}>
                  Cevaplar
                </Link>
                <Link className="btn sm primary" to={`/forms/${f.id}/analysis`}>
                  Analiz →
                </Link>
                <button className="btn sm danger" onClick={() => remove(f.id, f.title)}>
                  Sil
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
