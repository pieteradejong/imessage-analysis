import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { 
  Database, 
  Users, 
  MessageSquare, 
  CheckCircle, 
  XCircle, 
  AlertCircle,
  UserCheck,
  UserX,
  Calendar,
  Image,
} from "lucide-react";

interface DiagnosticsData {
  status: string;
  analysis_db_exists: boolean;
  analysis_db_path: string;
  message?: string;
  counts?: {
    handles: number;
    persons: number;
    messages: number;
    contact_methods: number;
  };
  enrichment?: {
    handles_total: number;
    handles_with_names: number;
    handles_from_contacts: number;
    handles_unlinked: number;
    name_coverage_percent: number;
    contacts_coverage_percent: number;
  };
  person_sources?: Record<string, number>;
  handle_types?: Record<string, number>;
  date_range?: {
    first_message: string | null;
    last_message: string | null;
  };
  etl_state?: Record<string, string>;
  top_contacts_sample?: Array<{
    id: string;
    display_name: string | null;
    source: string | null;
    message_count: number;
    has_name: boolean;
  }>;
  profile_pictures?: {
    supported: boolean;
    message: string;
  };
}

interface DiagnosticsPanelProps {
  data: DiagnosticsData | null;
  loading: boolean;
  error: string | null;
}

function formatNumber(n: number): string {
  return new Intl.NumberFormat().format(n);
}

function StatusIcon({ status }: { status: string }) {
  if (status === "ok") {
    return <CheckCircle className="h-5 w-5 text-green-500" />;
  }
  if (status === "not_initialized") {
    return <AlertCircle className="h-5 w-5 text-yellow-500" />;
  }
  return <XCircle className="h-5 w-5 text-red-500" />;
}

