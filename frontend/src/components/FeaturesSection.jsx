import React, { useEffect, useRef, useState } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { Layers, Brain, Code, UserCheck, Scroll, Terminal } from 'lucide-react';
import BorderGlow from './magicui/BorderGlow';

// Per-feature glow config — dark theme uses lighter/pastel colors with plus-lighter blend
// Light theme needs darker, fully saturated colors so they show on a white background
const featureGlowConfigDark = [
  { glowColor: '248 90 82', colors: ['#c4b5fd', '#e9d5ff', '#93c5fd'] }, // purple bright
  { glowColor: '161 85 65', colors: ['#6ee7b7', '#bbf7d0', '#34d399'] }, // green bright
  { glowColor: '22 100 68', colors: ['#fed7aa', '#fef08a', '#fb923c'] }, // orange bright
  { glowColor: '38 100 65', colors: ['#fef08a', '#fef9c3', '#fbbf24'] }, // amber bright
  { glowColor: '217 95 82', colors: ['#bfdbfe', '#c7d2fe', '#7dd3fc'] }, // blue bright
  { glowColor: '330 90 78', colors: ['#fbcfe8', '#fecdd3', '#e9d5ff'] }, // pink bright
];

const featureGlowConfigLight = [
  { glowColor: '248 85 45', colors: ['#4f46e5', '#7c3aed', '#1d4ed8'] }, // deep purple
  { glowColor: '161 98 28', colors: ['#059669', '#047857', '#0d9488'] }, // deep green
  { glowColor: '22 98 40',  colors: ['#ea580c', '#c2410c', '#d97706'] }, // deep orange
  { glowColor: '38 98 38',  colors: ['#d97706', '#b45309', '#ca8a04'] }, // deep amber
  { glowColor: '217 96 45', colors: ['#1d4ed8', '#4338ca', '#0369a1'] }, // deep blue
  { glowColor: '330 90 42', colors: ['#be185d', '#9f1239', '#86198f'] }, // deep pink
];

const leftFeatures = [
  {
    title: 'Auto Profiling',
    label: 'ANALYZE',
    icon: Layers,
    desc: 'Instantly scan datasets for schema, distributions, and anomalies—no rules needed.',
    accent: 'var(--feat-1-bg)',
    text: 'var(--feat-1)',
    cornerStyle: 'corner-br-sharp translate-x-right',
    index: 0
  },
  {
    title: 'Intelligent Strategy',
    label: 'RECOMMEND',
    icon: Brain,
    desc: 'AI recommends optimal imputation and scaling techniques based on your data context.',
    accent: 'var(--feat-2-bg)',
    text: 'var(--feat-2)',
    cornerStyle: 'corner-br-sharp translate-x-left',
    index: 1
  },
  {
    title: 'Smart Encoding',
    label: 'TRANSFORM',
    icon: Code,
    desc: 'Auto-handle high-cardinality categoricals with targeted embedding strategies.',
    accent: 'var(--feat-3-bg)',
    text: 'var(--feat-3)',
    cornerStyle: 'corner-tr-sharp translate-x-right',
    index: 2
  }
];

const rightFeatures = [
  {
    title: 'Human-in-the-Loop',
    label: 'CONTROL',
    icon: UserCheck,
    desc: 'Review, modify, and approve AI-generated strategies before any execution.',
    accent: 'var(--feat-4-bg)',
    text: 'var(--feat-4)',
    cornerStyle: 'corner-bl-sharp translate-x-left',
    index: 3
  },
  {
    title: 'Decision Log',
    label: 'AUDIT',
    icon: Scroll,
    desc: 'Every transformation is logged with an explainable rationale for full auditability.',
    accent: 'var(--feat-5-bg)',
    text: 'var(--feat-5)',
    cornerStyle: 'corner-bl-sharp translate-x-right',
    index: 4
  },
  {
    title: 'Pipeline Export',
    label: 'DEPLOY',
    icon: Terminal,
    desc: 'Export cleaning steps as native Python code, ready for any CI/CD pipeline.',
    accent: 'var(--feat-6-bg)',
    text: 'var(--feat-6)',
    cornerStyle: 'corner-tl-sharp translate-x-left',
    index: 5
  }
];

