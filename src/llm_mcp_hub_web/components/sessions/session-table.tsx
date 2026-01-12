"use client";

import Link from "next/link";
import { useSessions } from "@/lib/hooks";
import { formatRelativeTime } from "@/lib/utils";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { DeleteSessionButton } from "./delete-session-button";
import { AlertCircle, Info } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

export function SessionTable() {
  const { data, isLoading, error } = useSessions();

  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Session ID</TableHead>
                <TableHead>Provider</TableHead>
                <TableHead>Created</TableHead>
                <TableHead>Messages</TableHead>
                <TableHead className="w-24">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {[1, 2, 3].map((i) => (
                <TableRow key={i}>
                  <TableCell>
                    <Skeleton className="h-5 w-40" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-5 w-16" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-5 w-20" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-5 w-8" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-8 w-16" />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    // GET /v1/sessions API가 아직 구현되지 않은 경우
    return (
      <Alert>
        <Info className="h-4 w-4" />
        <AlertTitle>세션 목록 API 미구현</AlertTitle>
        <AlertDescription>
          백엔드에 <code>GET /v1/sessions</code> API가 구현되면 세션 목록이
          표시됩니다. 현재 개별 세션 조회 및 삭제 기능은 사용 가능합니다.
        </AlertDescription>
      </Alert>
    );
  }

  if (!data || data.sessions.length === 0) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center p-12 text-muted-foreground">
          <AlertCircle className="mr-2 h-5 w-5" />
          활성 세션이 없습니다.
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent className="p-0">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Session ID</TableHead>
              <TableHead>Provider</TableHead>
              <TableHead>Created</TableHead>
              <TableHead>Messages</TableHead>
              <TableHead className="w-24">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.sessions.map((session) => (
              <TableRow key={session.session_id}>
                <TableCell>
                  <Link
                    href={`/sessions/${session.session_id}`}
                    className="font-mono text-sm hover:underline"
                  >
                    {session.session_id.slice(0, 16)}...
                  </Link>
                </TableCell>
                <TableCell>
                  <Badge variant="secondary">{session.provider}</Badge>
                </TableCell>
                <TableCell className="text-muted-foreground">
                  {formatRelativeTime(session.created_at)}
                </TableCell>
                <TableCell>{session.message_count || "-"}</TableCell>
                <TableCell>
                  <DeleteSessionButton sessionId={session.session_id} />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
