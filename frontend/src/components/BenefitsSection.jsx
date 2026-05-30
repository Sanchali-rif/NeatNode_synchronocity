import React, { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

const PillarIcon = ({ path, color }) => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d={path}/>
  </svg>
);

const pillars = [
  {
    iconPath: 'M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z',
    accent: 'var(--benefit-1)',
    bg: 'var(--benefit-1-bg)',
    title: 'Transparency First',
    desc: 'No black box operations. Understand exactly how and why your data is being modified.',
    points: ['Detailed decision logs per action', 'Before/after distribution views', 'Confidence scores on imputations'],
  },
  {
    iconPath: 'M18 20V10M12 20V4M6 20v8',
    accent: 'var(--benefit-2)',
    bg: 'var(--benefit-2-bg)',
    title: 'You Stay in Control',
    desc: 'AI proposes — you decide. Every strategy is reviewed before a single row is touched.',
    points: ['Approve or reject each suggestion', 'Write custom rule overrides', 'One-click rollback on any step'],
  },
  {
    iconPath: 'M13 2L3 14h9l-1 8 10-12h-9l1-8z',
    accent: 'var(--benefit-3)',
    bg: 'var(--benefit-3-bg)',
    title: 'Pipeline as Code',
    desc: 'Bridge the gap between notebook experiments and production pipelines instantly.',
    points: ['Export as native Python code', 'Works with Airflow & Prefect', 'Reproducible across environments'],
  },
];

function BenefitsSection() {
  const sectionRef = useRef(null);
  const cardsRef = useRef([]);

  useEffect(() => {
    let ctx = gsap.context(() => {
      // Scale down as next card stacks on top — cards stay fully opaque
      cardsRef.current.forEach((card, i) => {
        if (i === cardsRef.current.length - 1) return; // last card never shrinks

        gsap.to(card, {
          scale: 0.93 - i * 0.02,
          scrollTrigger: {
            trigger: cardsRef.current[i + 1],
            start: 'top 85%',
            end: 'top 30%',
            scrub: true,
          }
        });
      });
    }, sectionRef);
    return () => ctx.revert();
  }, []);

  return (
    <section id="why" ref={sectionRef} style={{ background: 'var(--bg-surface)', padding: '10rem 0 12rem 0' }}>
      <style>
        {`
          .stack-card {
            flex-direction: column;
          }
          .stack-checklist {
            background: var(--bg-surface-alt);
          }
          @media (min-width: 768px) {
            .stack-card {
              flex-direction: row;
              align-items: center;
              justify-content: space-between;
            }
          }
        `}
      </style>

      <div className="container" style={{ maxWidth: '1000px' }}>

        <div style={{ textAlign: 'center', marginBottom: '6rem' }}>
          <div style={{ marginBottom: '1.25rem' }}>
            <span className="pill-badge">Why NeatNode</span>
          </div>
          <h2 style={{ fontSize: 'clamp(2.5rem, 5vw, 3.5rem)', color: 'var(--text-heading)', letterSpacing: '-0.04em' }}>
            Built Different, By Design
          </h2>
          <p style={{ color: 'var(--text-body)', fontSize: '18px', maxWidth: '520px', margin: '1.5rem auto 0', lineHeight: 1.6 }}>
            We didn't just build a cleaner. We built a transparent, controllable data preparation partner.
          </p>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '35vh' }}>
          {pillars.map((p, i) => (
            <div
              key={i}
              style={{
                position: 'sticky',
                top: '10vh',
                zIndex: (i + 1) * 10,
                background: 'var(--bg-page)',
              }}
            >
              <div
                ref={el => cardsRef.current[i] = el}
                className="card stack-card"
                style={{ 
                  padding: '4rem', 
                  position: 'relative', 
                  overflow: 'hidden',
                  width: '100%',
                  display: 'flex',
                  gap: '4rem',
                  transformOrigin: 'top center',
                  background: 'var(--bg-surface)',
                  boxShadow: '0 -20px 60px rgba(0,0,0,0.15)',
                }}
              >
                {/* Subtle blob background */}
                <div style={{
                  position: 'absolute', top: '-10%', right: '-5%',
                  width: '350px', height: '350px', borderRadius: '50%',
                  background: p.bg, opacity: 0.3, filter: 'blur(80px)',
                  pointerEvents: 'none',
                  zIndex: 0
                }}/>

                {/* Left Side: Icon, Title, Desc */}
                <div style={{ flex: '1 1 50%', maxWidth: '480px', position: 'relative', zIndex: 1 }}>
                  <div style={{
                    width: '64px', height: '64px', borderRadius: '16px',
                    background: p.bg,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    marginBottom: '2rem',
                    boxShadow: '0 8px 32px rgba(0,0,0,0.05)'
                  }}>
                    <PillarIcon path={p.iconPath} color="var(--text-heading)" />
                  </div>
                  
                  <h3 style={{ fontSize: '32px', fontWeight: 800, marginBottom: '1rem', color: 'var(--text-heading)', letterSpacing: '-0.03em' }}>
                    {p.title}
                  </h3>
                  <p style={{ fontSize: '17px', color: 'var(--text-body)', lineHeight: 1.7 }}>
                    {p.desc}
                  </p>
                </div>

                {/* Right Side: Checkmarks */}
                <div className="stack-checklist" style={{ flex: '1 1 45%', padding: '2.5rem', borderRadius: '20px', position: 'relative', zIndex: 1 }}>
                  <ul style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                    {p.points.map((pt, j) => (
                      <li key={j} style={{ display: 'flex', alignItems: 'center', gap: '16px', fontSize: '16px', color: 'var(--text-heading)', fontWeight: 500 }}>
                        <div style={{ 
                          width: '28px', height: '28px', borderRadius: '50%', 
                          background: p.accent, display: 'flex', alignItems: 'center', justifyContent: 'center',
                          boxShadow: '0 4px 12px ' + p.bg,
                          flexShrink: 0
                        }}>
                          <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                            <polyline points="4,8 7,11 12,5" stroke="#fff" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
                          </svg>
                        </div>
                        {pt}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          ))}
        </div>

      </div>
    </section>
  );
}

export default BenefitsSection;
