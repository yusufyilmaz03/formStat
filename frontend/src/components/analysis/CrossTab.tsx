import { useState } from "react";
import { runCrosstab } from "../../api/client";
import { byRole } from "../../lib/roles";
import type { Question } from "../../types";
import { QuestionSelect } from "./QuestionSelect";

export default function CrossTab({ formId, questions }: { formId: number; questions: Question[] }) {
  const cats = byRole(questions, "categorical");
  const [a, setA] = useState<number | null>(null);
  const [b, setB] = useState<number | null>(null);
  const [result, setResult] = useState<any>(null);
  const [busy, setBusy] = useState(false);

  const run = async () => {
    if (!a || !b || a === b) return;
    setBusy(true);
    setResult(null);
    try {
      setResult(await runCrosstab(formId, a, b));
    } finally {
      setBusy(false);
    }
  };

  const maxCount = result?.counts ? Math.max(...result.counts.flat()) : 0;

  return (
    <div className="stack">
      <div className="card stack">
        <p className="muted" style={{ margin: 0 }}>İki kategorik soruyu çaprazla; hücre yoğunluğu ısı haritası olarak gösterilir.</p>
        {cats.length < 2 ? (
          <div className="callout warn">Çapraz tablo için en az 2 kategorik (tek/çoklu seçim) soru gerekir.</div>
        ) : (
          <div className="row">
            <div style={{ flex: 1 }}><QuestionSelect questions={cats} value={a} onChange={setA} placeholder="Satır değişkeni" /></div>
            <span className="muted">×</span>
            <div style={{ flex: 1 }}><QuestionSelect questions={cats} value={b} onChange={setB} placeholder="Sütun değişkeni" /></div>
            <button className="btn primary" onClick={run} disabled={!a || !b || a === b || busy}>
              {busy ? "…" : "Oluştur"}
            </button>
          </div>
        )}
      </div>

      {result?.error && <div className="callout warn">{result.error}</div>}

      {result && !result.error && (
        <div className="card stack">
          <div className="spread">
            <h3 style={{ margin: 0 }}>{result.question_a.title} × {result.question_b.title}</h3>
            {result.chi_square?.p_value != null && (
              <span className={result.chi_square.p_value < 0.05 ? "badge green" : "badge gray"}>
                χ² p = {result.chi_square.p_value}
              </span>
            )}
          </div>

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th></th>
                  {result.col_labels.map((c: string) => <th key={c}>{c}</th>)}
                  <th>Toplam</th>
                </tr>
              </thead>
              <tbody>
                {result.counts.map((row: number[], i: number) => {
                  const rowTotal = row.reduce((s, v) => s + v, 0);
                  return (
                    <tr key={i}>
                      <th>{result.row_labels[i]}</th>
                      {row.map((v, j) => (
                        <td
                          key={j}
                          style={{
                            textAlign: "center",
                            background: `rgba(79,70,229,${maxCount ? (v / maxCount) * 0.55 : 0})`,
                            fontWeight: v === maxCount && v > 0 ? 700 : 400,
                          }}
                          title={`${result.row_percent[i][j]}% (satır)`}
                        >
                          {v}
                        </td>
                      ))}
                      <td style={{ textAlign: "center", fontWeight: 600 }}>{rowTotal}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {result.chi_square?.interpretation && (
            <div className="callout">
              {result.chi_square.interpretation}
              {result.chi_square.effect_size?.value != null && (
                <> (Cramér's V = {result.chi_square.effect_size.value})</>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
