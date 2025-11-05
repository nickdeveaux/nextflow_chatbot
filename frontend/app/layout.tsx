import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Nextflow Chat Assistant',
  description: 'Get help with Nextflow documentation and troubleshooting',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}

