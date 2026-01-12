"use client";

import { useTokenHealth } from "@/lib/hooks";
import { TokenCard } from "./token-card";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertCircle } from "lucide-react";

export function TokenCardList() {
  const { data: tokens, isLoading, error } = useTokenHealth();

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2">
        {[1, 2].map((i) => (
          <Card key={i}>
            <CardContent className="p-6">
              <Skeleton className="h-40 w-full" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (error || !tokens) {
    return (
      <Card className="border-destructive">
        <CardContent className="flex items-center gap-2 p-6 text-destructive">
          <AlertCircle className="h-5 w-5" />
          <span>토큰 상태를 불러올 수 없습니다.</span>
        </CardContent>
      </Card>
    );
  }

  const tokenEntries = Object.entries(tokens).filter(
    ([, status]) => status !== null && status !== undefined
  );

  if (tokenEntries.length === 0) {
    return (
      <Card>
        <CardContent className="p-6 text-center text-muted-foreground">
          등록된 토큰이 없습니다.
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {tokenEntries.map(([provider, status]) => (
        <TokenCard key={provider} provider={provider} status={status!} />
      ))}
    </div>
  );
}
