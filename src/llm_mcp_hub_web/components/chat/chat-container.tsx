"use client";

import { useState, useRef, useEffect } from "react";
import { useMutation } from "@tanstack/react-query";
import { sendChatMessage } from "@/lib/api";
import { useProviders } from "@/lib/hooks";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { ChatMessage } from "./chat-message";
import { ChatInput } from "./chat-input";
import { MessageSquare, Trash2, AlertCircle } from "lucide-react";
import type { ChatMessage as ChatMessageType } from "@/types";

export function ChatContainer() {
  const [messages, setMessages] = useState<ChatMessageType[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<string>("");
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { data: providers, isLoading: providersLoading } = useProviders();

  // 첫 번째 프로바이더를 기본값으로 설정
  useEffect(() => {
    if (providers && providers.length > 0 && !selectedProvider) {
      setSelectedProvider(providers[0].name);
      setSelectedModel(providers[0].default_model);
    }
  }, [providers, selectedProvider]);

  // 프로바이더 변경 시 모델 초기화
  useEffect(() => {
    if (selectedProvider && providers) {
      const provider = providers.find((p) => p.name === selectedProvider);
      if (provider) {
        setSelectedModel(provider.default_model);
      }
    }
  }, [selectedProvider, providers]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const chatMutation = useMutation({
    mutationFn: async (userMessage: string) => {
      const newMessages: ChatMessageType[] = [
        ...messages,
        { role: "user" as const, content: userMessage },
      ];

      return sendChatMessage(
        {
          messages: newMessages,
          provider: selectedProvider,
          model: selectedModel,
        },
        sessionId || undefined
      );
    },
    onMutate: (userMessage) => {
      // Optimistic update - 사용자 메시지 즉시 추가
      setMessages((prev) => [
        ...prev,
        { role: "user", content: userMessage },
      ]);
    },
    onSuccess: (response) => {
      // 응답 메시지 추가
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: response.response },
      ]);

      // 세션 ID 저장
      if (response.session_id) {
        setSessionId(response.session_id);
      }
    },
    onError: (error) => {
      // 에러 시 마지막 사용자 메시지 유지하고 에러 메시지 추가
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `오류가 발생했습니다: ${error instanceof Error ? error.message : "알 수 없는 오류"}`,
        },
      ]);
    },
  });

  const handleClearChat = () => {
    setMessages([]);
    setSessionId(null);
  };

  const currentProvider = providers?.find((p) => p.name === selectedProvider);

  if (providersLoading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-center">
            <div className="animate-pulse">프로바이더 로딩 중...</div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!providers || providers.length === 0) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          사용 가능한 LLM 프로바이더가 없습니다. 백엔드 설정을 확인하세요.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="flex flex-col" style={{ height: "calc(100vh - 180px)" }}>
      {/* Header with controls */}
      <Card className="mb-4 shrink-0">
        <CardHeader className="py-3 px-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <CardTitle className="flex items-center gap-2 text-lg">
              <MessageSquare className="h-5 w-5" />
              Chat
              {sessionId && (
                <Badge variant="outline" className="ml-2 font-mono text-xs">
                  {sessionId.slice(0, 8)}...
                </Badge>
              )}
            </CardTitle>
            <div className="flex flex-wrap items-center gap-2">
              <Select
                value={selectedProvider}
                onChange={(e) => setSelectedProvider(e.target.value)}
                className="w-28"
              >
                {providers.map((provider) => (
                  <option key={provider.name} value={provider.name}>
                    {provider.name}
                  </option>
                ))}
              </Select>
              <Select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className="w-48"
              >
                {currentProvider?.models.map((model) => (
                  <option key={model} value={model}>
                    {model}
                  </option>
                ))}
              </Select>
              <Button
                variant="outline"
                size="sm"
                onClick={handleClearChat}
                disabled={messages.length === 0}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Messages area */}
      <Card className="flex-1 min-h-0 flex flex-col">
        <CardContent className="p-0 flex-1 flex flex-col min-h-0">
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
                <MessageSquare className="h-12 w-12 mb-4 opacity-50" />
                <p>메시지를 입력하여 대화를 시작하세요</p>
                <p className="text-sm mt-2">
                  현재 선택: {selectedProvider} / {selectedModel}
                </p>
              </div>
            ) : (
              messages.map((message, index) => (
                <ChatMessage key={index} message={message} />
              ))
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input area */}
          <div className="border-t p-4 shrink-0">
            <ChatInput
              onSend={(message) => chatMutation.mutate(message)}
              isLoading={chatMutation.isPending}
            />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
