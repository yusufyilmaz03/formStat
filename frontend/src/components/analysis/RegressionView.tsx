import { useState } from "react";
import { runRegression } from "../../api/client";
import { byRole } from "../../lib/roles";
import type { Question } from "../../types";
import { QuestionSelect } from "./QuestionSelect";

export default function RegressionView({ formId, questions }: { formId: number; questions: Question[] }) {
  const usable = byRole(questions, "numeric", "categorical");
  const [target, setTarget] = useState<number | null>(null);
  const [predictors, setPredictors] = useState<number[]>([]);
  const [result, setResult] = useState<any>(null);
  const [busy, setBusy] = useState(false);

  const togglePred = (id: number) =>
    setPredictors((p) => (p.includes(id) ? p.filter((x) => x !== id) : [...p, id]));

  const run = async () => {
    if (!target || predictors.length === 0) return;
    setBusy(true);
    setResult(null);
    try {
      setResult(await runRegression(formId, target, predictors.filter((p) => p !== target)));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="stack">
      <div className="card stack">
        <p className="muted" style={{ margin: 0 }}>
          Bir hedef değişken seç; sayısal hedef → doğrusal, ikili kategorik hedef → lojistik regresyon çalışır.
        </p>
        <div>
          <label>Hedef değişken (bağımlı)</label>
          <QuestionSelect questions={usable} value={target} onChange={setTarget} placeholder="Hedef seç" />
        </div>
        <div>
          <label>Bağımsız değişkenler (yordayıcılar)</label>
          <div className="row">
            {usable.filter((q) => q.id !== target).map((q) => (
              <label key={q.id} className="row" style={{ width: "auto", fontWeight: 400, cursor: "pointer" }}>
                <input
                  type="checkbox"
                  style={{ width: "auto" }}
                  checked={predictors.includes(q.id!)}
                  onChange={() => togglePred(q.id!)}
                />
                {q.title}
              </label>
            ))}
          </div>
        </div>
        <div>
          <button className="btn primary" onClick={run} disabled={!target || predictors.length === 0 || busy}>
            {busy ? "Hesaplanıyor…" : "Regresyonu çalıştır"}
          </button>
        </div>
      </div>

      {result?.error && <div className="callout warn">{result.error}</div>}

      {result && !result.error && (
        <div className="card stack">
          <div className="spread">
            <h3 style={{ margin: 0 }}>
              {result.model_type === "linear" ? "Doğrusal regresyon" : "Lojistik regresyon"}: {result.target.title}
            </h3>
            <div className="row">
              {result.fit?.r_squared != null && <span className="badge">R² = {result.fit.r_squared}</span>}
              {result.fit?.pseudo_r_squared != null && <span className="badge">Pseudo R² = {result.fit.pseudo_r_squared}</span>}
              <span className="badge gray">n = {result.n}</span>
            </div>
          </div>
          <div className="callout">{result.interpretation}</div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>Değişken</th><th>Katsayı</th><th>Std. Hata</th><th>p-değeri</th><th>%95 GA</th><th></th></tr>
              </thead>
              <tbody>
                {result.coefficients.map((c: any, i: number) => (
                  <tr key={i}>
                    <td>{c.name}</td>
                    <td>{c.coef}</td>
                    <td className="muted">{c.std_err}</td>
                    <td>{c.p_value}</td>
                    <td className="muted">[{c.ci_low}, {c.ci_high}]</td>
                    <td>{c.significant ? <span className="badge green">anlamlı</span> : ""}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
