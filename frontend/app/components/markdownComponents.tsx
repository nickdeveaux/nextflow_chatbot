import React from 'react'

export const markdownComponents = {
  // Style code blocks
  code: ({ className, children, ...props }: any) => {
    const match = /language-(\w+)/.exec(className || '')
    const isInline = !match
    return isInline ? (
      <code className="markdown-inline-code" {...props}>
        {children}
      </code>
    ) : (
      <pre className="markdown-code-block">
        <code className={className} {...props}>
          {children}
        </code>
      </pre>
    )
  },
  // Style links
  a: ({ href, children, ...props }: any) => (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="markdown-link"
      {...props}
    >
      {children}
    </a>
  ),
  // Style lists
  ul: ({ children, ...props }: any) => (
    <ul className="markdown-list" {...props}>
      {children}
    </ul>
  ),
  ol: ({ children, ...props }: any) => (
    <ol className="markdown-list" {...props}>
      {children}
    </ol>
  ),
  // Style blockquotes
  blockquote: ({ children, ...props }: any) => (
    <blockquote className="markdown-blockquote" {...props}>
      {children}
    </blockquote>
  ),
}

