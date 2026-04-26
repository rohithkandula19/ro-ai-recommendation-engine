import { Suspense } from "react";
import WatchPartyRoom from "./client";

export function generateStaticParams() {
  return [{ room: "index" }];
}

export default function Page({ params }: { params: { room: string } }) {
  return (
    <Suspense fallback={<div className="p-8 text-white/50">Loading watch party…</div>}>
      <WatchPartyRoom room={params.room} />
    </Suspense>
  );
}
