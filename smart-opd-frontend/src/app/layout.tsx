import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import Navbar from '@/components/Navbar'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Smart OPD | Intelligent Hospital',
  description: 'AI-powered OPD management system',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-slate-50 min-h-screen antialiased`}>
        <Navbar />
        <main className="pb-8">{children}</main>
      </body>
    </html>
  )
}