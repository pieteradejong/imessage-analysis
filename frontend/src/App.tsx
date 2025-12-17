import { useEffect, useMemo, useState } from "react";
import { fetchLatest, fetchSummary, fetchTopChats, getApiBaseUrl } from "./api";
import type { LatestMessage, Summary, TopChat } from "./api";

type Tab = "overview" | "latest";

function formatNumber(n: number): string {
  return new Intl.NumberFormat().format(n);
}

export function App() {
  const [tab, setTab] = useState<Tab>("overview");
  const [error, setError] = useState<string | null>(null);

  const [summary, setSummary] = useState<Summary | null>(null);
  const [topChats, setTopChats] = useState<TopChat[] | null>(null);

  const [latestLimit, setLatestLimit] = useState<number>(25);
  const [latest, setLatest] = useState<LatestMessage[] | null>(null);

  const apiBaseUrl = useMemo(() => getApiBaseUrl(), []);

  useEffect(() => {
    let cancelled = false;
    setError(null);

    async function loadOverview() {
      try {
        const [s, t] = await Promise.all([fetchSummary(), fetchTopChats(25)]);
        if (cancelled) return;
        setSummary(s);
        setTopChats(t);
      } catch (e) {
        if (cancelled) return;
        setError(e instanceof Error ? e.message : String(e));
      }
    }

    if (tab === "overview") {
      loadOverview();
    }

    return () => {
      cancelled = true;
    };
  }, [tab]);

  useEffect(() => {
    let cancelled = false;
    setError(null);

    async function loadLatest() {
      try {
        const msgs = await fetchLatest(latestLimit);
        if (cancelled) return;
        setLatest(msgs);
      } catch (e) {
        if (cancelled) return;
        setError(e instanceof Error ? e.message : String(e));
      }
    }

    if (tab === "latest") {
      loadLatest();
    }

    return () => {
      cancelled = true;
    };
  }, [tab, latestLimit]);

  return (
    <div style={{ fontFamily: "system-ui, -apple-system, Segoe UI, Roboto, sans-serif", padding: 16, maxWidth: 1100, margin: "0 auto" }}>
      <header style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", gap: 16, marginBottom: 16 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 22 }}>iMessage Analysis</h1>
          <div style={{ opacity: 0.7, fontSize: 13 }}>
            API: <code>{apiBaseUrl}</code>
          </div>
        </div>
        <nav style={{ display: "flex", gap: 8 }}>
          <button onClick={() => setTab("overview")} disabled={tab === "overview"}>
            Overview
          </button>
          <button onClick={() => setTab("latest")} disabled={tab === "latest"}>
            Latest
          </button>
        </nav>
      </header>

      {error && (
        <div style={{ background: "#fee", border: "1px solid #f99", padding: 12, borderRadius: 8, marginBottom: 12 }}>
          <strong>Error</strong>
          <div style={{ whiteSpace: "pre-wrap" }}>{error}</div>
          <div style={{ marginTop: 8, opacity: 0.8 }}>
            If this is “Database file not found”, set <code>IMESSAGE_DB_PATH</code> before running the backend.
          </div>
        </div>
      )}

      {tab === "overview" && (
        <section>
          <h2 style={{ marginTop: 0 }}>Summary</h2>
          {!summary ? (
            <div>Loading…</div>
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 12 }}>
              <div style={{ border: "1px solid #ddd", borderRadius: 10, padding: 12 }}>
                <div style={{ opacity: 0.7 }}>Total messages</div>
                <div style={{ fontSize: 22, fontWeight: 700 }}>{formatNumber(summary.total_messages)}</div>
              </div>
              <div style={{ border: "1px solid #ddd", borderRadius: 10, padding: 12 }}>
                <div style={{ opacity: 0.7 }}>Total chats</div>
                <div style={{ fontSize: 22, fontWeight: 700 }}>{formatNumber(summary.total_chats)}</div>
              </div>
              <div style={{ border: "1px solid #ddd", borderRadius: 10, padding: 12 }}>
                <div style={{ opacity: 0.7 }}>Tables</div>
                <div style={{ fontSize: 22, fontWeight: 700 }}>{formatNumber(summary.table_count)}</div>
              </div>
              <div style={{ border: "1px solid #ddd", borderRadius: 10, padding: 12 }}>
                <div style={{ opacity: 0.7 }}>DB path</div>
                <div style={{ fontSize: 12, fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace", wordBreak: "break-all" }}>
                  {summary.db_path ?? "(unknown)"}
                </div>
                <div style={{ marginTop: 6, opacity: 0.7, fontSize: 12 }}>
                  In-memory: <code>{String(summary.use_memory ?? false)}</code>
                </div>
              </div>
            </div>
          )}

          <h2>Top chats</h2>
          {!topChats ? (
            <div>Loading…</div>
          ) : (
            <div style={{ border: "1px solid #ddd", borderRadius: 10, overflow: "hidden" }}>
              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr style={{ background: "#f7f7f7" }}>
                    <th style={{ textAlign: "left", padding: "10px 12px" }}>Chat</th>
                    <th style={{ textAlign: "right", padding: "10px 12px" }}>Messages</th>
                  </tr>
                </thead>
                <tbody>
                  {topChats.map((c) => (
                    <tr key={c.chat_identifier} style={{ borderTop: "1px solid #eee" }}>
                      <td style={{ padding: "10px 12px", fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace", fontSize: 12 }}>
                        {c.chat_identifier}
                      </td>
                      <td style={{ padding: "10px 12px", textAlign: "right" }}>{formatNumber(c.message_count)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}

      {tab === "latest" && (
        <section>
          <h2 style={{ marginTop: 0 }}>Latest messages</h2>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
            <label>
              Limit{" "}
              <input
                type="number"
                min={1}
                max={500}
                value={latestLimit}
                onChange={(e) => setLatestLimit(Number(e.target.value))}
                style={{ width: 90 }}
              />
            </label>
            <button onClick={() => setLatestLimit((x) => x)}>Refresh</button>
          </div>

          {!latest ? (
            <div>Loading…</div>
          ) : (
            <div style={{ display: "grid", gap: 10 }}>
              {latest.map((m, idx) => (
                <div key={`${m.date}-${idx}`} style={{ border: "1px solid #ddd", borderRadius: 10, padding: 12 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
                    <div style={{ fontWeight: 700 }}>{m.is_from_me ? "You" : "Them"}</div>
                    <div style={{ opacity: 0.7, fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace", fontSize: 12 }}>{m.date}</div>
                  </div>
                  <div style={{ marginTop: 6, whiteSpace: "pre-wrap" }}>{m.text ?? ""}</div>
                  <div style={{ marginTop: 8, opacity: 0.7, fontSize: 12 }}>
                    Chat: <code>{m.chat_identifier ?? ""}</code>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      )}
    </div>
  );
}

