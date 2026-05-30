import React from 'react';

function HeroSection() {
  const marqueeLogos = [
    {
      name: 'Missing Values',
      icon: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2" strokeDasharray="4 4" />
          <line x1="9" y1="9" x2="15" y2="15" />
          <line x1="15" y1="9" x2="9" y2="15" />
        </svg>
      )
    },
    {
      name: 'Outliers',
      icon: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
          <circle cx="12" cy="12" r="2" />
          <circle cx="12" cy="12" r="8" strokeDasharray="4 4" />
          <circle cx="20" cy="4" r="2" fill="currentColor" />
        </svg>
      )
    },
    {
      name: 'Duplicates',
      icon: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
          <rect x="8" y="8" width="12" height="12" rx="2" />
          <path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2" />
        </svg>
      )
    },
    {
      name: 'Bad Formats',
      icon: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
          <path d="M4 22h14a2 2 0 0 0 2-2V7l-5-5H6a2 2 0 0 0-2 2v4" />
          <path d="M14 2v4a2 2 0 0 0 2 2h4" />
          <path d="M3 15h6" />
          <path d="M3 18h6" />
        </svg>
      )
    },
    {
      name: 'Mixed Types',
      icon: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
          <path d="M4 7V4h16v3" />
          <path d="M9 20h6" />
          <path d="M12 4v16" />
        </svg>
      )
    }
  ];

  return (
    <section style={{ 
      position: 'relative', 
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      paddingTop: '100px',
      paddingBottom: '0',
      overflow: 'hidden',
      background: 'var(--bg-page)',
    }}>

      {/* === NEURA-STYLE GRADIENT BLOBS === */}
      {/* Purple blob - top center */}
      <div className="blob" style={{
        width: '520px', height: '420px',
        top: '10%', left: '55%', transform: 'translate(-50%, 0)',
        background: 'var(--blob-purple)',
      }} />
      {/* Orange blob - right */}
      <div className="blob" style={{
        width: '380px', height: '380px',
        top: '25%', right: '-60px',
        background: 'var(--blob-orange)',
      }} />
      {/* Green blob - left */}
      <div className="blob" style={{
        width: '340px', height: '340px',
        top: '30%', left: '-40px',
        background: 'var(--blob-green)',
      }} />
      {/* Peach blob - bottom center */}
      <div className="blob" style={{
        width: '500px', height: '280px',
        bottom: '5%', left: '50%', transform: 'translateX(-50%)',
        background: 'var(--blob-orange)',
        opacity: 0.4,
      }} />

      {/* === HERO CONTENT === */}
      <div className="container" style={{ textAlign: 'center', position: 'relative', zIndex: 1 }}>

        {/* Pill Badge */}
        <div style={{ marginBottom: '2rem' }}>
          <span className="pill-badge">
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--accent-primary)', display: 'inline-block' }}></span>
            AI-Powered Data Cleaning
          </span>
        </div>

        {/* Headline */}
        <h1 style={{
          fontSize: 'clamp(3rem, 7vw, 5.5rem)',
          fontWeight: 900,
          lineHeight: 1.05,
          letterSpacing: '-0.04em',
          color: 'var(--text-heading)',
          marginBottom: '1.5rem',
          maxWidth: '820px',
          margin: '0 auto 1.5rem auto',
        }}>
          Your Data Has Problems.<br/>
          <span style={{ 
            background: 'var(--accent-primary-gradient)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
          }}>We Fix Them.</span>
        </h1>

        {/* Subtext */}
        <p style={{
          fontSize: '18px',
          color: 'var(--text-body)',
          maxWidth: '560px',
          margin: '0 auto 2.5rem auto',
          lineHeight: 1.65,
          fontWeight: 400,
        }}>
          Crafting intelligent solutions that turn your messy, unreliable datasets into clean, production-ready pipelines.
        </p>

        {/* CTAs */}
        <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center', marginBottom: '4.5rem' }}>
          <a href="#pipeline" style={{ textDecoration: 'none' }}>
            <button className="btn-dark" style={{ fontSize: '15px', padding: '0.85rem 1.75rem' }}>
              See How It Works ↓
            </button>
          </a>
          <a href="#upload" style={{ textDecoration: 'none' }}>
            <button className="btn-dark" style={{ fontSize: '15px', padding: '0.85rem 1.75rem', display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}>
              Get Started
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M5 12h14M12 5l7 7-7 7"/>
              </svg>
            </button>
          </a>
        </div>

        {/* === HERO CARD — Data Profiling Table === */}
        <div className="card" style={{
          maxWidth: '860px',
          margin: '0 auto',
          padding: '0',
          overflow: 'hidden',
          borderRadius: '20px',
          boxShadow: 'var(--shadow-card)',
        }}>
          {/* Window bar */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '14px 20px',
            borderBottom: '1px solid var(--border-solid)',
            background: 'var(--bg-surface-alt)',
          }}>
            <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#ff5f57' }}/>
            <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#febc2e' }}/>
            <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#28c840' }}/>
            <div style={{ marginLeft: '10px', fontSize: '12px', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
              neatnode — profiling sales_2023.csv
            </div>
          </div>

          {/* Table */}
          <div style={{ overflowX: 'auto', padding: '8px 0' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
              <thead>
                <tr style={{ background: 'var(--bg-surface-alt)' }}>
                  {['Column', 'Dtype', 'Nulls %', 'Issue', 'Strategy'].map(h => (
                    <th key={h} style={{ 
                      textAlign: 'left', padding: '10px 20px', 
                      fontWeight: 600, fontSize: '12px', textTransform: 'uppercase',
                      letterSpacing: '0.05em', color: 'var(--text-muted)',
                      borderBottom: '1px solid var(--border-solid)'
                    }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {[
                  { col: 'revenue_usd', dtype: 'float64', nulls: '14.2%', issue: 'missing', strategy: 'KNN Imputation', issueColor: '#ef4444', stratColor: 'var(--accent-primary)' },
                  { col: 'customer_id', dtype: 'string',  nulls: '0.0%',  issue: 'high cardinality', strategy: 'Drop Column', issueColor: '#f59e0b', stratColor: 'var(--text-muted)' },
                  { col: 'category',   dtype: 'category', nulls: '5.1%',  issue: 'mixed', strategy: 'Mode + Encode', issueColor: '#ef4444', stratColor: 'var(--accent-primary)' },
                  { col: 'signup_date',dtype: 'datetime', nulls: '0.0%',  issue: 'none', strategy: 'Feature Extract', issueColor: '#10b981', stratColor: '#0099ff' },
                ].map((row, i) => (
                  <tr key={i} style={{ borderBottom: i < 3 ? '1px solid var(--border-solid)' : 'none' }}>
                    <td style={{ padding: '12px 20px', fontWeight: 600, color: 'var(--text-heading)', fontFamily: 'monospace', fontSize: '13px' }}>{row.col}</td>
                    <td style={{ padding: '12px 20px' }}>
                      <span style={{ background: 'var(--bg-surface-alt)', color: 'var(--accent-primary)', padding: '2px 8px', borderRadius: '5px', fontSize: '12px', fontWeight: 600 }}>{row.dtype}</span>
                    </td>
                    <td style={{ padding: '12px 20px', color: row.nulls === '0.0%' ? '#10b981' : '#ef4444', fontWeight: 600 }}>{row.nulls}</td>
                    <td style={{ padding: '12px 20px' }}>
                      <span style={{ background: row.issueColor + '15', color: row.issueColor, padding: '2px 8px', borderRadius: '5px', fontSize: '12px', fontWeight: 600, textTransform: 'capitalize' }}>{row.issue}</span>
                    </td>
                    <td style={{ padding: '12px 20px', color: row.stratColor, fontWeight: 500 }}>{row.strategy}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Status bar */}
          <div style={{ 
            padding: '12px 20px', 
            background: 'var(--bg-surface-alt)', 
            borderTop: '1px solid var(--border-solid)',
            display: 'flex', alignItems: 'center', gap: '16px',
            fontSize: '12px', color: 'var(--text-muted)'
          }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
              <span style={{ width: '7px', height: '7px', borderRadius: '50%', background: '#28c840', display: 'inline-block' }}></span>
              Profiling complete · 1.2s
            </span>
            <span>4 columns · 12,430 rows</span>
            <span>2 issues detected</span>
          </div>
        </div>
      </div>

      {/* === MARQUEE STRIP === */}
      <div style={{
        width: '100%', marginTop: '5rem',
        padding: '30px 0', background: 'transparent',
        overflow: 'hidden', whiteSpace: 'nowrap',
      }}>
        <div style={{ display: 'inline-flex', animation: 'marqueeLeft 40s linear infinite' }}>
          {[...Array(2)].map((_, si) => (
            <div key={si} style={{ display: 'flex', alignItems: 'center' }}>
              {marqueeLogos.map((item, i) => (
                <div key={`${si}-${i}`} style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '0 4rem', color: 'var(--text-muted)' }}>
                  {item.icon}
                  <span style={{ fontSize: '19px', fontWeight: 800, letterSpacing: '-0.03em', marginTop: '1px' }}>{item.name}</span>
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>

    </section>
  );
}

export default HeroSection;
