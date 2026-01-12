"use client";

import Link from "next/link";
import { useTokenHealth } from "@/lib/hooks";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { AlertTriangle, XCircle, ArrowRight } from "lucide-react";

export function TokenAlerts() {
  const { data: tokens } = useTokenHealth();

  if (!tokens) return null;

  const alerts: Array<{
    provider: string;
    type: "warning" | "error";
    message: string;
  }> = [];

  Object.entries(tokens).forEach(([provider, status]) => {
    if (!status) return;

    if (!status.valid) {
      alerts.push({
        provider,
        type: "error",
        message: status.error || "토큰이 만료되었거나 유효하지 않습니다.",
      });
    } else if (status.days_remaining !== undefined && status.days_remaining <= 14) {
      alerts.push({
        provider,
        type: "warning",
        message: `토큰이 ${status.days_remaining}일 후 만료됩니다.`,
      });
    }
  });

  if (alerts.length === 0) return null;

  return (
    <div className="space-y-3">
      {alerts.map((alert, index) => (
        <Alert
          key={index}
          variant={alert.type === "error" ? "destructive" : "warning"}
        >
          {alert.type === "error" ? (
            <XCircle className="h-4 w-4" />
          ) : (
            <AlertTriangle className="h-4 w-4" />
          )}
          <AlertTitle>
            {alert.provider.charAt(0).toUpperCase() + alert.provider.slice(1)}{" "}
            토큰 {alert.type === "error" ? "오류" : "경고"}
          </AlertTitle>
          <AlertDescription className="flex items-center justify-between">
            <span>{alert.message}</span>
            <Button variant="ghost" size="sm" asChild>
              <Link href="/tokens">
                확인하기
                <ArrowRight className="ml-1 h-4 w-4" />
              </Link>
            </Button>
          </AlertDescription>
        </Alert>
      ))}
    </div>
  );
}
