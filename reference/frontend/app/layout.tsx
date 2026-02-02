import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Genie Lamp Agent',
  description: 'Generate Databricks Genie Spaces from natural language requirements',
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
