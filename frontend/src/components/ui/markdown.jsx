import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import remarkGfm from 'remark-gfm';
import rehypeKatex from 'rehype-katex';
import rehypeHighlight from 'rehype-highlight';
import { Copy, Check } from 'lucide-react';
import { cn } from '@/lib/utils';
import 'katex/dist/katex.min.css';
import 'highlight.js/styles/github-dark.css';

// Copy button component for code blocks
const CopyButton = ({ code, className }) => {
  const [copied, setCopied] = useState(false);
  const timeoutRef = useRef(null);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      timeoutRef.current = setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  useEffect(() => {
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, []);

  return (
    <button
      onClick={handleCopy}
      className={cn(
        'absolute top-2 right-2 p-1.5 rounded-md',
        'bg-muted/80 hover:bg-muted',
        'text-muted-foreground hover:text-foreground',
        'transition-colors duration-200',
        'opacity-0 group-hover:opacity-100',
        'border border-border/50',
        className
      )}
      title={copied ? 'Copied!' : 'Copy code'}
    >
      {copied ? (
        <Check className="h-3.5 w-3.5 text-green-500" />
      ) : (
        <Copy className="h-3.5 w-3.5" />
      )}
    </button>
  );
};

// Custom components for markdown rendering
const components = {
  // Headings with ChatGPT-style design
  h1: ({ className, node, ...props }) => {
    const id = node?.children?.[0]?.value?.toLowerCase().replace(/\s+/g, '-');
    return (
      <h1
        id={id}
        className={cn(
          'text-2xl font-bold tracking-tight mt-8 mb-4',
          'scroll-mt-20',
          'text-foreground',
          'pb-2 border-b border-border/30',
          className
        )}
        {...props}
      />
    );
  },
  h2: ({ className, node, ...props }) => {
    const id = node?.children?.[0]?.value?.toLowerCase().replace(/\s+/g, '-');
    return (
      <h2
        id={id}
        className={cn(
          'text-xl font-semibold tracking-tight mt-6 mb-3',
          'scroll-mt-20',
          'text-foreground',
          className
        )}
        {...props}
      />
    );
  },
  h3: ({ className, node, ...props }) => {
    const id = node?.children?.[0]?.value?.toLowerCase().replace(/\s+/g, '-');
    return (
      <h3
        id={id}
        className={cn(
          'text-lg font-semibold tracking-tight mt-5 mb-2',
          'scroll-mt-20',
          'text-foreground',
          className
        )}
        {...props}
      />
    );
  },
  h4: ({ className, ...props }) => (
    <h4
      className={cn(
        'text-lg font-semibold tracking-tight mt-5 mb-2',
        'text-foreground',
        className
      )}
      {...props}
    />
  ),
  h5: ({ className, ...props }) => (
    <h5
      className={cn(
        'text-base font-semibold tracking-tight mt-4 mb-2',
        'text-foreground',
        className
      )}
      {...props}
    />
  ),
  h6: ({ className, ...props }) => (
    <h6
      className={cn(
        'text-sm font-semibold tracking-tight mt-3 mb-2',
        'text-muted-foreground',
        className
      )}
      {...props}
    />
  ),

  // Paragraphs with VS Code-style clarity
  p: ({ className, children, ...props }) => {
    // Check if paragraph contains only math (KaTeX renders math in spans/divs)
    const hasMath = children && (
      (typeof children === 'object' && children.props?.className?.includes('katex')) ||
      (Array.isArray(children) && children.some(child => 
        child?.props?.className?.includes('katex')
      ))
    );
    
    if (hasMath) {
      return <div className={cn('my-6', className)} {...props}>{children}</div>;
    }
    
    return (
      <p
        className={cn(
          'leading-[1.6] mb-4 text-foreground',
          'text-[15px]',
          'whitespace-pre-wrap',
          '[&:has(img)]:mb-2',
          '[&:has(code)]:mb-3',
          '[&:last-child]:mb-0',
          className
        )}
        {...props}
      >
        {children}
      </p>
    );
  },

  // Lists with ChatGPT-style spacing
  ul: ({ className, ...props }) => (
    <ul
      className={cn(
        'my-4 ml-6 list-disc space-y-1.5',
        'marker:text-muted-foreground/60',
        'marker:text-base',
        className
      )}
      {...props}
    />
  ),
  ol: ({ className, ...props }) => (
    <ol
      className={cn(
        'my-4 ml-6 list-decimal space-y-1.5',
        'marker:text-muted-foreground/60',
        'marker:font-medium',
        className
      )}
      {...props}
    />
  ),
  li: ({ className, ...props }) => (
    <li
      className={cn(
        'leading-7 pl-1.5',
        'text-[15px]',
        '[&>p]:mb-2 [&>p]:mt-0',
        '[&>ul]:mt-2 [&>ul]:mb-2',
        '[&>ol]:mt-2 [&>ol]:mb-2',
        className
      )}
      {...props}
    />
  ),

  // Enhanced code blocks with VS Code-style clarity
  code: ({ className, inline, children, ...props }) => {
    const match = /language-(\w+)/.exec(className || '');
    const codeString = String(children).replace(/\n$/, '');
    const isInline = inline || !match;

    if (isInline) {
      return (
        <code
          className={cn(
            'relative rounded bg-muted px-1.5 py-0.5',
            'font-mono text-[13px]',
            'text-foreground',
            'border border-border/40',
            'font-normal',
            className
          )}
          {...props}
        >
          {children}
        </code>
      );
    }

    const language = match ? match[1] : 'text';

    return (
      <div className="relative group my-4">
        <div className="absolute top-0 left-0 right-0 h-8 bg-muted/80 dark:bg-muted/50 rounded-t-md border-b border-border/40 flex items-center justify-between px-3 z-10">
          <span className="text-[11px] text-muted-foreground font-medium uppercase tracking-wide">
            {language}
          </span>
        </div>
        <pre
          className={cn(
            'overflow-x-auto rounded-md bg-muted/60 dark:bg-muted/40 p-4 pt-12',
            'font-mono text-[13px] leading-[1.5]',
            'border border-border/40',
            'shadow-sm',
            'm-0',
            'font-normal',
            className
          )}
        >
          <code
            className={cn(
              'block text-foreground',
              'font-mono',
              className
            )}
            {...props}
          >
            {children}
          </code>
        </pre>
        <CopyButton code={codeString} />
      </div>
    );
  },

  // Enhanced pre blocks
  pre: ({ className, children, ...props }) => {
    // Check if pre contains a code element (handled by code component)
    if (children?.props?.className?.includes('language-')) {
      return <>{children}</>;
    }
    
    return (
      <pre
        className={cn(
          'overflow-x-auto rounded-lg bg-muted p-4',
          'font-mono text-sm leading-relaxed',
          'border border-border',
          'my-4',
          className
        )}
        {...props}
      >
        {children}
      </pre>
    );
  },

  // Blockquotes with ChatGPT-style design
  blockquote: ({ className, ...props }) => (
    <blockquote
      className={cn(
        'my-4 border-l-4 border-primary/40 dark:border-primary/60 pl-4',
        'text-muted-foreground',
        'bg-muted/20 dark:bg-muted/10',
        'py-2 pr-4 rounded-r',
        'not-italic',
        className
      )}
      {...props}
    />
  ),

  // Enhanced tables with ChatGPT-style design
  table: ({ className, ...props }) => (
    <div className="my-5 w-full overflow-x-auto rounded-lg border border-border/50 shadow-sm">
      <table
        className={cn(
          'w-full border-collapse',
          'text-sm',
          className
        )}
        {...props}
      />
    </div>
  ),
  thead: ({ className, ...props }) => (
    <thead
      className={cn(
        'bg-muted/40 dark:bg-muted/20 border-b border-border/50',
        className
      )}
      {...props}
    />
  ),
  tbody: ({ className, ...props }) => (
    <tbody
      className={cn(
        'divide-y divide-border/30',
        className
      )}
      {...props}
    />
  ),
  tr: ({ className, ...props }) => (
    <tr
      className={cn(
        'm-0 border-t border-border/30 p-0',
        'hover:bg-muted/20 dark:hover:bg-muted/10 transition-colors',
        'even:bg-muted/10 dark:even:bg-muted/5',
        className
      )}
      {...props}
    />
  ),
  th: ({ className, ...props }) => (
    <th
      className={cn(
        'border-r border-border/30 px-4 py-2.5 text-left',
        'font-semibold text-foreground text-[13px]',
        'last:border-r-0',
        '[&[align=center]]:text-center [&[align=right]]:text-right',
        className
      )}
      {...props}
    />
  ),
  td: ({ className, ...props }) => (
    <td
      className={cn(
        'border-r border-border/30 px-4 py-2.5 text-left',
        'text-foreground text-[13px]',
        'last:border-r-0',
        '[&[align=center]]:text-center [&[align=right]]:text-right',
        className
      )}
      {...props}
    />
  ),

  // Links with ChatGPT-style design
  a: ({ className, ...props }) => (
    <a
      className={cn(
        'font-medium underline underline-offset-2',
        'text-primary hover:text-primary/80',
        'transition-colors',
        'decoration-primary/30 hover:decoration-primary/50',
        className
      )}
      {...props}
    />
  ),

  // Strong and emphasis
  strong: ({ className, ...props }) => (
    <strong
      className={cn('font-semibold text-foreground', className)}
      {...props}
    />
  ),
  em: ({ className, ...props }) => (
    <em className={cn('italic text-foreground', className)} {...props} />
  ),

  // Strikethrough (GitHub Flavored Markdown)
  del: ({ className, ...props }) => (
    <del
      className={cn(
        'line-through text-muted-foreground',
        className
      )}
      {...props}
    />
  ),

  // Task list items (GitHub Flavored Markdown)
  input: ({ className, type, checked, ...props }) => {
    if (type === 'checkbox') {
      return (
        <input
          type="checkbox"
          className={cn(
            'mr-2 h-4 w-4 rounded border-border',
            'accent-primary cursor-pointer',
            className
          )}
          checked={checked}
          readOnly
          {...props}
        />
      );
    }
    return <input className={className} {...props} />;
  },

  // Horizontal rule
  hr: ({ className, ...props }) => (
    <hr
      className={cn(
        'my-8 border-t border-border',
        className
      )}
      {...props}
    />
  ),

  // Images with ChatGPT-style design
  img: ({ className, ...props }) => (
    <img
      className={cn(
        'rounded-lg border border-border/50',
        'my-4 max-w-full h-auto',
        'shadow-md',
        'hover:shadow-lg transition-shadow',
        className
      )}
      {...props}
    />
  ),
};

// Preprocess content to fix math delimiters
function preprocessMath(content) {
  if (typeof content !== 'string') return content;
  
  // First, handle double-escaped backslashes (from JSON)
  // Fix \\[ to \[ and \\( to \(
  content = content.replace(/\\\\\[/g, '\\[');
  content = content.replace(/\\\\\(/g, '\\(');
  content = content.replace(/\\\\\]/g, '\\]');
  content = content.replace(/\\\\\)/g, '\\)');
  
  // Simple pattern to detect LaTeX math: backslash followed by letters or special chars
  // This matches common LaTeX commands like \sum, \theta, \begin, etc.
  const hasMathPattern = (text) => {
    return /\\[a-zA-Z]+\{?|\\[{}()\[\]^_=]|\\sum|\\theta|\\begin|\\end|\\frac|\\sqrt|\\int|\\partial|\\alpha|\\beta|\\gamma|\\delta|\\epsilon|\\pi|\\lambda|\\mu|\\sigma|\\phi|\\omega|\\cdot|\\times|\\div|\\pm|\\leq|\\geq|\\neq|\\approx|\\in|\\subset|\\cup|\\cap|\\emptyset|\\infty|\\nabla|\\Delta|\\forall|\\exists|\\rightarrow|\\leftarrow|\\Leftrightarrow|\\Rightarrow|\\Leftarrow|\\mapsto|\\to|\\left|\\right|\\big|\\Big|\\bigg|\\Bigg|\\vdots|\\cdots|\\ldots|\\ddots|\\matrix|\\pmatrix|\\bmatrix|\\vmatrix|\\Vmatrix|\\cases|\\align|\\eqnarray|\\split|\\multline|\\gather|\\gathered|\\alignat|\\flalign|\\xleftarrow|\\xrightarrow|\\xleftrightarrow|\\xLeftarrow|\\xRightarrow|\\xLeftrightarrow|\\xhookleftarrow|\\xhookrightarrow|\\xmapsto|\\xrightharpoonup|\\xrightharpoondown|\\xleftharpoonup|\\xleftharpoondown|\\xrightleftharpoons|\\xleftrightharpoons|\\xtwoheadleftarrow|\\xtwoheadrightarrow|\\xtofrom|\\xlongequal|\\xtwoheadrightarrow|\\xtwoheadleftarrow|\\xmapsto|\\xhookleftarrow|\\xhookrightarrow|\\xrightharpoonup|\\xrightharpoondown|\\xleftharpoonup|\\xleftharpoondown|\\xrightleftharpoons|\\xleftrightharpoons|\\xtwoheadleftarrow|\\xtwoheadrightarrow|\\xtofrom|\\xlongequal/i.test(text);
  };
  
  // Fix block math on separate lines: [\n...\n] -> \[...\]
  content = content.replace(/\n\s*\[\s*\n([^\]]+)\n\s*\]/g, (match, equation) => {
    if (hasMathPattern(equation)) {
      return '\n\\[\n' + equation + '\n\\]';
    }
    return match;
  });
  
  // Fix inline block math: [ equation ] -> \[ equation \]
  // Match [ content ] where content contains math patterns
  // But avoid matching if it's already escaped or if it's a markdown link/image
  content = content.replace(/\[\s*([^\]]+)\s*\]/g, (match, equation, offset, fullText) => {
    // Skip if it's already escaped (has backslash before) or part of a link/image
    if (offset > 0) {
      const before = fullText.substring(Math.max(0, offset - 2), offset);
      if (before.endsWith('\\') || before.endsWith('!') || before.endsWith(']')) {
        return match;
      }
    }
    // Skip if already properly formatted
    if (match.includes('\\[') || match.includes('\\]')) {
      return match;
    }
    // Check if it contains math patterns
    if (hasMathPattern(equation)) {
      return '\\[' + equation + '\\]';
    }
    return match;
  });
  
  // Fix inline math: ( ... ) -> \( ... \) when it contains math
  // But be careful not to break regular parentheses
  content = content.replace(/\(([^)]+)\)/g, (match, equation, offset, fullText) => {
    // Skip if already properly formatted
    if (match.includes('\\(') || match.includes('\\)')) {
      return match;
    }
    // Skip if it's escaped
    if (offset > 0 && fullText[offset - 1] === '\\') {
      return match;
    }
    // Check if it contains math patterns
    if (hasMathPattern(equation)) {
      return '\\( ' + equation + ' \\)';
    }
    return match;
  });
  
  return content;
}

