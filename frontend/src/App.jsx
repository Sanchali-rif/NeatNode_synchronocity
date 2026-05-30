import React, { useState, useEffect } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

import Navbar from './components/Navbar';
import HeroSection from './components/HeroSection';
import FeaturesSection from './components/FeaturesSection';
import PipelineSection from './components/PipelineSection';
import StatsSection from './components/StatsSection';
import BenefitsSection from './components/BenefitsSection';
import CTASection from './components/CTASection';
import Footer from './components/Footer';
import ModifiedClassicLoader from './components/ModifiedClassicLoader';
import Upload from './Upload';
import Result from './Result';
import Dashboard from './dashboard';
import ClickSpark from './components/ClickSpark';
import { useLenis } from './components/LenisProvider';
import './index.css';

gsap.registerPlugin(ScrollTrigger);

function App() {
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('theme') || 'light';
  });

  const [isLaunching, setIsLaunching] = useState(false);
  const [launchMessage, setLaunchMessage] = useState('');
  const [route, setRoute] = useState(() => window.location.hash || '#');

  const getResultToken = (hash) => {
    const m = hash.match(/^#result\/([a-f0-9]+)$/);
    return m ? m[1] : null;
  };

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  const lenis = useLenis();

  useEffect(() => {
    const handleHashChange = () => setRoute(window.location.hash || '#');
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  useEffect(() => {
    lenis?.scrollTo(0, { immediate: true });
    ScrollTrigger.refresh();
  }, [route, lenis]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
  };

  const handleLaunch = () => {
    setIsLaunching(true);
    setLaunchMessage('Initializing NeatNode engine...');
    
    setTimeout(() => {
      setLaunchMessage('Connecting to PostgreSQL database...');
    }, 800);

    setTimeout(() => {
      setLaunchMessage('Loading data profiling models...');
    }, 1600);

    setTimeout(() => {
      setIsLaunching(false);
      window.location.hash = '#upload';
    }, 2400);
  };

  return (
    <ClickSpark
      sparkColor={theme === 'dark' ? '#fff' : '#000'}
      sparkSize={10}
      sparkRadius={15}
      sparkCount={8}
      duration={400}
    >
      <Navbar theme={theme} toggleTheme={toggleTheme} />
      <main>
        {getResultToken(route) ? (
          <Result token={getResultToken(route)} theme={theme} />
        ) : route === '#upload' ? (
          <Upload theme={theme} />
        ) : route === '#dashboard' ? (
          <Dashboard />
        ) : (
          <>
            <HeroSection />
            <FeaturesSection />
            <PipelineSection />
            <StatsSection />
            <BenefitsSection />
            <CTASection onLaunch={handleLaunch} />
          </>
        )}
      </main>
      {!getResultToken(route) && route !== '#upload' && <Footer />}

      {/* Glassmorphic fullscreen loading overlay */}
      {isLaunching && (
        <div style={{
          position: 'fixed',
          inset: 0,
          background: theme === 'dark' ? 'rgba(3, 0, 20, 0.85)' : 'rgba(244, 244, 250, 0.85)',
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 9999,
          animation: 'fadeIn 0.3s ease-out'
        }}>
          <style>{`
            @keyframes fadeIn {
              from { opacity: 0; }
              to { opacity: 1; }
            }
            .overlay-container {
              display: flex;
              flex-direction: column;
              align-items: center;
              gap: 1.5rem;
            }
            .overlay-message {
              font-size: 15px;
              font-weight: 600;
              color: var(--text-heading);
              font-family: monospace;
              letter-spacing: 0.05em;
              text-align: center;
              animation: blink 1.5s ease-in-out infinite;
            }
          `}</style>
          <div className="overlay-container">
            <ModifiedClassicLoader />
            <div className="overlay-message">
              {launchMessage}
            </div>
          </div>
        </div>
      )}
    </ClickSpark>
  );
}

export default App;