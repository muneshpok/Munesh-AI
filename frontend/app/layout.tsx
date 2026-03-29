import type { ReactNode } from 'react';
import './styles.css';

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="header">
          <h1>Munesh AI</h1>
          <nav>
            <a href="/">Home</a>
            <a href="/chat">Chat</a>
            <a href="/dashboard">Dashboard</a>
            <a href="/tasks">Tasks</a>
          </nav>
        </header>
        <main className="container">{children}</main>
      </body>
    </html>
  );
}
