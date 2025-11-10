import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import { cn } from '@/lib/utils';

// Custom components for markdown rendering
const components = {
  // Headings
  h1: ({ className, ...props }) => (
    <h1 className={cn('text-2xl font-bold tracking-tight mt-6 mb-4', className)} {...props} />
  ),
  h2: ({ className, ...props }) => (
    <h2 className={cn('text-xl font-semibold tracking-tight mt-5 mb-3', className)} {...props} />
  ),
  h3: ({ className, ...props }) => (
    <h3 className={cn('text-lg font-semibold tracking-tight mt-4 mb-2', className)} {...props} />
  ),

  // Paragraphs
  p: ({ className, ...props }) => (
    <p className={cn('leading-7 mb-4', className)} {...props} />
  ),

  // Lists
  ul: ({ className, ...props }) => (
    <ul className={cn('my-4 ml-6 list-disc', className)} {...props} />
  ),
  ol: ({ className, ...props }) => (
    <ol className={cn('my-4 ml-6 list-decimal', className)} {...props} />
  ),
  li: ({ className, ...props }) => (
    <li className={cn('leading-7 mb-2', className)} {...props} />
  ),

  // Code blocks
  code: ({ className, inline, ...props }) => {
    const isInline = inline || !className?.includes('language-');
    return isInline ? (
      <code className={cn('relative rounded bg-muted px-[0.3rem] py-[0.2rem] font-mono text-sm font-semibold', className)} {...props} />
    ) : (
      <code className={cn('block overflow-x-auto rounded-lg bg-muted p-4 font-mono text-sm', className)} {...props} />
    );
  },

  // Blockquotes
  blockquote: ({ className, ...props }) => (
    <blockquote className={cn('mt-6 border-l-2 pl-6 italic', className)} {...props} />
  ),

  // Tables
  table: ({ className, ...props }) => (
    <div className="my-6 w-full overflow-y-auto">
      <table className={cn('w-full', className)} {...props} />
    </div>
  ),
  thead: ({ className, ...props }) => (
    <thead className={cn('border-b', className)} {...props} />
  ),
  tbody: ({ className, ...props }) => (
    <tbody className={cn('', className)} {...props} />
  ),
  tr: ({ className, ...props }) => (
    <tr className={cn('m-0 border-t p-0 even:bg-muted', className)} {...props} />
  ),
  th: ({ className, ...props }) => (
    <th className={cn('border px-4 py-2 text-left font-bold [&[align=center]]:text-center [&[align=right]]:text-right', className)} {...props} />
  ),
  td: ({ className, ...props }) => (
    <td className={cn('border px-4 py-2 text-left [&[align=center]]:text-center [&[align=right]]:text-right', className)} {...props} />
  ),

  // Links
  a: ({ className, ...props }) => (
    <a className={cn('font-medium underline underline-offset-4', className)} {...props} />
  ),

  // Strong and emphasis
  strong: ({ className, ...props }) => (
    <strong className={cn('font-semibold', className)} {...props} />
  ),
  em: ({ className, ...props }) => (
    <em className={cn('italic', className)} {...props} />
  ),
};

export function Markdown({ className, children, ...props }) {
  return (
    <div className={cn('prose prose-sm max-w-none dark:prose-invert', className)}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={components}
        {...props}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}
