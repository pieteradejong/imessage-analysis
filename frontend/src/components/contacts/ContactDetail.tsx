import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, MessageSquare, Type, Calendar, User, Phone, Mail } from "lucide-react";
import type { ContactDetail as ContactDetailType } from "@/api";

interface ContactDetailProps {
  detail: ContactDetailType;
  onBack: () => void;
}

function formatNumber(n: number): string {
  return new Intl.NumberFormat().format(n);
}

function getInitials(contact: ContactDetailType["contact"]): string {
  const c = contact as any; // Handle extended fields
  if (c.first_name && c.last_name) {
    return (c.first_name[0] + c.last_name[0]).toUpperCase();
  }
  if (c.first_name) return c.first_name.slice(0, 2).toUpperCase();
  if (c.last_name) return c.last_name.slice(0, 2).toUpperCase();
  if (c.display_name) {
    const parts = c.display_name.split(" ").filter(Boolean);
    if (parts.length >= 2) return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    return c.display_name.slice(0, 2).toUpperCase();
  }
  return contact.id.replace(/[^a-zA-Z0-9]/g, "").slice(0, 2).toUpperCase() || "??";
}

function getDisplayName(contact: ContactDetailType["contact"]): string | null {
  const c = contact as any;
  if (c.display_name) return c.display_name;
  if (c.first_name && c.last_name) return `${c.first_name} ${c.last_name}`;
  if (c.first_name) return c.first_name;
  if (c.last_name) return c.last_name;
  return null;
}

export function ContactDetail({ detail, onBack }: ContactDetailProps) {
  const { contact, statistics, chats } = detail;
  const displayName = getDisplayName(contact);
  const extContact = contact as any; // Extended contact fields

  return (
    <div className="space-y-6">
      <Button variant="ghost" onClick={onBack} className="gap-2">
        <ArrowLeft className="h-4 w-4" />
        Back to Contacts
      </Button>

      {/* Contact Header */}
      <div className="flex items-start gap-4">
        {/* Large Avatar */}
        <div className="h-20 w-20 rounded-full bg-primary/10 flex items-center justify-center text-2xl font-semibold text-primary flex-shrink-0">
          {getInitials(contact)}
        </div>
        
        <div className="flex-1 min-w-0">
          {displayName ? (
            <>
              <h2 className="text-2xl font-bold tracking-tight">{displayName}</h2>
              <div className="flex items-center gap-2 mt-1 text-muted-foreground">
                {extContact.handle_type === "phone" ? (
                  <Phone className="h-4 w-4" />
                ) : extContact.handle_type === "email" ? (
                  <Mail className="h-4 w-4" />
                ) : (
                  <User className="h-4 w-4" />
                )}
                <span className="font-mono">{contact.id}</span>
              </div>
            </>
          ) : (
            <h2 className="text-2xl font-bold tracking-tight font-mono">{contact.id}</h2>
          )}
          
          <div className="flex items-center gap-2 mt-2 flex-wrap">
            <Badge variant={contact.service === "iMessage" ? "default" : "secondary"}>
              {extContact.handle_type || contact.service}
            </Badge>
            {contact.country && (
              <span className="text-sm text-muted-foreground">{contact.country}</span>
            )}
            {extContact.person_source && (
              <Badge variant="outline" className="text-xs">
                {extContact.person_source === "contacts" ? "From Contacts" : 
                 extContact.person_source === "inferred" ? "Inferred" : extContact.person_source}
              </Badge>
            )}
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="rounded-full bg-primary/10 p-3">
                <MessageSquare className="h-6 w-6 text-primary" />
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Messages</p>
                <p className="text-3xl font-bold">{formatNumber(statistics.total_messages)}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="rounded-full bg-green-500/10 p-3">
                <Type className="h-6 w-6 text-green-500" />
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Characters</p>
                <p className="text-3xl font-bold">{formatNumber(statistics.total_characters)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Conversation Balance */}
      {statistics.total_messages > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Conversation Balance</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex h-8 overflow-hidden rounded-full">
                <div
                  className="flex items-center justify-center bg-green-500 text-white text-sm font-medium transition-all"
                  style={{ width: `${statistics.from_me.percentage ?? 50}%`, minWidth: "40px" }}
                >
                  {statistics.from_me.percentage?.toFixed(1)}%
                </div>
                <div
                  className="flex items-center justify-center bg-primary text-white text-sm font-medium transition-all"
                  style={{ width: `${statistics.from_them.percentage ?? 50}%`, minWidth: "40px" }}
                >
                  {statistics.from_them.percentage?.toFixed(1)}%
                </div>
              </div>
              <div className="flex justify-between text-sm">
                <div className="flex items-center gap-2">
                  <div className="h-3 w-3 rounded-full bg-green-500" />
                  <span>You: {formatNumber(statistics.from_me.message_count)} messages</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="h-3 w-3 rounded-full bg-primary" />
                  <span>Them: {formatNumber(statistics.from_them.message_count)} messages</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Date Range */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-muted-foreground mb-1">
              <Calendar className="h-4 w-4" />
              <span className="text-xs">First (from you)</span>
            </div>
            <p className="font-mono text-sm">
              {statistics.from_me.first_message || "—"}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-muted-foreground mb-1">
              <Calendar className="h-4 w-4" />
              <span className="text-xs">Last (from you)</span>
            </div>
            <p className="font-mono text-sm">
              {statistics.from_me.last_message || "—"}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-muted-foreground mb-1">
              <Calendar className="h-4 w-4" />
              <span className="text-xs">First (from them)</span>
            </div>
            <p className="font-mono text-sm">
              {statistics.from_them.first_message || "—"}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-muted-foreground mb-1">
              <Calendar className="h-4 w-4" />
              <span className="text-xs">Last (from them)</span>
            </div>
            <p className="font-mono text-sm">
              {statistics.from_them.last_message || "—"}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Chats */}
      {chats.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Chats ({chats.length})</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Chat</TableHead>
                  <TableHead className="text-right">Messages</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {chats.map((chat) => (
                  <TableRow key={chat.chat_identifier}>
                    <TableCell>
                      <div className="font-medium">
                        {chat.display_name || chat.chat_identifier}
                      </div>
                      {chat.display_name && (
                        <div className="text-xs text-muted-foreground font-mono mt-0.5">
                          {chat.chat_identifier}
                        </div>
                      )}
                    </TableCell>
                    <TableCell className="text-right font-medium">
                      {formatNumber(chat.message_count)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
