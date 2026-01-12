"use client";

import { useParams } from "next/navigation";
import { PageHeader } from "@/components/layout";
import { SessionDetail } from "@/components/sessions/session-detail";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default function SessionDetailPage() {
  const params = useParams();
  const sessionId = params.id as string;

  return (
    <div>
      <PageHeader title="Session Detail" description={sessionId}>
        <Button variant="outline" asChild>
          <Link href="/sessions">
            <ArrowLeft className="mr-2 h-4 w-4" />
            목록으로
          </Link>
        </Button>
      </PageHeader>
      <SessionDetail sessionId={sessionId} />
    </div>
  );
}
