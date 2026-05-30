import React, { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

const stats = [
  { value: '95%',  label: 'imputation accuracy achieved on average across datasets' },
  { value: '<2s',  label: 'profile time to analyze and scan a 1M row dataset' },
  { value: '5+',   label: 'advanced cleaning algorithms and strategies built-in' },
  { value: '100%', label: 'explainable actions recorded in the full decision log' },
];

function StatsSection() {
  const sectionRef = useRef(null);
  const itemsRef = useRef([]);

  useEffect(() => {
    let ctx = gsap.context(() => {
      gsap.fromTo(itemsRef.current,
        { y: 20, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.8, stagger: 0.15, ease: 'power3.out',
          scrollTrigger: { trigger: sectionRef.current, start: 'top 85%' }
        }
      );
    }, sectionRef);
    return () => ctx.revert();
  }, []);

  const handleMouseMove = (e) => {
    if (!sectionRef.current) return;
    // Global mouse X for the full-width border lines
    sectionRef.current.style.setProperty('--global-mouse-x', `${e.clientX}px`);
  };

  return (
    <section 
      ref={sectionRef} 
      onMouseMove={handleMouseMove}
      style={{ background: 'var(--bg-page)', padding: '8rem 0', position: 'relative', overflow: 'hidden' }}
    >
      <style>
        {`
          .stats-grid-wrapper {
            position: relative;
          }

          .stats-grid {
            display: flex;
            flex-direction: column;
            gap: 4rem;
            position: relative;
            padding: 4rem 0;
            z-index: 1;
          }
          .stat-divider {
            display: none;
          }
          
          /* Hover effect for individual stat items */
          .stat-item {
            transition: transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            border-radius: 16px;
            position: relative;
            z-index: 2;
            cursor: pointer;
          }
          .stat-item:hover {
            transform: translateY(-8px) scale(1.02);
          }
          .stat-item .stat-value {
            transition: color 0.3s ease, text-shadow 0.3s ease;
          }
          .stat-item:hover .stat-value {
            color: #ea580c; /* Soft orange accent */
            text-shadow: 0 10px 30px rgba(234, 88, 12, 0.25);
          }

          /* Dynamic glowing border line */
          .glow-line {
            position: absolute;
            left: 50%;
            transform: translateX(-50%);
            width: 100vw;
            height: 1px;
            background: linear-gradient(90deg, transparent 0%, var(--border-solid) 15%, var(--border-solid) 85%, transparent 100%);
            z-index: 2;
            pointer-events: none;
          }
          .glow-line-inner {
            position: absolute;
            inset: 0;
            background: radial-gradient(350px circle at var(--global-mouse-x, 50vw) 0, #ea580c, transparent 100%);
            opacity: 0.9;
          }

          @media (min-width: 768px) {
            .stats-grid {
              flex-direction: row;
              justify-content: space-between;
              align-items: stretch;
              gap: 0;
            }
            .stat-divider {
              display: block;
              width: 1px;
              background: linear-gradient(180deg, transparent, var(--border-solid) 20%, var(--border-solid) 80%, transparent);
            }
            .stat-item {
              flex: 1;
              padding: 0 2rem;
            }
          }
        `}
      </style>

      <div className="container" style={{ maxWidth: '1200px', margin: '0 auto', textAlign: 'center' }}>
        
        {/* Hover.dev style Heading */}
        <div style={{ marginBottom: '4rem' }}>
          <h2 style={{ 
            fontSize: 'clamp(2.5rem, 6vw, 4.5rem)', 
            fontWeight: 400, 
            lineHeight: 1.1, 
            letterSpacing: '-0.04em',
            color: 'var(--text-heading)',
            margin: 0
          }}>
            The control layer<br />
            for modern data teams
          </h2>
        </div>

        {/* Stats Grid Container with Glow Follower */}
        <div className="stats-grid-wrapper">
          
          {/* Top Glowing Line */}
          <div className="glow-line" style={{ top: 0 }}>
            <div className="glow-line-inner"></div>
          </div>

          <div className="stats-grid">
            {stats.map((s, i) => (
              <React.Fragment key={i}>
                <div
                  ref={el => itemsRef.current[i] = el}
                  className="stat-item"
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                  }}
                >
                  <div 
                    className="stat-value"
                    style={{
                      fontSize: 'clamp(4rem, 8vw, 5.5rem)',
                      fontWeight: 300,
                      letterSpacing: '-0.05em',
                      color: 'var(--text-heading)',
                      lineHeight: 1,
                      marginBottom: '1.25rem',
                    }}
                  >
                    {s.value}
                  </div>
                  <div style={{ 
                    fontSize: '15px', 
                    color: 'var(--text-muted)', 
                    fontWeight: 400,
                    lineHeight: 1.6,
                    maxWidth: '220px'
                  }}>
                    {s.label}
                  </div>
                </div>

                {/* Vertical separator for all but last item */}
                {i < stats.length - 1 && (
                  <div className="stat-divider"></div>
                )}
              </React.Fragment>
            ))}
          </div>

          {/* Bottom Glowing Line */}
          <div className="glow-line" style={{ bottom: 0 }}>
            <div className="glow-line-inner"></div>
          </div>

        </div>
      </div>
    </section>
  );
}

export default StatsSection;