export function DiagnosticsPanel({ data, loading, error }: DiagnosticsPanelProps) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    );
  }

  if (error) {
    return (
      <Card className="border-destructive">
        <CardContent className="p-6">
          <div className="flex items-center gap-3">
            <XCircle className="h-6 w-6 text-destructive" />
            <div>
              <p className="font-semibold">Error loading diagnostics</p>
              <p className="text-sm text-muted-foreground">{error}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!data) {
    return null;
  }

  // Not initialized state
  if (data.status === "not_initialized") {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center gap-3 mb-4">
            <AlertCircle className="h-6 w-6 text-yellow-500" />
            <div>
              <p className="font-semibold">Analysis database not initialized</p>
              <p className="text-sm text-muted-foreground">{data.message}</p>
            </div>
          </div>
          <code className="block bg-muted p-3 rounded text-sm">
            ./run_etl.sh
          </code>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Status Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <StatusIcon status={data.status} />
              <div>
                <CardTitle>Analysis Database</CardTitle>
                <CardDescription className="font-mono text-xs mt-1">
                  {data.analysis_db_path}
                </CardDescription>
              </div>
            </div>
            <Badge variant={data.status === "ok" ? "default" : "destructive"}>
              {data.status === "ok" ? "Healthy" : data.status}
            </Badge>
          </div>
        </CardHeader>
      </Card>

      {/* Counts Grid */}
      {data.counts && (
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <Users className="h-8 w-8 text-primary opacity-80" />
                <div>
                  <p className="text-2xl font-bold">{formatNumber(data.counts.handles)}</p>
                  <p className="text-xs text-muted-foreground">Contacts/Handles</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <UserCheck className="h-8 w-8 text-green-500 opacity-80" />
                <div>
                  <p className="text-2xl font-bold">{formatNumber(data.counts.persons)}</p>
                  <p className="text-xs text-muted-foreground">Resolved Persons</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <MessageSquare className="h-8 w-8 text-blue-500 opacity-80" />
                <div>
                  <p className="text-2xl font-bold">{formatNumber(data.counts.messages)}</p>
                  <p className="text-xs text-muted-foreground">Messages</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <Database className="h-8 w-8 text-purple-500 opacity-80" />
                <div>
                  <p className="text-2xl font-bold">{formatNumber(data.counts.contact_methods)}</p>
                  <p className="text-xs text-muted-foreground">Contact Methods</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Enrichment Stats */}
      {data.enrichment && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Contact Enrichment</CardTitle>
            <CardDescription>
              How many contacts have names from your Contacts app
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Name Coverage Bar */}
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>Contacts with Names</span>
                  <span className="font-medium">
                    {data.enrichment.handles_with_names} / {data.enrichment.handles_total}
                    ({data.enrichment.name_coverage_percent}%)
                  </span>
                </div>
                <div className="h-3 bg-muted rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-green-500 transition-all"
                    style={{ width: `${data.enrichment.name_coverage_percent}%` }}
                  />
                </div>
              </div>

              {/* From Contacts Bar */}
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>Matched to Contacts App</span>
                  <span className="font-medium">
                    {data.enrichment.handles_from_contacts} / {data.enrichment.handles_total}
                    ({data.enrichment.contacts_coverage_percent}%)
                  </span>
                </div>
                <div className="h-3 bg-muted rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-blue-500 transition-all"
                    style={{ width: `${data.enrichment.contacts_coverage_percent}%` }}
                  />
                </div>
              </div>

              {/* Stats breakdown */}
              <div className="grid grid-cols-3 gap-4 pt-4 border-t">
                <div className="text-center">
                  <div className="flex items-center justify-center gap-1 text-green-600">
                    <UserCheck className="h-4 w-4" />
                    <span className="text-lg font-semibold">{data.enrichment.handles_with_names}</span>
                  </div>
                  <p className="text-xs text-muted-foreground">With Names</p>
                </div>
                <div className="text-center">
                  <div className="flex items-center justify-center gap-1 text-blue-600">
                    <Users className="h-4 w-4" />
                    <span className="text-lg font-semibold">{data.enrichment.handles_from_contacts}</span>
                  </div>
                  <p className="text-xs text-muted-foreground">From Contacts</p>
                </div>
                <div className="text-center">
                  <div className="flex items-center justify-center gap-1 text-yellow-600">
                    <UserX className="h-4 w-4" />
                    <span className="text-lg font-semibold">{data.enrichment.handles_unlinked}</span>
                  </div>
                  <p className="text-xs text-muted-foreground">Unlinked</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Profile Pictures Status */}
      {data.profile_pictures && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Image className="h-5 w-5" />
              Profile Pictures
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-3">
              {data.profile_pictures.supported ? (
                <CheckCircle className="h-5 w-5 text-green-500" />
              ) : (
                <AlertCircle className="h-5 w-5 text-yellow-500" />
              )}
              <span className="text-sm text-muted-foreground">
                {data.profile_pictures.message}
              </span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Date Range */}
      {data.date_range && (data.date_range.first_message || data.date_range.last_message) && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Message Date Range
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-muted-foreground">First Message</p>
                <p className="font-mono text-sm">{data.date_range.first_message || "—"}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Last Message</p>
                <p className="font-mono text-sm">{data.date_range.last_message || "—"}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Person Sources & Handle Types */}
      <div className="grid gap-4 md:grid-cols-2">
        {data.person_sources && Object.keys(data.person_sources).length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Person Sources</CardTitle>
              <CardDescription>Where contact names come from</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {Object.entries(data.person_sources).map(([source, count]) => (
                  <div key={source} className="flex justify-between items-center">
                    <Badge variant={source === "contacts" ? "default" : "secondary"}>
                      {source}
                    </Badge>
                    <span className="font-mono">{formatNumber(count)}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {data.handle_types && Object.keys(data.handle_types).length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Handle Types</CardTitle>
              <CardDescription>Phone numbers vs emails</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {Object.entries(data.handle_types).map(([type, count]) => (
                  <div key={type} className="flex justify-between items-center">
                    <Badge variant="outline">{type}</Badge>
                    <span className="font-mono">{formatNumber(count)}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Top Contacts Sample */}
      {data.top_contacts_sample && data.top_contacts_sample.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Top 10 Contacts (Sample)</CardTitle>
            <CardDescription>Most messaged contacts and their enrichment status</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Contact</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Source</TableHead>
                  <TableHead className="text-right">Messages</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.top_contacts_sample.map((contact, idx) => (
                  <TableRow key={idx}>
                    <TableCell className="font-mono text-xs">{contact.id}</TableCell>
                    <TableCell>
                      {contact.has_name ? (
                        <span className="flex items-center gap-1">
                          <CheckCircle className="h-3 w-3 text-green-500" />
                          {contact.display_name}
                        </span>
                      ) : (
                        <span className="flex items-center gap-1 text-muted-foreground">
                          <XCircle className="h-3 w-3" />
                          No name
                        </span>
                      )}
                    </TableCell>
                    <TableCell>
                      {contact.source && (
                        <Badge variant={contact.source === "contacts" ? "default" : "secondary"} className="text-xs">
                          {contact.source}
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-right font-mono">
                      {formatNumber(contact.message_count)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* ETL State */}
      {data.etl_state && Object.keys(data.etl_state).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">ETL State</CardTitle>
            <CardDescription>Last sync information</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 font-mono text-sm">
              {Object.entries(data.etl_state).map(([key, value]) => (
                <div key={key} className="flex justify-between">
                  <span className="text-muted-foreground">{key}</span>
                  <span>{value}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
