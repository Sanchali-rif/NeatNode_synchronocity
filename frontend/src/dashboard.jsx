import React from 'react';

export default function Dashboard() {
  return (
    <div style={{
      minHeight: '100vh',
      padding: '120px 24px 48px',
      background: 'var(--bg-page)',
      color: 'var(--text-body)',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'flex-start',
      width: '100vw',
      boxSizing: 'border-box'
    }}>
      <div style={{
        width: '100%',
        maxWidth: 980,
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-solid)',
        borderRadius: 24,
        padding: '40px',
        boxShadow: '0 24px 80px rgba(15, 23, 42, 0.12)'
      }}>
        <h1 style={{ margin: 0, fontSize: '2.25rem', color: 'var(--text-heading)' }}>Dashboard</h1>
        <p style={{ marginTop: 16, fontSize: '1rem', color: 'var(--text-body)', lineHeight: 1.7 }}>
          This is the new dashboard page. Add your dashboard content here.
        </p>
      </div>
    </div>
  );
}