const FeatureCard = ({ feature, cardsRef, isDark }) => {
  const Icon = feature.icon;
  const glow = isDark
    ? featureGlowConfigDark[feature.index]
    : featureGlowConfigLight[feature.index];

  return (
    <div className={`card-wrapper ${feature.cornerStyle}`}>
      <BorderGlow
        glowColor={glow.glowColor}
        colors={glow.colors}
        backgroundColor="var(--bg-surface)"
        borderRadius={20}
        glowRadius={36}
        glowIntensity={isDark ? 1.8 : 2.4}
        edgeSensitivity={isDark ? 25 : 15}
        coneSpread={isDark ? 22 : 28}
        fillOpacity={0}
        className="feature-border-glow"
      >
        <div
          ref={el => cardsRef.current[feature.index] = el}
          className="feature-card-inner"
          style={{
            position: 'relative',
            padding: '28px',
            cursor: 'default',
            display: 'flex',
            flexDirection: 'column',
            height: '100%',
            overflow: 'hidden',
          }}
        >


          {/* Icon */}
          <div style={{
            color: feature.text,
            marginBottom: '1rem',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '44px',
            height: '44px',
            borderRadius: '12px',
            background: feature.accent
          }}>
            <Icon size={22} strokeWidth={2} />
          </div>

          {/* Label */}
          <div style={{
            fontSize: '11px',
            fontWeight: 700,
            color: feature.text,
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
            marginBottom: '0.5rem'
          }}>
            {feature.label}
          </div>

          <h3 style={{
            fontSize: '18px',
            fontWeight: 700,
            marginBottom: '0.625rem',
            color: 'var(--text-heading)'
          }}>
            {feature.title}
          </h3>

          <p style={{
            fontSize: '14px',
            color: 'var(--text-body)',
            lineHeight: 1.6,
            margin: 0
          }}>
            {feature.desc}
          </p>

          {/* Bottom gradient border line */}
          <div
            className="bottom-gradient-line"
            style={{
              background: `linear-gradient(90deg, transparent, ${feature.text}, transparent)`
            }}
          />
        </div>
      </BorderGlow>
    </div>
  );
};

