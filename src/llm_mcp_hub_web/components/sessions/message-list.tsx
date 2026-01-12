"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { User, Bot, Settings } from "lucide-react";
import { cn } from "@/lib/utils";
import type { SessionMessage } from "@/types";

interface MessageListProps {
  messages: SessionMessage[];
}

export function MessageList({ messages }: MessageListProps) {
  const getRoleConfig = (role: string) => {
    switch (role) {
      case "user":
        return {
          icon: User,
          label: "User",
          bgColor: "bg-blue-50",
          borderColor: "border-l-blue-500",
        };
      case "assistant":
        return {
          icon: Bot,
          label: "Assistant",
          bgColor: "bg-green-50",
          borderColor: "border-l-green-500",
        };
      case "system":
        return {
          icon: Settings,
          label: "System",
          bgColor: "bg-gray-50",
          borderColor: "border-l-gray-500",
        };
      default:
        return {
          icon: User,
          label: role,
          bgColor: "bg-gray-50",
          borderColor: "border-l-gray-500",
        };
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>대화 내역 ({messages.length})</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {messages.map((message, index) => {
          const config = getRoleConfig(message.role);
          const Icon = config.icon;

          return (
            <div
              key={index}
              className={cn(
                "rounded-lg border-l-4 p-4",
                config.bgColor,
                config.borderColor
              )}
            >
              <div className="mb-2 flex items-center gap-2">
                <Icon className="h-4 w-4" />
                <span className="text-sm font-medium">{config.label}</span>
                {message.timestamp && (
                  <span className="text-xs text-muted-foreground">
                    {new Date(message.timestamp).toLocaleTimeString("ko-KR")}
                  </span>
                )}
              </div>
              <p className="whitespace-pre-wrap text-sm">{message.content}</p>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
