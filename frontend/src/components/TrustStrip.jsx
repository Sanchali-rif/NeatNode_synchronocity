import React from 'react';

function TrustStrip() {
  const companies = ['ACME CORP', 'GLOBAL TECH', 'DATAWORKS', 'SYNTHETIX', 'NEURALABS'];
  return (
    <div style={{ background: 'var(--bg-surface)', padding: '3.5rem 0', borderBottom: '1px solid var(--border-solid)' }}>
      <div className="container" style={{ textAlign: 'center' }}>
        <p style={{ fontSize: '13px', fontWeight: 500, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '2rem' }}>
          Used by data teams at hackathons worldwide
        </p>
        <div style={{ display: 'flex', justifyContent: 'center', gap: '4rem', flexWrap: 'wrap' }}>
          {companies.map(c => (
            <div key={c} style={{ fontSize: '15px', fontWeight: 800, color: 'var(--trust-logo-color)', letterSpacing: '-0.01em' }}>{c}</div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default TrustStrip;
