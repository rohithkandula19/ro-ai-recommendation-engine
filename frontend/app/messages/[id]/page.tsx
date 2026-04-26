import DMPage from "./client";

export function generateStaticParams() {
  return [{ id: "index" }];
}

export default function Page({ params }: { params: { id: string } }) {
  return <DMPage params={params} />;
}
