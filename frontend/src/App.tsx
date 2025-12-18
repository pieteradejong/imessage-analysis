import { useEffect, useMemo, useState } from "react";
import {
  fetchLatest,
  fetchSummary,
  fetchTopChats,
  fetchContacts,
  fetchContactDetail,
  getApiBaseUrl,
} from "./api";
import type {
  LatestMessage,
  Summary,
  TopChat,
  Contact,
  ContactDetail,
} from "./api";

type Tab = "overview" | "latest" | "contacts";

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

  // Contacts state
  const [contacts, setContacts] = useState<Contact[] | null>(null);
  const [contactSearch, setContactSearch] = useState<string>("");
  const [selectedContactId, setSelectedContactId] = useState<string | null>(null);
  const [contactDetail, setContactDetail] = useState<ContactDetail | null>(null);
  const [contactDetailLoading, setContactDetailLoading] = useState(false);

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

  // Load contacts when tab is selected
  useEffect(() => {
    let cancelled = false;
    setError(null);

    async function loadContacts() {
      try {
        const data = await fetchContacts();
        if (cancelled) return;
        setContacts(data);
      } catch (e) {
        if (cancelled) return;
        setError(e instanceof Error ? e.message : String(e));
      }
    }

    if (tab === "contacts" && contacts === null) {
      loadContacts();
    }

    return () => {
      cancelled = true;
    };
  }, [tab, contacts]);

  // Load contact detail when a contact is selected
  useEffect(() => {
    let cancelled = false;

    async function loadContactDetail() {
      if (!selectedContactId) return;
      setContactDetailLoading(true);
      setError(null);

      try {
        const data = await fetchContactDetail(selectedContactId);
        if (cancelled) return;
        setContactDetail(data);
      } catch (e) {
        if (cancelled) return;
        setError(e instanceof Error ? e.message : String(e));
      } finally {
        if (!cancelled) setContactDetailLoading(false);
      }
    }

    if (selectedContactId) {
      loadContactDetail();
    } else {
      setContactDetail(null);
    }

    return () => {
      cancelled = true;
    };
  }, [selectedContactId]);

  // Filter contacts by search term
  const filteredContacts = useMemo(() => {
    if (!contacts) return null;
    if (!contactSearch.trim()) return contacts;
    const search = contactSearch.toLowerCase();
    return contacts.filter(
      (c) =>
        c.id.toLowerCase().includes(search) ||
        c.service.toLowerCase().includes(search) ||
        (c.country && c.country.toLowerCase().includes(search))
    );
  }, [contacts, contactSearch]);

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
          <button onClick={() => { setTab("contacts"); setSelectedContactId(null); }} disabled={tab === "contacts"}>
            Contacts
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
                      <td style={{ padding: "10px 12px" }}>
                        <div style={{ fontWeight: c.display_name ? 600 : 400 }}>
                          {c.display_name || c.chat_identifier}
                        </div>
                        {c.display_name && (
                          <div style={{ opacity: 0.6, fontSize: 11, fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace", marginTop: 2 }}>
                            {c.chat_identifier}
                          </div>
                        )}
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
                    <div>
                      <div style={{ fontWeight: 700 }}>{m.is_from_me ? "You" : m.display_name || "Them"}</div>
                      {!m.is_from_me && m.display_name && (
                        <div style={{ opacity: 0.6, fontSize: 11, fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace", marginTop: 2 }}>
                          {m.chat_identifier}
                        </div>
                      )}
                    </div>
                    <div style={{ opacity: 0.7, fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace", fontSize: 12 }}>{m.date}</div>
                  </div>
                  <div style={{ marginTop: 6, whiteSpace: "pre-wrap" }}>{m.text ?? ""}</div>
                  {!m.display_name && (
                    <div style={{ marginTop: 8, opacity: 0.7, fontSize: 12 }}>
                      Chat: <code>{m.chat_identifier ?? ""}</code>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </section>
      )}

      {tab === "contacts" && !selectedContactId && (
        <section>
          <h2 style={{ marginTop: 0 }}>Contacts</h2>
          <div style={{ marginBottom: 16 }}>
            <input
              type="text"
              placeholder="Search contacts..."
              value={contactSearch}
              onChange={(e) => setContactSearch(e.target.value)}
              style={{
                width: "100%",
                maxWidth: 400,
                padding: "10px 14px",
                fontSize: 15,
                border: "1px solid #ddd",
                borderRadius: 8,
              }}
            />
          </div>

          {!filteredContacts ? (
            <div>Loading…</div>
          ) : filteredContacts.length === 0 ? (
            <div style={{ opacity: 0.7 }}>No contacts found.</div>
          ) : (
            <>
              <div style={{ marginBottom: 12, opacity: 0.7, fontSize: 13 }}>
                Showing {filteredContacts.length} of {contacts?.length ?? 0} contacts
              </div>
              <div style={{ border: "1px solid #ddd", borderRadius: 10, overflow: "hidden" }}>
                <table style={{ width: "100%", borderCollapse: "collapse" }}>
                  <thead>
                    <tr style={{ background: "#f7f7f7" }}>
                      <th style={{ textAlign: "left", padding: "10px 12px" }}>ID</th>
                      <th style={{ textAlign: "left", padding: "10px 12px" }}>Service</th>
                      <th style={{ textAlign: "left", padding: "10px 12px" }}>Country</th>
                      <th style={{ textAlign: "center", padding: "10px 12px" }}></th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredContacts.map((c) => (
                      <tr key={c.rowid} style={{ borderTop: "1px solid #eee" }}>
                        <td style={{ padding: "10px 12px", fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace", fontSize: 13 }}>
                          {c.id}
                        </td>
                        <td style={{ padding: "10px 12px" }}>
                          <span
                            style={{
                              display: "inline-block",
                              padding: "2px 8px",
                              borderRadius: 4,
                              fontSize: 12,
                              background: c.service === "iMessage" ? "#e3f2fd" : "#f3e5f5",
                              color: c.service === "iMessage" ? "#1565c0" : "#7b1fa2",
                            }}
                          >
                            {c.service}
                          </span>
                        </td>
                        <td style={{ padding: "10px 12px", opacity: c.country ? 1 : 0.4 }}>
                          {c.country || "—"}
                        </td>
                        <td style={{ padding: "10px 12px", textAlign: "center" }}>
                          <button
                            onClick={() => setSelectedContactId(c.id)}
                            style={{
                              padding: "6px 12px",
                              fontSize: 13,
                              cursor: "pointer",
                              border: "1px solid #ddd",
                              borderRadius: 6,
                              background: "#fff",
                            }}
                          >
                            View
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </section>
      )}

      {tab === "contacts" && selectedContactId && (
        <section>
          <button
            onClick={() => setSelectedContactId(null)}
            style={{
              marginBottom: 16,
              padding: "8px 16px",
              fontSize: 14,
              cursor: "pointer",
              border: "1px solid #ddd",
              borderRadius: 6,
              background: "#fff",
            }}
          >
            ← Back to Contacts
          </button>

          {contactDetailLoading ? (
            <div>Loading…</div>
          ) : !contactDetail ? (
            <div>Contact not found.</div>
          ) : (
            <div>
              <h2 style={{ marginTop: 0, marginBottom: 8 }}>{contactDetail.contact.id}</h2>

              {/* Contact Info */}
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 12, marginBottom: 24 }}>
                <div style={{ border: "1px solid #ddd", borderRadius: 10, padding: 12 }}>
                  <div style={{ opacity: 0.7, fontSize: 12 }}>Service</div>
                  <div style={{ fontWeight: 600 }}>{contactDetail.contact.service}</div>
                </div>
                <div style={{ border: "1px solid #ddd", borderRadius: 10, padding: 12 }}>
                  <div style={{ opacity: 0.7, fontSize: 12 }}>Country</div>
                  <div style={{ fontWeight: 600 }}>{contactDetail.contact.country || "—"}</div>
                </div>
                {contactDetail.contact.person_centric_id && (
                  <div style={{ border: "1px solid #ddd", borderRadius: 10, padding: 12 }}>
                    <div style={{ opacity: 0.7, fontSize: 12 }}>Person ID</div>
                    <div style={{ fontWeight: 600, fontSize: 11, fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace", wordBreak: "break-all" }}>
                      {contactDetail.contact.person_centric_id}
                    </div>
                  </div>
                )}
              </div>

              {/* Statistics */}
              <h3>Message Statistics</h3>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 12, marginBottom: 16 }}>
                <div style={{ border: "1px solid #ddd", borderRadius: 10, padding: 12 }}>
                  <div style={{ opacity: 0.7, fontSize: 12 }}>Total Messages</div>
                  <div style={{ fontSize: 24, fontWeight: 700 }}>{formatNumber(contactDetail.statistics.total_messages)}</div>
                </div>
                <div style={{ border: "1px solid #ddd", borderRadius: 10, padding: 12 }}>
                  <div style={{ opacity: 0.7, fontSize: 12 }}>Total Characters</div>
                  <div style={{ fontSize: 24, fontWeight: 700 }}>{formatNumber(contactDetail.statistics.total_characters)}</div>
                </div>
              </div>

              {/* Conversation Balance */}
              {contactDetail.statistics.total_messages > 0 && (
                <div style={{ marginBottom: 24 }}>
                  <h4 style={{ marginBottom: 8 }}>Conversation Balance</h4>
                  <div style={{ display: "flex", height: 32, borderRadius: 8, overflow: "hidden", marginBottom: 8 }}>
                    <div
                      style={{
                        width: `${contactDetail.statistics.from_me.percentage ?? 50}%`,
                        background: "#4caf50",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        color: "#fff",
                        fontWeight: 600,
                        fontSize: 13,
                        minWidth: 40,
                      }}
                    >
                      {contactDetail.statistics.from_me.percentage?.toFixed(1)}%
                    </div>
                    <div
                      style={{
                        width: `${contactDetail.statistics.from_them.percentage ?? 50}%`,
                        background: "#2196f3",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        color: "#fff",
                        fontWeight: 600,
                        fontSize: 13,
                        minWidth: 40,
                      }}
                    >
                      {contactDetail.statistics.from_them.percentage?.toFixed(1)}%
                    </div>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13 }}>
                    <span><span style={{ color: "#4caf50" }}>■</span> You: {formatNumber(contactDetail.statistics.from_me.message_count)} messages</span>
                    <span><span style={{ color: "#2196f3" }}>■</span> Them: {formatNumber(contactDetail.statistics.from_them.message_count)} messages</span>
                  </div>
                </div>
              )}

              {/* Date Range */}
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 12, marginBottom: 24 }}>
                <div style={{ border: "1px solid #ddd", borderRadius: 10, padding: 12 }}>
                  <div style={{ opacity: 0.7, fontSize: 12 }}>First Message (from you)</div>
                  <div style={{ fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace", fontSize: 13 }}>
                    {contactDetail.statistics.from_me.first_message || "—"}
                  </div>
                </div>
                <div style={{ border: "1px solid #ddd", borderRadius: 10, padding: 12 }}>
                  <div style={{ opacity: 0.7, fontSize: 12 }}>Last Message (from you)</div>
                  <div style={{ fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace", fontSize: 13 }}>
                    {contactDetail.statistics.from_me.last_message || "—"}
                  </div>
                </div>
                <div style={{ border: "1px solid #ddd", borderRadius: 10, padding: 12 }}>
                  <div style={{ opacity: 0.7, fontSize: 12 }}>First Message (from them)</div>
                  <div style={{ fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace", fontSize: 13 }}>
                    {contactDetail.statistics.from_them.first_message || "—"}
                  </div>
                </div>
                <div style={{ border: "1px solid #ddd", borderRadius: 10, padding: 12 }}>
                  <div style={{ opacity: 0.7, fontSize: 12 }}>Last Message (from them)</div>
                  <div style={{ fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace", fontSize: 13 }}>
                    {contactDetail.statistics.from_them.last_message || "—"}
                  </div>
                </div>
              </div>

              {/* Chats */}
              {contactDetail.chats.length > 0 && (
                <>
                  <h3>Chats ({contactDetail.chats.length})</h3>
                  <div style={{ border: "1px solid #ddd", borderRadius: 10, overflow: "hidden" }}>
                    <table style={{ width: "100%", borderCollapse: "collapse" }}>
                      <thead>
                        <tr style={{ background: "#f7f7f7" }}>
                          <th style={{ textAlign: "left", padding: "10px 12px" }}>Chat</th>
                          <th style={{ textAlign: "right", padding: "10px 12px" }}>Messages</th>
                        </tr>
                      </thead>
                      <tbody>
                        {contactDetail.chats.map((chat) => (
                          <tr key={chat.chat_identifier} style={{ borderTop: "1px solid #eee" }}>
                            <td style={{ padding: "10px 12px" }}>
                              <div style={{ fontWeight: chat.display_name ? 600 : 400 }}>
                                {chat.display_name || chat.chat_identifier}
                              </div>
                              {chat.display_name && (
                                <div style={{ opacity: 0.6, fontSize: 11, fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace", marginTop: 2 }}>
                                  {chat.chat_identifier}
                                </div>
                              )}
                            </td>
                            <td style={{ padding: "10px 12px", textAlign: "right" }}>{formatNumber(chat.message_count)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              )}
            </div>
          )}
        </section>
      )}
    </div>
  );
}

