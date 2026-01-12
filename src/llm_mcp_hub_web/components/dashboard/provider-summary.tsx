"use client";

import Link from "next/link";
import { useProviders } from "@/lib/hooks";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Server, ArrowRight } from "lucide-react";

export function ProviderSummary() {
  const { data: providers, isLoading } = useProviders();

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Server className="h-5 w-5" />
            LLM Providers
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-24 w-full" />
        </CardContent>
      </Card>
    );
  }

  const totalProviders = providers?.length || 0;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          <Server className="h-5 w-5" />
          LLM Providers
        </CardTitle>
        <Button variant="ghost" size="sm" asChild>
          <Link href="/providers">
            자세히 보기
            <ArrowRight className="ml-1 h-4 w-4" />
          </Link>
        </Button>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-4">
          <div className="text-3xl font-bold">{totalProviders}</div>
          <div className="text-sm text-muted-foreground">
            개의 프로바이더가 연결됨
          </div>
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          {providers?.map((provider) => (
            <Badge key={provider.name} variant="secondary">
              {provider.name} ({provider.models.length} models)
            </Badge>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
