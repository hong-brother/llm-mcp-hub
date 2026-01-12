import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "@/styles/globals.css";
import { Providers } from "@/components/providers";
import { AppSidebar, AppHeader } from "@/components/layout";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "LLM MCP Hub - Admin Dashboard",
  description: "Multi-LLM Provider Hub Administration",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body className={inter.className}>
        <Providers>
          <div className="flex min-h-screen">
            <AppSidebar />
            <div className="flex-1 pl-64">
              <AppHeader />
              <main className="p-6">{children}</main>
            </div>
          </div>
        </Providers>
      </body>
    </html>
  );
}