function FeaturesSection() {
  const sectionRef = useRef(null);
  const cardsRef = useRef([]);

  useEffect(() => {
    let ctx = gsap.context(() => {
      gsap.fromTo(cardsRef.current.filter(Boolean),
        { y: 36, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.75, stagger: 0.1, ease: 'power3.out',
          scrollTrigger: { trigger: sectionRef.current, start: 'top 80%' }
        }
      );
    }, sectionRef);
    return () => ctx.revert();
  }, []);

  return (
    <section id="features" ref={sectionRef} style={{ background: 'var(--bg-page)', padding: '8rem 0', position: 'relative', overflow: 'hidden' }}>
      <style>{`
        .features-grid {
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
        }

        .card-wrapper {
          width: 100%;
          transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        }

        /* Make BorderGlow fill the card-wrapper */
        .feature-border-glow {
          width: 100% !important;
          height: 100% !important;
          backdrop-filter: var(--card-backdrop);
          -webkit-backdrop-filter: var(--card-backdrop);
        }

        /* Override BorderGlow default dark background for light theme */
        :root .feature-border-glow {
          border-color: var(--border-solid) !important;
        }

        [data-theme="dark"] .feature-border-glow {
          border-color: rgba(255,255,255,0.08) !important;
        }

        /* Remove inner mesh-gradient radial fill — keep only border outline glow */
        .feature-border-glow::before,
        .feature-border-glow::after {
          display: none !important;
        }

        .center-col {
          order: -1;
          margin-bottom: 2.5rem;
          align-self: center;
          text-align: center;
        }

        @media (min-width: 768px) {
          .features-grid {
            display: grid;
            grid-template-columns: 1fr 1.1fr 1fr;
            align-items: center;
            gap: 2rem;
          }

          .center-col {
            order: 0;
            margin-bottom: 0;
          }

          .translate-x-right {
            transform: translateX(16px);
          }

          .translate-x-left {
            transform: translateX(-16px);
          }

          .translate-x-right:hover {
            transform: translate(16px, -5px) !important;
          }
          .translate-x-left:hover {
            transform: translate(-16px, -5px) !important;
          }
        }

        @media (max-width: 767px) {
          .card-wrapper:hover {
            transform: translateY(-5px) !important;
          }
        }

        /* Sharp corner custom rules */
        .corner-br-sharp .feature-border-glow {
          border-bottom-right-radius: 2px !important;
        }
        .corner-tr-sharp .feature-border-glow {
          border-top-right-radius: 2px !important;
        }
        .corner-bl-sharp .feature-border-glow {
          border-bottom-left-radius: 2px !important;
        }
        .corner-tl-sharp .feature-border-glow {
          border-top-left-radius: 2px !important;
        }

        .feature-card-inner {
          transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
        }

        /* Decorative bottom line gradient */
        .bottom-gradient-line {
          position: absolute;
          bottom: -1px;
          left: 50%;
          transform: translateX(-50%);
          height: 1px;
          width: 50%;
          opacity: 0.6;
          pointer-events: none;
        }

        /* Radial glow inside the card */
        .radial-glow {
          position: absolute;
          inset: 0;
          opacity: 0.6;
          pointer-events: none;
          border-radius: inherit;
        }

        .features-badge {
          position: relative;
          background: var(--bg-surface);
          color: var(--text-body);
          border: 1px solid var(--border-solid);
          margin: 0 auto 1.5rem auto;
          width: fit-content;
          border-radius: 999px;
          border-bottom-left-radius: 2px;
          padding: 6px 16px;
          font-size: 13px;
          font-weight: 500;
          display: flex;
          align-items: center;
          gap: 8px;
          box-shadow: var(--shadow-card);
        }

        .badge-line {
          position: absolute;
          bottom: -1px;
          left: 50%;
          transform: translateX(-50%);
          height: 1px;
          width: 40%;
          background: linear-gradient(90deg, transparent, var(--accent-primary), transparent);
        }

        .badge-glow {
          position: absolute;
          inset: 0;
          background: radial-gradient(30% 40% at 50% 100%, var(--accent-primary) 15%, transparent 100%);
          opacity: 0.15;
          border-radius: inherit;
          pointer-events: none;
        }
      `}</style>

      <div className="container">
        <div className="features-grid">
          {/* Left Column */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            {leftFeatures.map((f, i) => (
              <FeatureCard key={`left-${i}`} feature={f} cardsRef={cardsRef} />
            ))}
          </div>

          {/* Center Column */}
          <div className="center-col">
            <div className="features-badge">
              <span style={{ position: 'relative', zIndex: 1, display: 'flex', alignItems: 'center', gap: '6px' }}>
                Core Capabilities
              </span>
              <span className="badge-line"></span>
              <span className="badge-glow"></span>
            </div>
            <h2 style={{ fontSize: 'clamp(2rem, 3.5vw, 2.5rem)', marginBottom: '1.25rem', color: 'var(--text-heading)', lineHeight: '1.2' }}>
              Six Pillars of Intelligent Cleaning
            </h2>
            <p style={{ color: 'var(--text-body)', fontSize: '16px', maxWidth: '340px', margin: '0 auto', lineHeight: '1.6' }}>
              A robust foundation to handle any data mess with precision and full transparency.
            </p>
          </div>

          {/* Right Column */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            {rightFeatures.map((f, i) => (
              <FeatureCard key={`right-${i}`} feature={f} cardsRef={cardsRef} />
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

export default FeaturesSection;
