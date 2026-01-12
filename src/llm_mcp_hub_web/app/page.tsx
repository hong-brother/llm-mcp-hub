"use client";

import { PageHeader } from "@/components/layout";
import { SystemStatus } from "@/components/dashboard/system-status";
import { ComponentCards } from "@/components/dashboard/component-cards";
import { ProviderSummary } from "@/components/dashboard/provider-summary";
import { TokenAlerts } from "@/components/dashboard/token-alerts";

export default function DashboardPage() {
  return (
    <div>
      <PageHeader
        title="Dashboard"
        description="LLM MCP Hub 시스템 상태를 한눈에 확인하세요"
      />

      <div className="space-y-6">
        {/* Token Alerts */}
        <TokenAlerts />

        {/* System Status */}
        <SystemStatus />

        {/* Component Health Cards */}
        <ComponentCards />

        {/* Provider Summary */}
        <ProviderSummary />
      </div>
    </div>
  );
}
