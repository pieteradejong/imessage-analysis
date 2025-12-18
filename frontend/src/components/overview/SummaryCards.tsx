import { Card, CardContent } from "@/components/ui/card";
import { Database, MessageSquare, MessagesSquare, HardDrive } from "lucide-react";
import type { Summary } from "@/api";

interface SummaryCardsProps {
  summary: Summary;
}

function formatNumber(n: number): string {
  return new Intl.NumberFormat().format(n);
}

export function SummaryCards({ summary }: SummaryCardsProps) {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center gap-4">
            <div className="rounded-full bg-primary/10 p-3">
              <MessageSquare className="h-6 w-6 text-primary" />
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Total Messages</p>
              <p className="text-2xl font-bold">{formatNumber(summary.total_messages)}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-6">
          <div className="flex items-center gap-4">
            <div className="rounded-full bg-green-500/10 p-3">
              <MessagesSquare className="h-6 w-6 text-green-500" />
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Total Chats</p>
              <p className="text-2xl font-bold">{formatNumber(summary.total_chats)}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-6">
          <div className="flex items-center gap-4">
            <div className="rounded-full bg-orange-500/10 p-3">
              <Database className="h-6 w-6 text-orange-500" />
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Tables</p>
              <p className="text-2xl font-bold">{formatNumber(summary.table_count)}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-6">
          <div className="flex items-center gap-4">
            <div className="rounded-full bg-purple-500/10 p-3">
              <HardDrive className="h-6 w-6 text-purple-500" />
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Database</p>
              <p className="text-xs font-mono text-muted-foreground truncate max-w-[180px]" title={summary.db_path ?? "unknown"}>
                {summary.db_path ?? "(unknown)"}
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                In-memory: {String(summary.use_memory ?? false)}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
