"use client";

import { useSession } from "@/lib/hooks";
import { formatDateTime } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { DeleteSessionButton } from "./delete-session-button";
import { MessageList } from "./message-list";
import { Clock, Bot, Hash, AlertCircle } from "lucide-react";

interface SessionDetailProps {
  sessionId: string;
}

export function SessionDetail({ sessionId }: SessionDetailProps) {
  const { data: session, isLoading, error } = useSession(sessionId);

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Card>
          <CardContent className="p-6">
            <Skeleton className="h-32 w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error || !session) {
    return (
      <Card className="border-destructive">
        <CardContent className="flex items-center gap-2 p-6 text-destructive">
          <AlertCircle className="h-5 w-5" />
          <span>세션을 찾을 수 없습니다.</span>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Session Info */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>세션 정보</CardTitle>
          <DeleteSessionButton sessionId={sessionId} variant="destructive" />
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <div className="flex items-start gap-3">
              <Hash className="mt-0.5 h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium text-muted-foreground">
                  Session ID
                </p>
                <p className="break-all font-mono text-sm">
                  {session.session_id}
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <Bot className="mt-0.5 h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium text-muted-foreground">
                  Provider / Model
                </p>
                <div className="flex items-center gap-2">
                  <Badge variant="secondary">{session.provider}</Badge>
                  <span className="text-sm">{session.model}</span>
                </div>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <Clock className="mt-0.5 h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium text-muted-foreground">
                  생성 시각
                </p>
                <p className="text-sm">{formatDateTime(session.created_at)}</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <Clock className="mt-0.5 h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium text-muted-foreground">
                  만료 시각
                </p>
                <p className="text-sm">
                  {session.expires_at
                    ? formatDateTime(session.expires_at)
                    : "-"}
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Messages */}
      {session.messages && session.messages.length > 0 && (
        <MessageList messages={session.messages} />
      )}
    </div>
  );
}
