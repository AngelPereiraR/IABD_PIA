import { useLocale } from '../../hooks/useLocale';

export function Footer({ dark = false }) {
  const { t } = useLocale();
  const currentYear = new Date().getFullYear();

  // Auto-detect dark mode if not explicitly passed
  const isDark = dark || window.location.pathname === '/' || window.location.pathname.startsWith('/dashboard');

  const bgClass = isDark ? 'bg-brand-black' : 'bg-white';
  const borderClass = isDark ? 'border-brand-gold/30' : 'border-gray-200';
  const textClass = isDark ? 'text-brand-white/70' : 'text-gray-600';

  return (
    <footer className={`${bgClass} border-t ${borderClass} py-6 px-4`}>
      <div className="max-w-7xl mx-auto text-center text-sm font-mono">
        <p className={textClass}><span className="font-sans">©</span> {currentYear} OptiCV. {t('shared.footer')}</p>
      </div>
    </footer>
  );
}
