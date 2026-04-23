export function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-white border-t border-gray-200 py-6 px-4">
      <div className="max-w-7xl mx-auto text-center text-gray-600 text-sm">
        <p>© {currentYear} OptiCV. Intelligent job offer analysis for professionals.</p>
      </div>
    </footer>
  );
}
