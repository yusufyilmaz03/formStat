import { useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { runTest } from "../../api/client";
import { byRole } from "../../lib/roles";
import { colorAt } from "../../lib/colors";
import type { Question } from "../../types";
import { QuestionSelect } from "./QuestionSelect";

export default function TestRunner({ formId, questions }: { formId: number; questions: Question[] }) {
  const usable = byRole(questions, "numeric", "categorical");
  const [a, setA] = useState<number | null>(null);
  const [b, setB] = useState<number | null>(null);
  const [result, setResult] = useState<any>(null);
  const [busy, setBusy] = useState(false);

  const run = async () => {
    if (!a || !b || a === b) return;
    setBusy(true);
    setResult(null);
    try {
      setResult(await runTest(formId, a, b));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="stack">
      <div className="card stack">
        <p className="muted" style={{ margin: 0 }}>
          İki değişken seç — sistem tiplere göre uygun testi (korelasyon, t-testi, ANOVA veya ki-kare) otomatik seçer.
        </p>
        <div className="row">
          <div style={{ flex: 1 }}><QuestionSelect questions={usable} value={a} onChange={setA} placeholder="1. değişken" /></div>
          <span className="muted">vs</span>
          <div style={{ flex: 1 }}><QuestionSelect questions={usable} value={b} onChange={setB} placeholder="2. değişken" /></div>
          <button className="btn primary" onClick={run} disabled={!a || !b || a === b || busy}>
            {busy ? "…" : "Testi çalıştır"}
          </button>
        </div>
      </div>

      {result && <TestResult result={result} />}
    </div>
  );
}

function TestResult({ result }: { result: any }) {
  if (result.error) return <div className="callout warn">{result.error}</div>;

  const es = result.effect_size;
  return (
    <div className="card stack">
      <div className="spread">
        <h3 style={{ margin: 0 }}>{result.test_label}</h3>
        <span className={result.p_value != null && result.p_value < 0.05 ? "badge green" : "badge gray"}>
          p = {result.p_value ?? "—"}
        </span>
      </div>
      <div className="callout">{result.interpretation}</div>

      <div className="row" style={{ gap: 24 }}>
        {result.statistic != null && <Metric label="İstatistik" value={result.statistic} />}
        {es?.value != null && <Metric label={es.name} value={es.value} />}
        {result.n != null && <Metric label="n" value={result.n} />}
      </div>

      {/* Korelasyon: scatter */}
      {result.test === "correlation" && result.scatter && (
        <ResponsiveContainer width="100%" height={280}>
          <ScatterChart margin={{ left: 8, bottom: 8 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" dataKey="x" name={result.question_a?.title} tick={{ fontSize: 11 }} />
            <YAxis type="number" dataKey="y" name={result.question_b?.title} tick={{ fontSize: 11 }} />
            <Tooltip cursor={{ strokeDasharray: "3 3" }} />
            <Scatter data={result.scatter} fill={colorAt(0)} />
          </ScatterChart>
        </ResponsiveContainer>
      )}

      {/* Grup karşılaştırma: ortalama bar */}
      {(result.test === "t_test" || result.test === "anova") && result.groups && (
        <>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={result.groups} margin={{ left: 0, bottom: 8 }}>
              <XAxis dataKey="group" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="mean" fill={colorAt(1)} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Grup</th><th>n</th><th>Ortalama</th><th>Std</th></tr></thead>
              <tbody>
                {result.groups.map((g: any) => (
                  <tr key={g.group}><td>{g.group}</td><td>{g.n}</td><td>{g.mean}</td><td>{g.std}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
          {result.posthoc && (
            <details>
              <summary className="muted" style={{ cursor: "pointer" }}>Post-hoc (Tukey) karşılaştırmaları</summary>
              <div className="table-wrap" style={{ marginTop: 8 }}>
                <table>
                  <thead><tr><th>Grup 1</th><th>Grup 2</th><th>Fark</th><th>p</th><th>Anlamlı?</th></tr></thead>
                  <tbody>
                    {result.posthoc.map((p: any, i: number) => (
                      <tr key={i}>
                        <td>{p.group1}</td><td>{p.group2}</td><td>{p.mean_diff}</td><td>{p.p_adj}</td>
                        <td>{p.reject ? "✓" : "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </details>
          )}
        </>
      )}

      {/* Korelasyon detay */}
      {result.test === "correlation" && (
        <div className="row muted" style={{ fontSize: 13, gap: 20 }}>
          <span>Pearson r = <b>{result.pearson?.r}</b> (p={result.pearson?.p_value})</span>
          <span>Spearman ρ = <b>{result.spearman?.r}</b> (p={result.spearman?.p_value})</span>
        </div>
      )}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: any }) {
  return (
    <div>
      <div className="muted" style={{ fontSize: 12 }}>{label}</div>
      <div style={{ fontSize: 20, fontWeight: 700 }}>{value}</div>
    </div>
  );
}
