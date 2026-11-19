import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'QIP Quantum Studio',
  description: 'Quantum Image Processing Studio - 6-Stage Real-time Pipeline',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full">
      <body className="bg-[#090a0f] text-[#e2e8f0] h-screen overflow-hidden antialiased">
        {children}
      </body>
    </html>
  );
}
