import React from 'react';

function Footer() {
  const links = {
    Product: [
      { label: 'Features', href: '#' },
      { label: 'Pipeline', href: '#' },
      { label: 'How it Works', href: '#' },
      { label: 'Changelog', href: '#' },
    ],
    Resources: [
      { label: 'Documentation', href: '#' },
      { label: 'GitHub', href: 'https://github.com/Sanchali-rif/NeatNode_synchronocity', external: true },
      { label: 'Devpost', href: '#' },
      { label: 'API Reference', href: '#' },
    ],
    Company: [
      { label: 'About', href: '#' },
      { label: 'Blog', href: '#' },
      { label: 'Team', href: '#' },
      { label: 'Contact', href: '#' },
    ],
  };

  const currentYear = new Date().getFullYear();

  return (
    <footer className="footer-wrapper">
      {/* 1. Top border with moving energy flow */}
      <div className="footer-top-border animate-energy-flow" />

      <div className="container relative-container">
        {/* 2. Glow effect behind the footer content */}
        <span className="footer-glow" />

        {/* 3. Main Footer Grid */}
        <div className="footer-grid">
          {/* Brand & Description Column */}
          <div className="footer-brand-column">
            <div className="footer-logo-row">
              <div className="footer-logo-box">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
                </svg>
              </div>
              <span className="footer-brand-name">NeatNode</span>
            </div>
            
            <p className="footer-description">
              Intelligent, explainable data cleaning — built for the modern data team.
            </p>

            {/* Premium Social Icon Buttons using custom inline SVGs */}
            <div className="footer-social-row">
              <a
                href="#"
                className="footer-social-btn"
                aria-label="Twitter"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="footer-social-icon">
                  <path d="M22 4s-.7 2.1-2 3.4c1.6 10-9.4 17.3-18 11.6 2.2.1 4.4-.6 6-2C3 15.5.5 9.6 3 5c2.2 2.6 5.6 4.1 9 4-.9-4.2 4-6.6 7-3.8 1.1 0 3-1.2 3-1.2z" />
                </svg>
              </a>
              <a
                href="https://github.com/Sanchali-rif/NeatNode_synchronocity"
                className="footer-social-btn"
                aria-label="GitHub"
                target="_blank"
                rel="noopener noreferrer"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="footer-social-icon">
                  <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4" />
                  <path d="M9 18c-4.51 2-5-2-7-2" />
                </svg>
              </a>
              <a
                href="#"
                className="footer-social-btn"
                aria-label="LinkedIn"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="footer-social-icon">
                  <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z" />
                  <rect width="4" height="12" x="2" y="9" />
                  <circle cx="4" cy="4" r="2" />
                </svg>
              </a>
            </div>

            {/* Newsletter Subscription */}
            <form onSubmit={(e) => e.preventDefault()} className="footer-newsletter-form">
              <label htmlFor="footer-email" className="footer-newsletter-label">
                Subscribe to our newsletter
              </label>
              <div className="footer-input-group">
                <input
                  type="email"
                  id="footer-email"
                  placeholder="Enter your email"
                  className="footer-newsletter-input"
                  required
                />
                <button type="submit" className="footer-newsletter-btn">
                  Subscribe
                </button>
              </div>
              <p className="footer-newsletter-hint">
                Get the latest updates, tutorials, and exclusive offers.
              </p>
            </form>

            <h1 className="footer-watermark">NeatNode</h1>
          </div>

          {/* Links Columns */}
          <div className="footer-links-grid">
            {Object.entries(links).map(([cat, items]) => (
              <div key={cat} className="footer-links-column">
                <h3 className="footer-column-title">{cat}</h3>
                <ul className="footer-links-list">
                  {items.map(item => (
                    <li key={item.label}>
                      <a
                        href={item.href}
                        className="footer-animated-link"
                        {...(item.external ? { target: '_blank', rel: 'noopener noreferrer' } : {})}
                      >
                        <span className="footer-link-arrow">→</span>
                        {item.label}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>

        {/* 4. Bottom Divider Line */}
        <div className="footer-bottom-divider" />

        {/* 5. Bottom Section */}
        <div className="footer-bottom-bar">
          <p className="footer-copyright">
            &copy; {currentYear} NeatNode. Built with ❤️
          </p>
          <div className="footer-bottom-links">
            {['Twitter', 'GitHub', 'LinkedIn'].map(s => (
              <a key={s} href="#" className="footer-bottom-link">
                {s}
              </a>
            ))}
          </div>
        </div>
      </div>

      <style>{`
        /* ===== Premium Footer Styling ===== */
        .footer-wrapper {
          position: relative;
          background: linear-gradient(180deg, var(--bg-surface) 0%, var(--bg-surface-alt) 100%);
          border-top: 1px solid var(--border-solid);
          padding-top: 5rem;
          padding-bottom: 3rem;
          overflow: hidden;
          width: 100%;
          transition: background-color 0.4s ease, border-color 0.4s ease;
          z-index: 10;
          box-shadow: 0 -15px 40px rgba(26, 29, 33, 0.03); /* Subtle top shade in light theme */
        }

        [data-theme="dark"] .footer-wrapper {
          background: var(--bg-surface);
          box-shadow: none;
        }

        .relative-container {
          position: relative;
          z-index: 2;
        }

        /* Ambient Glow Backdrop */
        .footer-glow {
          position: absolute;
          inset-x: 0;
          bottom: 0;
          left: 0;
          height: 100%;
          width: 100%;
          background: radial-gradient(circle at bottom, var(--accent-primary) 0%, transparent 60%);
          opacity: 0.06;
          z-index: -1;
          pointer-events: none;
        }

        [data-theme="dark"] .footer-glow {
          opacity: 0.05;
        }

        /* Top Line Energy Flow Animation */
        .footer-top-border {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 2px;
          background: linear-gradient(90deg, transparent, var(--accent-primary), transparent);
          background-size: 200% 100%;
        }

        .animate-energy-flow {
          animation: energy-flow 6s linear infinite;
        }

        @keyframes energy-flow {
          0% {
            background-position: -200% 0;
          }
          100% {
            background-position: 200% 0;
          }
        }

        /* Main Grid */
        .footer-grid {
          display: grid;
          grid-template-columns: 1fr;
          gap: 4rem;
          margin-bottom: 4rem;
        }

        @media (min-width: 1024px) {
          .footer-grid {
            grid-template-columns: 2fr 3fr;
            gap: 6rem;
          }
        }

        /* Brand Column */
        .footer-brand-column {
          display: flex;
          flex-direction: column;
          align-items: flex-start;
          gap: 1.5rem;
        }

        .footer-logo-row {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .footer-logo-box {
          width: 40px;
          height: 40px;
          border-radius: 10px;
          background: var(--accent-primary-gradient);
          display: flex;
          align-items: center;
          justify-content: center;
          box-shadow: 0 0 16px rgba(91, 73, 233, 0.15);
          transition: transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }

        .footer-logo-box:hover {
          transform: rotate(12deg) scale(1.08);
        }

        .footer-logo-box svg {
          stroke: #ffffff !important;
        }

        .footer-brand-name {
          font-weight: 850;
          font-size: 21px;
          color: var(--text-heading);
          letter-spacing: -0.03em;
        }

        .footer-description {
          font-size: 14.5px;
          color: var(--text-body);
          line-height: 1.7;
          max-width: 320px;
          margin: 0;
        }

        /* Social Icon Buttons */
        .footer-social-row {
          display: flex;
          gap: 0.75rem;
        }

        .footer-social-btn {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 38px;
          height: 38px;
          border-radius: 9px;
          border: 1px solid var(--border-solid);
          background: var(--bg-surface);
          color: var(--text-body);
          transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }

        .footer-social-btn:hover {
          background: var(--accent-primary);
          color: #ffffff;
          border-color: var(--accent-primary);
          transform: translateY(-4px) scale(1.1) rotate(-8deg);
          box-shadow: 0 8px 16px rgba(91, 73, 233, 0.25);
        }

        .footer-social-icon {
          width: 16px;
          height: 16px;
        }

        /* Newsletter Subscription */
        .footer-newsletter-form {
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
          max-width: 320px;
          width: 100%;
          margin-top: 1rem;
        }

        .footer-newsletter-label {
          font-size: 13.5px;
          font-weight: 650;
          color: var(--text-heading);
          letter-spacing: -0.01em;
        }

        .footer-input-group {
          position: relative;
          display: flex;
          align-items: center;
          width: 100%;
        }

        .footer-newsletter-input {
          width: 100%;
          height: 46px;
          padding: 0 100px 0 1rem;
          border-radius: 10px;
          border: 1px solid var(--border-solid);
          background: var(--bg-surface-alt);
          color: var(--text-heading);
          font-size: 14px;
          outline: none;
          transition: all 0.3s ease;
        }

        .footer-newsletter-input:focus {
          border-color: var(--accent-primary);
          background: var(--bg-surface);
          box-shadow: 0 0 0 3px rgba(91, 73, 233, 0.12);
        }

        .footer-newsletter-btn {
          position: absolute;
          right: 5px;
          height: 36px;
          padding: 0 14px;
          border-radius: 7px;
          background: var(--btn-dark-bg);
          color: var(--btn-dark-text);
          font-size: 13px;
          font-weight: 600;
          transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        }

        .footer-newsletter-btn:hover {
          background: var(--accent-primary);
          color: #ffffff;
          padding: 0 18px;
        }

        .footer-newsletter-hint {
          font-size: 11.5px;
          color: var(--text-muted);
          line-height: 1.4;
        }

        /* Large Watermark Heading */
        .footer-watermark {
          font-size: clamp(3.5rem, 8vw, 6rem);
          font-weight: 950;
          letter-spacing: -0.05em;
          background: linear-gradient(180deg, var(--text-heading) 0%, transparent 100%);
          background-clip: text;
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          opacity: 0.22;
          user-select: none;
          margin-top: 1.5rem;
          line-height: 0.9;
        }

        [data-theme="dark"] .footer-watermark {
          background: linear-gradient(180deg, var(--text-muted) 0%, transparent 100%);
          background-clip: text;
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          opacity: 0.08;
        }

        /* Links Columns Grid */
        .footer-links-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 3rem;
          width: 100%;
        }

        @media (min-width: 640px) {
          .footer-links-grid {
            grid-template-columns: repeat(3, 1fr);
          }
        }

        .footer-links-column {
          display: flex;
          flex-direction: column;
          align-items: flex-start;
        }

        .footer-column-title {
          font-size: 12px;
          font-weight: 750;
          color: var(--text-heading);
          text-transform: uppercase;
          letter-spacing: 0.1em;
          margin-bottom: 1.5rem;
          position: relative;
          padding-left: 10px;
          border-left: 2px solid var(--accent-primary);
          line-height: 1;
        }

        .footer-links-list {
          display: flex;
          flex-direction: column;
          gap: 0.85rem;
          list-style: none;
          padding: 0;
          margin: 0;
        }

        .footer-animated-link {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          font-size: 14.5px;
          color: var(--text-body);
          transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
          left: 0;
        }

        .footer-link-arrow {
          font-size: 12px;
          color: var(--accent-primary);
          opacity: 0;
          transform: translateX(-6px);
          transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        }

        .footer-animated-link:hover {
          color: var(--text-heading);
          transform: translateX(6px);
        }

        .footer-animated-link:hover .footer-link-arrow {
          opacity: 1;
          transform: translateX(0);
        }

        /* Bottom Section Divider */
        .footer-bottom-divider {
          width: 100%;
          height: 1px;
          background: var(--border-solid);
          margin-bottom: 2rem;
          position: relative;
        }

        .footer-bottom-divider::after {
          content: '';
          position: absolute;
          top: -0.5px;
          left: 10%;
          width: 80%;
          height: 2px;
          background: linear-gradient(90deg, transparent, var(--accent-primary), transparent);
          opacity: 0.35;
        }

        /* Bottom Bar */
        .footer-bottom-bar {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: space-between;
          gap: 1.5rem;
          width: 100%;
        }

        @media (min-width: 768px) {
          .footer-bottom-bar {
            flex-direction: row;
          }
        }

        .footer-copyright {
          font-size: 13.5px;
          color: var(--text-muted);
          margin: 0;
        }

        .footer-bottom-links {
          display: flex;
          align-items: center;
          gap: 2rem;
        }

        .footer-bottom-link {
          font-size: 13.5px;
          color: var(--text-muted);
          transition: color 0.25s ease, transform 0.2s ease;
        }

        .footer-bottom-link:hover {
          color: var(--text-heading);
          transform: translateY(-1px);
        }
      `}</style>
    </footer>
  );
}

export default Footer;
