import { Link, useNavigate } from 'react-router-dom';
import { Zap, BarChart3, FileText, Download, LogIn, UserPlus, ArrowRight } from 'lucide-react';
import { Footer, LanguageSwitcher } from '../../../shared/components';
import useStore from '../../../stores/globalStore';
import { useLocale } from '../../../hooks/useLocale';
import { useEffect, useState } from 'react';

export function LandingPage() {
  const navigate = useNavigate();
  const { t, locale, changeLocale, isSyncing } = useLocale();
  const token = useStore((state) => state.auth.token);
  const [visibleFeatures, setVisibleFeatures] = useState([false, false, false, false]);
  const [hoveredIndex, setHoveredIndex] = useState(null);

  const features = [
    { icon: FileText, titleKey: 'landing.features.uploadCV.title', descKey: 'landing.features.uploadCV.desc' },
    { icon: BarChart3, titleKey: 'landing.features.smartAnalysis.title', descKey: 'landing.features.smartAnalysis.desc' },
    { icon: Zap, titleKey: 'landing.features.quickScreening.title', descKey: 'landing.features.quickScreening.desc' },
    { icon: Download, titleKey: 'landing.features.adaptedCVs.title', descKey: 'landing.features.adaptedCVs.desc' },
  ];

  useEffect(() => {
    const timings = [100, 200, 300, 400];
    const timers = timings.map((delay, idx) =>
      setTimeout(() => setVisibleFeatures(prev => { prev[idx] = true; return [...prev]; }), delay)
    );
    return () => timers.forEach(t => clearTimeout(t));
  }, []);

  return (
    <div className="flex flex-col min-h-screen bg-brand-black text-brand-white">
      {/* Decorative noise background */}
      <div className="fixed inset-0 opacity-5 pointer-events-none" style={{
        backgroundImage: 'url("data:image/svg+xml,%3Csvg viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg"%3E%3Cfilter id="noiseFilter"%3E%3CfeTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="4" result="noise"/%3E%3C/filter%3E%3Crect width="400" height="400" fill="white" filter="url(%23noiseFilter)"/%3E%3C/svg%3E")',
        backgroundSize: '100px 100px'
      }} />

      {/* NAV */}
      <nav className="relative z-10 flex justify-between items-center px-6 md:px-8 py-6 border-b border-brand-gold/30">
        <h1 className="text-xl md:text-2xl font-display font-black text-brand-gold tracking-tight">OptiCV</h1>
        <div className="flex gap-3 md:gap-4 items-center">
          <LanguageSwitcher locale={locale} onChange={changeLocale} isSyncing={isSyncing} compact />

          {token ? (
            <button
              onClick={() => navigate('/dashboard')}
              className="flex items-center justify-center gap-2 px-4 py-2 border border-brand-gold text-brand-gold hover:bg-brand-gold hover:text-brand-black transition text-sm font-mono"
              title="Go to Dashboard"
            >
              <BarChart3 size={16} />
              <span className="hidden sm:inline">{t('landing.dashboard')}</span>
            </button>
          ) : (
            <>
              <Link
                to="/auth/login"
                className="flex items-center gap-2 px-3 md:px-4 py-2 border border-brand-gray-light text-brand-white hover:border-brand-gold transition text-sm font-mono"
                title={t('auth.login')}
              >
                <LogIn size={16} />
                <span className="hidden sm:inline">{t('auth.login')}</span>
              </Link>
              <Link
                to="/auth/register"
                className="flex items-center gap-2 px-3 md:px-4 py-2 bg-brand-gold text-brand-black hover:opacity-90 transition text-sm font-mono font-bold"
                title={t('auth.register')}
              >
                <UserPlus size={16} />
                <span className="hidden sm:inline">{t('auth.register')}</span>
              </Link>
            </>
          )}
        </div>
      </nav>

      <div className="flex-1 relative z-0 bg-brand-black">
        {/* HERO SECTION */}
        <section className="px-6 md:px-8 py-16 md:py-32 max-w-7xl mx-auto">
          {/* Hero title with staggered animation */}
          <div className="mb-8 space-y-4">
            <h2 className="text-5xl md:text-7xl font-display font-black text-brand-white leading-tight" style={{ animation: 'fadeInUp 0.8s ease-out' }}>
              {t('landing.title')}
            </h2>
          </div>

          {/* Subtitle */}
          <p className="text-lg md:text-xl text-brand-white/70 max-w-2xl mb-12 font-mono leading-relaxed" style={{ animation: 'fadeInUp 0.8s ease-out 0.15s both' }}>
            {t('landing.subtitle')}
          </p>

          {/* CTA Button */}
          <div style={{ animation: 'fadeInUp 0.8s ease-out 0.3s both' }}>
            <Link
              to="/auth/register"
              className="inline-flex items-center gap-3 px-8 py-4 border-2 border-brand-gold text-brand-gold font-display font-bold text-lg hover:bg-brand-gold hover:text-brand-black transition duration-300"
            >
              {t('landing.getStarted')}
              <ArrowRight size={20} />
            </Link>
          </div>
        </section>

        {/* DIVIDER */}
        <div className="px-6 md:px-8 py-12">
          <div className="flex items-center gap-8 max-w-7xl mx-auto">
            <div className="flex-1 h-px bg-gradient-to-r from-brand-gold/30 to-transparent" />
            <span className="text-brand-gold/60 font-mono text-sm uppercase tracking-widest whitespace-nowrap">{t('landing.whyOptiCV')}</span>
            <div className="flex-1 h-px bg-gradient-to-l from-brand-gold/30 to-transparent" />
          </div>
        </div>

        {/* FEATURES SECTION */}
        <section className="px-6 md:px-8 py-20 max-w-7xl mx-auto bg-brand-black">
          {/* Grid with dynamic hover scaling */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 md:gap-12 auto-rows-max">
            {/* Feature 1 */}
            {visibleFeatures[0] && (
              <div
                onMouseEnter={() => setHoveredIndex(0)}
                onMouseLeave={() => setHoveredIndex(null)}
                className="transition-all duration-300"
                style={{
                  animation: 'fadeIn 0.6s ease-out',
                  transform: hoveredIndex === 0 ? 'scale(1.05)' : 'scale(1)',
                  zIndex: hoveredIndex === 0 ? 10 : 1,
                }}
              >
                <FeatureCard
                  number="01"
                  icon={features[0].icon}
                  titleKey={features[0].titleKey}
                  descKey={features[0].descKey}
                  t={t}
                />
              </div>
            )}

            {/* Feature 2 */}
            {visibleFeatures[1] && (
              <div
                onMouseEnter={() => setHoveredIndex(1)}
                onMouseLeave={() => setHoveredIndex(null)}
                className="transition-all duration-300"
                style={{
                  animation: 'fadeIn 0.6s ease-out',
                  transform: hoveredIndex === 1 ? 'scale(1.05)' : 'scale(1)',
                  zIndex: hoveredIndex === 1 ? 10 : 1,
                }}
              >
                <FeatureCard
                  number="02"
                  icon={features[1].icon}
                  titleKey={features[1].titleKey}
                  descKey={features[1].descKey}
                  t={t}
                />
              </div>
            )}

            {/* Feature 3 */}
            {visibleFeatures[2] && (
              <div
                onMouseEnter={() => setHoveredIndex(2)}
                onMouseLeave={() => setHoveredIndex(null)}
                className="transition-all duration-300"
                style={{
                  animation: 'fadeIn 0.6s ease-out',
                  transform: hoveredIndex === 2 ? 'scale(1.05)' : 'scale(1)',
                  zIndex: hoveredIndex === 2 ? 10 : 1,
                }}
              >
                <FeatureCard
                  number="03"
                  icon={features[2].icon}
                  titleKey={features[2].titleKey}
                  descKey={features[2].descKey}
                  t={t}
                />
              </div>
            )}

            {/* Feature 4 */}
            {visibleFeatures[3] && (
              <div
                onMouseEnter={() => setHoveredIndex(3)}
                onMouseLeave={() => setHoveredIndex(null)}
                className="transition-all duration-300"
                style={{
                  animation: 'fadeIn 0.6s ease-out',
                  transform: hoveredIndex === 3 ? 'scale(1.05)' : 'scale(1)',
                  zIndex: hoveredIndex === 3 ? 10 : 1,
                }}
              >
                <FeatureCard
                  number="04"
                  icon={features[3].icon}
                  titleKey={features[3].titleKey}
                  descKey={features[3].descKey}
                  t={t}
                />
              </div>
            )}
          </div>
        </section>
      </div>

      <Footer dark={true} />
    </div>
  );
}

function FeatureCard({ number, icon: Icon, titleKey, descKey, t }) {
  return (
    <div className="group relative p-8 bg-brand-gray border-2 border-brand-gray-light hover:border-brand-gold hover:bg-brand-gray-light shadow-lg hover:shadow-xl hover:shadow-brand-gold/20 transition duration-300 cursor-default h-full">
      {/* Number index - top left */}
      <div className="text-6xl font-display font-black text-brand-gold leading-none mb-6 group-hover:text-brand-gold transition">
        {number}/
      </div>

      {/* Icon - top right */}
      <div className="absolute top-8 right-8">
        <Icon size={40} className="text-brand-gold group-hover:text-brand-white group-hover:scale-125 transition duration-300" />
      </div>

      {/* Title */}
      <h3 className="font-display font-bold mb-4 text-brand-white text-xl group-hover:text-brand-gold transition">
        {t(titleKey)}
      </h3>

      {/* Description */}
      <p className="text-brand-white/70 font-mono text-sm leading-relaxed group-hover:text-brand-white/90 transition">
        {t(descKey)}
      </p>
    </div>
  );
}
