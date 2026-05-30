import { useEffect, useRef, useState } from 'react';
import { gsap } from 'gsap';
import './PillNav.css';

const PillNav = ({
  logo,
  logoAlt = 'Logo',
  logoHref = '#',
  items,
  activeHref,
  className = '',
  ease = 'power3.easeOut',
  baseColor = '#0d0b1a',
  pillColor = '#1e1a2e',
  hoveredPillTextColor = 'rgba(220,216,255,0.95)',
  pillTextColor,
  onMobileMenuClick,
  initialLoadAnimation = true,
}) => {
  const resolvedPillTextColor = pillTextColor ?? 'rgba(220,216,255,0.8)';
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const circleRefs      = useRef([]);
  const tlRefs          = useRef([]);
  const activeTweenRefs = useRef([]);
  const logoImgRef      = useRef(null);
  const logoTweenRef    = useRef(null);
  const hamburgerRef    = useRef(null);
  const mobileMenuRef   = useRef(null);
  const navItemsRef     = useRef(null);
  const logoRef         = useRef(null);

  useEffect(() => {
    const layout = () => {
      circleRefs.current.forEach((circle, index) => {
        if (!circle?.parentElement) return;

        const pill = circle.parentElement;
        const rect = pill.getBoundingClientRect();
        const { width: w, height: h } = rect;
        if (!w || !h) return;

        const R      = ((w * w) / 4 + h * h) / (2 * h);
        const D      = Math.ceil(2 * R) + 2;
        const delta  = Math.ceil(R - Math.sqrt(Math.max(0, R * R - (w * w) / 4))) + 1;
        const originY = D - delta;

        circle.style.width  = `${D}px`;
        circle.style.height = `${D}px`;
        circle.style.bottom = `-${delta}px`;

        gsap.set(circle, { xPercent: -50, scale: 0, transformOrigin: `50% ${originY}px` });

        const label = pill.querySelector('.pill-label');
        const white = pill.querySelector('.pill-label-hover');

        if (label) gsap.set(label, { y: 0 });
        if (white) gsap.set(white, { y: h + 12, opacity: 0 });

        tlRefs.current[index]?.kill();
        const tl = gsap.timeline({ paused: true });

        tl.to(circle, { scale: 1.2, xPercent: -50, duration: 2, ease, overwrite: 'auto' }, 0);
        if (label) tl.to(label, { y: -(h + 8), duration: 2, ease, overwrite: 'auto' }, 0);
        if (white) {
          gsap.set(white, { y: Math.ceil(h + 100), opacity: 0 });
          tl.to(white, { y: 0, opacity: 1, duration: 2, ease, overwrite: 'auto' }, 0);
        }

        tlRefs.current[index] = tl;
      });
    };

    layout();
    window.addEventListener('resize', layout);
    document.fonts?.ready?.then(layout).catch(() => {});

    const menu = mobileMenuRef.current;
    if (menu) gsap.set(menu, { visibility: 'hidden', opacity: 0 });

    if (initialLoadAnimation) {
      const logo     = logoRef.current;
      const navItems = navItemsRef.current;

      if (logo) {
        gsap.fromTo(logo, { scale: 0, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.55, ease });
      }
      if (navItems) {
        gsap.fromTo(navItems, { opacity: 0, x: -10 }, { opacity: 1, x: 0, duration: 0.55, delay: 0.1, ease });
      }
    }

    return () => window.removeEventListener('resize', layout);
  }, [items, ease, initialLoadAnimation]);

  const handleEnter = i => {
    const tl = tlRefs.current[i];
    if (!tl) return;
    activeTweenRefs.current[i]?.kill();
    activeTweenRefs.current[i] = tl.tweenTo(tl.duration(), { duration: 0.3, ease, overwrite: 'auto' });
  };

  const handleLeave = i => {
    const tl = tlRefs.current[i];
    if (!tl) return;
    activeTweenRefs.current[i]?.kill();
    activeTweenRefs.current[i] = tl.tweenTo(0, { duration: 0.2, ease, overwrite: 'auto' });
  };

  const handleLogoEnter = () => {
    const img = logoImgRef.current;
    if (!img) return;
    logoTweenRef.current?.kill();
    gsap.set(img, { rotate: 0 });
    logoTweenRef.current = gsap.to(img, { rotate: 360, duration: 0.35, ease, overwrite: 'auto' });
  };

  const toggleMobileMenu = () => {
    const newState   = !isMobileMenuOpen;
    setIsMobileMenuOpen(newState);

    const hamburger = hamburgerRef.current;
    const menu      = mobileMenuRef.current;

    if (hamburger) {
      const lines = hamburger.querySelectorAll('.hamburger-line');
      if (newState) {
        gsap.to(lines[0], { rotation: 45,  y:  3, duration: 0.3, ease });
        gsap.to(lines[1], { rotation: -45, y: -3, duration: 0.3, ease });
      } else {
        gsap.to(lines[0], { rotation: 0, y: 0, duration: 0.3, ease });
        gsap.to(lines[1], { rotation: 0, y: 0, duration: 0.3, ease });
      }
    }

    if (menu) {
      if (newState) {
        gsap.set(menu, { visibility: 'visible' });
        gsap.fromTo(menu,
          { opacity: 0, y: 8 },
          { opacity: 1, y: 0, duration: 0.3, ease, transformOrigin: 'top center' }
        );
      } else {
        gsap.to(menu, {
          opacity: 0, y: 8, duration: 0.2, ease,
          transformOrigin: 'top center',
          onComplete: () => gsap.set(menu, { visibility: 'hidden' }),
        });
      }
    }

    onMobileMenuClick?.();
  };

  const cssVars = {
    '--base':      baseColor,
    '--pill-bg':   pillColor,
    '--hover-text': hoveredPillTextColor,
    '--pill-text': resolvedPillTextColor,
  };

  return (
    <div className="pill-nav-container">
      <nav className={`pill-nav ${className}`} aria-label="Primary" style={cssVars}>

        {/* Logo */}
        <a
          className="pill-logo"
          href={logoHref}
          aria-label="Home"
          onMouseEnter={handleLogoEnter}
          ref={logoRef}
        >
          <img src={logo} alt={logoAlt} ref={logoImgRef} />
        </a>

        {/* Desktop nav items */}
        <div className="pill-nav-items desktop-only" ref={navItemsRef}>
          <ul className="pill-list" role="menubar">
            {items.map((item, i) => (
              <li key={item.href || `item-${i}`} role="none">
                <a
                  role="menuitem"
                  href={item.href}
                  className={`pill${activeHref === item.href ? ' is-active' : ''}`}
                  aria-label={item.ariaLabel || item.label}
                  onMouseEnter={() => handleEnter(i)}
                  onMouseLeave={() => handleLeave(i)}
                >
                  <span
                    className="hover-circle"
                    aria-hidden="true"
                    ref={el => { circleRefs.current[i] = el; }}
                  />
                  <span className="label-stack">
                    <span className="pill-label">{item.label}</span>
                    <span className="pill-label-hover" aria-hidden="true">{item.label}</span>
                  </span>
                </a>
              </li>
            ))}
          </ul>
        </div>

        {/* Mobile hamburger */}
        <button
          className="mobile-menu-button mobile-only"
          onClick={toggleMobileMenu}
          aria-label="Toggle menu"
          ref={hamburgerRef}
        >
          <span className="hamburger-line" />
          <span className="hamburger-line" />
        </button>
      </nav>

      {/* Mobile dropdown */}
      <div className="mobile-menu-popover mobile-only" ref={mobileMenuRef} style={cssVars}>
        <ul className="mobile-menu-list">
          {items.map((item, i) => (
            <li key={item.href || `mobile-item-${i}`}>
              <a
                href={item.href}
                className={`mobile-menu-link${activeHref === item.href ? ' is-active' : ''}`}
                onClick={() => setIsMobileMenuOpen(false)}
              >
                {item.label}
              </a>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default PillNav;