export function Markdown({ className, children, ...props }) {
  // Preprocess children to fix math delimiters
  const processedChildren = typeof children === 'string' 
    ? preprocessMath(children) 
    : children;
  
  return (
    <div
      className={cn(
        'markdown-content',
        // VS Code-style: Crystal clear, professional rendering
        'text-[15px] leading-[1.6]',
        'text-foreground',
        'font-sans',
        // Perfect spacing like VS Code
        '[&>h1]:mt-0 [&>h1]:mb-4 [&>h1:first-child]:mt-0',
        '[&>h2]:mt-8 [&>h2]:mb-3 [&>h2:first-child]:mt-0',
        '[&>h3]:mt-6 [&>h3]:mb-2 [&>h3:first-child]:mt-0',
        '[&>h4]:mt-5 [&>h4]:mb-2',
        '[&>h5]:mt-4 [&>h5]:mb-2',
        '[&>h6]:mt-4 [&>h6]:mb-2',
        '[&>p]:mb-4 [&>p:last-child]:mb-0',
        '[&>ul]:mb-4 [&>ol]:mb-4',
        '[&>blockquote]:my-4',
        '[&>pre]:my-4',
        '[&>table]:my-4',
        '[&>hr]:my-8',
        '[&>img]:my-4',
        // Math equation styling - VS Code style
        '[&_.katex]:text-foreground',
        '[&_.katex-display]:my-6',
        '[&_.katex-display]:overflow-x-auto',
        '[&_.katex-display]:overflow-y-hidden',
        '[&_.katex-display]:text-center',
        // Better code block spacing
        '[&>pre+*]:mt-4',
        '[&>p+pre]:mt-4',
        '[&>pre+p]:mt-4',
        className
      )}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[
          [rehypeKatex, { throwOnError: false, errorColor: '#cc0000' }],
          rehypeHighlight,
        ]}
        components={components}
        {...props}
      >
        {processedChildren}
      </ReactMarkdown>
    </div>
  );
}
