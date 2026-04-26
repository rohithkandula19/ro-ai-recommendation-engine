import CollectionPage from "./client";

export function generateStaticParams() {
  return [{ slug: "index" }];
}

export default function Page({ params }: { params: { slug: string } }) {
  return <CollectionPage params={params} />;
}
