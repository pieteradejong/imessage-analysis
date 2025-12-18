import { MessageSquare } from "lucide-react";

interface HeaderProps {
  apiBaseUrl: string;
}

export function Header({ apiBaseUrl }: HeaderProps) {
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 max-w-screen-xl items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-primary p-2">
            <MessageSquare className="h-5 w-5 text-primary-foreground" />
          </div>
          <div>
            <h1 className="text-lg font-semibold tracking-tight">iMessage Analysis</h1>
            <p className="text-xs text-muted-foreground">Explore your message history</p>
          </div>
        </div>
        <div className="hidden sm:block text-xs text-muted-foreground">
          API: <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-[10px]">{apiBaseUrl}</code>
        </div>
      </div>
    </header>
  );
}
