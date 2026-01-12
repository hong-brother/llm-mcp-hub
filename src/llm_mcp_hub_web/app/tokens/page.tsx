"use client";

import { PageHeader } from "@/components/layout";
import { TokenCardList } from "@/components/tokens/token-card-list";

export default function TokensPage() {
  return (
    <div>
      <PageHeader
        title="OAuth Tokens"
        description="LLM 프로바이더 인증 토큰 상태를 모니터링합니다"
      />
      <TokenCardList />
    </div>
  );
}
