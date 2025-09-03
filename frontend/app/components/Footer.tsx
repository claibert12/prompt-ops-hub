export default function Footer() {
  return (
    <footer className="bg-white/80 backdrop-blur border-t border-gray-200 mt-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 text-center text-sm text-gray-600">
        © {new Date().getFullYear()} Prompt Ops Hub. Built with ❤️ for dependable AI code changes.
      </div>
    </footer>
  );
}
