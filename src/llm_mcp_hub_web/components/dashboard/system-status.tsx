"use client";

import { useHealth } from "@/lib/hooks";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Activity, CheckCircle, AlertTriangle, XCircle } from "lucide-react";

export function SystemStatus() {
  const { data: health, isLoading, error } = useHealth();

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            시스템 상태
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-24 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (error || !health) {
    return (
      <Card className="border-destructive">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-destructive">
            <XCircle className="h-5 w-5" />
            시스템 상태
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-destructive">서버에 연결할 수 없습니다.</p>
        </CardContent>
      </Card>
    );
  }

  const statusConfig = {
    healthy: {
      icon: CheckCircle,
      color: "text-green-600",
      bgColor: "bg-green-50",
      borderColor: "border-green-200",
      label: "정상",
    },
    degraded: {
      icon: AlertTriangle,
      color: "text-yellow-600",
      bgColor: "bg-yellow-50",
      borderColor: "border-yellow-200",
      label: "일부 장애",
    },
    unhealthy: {
      icon: XCircle,
      color: "text-red-600",
      bgColor: "bg-red-50",
      borderColor: "border-red-200",
      label: "장애",
    },
  };

  const config = statusConfig[health.status];
  const StatusIcon = config.icon;

  return (
    <Card className={config.borderColor}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Activity className="h-5 w-5" />
          시스템 상태
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div
          className={`flex items-center gap-4 rounded-lg p-4 ${config.bgColor}`}
        >
          <StatusIcon className={`h-12 w-12 ${config.color}`} />
          <div>
            <div className="flex items-center gap-2">
              <span className={`text-2xl font-bold ${config.color}`}>
                {config.label}
              </span>
              <Badge
                variant={
                  health.status === "healthy"
                    ? "success"
                    : health.status === "degraded"
                      ? "warning"
                      : "destructive"
                }
              >
                {health.status.toUpperCase()}
              </Badge>
            </div>
            <p className="text-sm text-muted-foreground">
              버전: {health.version}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
