import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getForm, getOverview } from "../api/client";
import { CategoryBar, Histogram } from "../components/charts/DistributionChart";
import FormHeader from "../components/FormHeader";
import CrossTab from "../components/analysis/CrossTab";
import InsightsView from "../components/analysis/InsightsView";
import RegressionView from "../components/analysis/RegressionView";
import SegmentationView from "../components/analysis/SegmentationView";
import TestRunner from "../components/analysis/TestRunner";
import { QUESTION_TYPE_LABELS, type Form } from "../types";

const TABS = [
  ["overview", "Genel Bakış"],
  ["charts", "Grafikler"],
  ["crosstab", "Çapraz Tablo"],
  ["test", "Test Çalıştır"],
  ["regression", "Regresyon"],
  ["segmentation", "Segmentasyon"],
  ["insights", "İçgörüler"],
] as const;

export default function AnalysisDashboard() {
  const { id } = useParams();
  const formId = Number(id);
  const [form, setForm] = useState<Form | null>(null);
  const [overview, setOverview] = useState<any>(null);
  const [tab, setTab] = useState<string>("overview");

  useEffect(() => {
    getForm(formId).then(setForm);
    getOverview(formId).then(setOverview);
  }, [formId]);

  if (!form || !overview) return <div className="spinner">Yükleniyor…</div>;

  const empty = overview.response_count === 0;

  return (
    <div>
      <FormHeader formId={formId} title={form.title} active="analysis" responseCount={overview.response_count} />

      {empty ? (
        <div className="card" style={{ textAlign: "center", padding: 40 }}>
          <p style={{ fontSize: 32, margin: 0 }}>📭</p>
          <h2>Analiz için cevap yok</h2>
          <p className="muted">Önce cevap ekleyin.</p>
          <Link className="btn primary" to={`/forms/${formId}/responses`}>Cevaplar sayfası →</Link>
        </div>
      ) : (
        <>
          <div className="tabs">
            {TABS.map(([key, label]) => (
              <div key={key} className={`tab ${tab === key ? "active" : ""}`} onClick={() => setTab(key)}>
                {label}
              </div>
            ))}
          </div>

          {tab === "overview" && <Overview overview={overview} />}
          {tab === "charts" && <Charts overview={overview} />}
          {tab === "crosstab" && <CrossTab formId={formId} questions={form.questions} />}
          {tab === "test" && <TestRunner formId={formId} questions={form.questions} />}
          {tab === "regression" && <RegressionView formId={formId} questions={form.questions} />}
          {tab === "segmentation" && <SegmentationView formId={formId} questions={form.questions} />}
          {tab === "insights" && <InsightsView formId={formId} />}
        </>
      )}
    </div>
  );
}

// ---------- Genel Bakış ----------
function Overview({ overview }: { overview: any }) {
  const keyStat = (q: any): string => {
    const s = q.summary || {};
    if (q.role === "numeric") return s.mean != null ? `ort. ${s.mean}` : "—";
    if (q.role === "categorical" || q.role === "multi") return s.mode ? `en sık: ${s.mode}` : "—";
    return s.unique != null ? `${s.unique} farklı` : "—";
  };
  return (
    <div className="stack">
      <div className="grid cols-3">
        <div className="card stat"><div className="value">{overview.response_count}</div><div className="label">Cevap</div></div>
        <div className="card stat"><div className="value">{overview.question_count}</div><div className="label">Soru</div></div>
        <div className="card stat"><div className="value">{overview.completion_rate ?? "—"}%</div><div className="label">Doldurma oranı</div></div>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr><th>Soru</th><th>Tip</th><th>Yanıt</th><th>Eksik</th><th>Özet</th></tr>
          </thead>
          <tbody>
            {overview.questions.map((q: any) => (
              <tr key={q.id}>
                <td>{q.title}</td>
                <td><span className="pill-type">{QUESTION_TYPE_LABELS[q.type as keyof typeof QUESTION_TYPE_LABELS]}</span></td>
                <td>{q.answered}</td>
                <td className="muted">{q.missing}</td>
                <td>{keyStat(q)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ---------- Grafikler ----------
function Charts({ overview }: { overview: any }) {
  return (
    <div className="grid cols-2">
      {overview.questions.map((q: any) => (
        <div key={q.id} className="card stack">
          <div className="spread">
            <h3 style={{ margin: 0 }}>{q.title}</h3>
            <span className="pill-type">{q.answered} yanıt</span>
          </div>
          <QuestionChart q={q} />
        </div>
      ))}
    </div>
  );
}

function QuestionChart({ q }: { q: any }) {
  const s = q.summary || {};
  if (q.role === "numeric") {
    if (!s.histogram?.length) return <p className="muted">Veri yok.</p>;
    return (
      <>
        <Histogram bins={s.histogram} />
        <div className="row muted" style={{ fontSize: 12, justifyContent: "space-between" }}>
          <span>Ort: <b>{s.mean}</b></span>
          <span>Medyan: <b>{s.median}</b></span>
          <span>Std: <b>{s.std}</b></span>
          <span>Min–Max: <b>{s.min}–{s.max}</b></span>
        </div>
      </>
    );
  }
  if (q.role === "categorical" || q.role === "multi") {
    if (!s.distribution?.length) return <p className="muted">Veri yok.</p>;
    return <CategoryBar data={s.distribution} />;
  }
  // text
  if (!s.top_values?.length) return <p className="muted">Metin cevabı yok.</p>;
  return (
    <div className="stack" style={{ gap: 4 }}>
      <span className="muted" style={{ fontSize: 12 }}>En sık yanıtlar:</span>
      {s.top_values.slice(0, 6).map((t: any, i: number) => (
        <div key={i} className="spread"><span>{t.label}</span><span className="badge gray">{t.count}</span></div>
      ))}
    </div>
  );
}
