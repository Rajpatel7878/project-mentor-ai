import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Project Mentor AI',
  description: 'JARVIS-inspired AI mentor with full system control',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="font-body antialiased">{children}</body>
    </html>
  );
}
