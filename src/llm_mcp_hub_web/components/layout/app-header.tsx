"use client";

import { useHealth } from "@/lib/hooks";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

export function AppHeader() {
  const { data: health, isLoading } = useHealth();

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b bg-background px-6">
      <div />
      <div className="flex items-center gap-4">
        {isLoading ? (
          <Skeleton className="h-5 w-20" />
        ) : health ? (
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">System:</span>
            <Badge
              variant={
                health.status === "healthy"
                  ? "success"
                  : health.status === "degraded"
                    ? "warning"
                    : "destructive"
              }
            >
              {health.status}
            </Badge>
          </div>
        ) : null}
        <span className="text-sm text-muted-foreground">
          v{health?.version || "-"}
        </span>
      </div>
    </header>
  );
}
