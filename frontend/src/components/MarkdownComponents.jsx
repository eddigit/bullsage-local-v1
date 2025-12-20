// Shared Markdown component configurations for ReactMarkdown
// These are defined as static objects to avoid React's "no-unstable-nested-components" warning

export const lessonMarkdownComponents = {
  h1: ({ children }) => <h1 className="text-2xl font-bold text-foreground mb-4 mt-6 first:mt-0">{children}</h1>,
  h2: ({ children }) => <h2 className="text-xl font-semibold text-foreground mb-3 mt-5">{children}</h2>,
  h3: ({ children }) => <h3 className="text-lg font-semibold text-foreground mb-2 mt-4">{children}</h3>,
  p: ({ children }) => <p className="text-muted-foreground mb-3 leading-relaxed">{children}</p>,
  ul: ({ children }) => <ul className="list-disc list-inside space-y-1 mb-4 text-muted-foreground">{children}</ul>,
  ol: ({ children }) => <ol className="list-decimal list-inside space-y-1 mb-4 text-muted-foreground">{children}</ol>,
  li: ({ children }) => <li className="text-muted-foreground">{children}</li>,
  strong: ({ children }) => <strong className="text-foreground font-semibold">{children}</strong>,
  blockquote: ({ children }) => (
    <blockquote className="border-l-4 border-primary pl-4 py-2 my-4 bg-primary/10 rounded-r-lg italic text-foreground">
      {children}
    </blockquote>
  ),
  code: ({ children }) => (
    <code className="bg-white/10 px-2 py-1 rounded text-sm font-mono text-primary">{children}</code>
  ),
  pre: ({ children }) => (
    <pre className="bg-black/50 p-4 rounded-lg overflow-x-auto my-4 border border-white/10">
      {children}
    </pre>
  ),
  table: ({ children }) => (
    <div className="overflow-x-auto my-4">
      <table className="w-full border-collapse border border-white/20 rounded-lg">{children}</table>
    </div>
  ),
  th: ({ children }) => (
    <th className="border border-white/20 px-4 py-2 bg-white/10 text-left font-semibold">{children}</th>
  ),
  td: ({ children }) => (
    <td className="border border-white/20 px-4 py-2">{children}</td>
  ),
  hr: () => <hr className="my-6 border-white/10" />,
};

export const chatMarkdownComponents = {
  p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
  ul: ({ children }) => <ul className="list-disc pl-4 mb-2">{children}</ul>,
  ol: ({ children }) => <ol className="list-decimal pl-4 mb-2">{children}</ol>,
  li: ({ children }) => <li className="mb-1">{children}</li>,
  strong: ({ children }) => <strong className="text-primary">{children}</strong>,
  code: ({ children }) => (
    <code className="bg-white/10 px-1 py-0.5 rounded font-mono text-sm">
      {children}
    </code>
  ),
};
