"use client";

import { cn } from "@/lib/utils";
import { User, Bot } from "lucide-react";
import type { ChatMessage as ChatMessageType } from "@/types";

interface ChatMessageProps {
  message: ChatMessageType;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <div
      className={cn(
        "flex gap-3 p-4 rounded-lg",
        isUser ? "bg-blue-50" : "bg-gray-50"
      )}
    >
      <div
        className={cn(
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
          isUser ? "bg-blue-500" : "bg-gray-500"
        )}
      >
        {isUser ? (
          <User className="h-4 w-4 text-white" />
        ) : (
          <Bot className="h-4 w-4 text-white" />
        )}
      </div>
      <div className="flex-1 space-y-1">
        <p className="text-sm font-medium">
          {isUser ? "You" : "Assistant"}
        </p>
        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
      </div>
    </div>
  );
}
