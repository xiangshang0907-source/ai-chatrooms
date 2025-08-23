import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'AI Chatrooms',
  description: 'Chat with AI agents in virtual rooms',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh">
      <body style={{ 
        minHeight: '100vh',
        backgroundColor: '#f3f4f6',
        fontFamily: 'system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial',
        margin: 0,
        padding: 0
      }}>
        {children}
      </body>
    </html>
  );
}