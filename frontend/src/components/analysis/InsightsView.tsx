import { useEffect, useState } from "react";
import { getInsights } from "../../api/client";

const TYPE_META: Record<string, { icon: string; label: string }> = {
  relationship: { icon: "🔗", label: "İlişki" },
  distribution: { icon: "📈", label: "Dağılım" },
  quality: { icon: "⚠️", label: "Veri kalitesi" },
  info: { icon: "ℹ️", label: "Bilgi" },
};

const SEV_BADGE: Record<string, string> = { high: "badge green", medium: "badge amber", low: "badge gray" };

export default function InsightsView({ formId }: { formId: number }) {
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    getInsights(formId).then(setData);
  }, [formId]);

  if (!data) return <div className="spinner">İçgörüler hesaplanıyor…</div>;

  return (
    <div className="stack">
      <p className="muted" style={{ margin: 0 }}>
        {data.response_count} cevap otomatik tarandı: anlamlı ilişkiler, dikkat çekici dağılımlar ve veri kalitesi uyarıları.
      </p>
      {data.findings.map((f: any, i: number) => {
        const meta = TYPE_META[f.type] || TYPE_META.info;
        return (
          <div key={i} className="card">
            <div className="spread">
              <div className="row">
                <span style={{ fontSize: 20 }}>{meta.icon}</span>
                <div>
                  <div style={{ fontWeight: 600 }}>{f.title}</div>
                  <div className="muted">{f.detail}</div>
                </div>
              </div>
              <span className={SEV_BADGE[f.severity] || "badge gray"}>{meta.label}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
