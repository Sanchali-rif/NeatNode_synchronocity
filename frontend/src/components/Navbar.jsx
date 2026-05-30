import React, { useEffect, useRef, useState } from 'react';
import gsap from 'gsap';
import PillNav from './magicui/PillNav';
import { useLenis } from './LenisProvider';

const NAV_ITEMS = [
  { label: 'Features',     href: '#features' },
  { label: 'How it Works', href: '#pipeline' },
  { label: 'Why NeatNode', href: '#why'      },
];

/* Logo — white icon works on both dark-indigo (dark mode) and accent-indigo (light mode) backgrounds */
const LOGO_SVG = `data:image/svg+xml,${encodeURIComponent(
  `<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.92)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>`
)}`;


/* ── Moon icon ── */
const MoonIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
  </svg>
);

/* ── Sun icon ── */
const SunIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="5" />
    <line x1="12" y1="1"  x2="12" y2="3"  />
    <line x1="12" y1="21" x2="12" y2="23" />
    <line x1="4.22"  y1="4.22"  x2="5.64"  y2="5.64"  />
    <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
    <line x1="1"  y1="12" x2="3"  y2="12" />
    <line x1="21" y1="12" x2="23" y2="12" />
    <line x1="4.22"  y1="19.78" x2="5.64"  y2="18.36" />
    <line x1="18.36" y1="5.64"  x2="19.78" y2="4.22"  />
  </svg>
);

function Navbar({ theme, toggleTheme }) {
  const [scrolled, setScrolled]   = useState(false);
  const toggleBtnRef              = useRef(null);
  const lenis                     = useLenis();

  /* Scroll detection */
  useEffect(() => {
    const onScroll = () => setScrolled((lenis?.scroll ?? window.scrollY) > 40);
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener('scroll', onScroll);
  }, [lenis]);

  /* Entrance animation for toggle button */
  useEffect(() => {
    if (toggleBtnRef.current) {
      gsap.fromTo(
        toggleBtnRef.current,
        { scale: 0, opacity: 0 },
        { scale: 1, opacity: 1, duration: 0.55, delay: 0.18, ease: 'power3.out' }
      );
    }
  }, []);

  const isDark = theme === 'dark';

  /* ── PillNav color tokens ── */
  // Dark: deep space-indigo outer ring, glassy violet pill slots, bright lavender text
  // Light: pure white pill container, rich indigo outer ring, deep navy text
  const baseColor            = isDark ? '#0a0820'          : '#5b49e9';   // accent-primary for light
  const pillColor            = isDark ? 'rgba(30,24,58,0.95)'  : '#ffffff';
  const pillTextColor        = isDark ? 'rgba(196,186,255,0.75)' : '#2a2060';
  const hoveredPillTextColor = isDark ? '#e8e4ff'          : '#ffffff';

  /* Toggle button styles */
  const toggleStyle = {
    width:           '46px',
    height:          '46px',
    borderRadius:    '50%',
    background:      isDark ? '#0a0820'  : '#5b49e9',
    border:          isDark
                       ? '1px solid rgba(139,92,246,0.35)'
                       : '1px solid rgba(91,73,233,0.4)',
    backdropFilter:  'blur(16px)',
    WebkitBackdropFilter: 'blur(16px)',
    color:           isDark ? 'rgba(196,186,255,0.9)' : '#ffffff',
    display:         'flex',
    alignItems:      'center',
    justifyContent:  'center',
    cursor:          'pointer',
    flexShrink:      0,
    boxShadow:       isDark
                       ? '0 2px 12px rgba(91,73,233,0.35), 0 0 0 1px rgba(139,92,246,0.1)'
                       : '0 2px 12px rgba(91,73,233,0.45), 0 4px 20px rgba(91,73,233,0.2)',
    transition:      'transform 0.25s cubic-bezier(0.16,1,0.3,1), box-shadow 0.25s ease',
  };

  return (
    <>
      <style>{`
        .navbar-fixed-wrapper {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          z-index: 200;
          display: flex;
          justify-content: center;
          pointer-events: none;
          transition: padding 0.5s cubic-bezier(0.16, 1, 0.3, 1);
        }

        .navbar-inner {
          display: flex;
          align-items: center;
          gap: 8px;
          pointer-events: auto;
        }

        /* Mobile: stretch across full width */
        @media (max-width: 768px) {
          .navbar-inner {
            width: 100%;
            padding: 0 1rem;
            justify-content: space-between;
          }
          .pill-nav-container {
            flex: 1;
          }
        }

        .theme-toggle-btn:hover {
          transform: scale(1.08) !important;
        }

        .theme-toggle-btn:active {
          transform: scale(0.95) !important;
        }
      `}</style>

      <div
        className="navbar-fixed-wrapper"
        style={{ paddingTop: scrolled ? '14px' : '26px' }}
      >
        <div className="navbar-inner">
          <PillNav
            logo={LOGO_SVG}
            logoAlt="NeatNode"
            logoHref="#"
            items={NAV_ITEMS}
            baseColor={baseColor}
            pillColor={pillColor}
            pillTextColor={pillTextColor}
            hoveredPillTextColor={hoveredPillTextColor}
            ease="power3.easeOut"
            initialLoadAnimation
          />

          {/* Theme toggle – matching pill-logo circle style */}
          <button
            ref={toggleBtnRef}
            className="theme-toggle-btn"
            onClick={toggleTheme}
            style={toggleStyle}
            title={isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            aria-label={isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
          >
            {isDark ? <SunIcon /> : <MoonIcon />}
          </button>
        </div>
      </div>
    </>
  );
}

export default Navbar;
