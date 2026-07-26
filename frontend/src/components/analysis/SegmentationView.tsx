import { useState } from "react";
import {
  CartesianGrid,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import { runSegmentation } from "../../api/client";
import { byRole } from "../../lib/roles";
import { colorAt } from "../../lib/colors";
import type { Question } from "../../types";

export default function SegmentationView({ formId, questions }: { formId: number; questions: Question[] }) {
  const numeric = byRole(questions, "numeric");
  const [selected, setSelected] = useState<number[]>(numeric.map((q) => q.id!));
  const [auto, setAuto] = useState(true);
  const [k, setK] = useState(3);
  const [result, setResult] = useState<any>(null);
  const [busy, setBusy] = useState(false);

  const toggle = (id: number) =>
    setSelected((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]));

  const run = async () => {
    if (selected.length < 2) return;
    setBusy(true);
    setResult(null);
    try {
      setResult(await runSegmentation(formId, selected, auto ? null : k));
    } finally {
      setBusy(false);
    }
  };

  const clusters: number[] = result?.scatter ? Array.from(new Set(result.scatter.map((p: any) => p.cluster))) : [];

  return (
    <div className="stack">
      <div className="card stack">
        <p className="muted" style={{ margin: 0 }}>
          Sayısal cevaplardan cevaplayıcı segmentleri (K-means). Küme sayısı otomatik (silhouette) seçilebilir.
        </p>
        {numeric.length < 2 ? (
          <div className="callout warn">Segmentasyon için en az 2 sayısal soru gerekir.</div>
        ) : (
          <>
            <div>
              <label>Kullanılacak sayısal sorular</label>
              <div className="row">
                {numeric.map((q) => (
                  <label key={q.id} className="row" style={{ width: "auto", fontWeight: 400, cursor: "pointer" }}>
                    <input type="checkbox" style={{ width: "auto" }} checked={selected.includes(q.id!)} onChange={() => toggle(q.id!)} />
                    {q.title}
                  </label>
                ))}
              </div>
            </div>
            <div className="row">
              <label className="row" style={{ width: "auto", fontWeight: 400, cursor: "pointer" }}>
                <input type="checkbox" style={{ width: "auto" }} checked={auto} onChange={(e) => setAuto(e.target.checked)} />
                Küme sayısını otomatik seç
              </label>
              {!auto && (
                <div className="row">
                  <span className="muted">k =</span>
                  <input type="number" min={2} max={8} value={k} style={{ width: 70 }} onChange={(e) => setK(Number(e.target.value))} />
                </div>
              )}
              <button className="btn primary" onClick={run} disabled={selected.length < 2 || busy}>
                {busy ? "Kümeleniyor…" : "Segmentleri bul"}
              </button>
            </div>
          </>
        )}
      </div>

      {result?.error && <div className="callout warn">{result.error}</div>}

      {result && !result.error && (
        <div className="card stack">
          <div className="spread">
            <h3 style={{ margin: 0 }}>{result.n_clusters} segment bulundu</h3>
            <span className="badge gray">silhouette = {result.silhouette ?? "—"}</span>
          </div>

          {result.scatter?.length > 0 && (
            <ResponsiveContainer width="100%" height={300}>
              <ScatterChart margin={{ left: 8, bottom: 8 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" dataKey="x" name="PCA-1" tick={{ fontSize: 11 }} />
                <YAxis type="number" dataKey="y" name="PCA-2" tick={{ fontSize: 11 }} />
                <ZAxis range={[60, 60]} />
                <Tooltip cursor={{ strokeDasharray: "3 3" }} />
                {clusters.map((c) => (
                  <Scatter
                    key={c}
                    name={`Segment ${c + 1}`}
                    data={result.scatter.filter((p: any) => p.cluster === c)}
                    fill={colorAt(c)}
                  />
                ))}
              </ScatterChart>
            </ResponsiveContainer>
          )}

          <h3 style={{ margin: "8px 0 0" }}>Segment profilleri</h3>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Segment</th>
                  <th>Büyüklük</th>
                  {result.features.map((f: string) => <th key={f}>{f} (ort.)</th>)}
                </tr>
              </thead>
              <tbody>
                {result.clusters.map((c: any) => (
                  <tr key={c.cluster}>
                    <td><span className="badge" style={{ background: colorAt(c.cluster), color: "#fff" }}>Segment {c.cluster + 1}</span></td>
                    <td>{c.size}</td>
                    {result.features.map((f: string) => <td key={f}>{c.means[f] ?? "—"}</td>)}
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
