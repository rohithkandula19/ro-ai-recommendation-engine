import WatchRedirect from "./redirect";

export function generateStaticParams() {
  return [{ id: "index" }];
}

export default function WatchPage({ params }: { params: { id: string } }) {
  return <WatchRedirect id={params.id} />;
}
