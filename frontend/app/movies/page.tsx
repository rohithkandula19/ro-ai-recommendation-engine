import { CatalogGrid } from "@/components/browse/CatalogGrid";

export default function MoviesPage() {
  return <CatalogGrid endpoint="/movies" title="Movies" showRuntime />;
}
