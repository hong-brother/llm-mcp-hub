"use client";

import { useDetailedHealth } from "@/lib/hooks";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Database, Bot, CheckCircle, XCircle } from "lucide-react";

export function ComponentCards() {
  const { data: health, isLoading } = useDetailedHealth();

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-3">
        {[1, 2, 3].map((i) => (
          <Card key={i}>
            <CardHeader>
              <Skeleton className="h-6 w-24" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-16 w-full" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (!health?.components) {
    return null;
  }

  const componentIcons: Record<string, typeof Database> = {
    redis: Database,
    claude: Bot,
    gemini: Bot,
  };

  return (
    <div className="grid gap-4 md:grid-cols-3">
      {Object.entries(health.components).map(([name, component]) => {
        const Icon = componentIcons[name] || Database;
        const isHealthy = component.status === "healthy";

        return (
          <Card key={name}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="flex items-center gap-2 text-sm font-medium">
                <Icon className="h-4 w-4" />
                {name.charAt(0).toUpperCase() + name.slice(1)}
              </CardTitle>
              <Badge variant={isHealthy ? "success" : "destructive"}>
                {isHealthy ? (
                  <CheckCircle className="mr-1 h-3 w-3" />
                ) : (
                  <XCircle className="mr-1 h-3 w-3" />
                )}
                {component.status}
              </Badge>
            </CardHeader>
            <CardContent>
              {component.latency_ms !== undefined && (
                <p className="text-sm text-muted-foreground">
                  Latency: {component.latency_ms}ms
                </p>
              )}
              {component.supported_models && (
                <p className="text-sm text-muted-foreground">
                  Models: {component.supported_models.length}개
                </p>
              )}
              {component.error && (
                <p className="text-sm text-destructive">{component.error}</p>
              )}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
