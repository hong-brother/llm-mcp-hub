"use client";

import { PageHeader } from "@/components/layout";
import { SessionTable } from "@/components/sessions/session-table";

export default function SessionsPage() {
  return (
    <div>
      <PageHeader
        title="Sessions"
        description="활성 대화 세션을 관리합니다"
      />
      <SessionTable />
    </div>
  );
}
