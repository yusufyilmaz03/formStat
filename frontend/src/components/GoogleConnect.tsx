import { useEffect, useState } from "react";
import { googleAuthUrl, googleDisconnect, googleStatus } from "../api/client";

export default function GoogleConnect() {
  const [status, setStatus] = useState<{ client_configured: boolean; connected: boolean } | null>(null);
  const [busy, setBusy] = useState(false);

  const refresh = () => googleStatus().then(setStatus).catch(() => setStatus(null));

  useEffect(() => {
    refresh();
    // OAuth dönüşünde adres çubuğunu temizle
    const params = new URLSearchParams(window.location.search);
    if (params.get("google")) {
      window.history.replaceState({}, "", window.location.pathname);
      setTimeout(refresh, 300);
    }
  }, []);

  const connect = async () => {
    setBusy(true);
    try {
      const { url } = await googleAuthUrl();
      window.location.href = url;
    } catch (e: any) {
      alert(e?.response?.data?.detail || "Google bağlantısı başlatılamadı.");
      setBusy(false);
    }
  };

  const disconnect = async () => {
    setBusy(true);
    await googleDisconnect();
    await refresh();
    setBusy(false);
  };

  if (!status) return <span className="muted" style={{ fontSize: 13 }}>…</span>;

  if (status.connected) {
    return (
      <div className="row">
        <span className="badge green">● Google bağlı</span>
        <button className="btn sm ghost muted" onClick={disconnect} disabled={busy}>
          Bağlantıyı kes
        </button>
      </div>
    );
  }

  return (
    <div className="row">
      {!status.client_configured && (
        <span className="badge amber" title="data/client_secret.json bulunamadı">
          client_secret.json yok
        </span>
      )}
      <button className="btn sm primary" onClick={connect} disabled={busy}>
        Google'a Bağlan
      </button>
    </div>
  );
}
