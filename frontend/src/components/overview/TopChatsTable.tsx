import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { TopChat } from "@/api";

interface TopChatsTableProps {
  chats: TopChat[];
}

function formatNumber(n: number): string {
  return new Intl.NumberFormat().format(n);
}

export function TopChatsTable({ chats }: TopChatsTableProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Top Chats</CardTitle>
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
  );
}
