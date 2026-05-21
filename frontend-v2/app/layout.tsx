import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'PassiveWEALTH - Long-Term Portfolio Reconstruction Engine',
  description: 'Reconstruct your long-term Indian equity portfolio, track splits, bonus issues, and cumulative dividend wealth in Swiss International style.',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;700;800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet" />
      </head>
      <body className="antialiased">
        {children}
      </body>
    </html>
  )
}
