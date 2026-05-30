import React, { useRef } from 'react';
import gsap from 'gsap';

function CTASection({ onLaunch }) {
  const sectionRef = useRef(null);

  return (
    <section ref={sectionRef} style={{
      background: 'var(--bg-page)',
      padding: '10rem 0',
      position: 'relative',
      overflow: 'hidden',
      textAlign: 'center',
    }}>
      {/* Gradient blobs behind CTA */}
      <div className="blob" style={{ width: '500px', height: '400px', top: '-60px', left: '50%', transform: 'translateX(-50%)', background: 'var(--blob-purple)' }}/>
      <div className="blob" style={{ width: '360px', height: '360px', bottom: '-80px', right: '10%', background: 'var(--blob-green)' }}/>
      <div className="blob" style={{ width: '300px', height: '300px', bottom: '-60px', left: '8%', background: 'var(--blob-orange)' }}/>

      <div className="container" style={{ position: 'relative', zIndex: 1 }}>
        {/* Pill */}
        <div style={{ marginBottom: '2rem' }}>
          <span className="pill-badge">Ready to Start?</span>
        </div>

        <h2 style={{
          fontSize: 'clamp(2.5rem, 6vw, 4.5rem)',
          fontWeight: 900,
          letterSpacing: '-0.04em',
          color: 'var(--text-heading)',
          maxWidth: '700px',
          margin: '0 auto 1.5rem auto',
          lineHeight: 1.05,
        }}>
          Your Clean Dataset Awaits.
        </h2>

        <p style={{
          fontSize: '18px', color: 'var(--text-body)', maxWidth: '500px',
          margin: '0 auto 3rem auto', lineHeight: 1.7,
        }}>
          Stop wasting hours on manual data wrangling. Let AI handle the heavy lifting — while you stay in full control.
        </p>

        <a href="#upload" style={{ textDecoration: 'none' }}>
          <button
            className="btn-dark"
            style={{ fontSize: '17px', padding: '1rem 2.25rem', borderRadius: '12px', gap: '10px', display: 'inline-flex', alignItems: 'center' }}
          >
            Enter NeatNode
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M5 12h14M12 5l7 7-7 7"/>
            </svg>
          </button>
        </a>
      </div>
    </section>
  );
}

export default CTASection;
