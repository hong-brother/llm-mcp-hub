"use client";

import { useProviders, useDetailedHealth } from "@/lib/hooks";
import { ProviderCard } from "./provider-card";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent } from "@/components/ui/card";
import { AlertCircle } from "lucide-react";

export function ProviderGrid() {
  const { data: providers, isLoading, error } = useProviders();
  const { data: health } = useDetailedHealth();

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

  if (error || !providers) {
    return (
      <Card className="border-destructive">
        <CardContent className="flex items-center gap-2 p-6 text-destructive">
          <AlertCircle className="h-5 w-5" />
          <span>프로바이더 정보를 불러올 수 없습니다.</span>
        </CardContent>
      </Card>
    );
  }

  if (providers.length === 0) {
    return (
      <Card>
        <CardContent className="p-6 text-center text-muted-foreground">
          연동된 프로바이더가 없습니다.
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {providers.map((provider) => {
        const componentHealth = health?.components?.[provider.name];
        const status = componentHealth?.status === "healthy" ? "healthy" : "unhealthy";

        return (
          <ProviderCard
            key={provider.name}
            provider={provider}
            status={status}
          />
        );
      })}
    </div>
  );
}
