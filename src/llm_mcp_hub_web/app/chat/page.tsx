"use client";

import { PageHeader } from "@/components/layout";
import { ChatContainer } from "@/components/chat";

export default function ChatPage() {
  return (
    <div>
      <PageHeader
        title="Chat"
        description="LLM 프로바이더와 대화합니다"
      />
      <ChatContainer />
    </div>
  );
}
