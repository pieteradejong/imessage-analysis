import { cn } from "@/lib/utils";
import type { LatestMessage } from "@/api";

interface MessageCardProps {
  message: LatestMessage;
}

export function MessageCard({ message }: MessageCardProps) {
  // Don't render empty messages
  const hasContent = message.text && message.text.trim().length > 0;
  
  if (!hasContent) {
    return (
      <div className={cn(
        "flex",
        message.is_from_me ? "justify-end" : "justify-start"
      )}>
        <div className={cn(
          "max-w-[85%] sm:max-w-[70%]",
          message.is_from_me ? "items-end" : "items-start"
        )}>
          <div className={cn(
            "rounded-2xl px-4 py-2.5 shadow-sm",
            message.is_from_me 
              ? "bg-primary text-primary-foreground rounded-br-md" 
              : "bg-muted rounded-bl-md"
          )}>
            {!message.is_from_me && (
              <p className="text-xs font-medium mb-1 opacity-80">
                {message.display_name || message.handle_id || "Unknown"}
              </p>
            )}
            <p className="text-sm italic opacity-60">
              [attachment or empty message]
            </p>
          </div>
          <div className={cn(
            "flex items-center gap-2 mt-1 px-2",
            message.is_from_me ? "justify-end" : "justify-start"
          )}>
            <time className="text-[10px] text-muted-foreground font-mono">
              {message.date}
            </time>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={cn(
      "flex",
      message.is_from_me ? "justify-end" : "justify-start"
    )}>
      <div className={cn(
        "max-w-[85%] sm:max-w-[70%]",
        message.is_from_me ? "items-end" : "items-start"
      )}>
        <div className={cn(
          "rounded-2xl px-4 py-2.5 shadow-sm",
          message.is_from_me 
            ? "bg-primary text-primary-foreground rounded-br-md" 
            : "bg-muted rounded-bl-md"
        )}>
          {!message.is_from_me && (
            <p className={cn(
              "text-xs font-medium mb-1",
              message.is_from_me ? "text-primary-foreground/80" : "text-muted-foreground"
            )}>
              {message.display_name || message.handle_id || "Unknown"}
            </p>
          )}
          <p className="text-sm whitespace-pre-wrap break-words">
            {message.text}
          </p>
        </div>
        <div className={cn(
          "flex items-center gap-2 mt-1 px-2",
          message.is_from_me ? "justify-end" : "justify-start"
        )}>
          <time className="text-[10px] text-muted-foreground font-mono">
            {message.date}
          </time>
          {!message.is_from_me && message.display_name && message.handle_id && (
            <span className="text-[10px] text-muted-foreground font-mono truncate max-w-[150px]">
              {message.handle_id}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
