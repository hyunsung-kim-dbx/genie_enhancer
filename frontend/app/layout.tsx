import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Genie Space Enhancement',
  description: 'Automated improvement system for Databricks Genie Spaces',
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
