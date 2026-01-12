"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Key,
  CheckCircle,
  AlertTriangle,
  XCircle,
  ExternalLink,
} from "lucide-react";
import type { TokenStatus } from "@/types";

interface TokenCardProps {
  provider: string;
  status: TokenStatus;
}

export function TokenCard({ provider, status }: TokenCardProps) {
  const getStatusConfig = () => {
    if (!status.valid) {
      return {
        variant: "destructive" as const,
        icon: XCircle,
        label: "Expired / Invalid",
        color: "text-red-600",
        bgColor: "bg-red-50",
      };
    }
    if (status.days_remaining !== undefined && status.days_remaining <= 14) {
      return {
        variant: "warning" as const,
        icon: AlertTriangle,
        label: `${status.days_remaining}일 후 만료`,
        color: "text-yellow-600",
        bgColor: "bg-yellow-50",
      };
    }
    return {
      variant: "success" as const,
      icon: CheckCircle,
      label: "Valid",
      color: "text-green-600",
      bgColor: "bg-green-50",
    };
  };

  const config = getStatusConfig();
  const StatusIcon = config.icon;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="flex items-center gap-2">
          <Key className="h-5 w-5" />
          {provider.charAt(0).toUpperCase() + provider.slice(1)}
        </CardTitle>
        <Badge variant={config.variant}>
          <StatusIcon className="mr-1 h-3 w-3" />
          {config.label}
        </Badge>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className={`rounded-lg p-4 ${config.bgColor}`}>
          <div className="flex items-center gap-3">
            <StatusIcon className={`h-8 w-8 ${config.color}`} />
            <div>
              <p className={`font-semibold ${config.color}`}>
                {status.valid ? "토큰 유효" : "토큰 무효"}
              </p>
              {status.error && (
                <p className="text-sm text-muted-foreground">{status.error}</p>
              )}
              {status.expires_at && (
                <p className="text-sm text-muted-foreground">
                  만료일: {new Date(status.expires_at).toLocaleDateString("ko-KR")}
                </p>
              )}
            </div>
          </div>
        </div>

        <Button variant="outline" className="w-full" asChild>
          <a
            href={
              provider === "claude"
                ? "https://console.anthropic.com"
                : "https://aistudio.google.com"
            }
            target="_blank"
            rel="noopener noreferrer"
          >
            토큰 갱신 안내
            <ExternalLink className="ml-2 h-4 w-4" />
          </a>
        </Button>
      </CardContent>
    </Card>
  );
}
