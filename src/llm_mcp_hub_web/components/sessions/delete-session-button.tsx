"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useDeleteSession } from "@/lib/hooks";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Trash2, Loader2 } from "lucide-react";

interface DeleteSessionButtonProps {
  sessionId: string;
  variant?: "ghost" | "destructive";
  redirectOnDelete?: boolean;
}

export function DeleteSessionButton({
  sessionId,
  variant = "ghost",
  redirectOnDelete = false,
}: DeleteSessionButtonProps) {
  const [open, setOpen] = useState(false);
  const router = useRouter();
  const deleteSession = useDeleteSession();

  const handleDelete = async () => {
    try {
      await deleteSession.mutateAsync(sessionId);
      setOpen(false);
      if (redirectOnDelete) {
        router.push("/sessions");
      }
    } catch {
      // Error handled by React Query
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant={variant} size="sm">
          <Trash2 className="h-4 w-4" />
          {variant === "destructive" && <span className="ml-2">삭제</span>}
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>세션 삭제</DialogTitle>
          <DialogDescription>
            이 세션을 삭제하시겠습니까? 모든 대화 기록이 영구적으로 삭제됩니다.
          </DialogDescription>
        </DialogHeader>
        <div className="rounded-lg bg-muted p-3">
          <p className="break-all font-mono text-sm">{sessionId}</p>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            취소
          </Button>
          <Button
            variant="destructive"
            onClick={handleDelete}
            disabled={deleteSession.isPending}
          >
            {deleteSession.isPending ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Trash2 className="mr-2 h-4 w-4" />
            )}
            삭제
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
