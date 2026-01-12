"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Server,
  Key,
  MessageSquare,
  MessagesSquare,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navigation = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Chat", href: "/chat", icon: MessagesSquare },
  { name: "Providers", href: "/providers", icon: Server },
  { name: "Tokens", href: "/tokens", icon: Key },
  { name: "Sessions", href: "/sessions", icon: MessageSquare },
];

export function AppSidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 z-40 h-screen w-64 border-r bg-background">
      <div className="flex h-16 items-center border-b px-6">
        <Link href="/" className="flex items-center gap-2 font-semibold">
          <Server className="h-6 w-6" />
          <span>LLM MCP Hub</span>
        </Link>
      </div>
      <nav className="space-y-1 p-4">
        {navigation.map((item) => {
          const isActive =
            item.href === "/"
              ? pathname === "/"
              : pathname.startsWith(item.href);

          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-secondary text-secondary-foreground"
                  : "text-muted-foreground hover:bg-secondary hover:text-secondary-foreground"
              )}
            >
              <item.icon className="h-4 w-4" />
              {item.name}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
