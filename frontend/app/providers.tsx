"use client";

import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "@/lib/queryClient";
import { ToastProvider } from "@/components/ui/Toast";
import { ServiceFilterProvider } from "@/hooks/useServiceFilter";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <ServiceFilterProvider>
        <ToastProvider>{children}</ToastProvider>
      </ServiceFilterProvider>
    </QueryClientProvider>
  );
}
