import PublicProfile from "./client";

export function generateStaticParams() {
  return [{ email: "index%40example.com" }];
}

export default function Page({ params }: { params: { email: string } }) {
  return <PublicProfile params={params} />;
}
