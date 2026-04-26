import LegalPage from "./client";

export function generateStaticParams() {
  return [
    { kind: "privacy" },
    { kind: "terms" },
    { kind: "cookies" },
    { kind: "attributions" },
  ];
}

export default function Page({ params }: { params: { kind: string } }) {
  return <LegalPage params={params} />;
}
