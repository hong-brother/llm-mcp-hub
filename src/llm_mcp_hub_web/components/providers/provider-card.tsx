"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Bot, CheckCircle, XCircle } from "lucide-react";
import type { ProviderInfo } from "@/types";

interface ProviderCardProps {
  provider: ProviderInfo;
  status?: "healthy" | "unhealthy";
}

export function ProviderCard({ provider, status = "healthy" }: ProviderCardProps) {
  const isHealthy = status === "healthy";

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="flex items-center gap-2">
          <Bot className="h-5 w-5" />
          {provider.name.charAt(0).toUpperCase() + provider.name.slice(1)}
        </CardTitle>
        <Badge variant={isHealthy ? "success" : "destructive"}>
          {isHealthy ? (
            <CheckCircle className="mr-1 h-3 w-3" />
          ) : (
            <XCircle className="mr-1 h-3 w-3" />
          )}
          {isHealthy ? "available" : "unavailable"}
        </Badge>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <p className="text-sm font-medium text-muted-foreground">
            기본 모델
          </p>
          <p className="font-mono text-sm">{provider.default_model}</p>
        </div>
        <div>
          <p className="mb-2 text-sm font-medium text-muted-foreground">
            지원 모델 ({provider.models.length})
          </p>
          <div className="flex flex-wrap gap-1">
            {provider.models.map((model) => (
              <Badge key={model} variant="outline" className="font-mono text-xs">
                {model}
              </Badge>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
