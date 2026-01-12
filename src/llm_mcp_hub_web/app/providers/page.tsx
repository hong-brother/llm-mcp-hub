"use client";

import { PageHeader } from "@/components/layout";
import { ProviderGrid } from "@/components/providers/provider-grid";

export default function ProvidersPage() {
  return (
    <div>
      <PageHeader
        title="Providers"
        description="연동된 LLM 프로바이더를 관리합니다"
      />
      <ProviderGrid />
    </div>
  );
}
