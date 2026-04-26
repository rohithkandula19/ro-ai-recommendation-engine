import { RichContentDetail } from "@/components/content/RichContentDetail";

export function generateStaticParams() {
  return [{ id: "index" }];
}

export default function ContentDetailPage({ params }: { params: { id: string } }) {
  return <RichContentDetail id={params.id} />;
}
