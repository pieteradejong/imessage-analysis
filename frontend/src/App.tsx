import { useEffect, useMemo, useState } from "react";
import {
  fetchLatest,
  fetchSummary,
  fetchTopChats,
  fetchContacts,
  fetchContactDetail,
  fetchDiagnostics,
  getApiBaseUrl,
} from "./api";
import type {
  LatestMessage,
  Summary,
  TopChat,
  Contact,
  ContactDetail,
  DiagnosticsData,
} from "./api";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Header } from "@/components/layout/Header";
import { SummaryCards } from "@/components/overview/SummaryCards";
import { TopChatsTable } from "@/components/overview/TopChatsTable";
import { MessageCard } from "@/components/latest/MessageCard";
import { ContactsTable } from "@/components/contacts/ContactsTable";
import { ContactDetail as ContactDetailComponent } from "@/components/contacts/ContactDetail";
import { DiagnosticsPanel } from "@/components/diagnostics/DiagnosticsPanel";
import { AlertCircle, RefreshCw, Loader2 } from "lucide-react";

type Tab = "contacts" | "latest" | "dashboard" | "diagnostics";

export function App() {
  const [tab, setTab] = useState<Tab>("contacts");
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

  // Diagnostics state
  const [diagnostics, setDiagnostics] = useState<DiagnosticsData | null>(null);
  const [diagnosticsLoading, setDiagnosticsLoading] = useState(false);
  const [diagnosticsError, setDiagnosticsError] = useState<string | null>(null);

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

    if (tab === "dashboard") {
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

  // Load diagnostics when tab is selected
  useEffect(() => {
    let cancelled = false;

    async function loadDiagnostics() {
      setDiagnosticsLoading(true);
      setDiagnosticsError(null);

      try {
        const data = await fetchDiagnostics();
        if (cancelled) return;
        setDiagnostics(data);
      } catch (e) {
        if (cancelled) return;
        setDiagnosticsError(e instanceof Error ? e.message : String(e));
      } finally {
        if (!cancelled) setDiagnosticsLoading(false);
      }
    }

    if (tab === "diagnostics") {
      loadDiagnostics();
    }

    return () => {
      cancelled = true;
    };
  }, [tab]);

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
    if (!contacts) return [];
    if (!contactSearch.trim()) return contacts;
    const search = contactSearch.toLowerCase();
    return contacts.filter(
      (c) =>
        c.id.toLowerCase().includes(search) ||
        c.service.toLowerCase().includes(search) ||
        (c.country && c.country.toLowerCase().includes(search)) ||
        (c.display_name && c.display_name.toLowerCase().includes(search)) ||
        (c.first_name && c.first_name.toLowerCase().includes(search)) ||
        (c.last_name && c.last_name.toLowerCase().includes(search))
    );
  }, [contacts, contactSearch]);

  return (
    <div className="min-h-screen bg-background">
      <Header apiBaseUrl={apiBaseUrl} />

      <main className="container max-w-screen-xl py-6">
        {error && (
          <Card className="mb-6 border-destructive">
            <CardContent className="p-4">
              <div className="flex items-start gap-3">
                <AlertCircle className="h-5 w-5 text-destructive mt-0.5" />
                <div>
                  <p className="font-semibold text-destructive">Error</p>
                  <p className="text-sm text-muted-foreground whitespace-pre-wrap mt-1">
                    {error}
                  </p>
                  <p className="text-xs text-muted-foreground mt-2">
                    If analysis.db is not found, run <code className="bg-muted px-1 rounded">./run_etl.sh</code> first.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        <Tabs value={tab} onValueChange={(v) => { setTab(v as Tab); setSelectedContactId(null); }}>
          <TabsList className="mb-6">
            <TabsTrigger value="contacts">Contacts</TabsTrigger>
            <TabsTrigger value="latest">Latest</TabsTrigger>
            <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
            <TabsTrigger value="diagnostics">Diagnostics</TabsTrigger>
          </TabsList>

          <TabsContent value="dashboard" className="space-y-6">
            {!summary ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            ) : (
              <>
                <SummaryCards summary={summary} />
                {topChats && <TopChatsTable chats={topChats} />}
              </>
            )}
          </TabsContent>

          <TabsContent value="latest" className="space-y-4">
            <Card>
              <CardHeader className="pb-4">
                <CardTitle className="text-lg">Latest Messages</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-3">
                  <label className="text-sm text-muted-foreground">Limit</label>
                  <Input
                    type="number"
                    min={1}
                    max={500}
                    value={latestLimit}
                    onChange={(e) => setLatestLimit(Number(e.target.value))}
                    className="w-24"
                  />
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setLatest(null)}
                    className="gap-2"
                  >
                    <RefreshCw className="h-4 w-4" />
                    Refresh
                  </Button>
                </div>
              </CardContent>
            </Card>

            {!latest ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            ) : (
              <div className="space-y-3">
                {latest.map((message, idx) => (
                  <MessageCard key={`${message.date}-${idx}`} message={message} />
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="contacts">
            {selectedContactId ? (
              contactDetailLoading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
              ) : contactDetail ? (
                <ContactDetailComponent
                  detail={contactDetail}
                  onBack={() => setSelectedContactId(null)}
                />
              ) : (
                <div className="text-center py-12 text-muted-foreground">
                  Contact not found.
                </div>
              )
            ) : !contacts ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            ) : (
              <ContactsTable
                contacts={contacts}
                filteredContacts={filteredContacts}
                searchValue={contactSearch}
                onSearchChange={setContactSearch}
                onSelectContact={setSelectedContactId}
              />
            )}
          </TabsContent>

          <TabsContent value="diagnostics">
            <DiagnosticsPanel
              data={diagnostics}
              loading={diagnosticsLoading}
              error={diagnosticsError}
            />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
