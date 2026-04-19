export function Footer() {
  return (
    <footer className="mt-24 border-t border-white/10 px-6 py-8 text-sm text-white/50">
      <div className="mx-auto max-w-6xl">
        <p>© {new Date().getFullYear()} RO AI Recommendation Engine</p>
        <p className="mt-2">A Netflix-style demo. All content is fictional.</p>
      </div>
    </footer>
  );
}
