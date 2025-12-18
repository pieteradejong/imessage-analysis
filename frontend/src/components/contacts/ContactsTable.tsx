import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Search, User, MessageSquare, Send, Inbox } from "lucide-react";
import type { Contact } from "@/api";

interface ContactsTableProps {
  contacts: Contact[];
  filteredContacts: Contact[];
  searchValue: string;
  onSearchChange: (value: string) => void;
  onSelectContact: (id: string) => void;
}

function formatNumber(n: number): string {
  return new Intl.NumberFormat().format(n);
}

function getInitials(contact: Contact): string {
  // Try first/last name first
  if (contact.first_name && contact.last_name) {
    return (contact.first_name[0] + contact.last_name[0]).toUpperCase();
  }
  if (contact.first_name) {
    return contact.first_name.slice(0, 2).toUpperCase();
  }
  if (contact.last_name) {
    return contact.last_name.slice(0, 2).toUpperCase();
  }
  // Fall back to display name
  if (contact.display_name) {
    const parts = contact.display_name.split(" ").filter(Boolean);
    if (parts.length >= 2) {
      return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    }
    return contact.display_name.slice(0, 2).toUpperCase();
  }
  // Fall back to id
  return contact.id.replace(/[^a-zA-Z0-9]/g, "").slice(0, 2).toUpperCase() || "??";
}

function getDisplayName(contact: Contact): string | null {
  if (contact.display_name) return contact.display_name;
  if (contact.first_name && contact.last_name) {
    return `${contact.first_name} ${contact.last_name}`;
  }
  if (contact.first_name) return contact.first_name;
  if (contact.last_name) return contact.last_name;
  return null;
}

function getSourceBadge(source: string | null | undefined) {
  if (!source) return null;
  
  const variants: Record<string, { label: string; className: string }> = {
    contacts: { label: "Contacts", className: "bg-green-100 text-green-800" },
    inferred: { label: "Inferred", className: "bg-yellow-100 text-yellow-800" },
    manual: { label: "Manual", className: "bg-blue-100 text-blue-800" },
  };
  
  const config = variants[source] || { label: source, className: "bg-gray-100 text-gray-800" };
  
  return (
    <span className={`text-[10px] px-1.5 py-0.5 rounded ${config.className}`}>
      {config.label}
    </span>
  );
}

export function ContactsTable({
  contacts,
  filteredContacts,
  searchValue,
  onSearchChange,
  onSelectContact,
}: ContactsTableProps) {
  // Check if we have enriched data (from analysis.db)
  const hasEnrichedData = filteredContacts.some(c => c.person_source !== undefined);
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Contacts</CardTitle>
        <CardDescription>
          {filteredContacts.length === contacts.length
            ? `${contacts.length} contacts`
            : `Showing ${filteredContacts.length} of ${contacts.length} contacts`}
          {hasEnrichedData && (
            <span className="ml-2 text-green-600">• Enriched with names</span>
          )}
        </CardDescription>
        <div className="relative mt-2">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search by name, phone, or email..."
            value={searchValue}
            onChange={(e) => onSearchChange(e.target.value)}
            className="pl-9 max-w-md"
          />
        </div>
      </CardHeader>
      <CardContent>
        {filteredContacts.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground">
            <User className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No contacts found.</p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Contact</TableHead>
                <TableHead>Type</TableHead>
                <TableHead className="text-right">Messages</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredContacts.map((contact) => {
                const displayName = getDisplayName(contact);
                
                return (
                  <TableRow 
                    key={contact.rowid}
                    className="cursor-pointer"
                    onClick={() => onSelectContact(contact.id)}
                  >
                    <TableCell>
                      <div className="flex items-center gap-3">
                        {/* Avatar */}
                        <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center text-sm font-medium text-primary flex-shrink-0">
                          {getInitials(contact)}
                        </div>
                        
                        {/* Name & ID */}
                        <div className="min-w-0 flex-1">
                          {displayName ? (
                            <>
                              <div className="font-medium truncate flex items-center gap-2">
                                {displayName}
                                {getSourceBadge(contact.person_source)}
                              </div>
                              <div className="text-xs text-muted-foreground font-mono truncate">
                                {contact.id}
                              </div>
                            </>
                          ) : (
                            <div className="font-mono text-sm truncate">
                              {contact.id}
                            </div>
                          )}
                          
                          {/* Date range if available */}
                          {contact.first_message && (
                            <div className="text-[10px] text-muted-foreground mt-0.5">
                              {contact.first_message.split(" ")[0]} — {contact.last_message?.split(" ")[0]}
                            </div>
                          )}
                        </div>
                      </div>
                    </TableCell>
                    
                    <TableCell>
                      <div className="flex flex-col gap-1">
                        <Badge
                          variant={contact.service === "iMessage" ? "default" : "secondary"}
                          className="w-fit"
                        >
                          {contact.handle_type || contact.service}
                        </Badge>
                        {contact.country && (
                          <span className="text-xs text-muted-foreground">
                            {contact.country}
                          </span>
                        )}
                      </div>
                    </TableCell>
                    
                    <TableCell className="text-right">
                      <div className="space-y-1">
                        <div className="flex items-center justify-end gap-1.5">
                          <MessageSquare className="h-3.5 w-3.5 text-muted-foreground" />
                          <span className="font-semibold">
                            {formatNumber(contact.message_count)}
                          </span>
                        </div>
                        
                        {/* Sent/Received breakdown */}
                        {(contact.sent_count !== undefined || contact.received_count !== undefined) && (
                          <div className="flex items-center justify-end gap-3 text-xs text-muted-foreground">
                            <span className="flex items-center gap-1">
                              <Send className="h-3 w-3" />
                              {formatNumber(contact.sent_count || 0)}
                            </span>
                            <span className="flex items-center gap-1">
                              <Inbox className="h-3 w-3" />
                              {formatNumber(contact.received_count || 0)}
                            </span>
                          </div>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
