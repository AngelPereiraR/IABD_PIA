import { ES, GB } from 'country-flag-icons/react/3x2';
import { useState, useRef, useEffect } from 'react';
import { useLocale } from '../../hooks/useLocale';

export function LanguageSwitcher({ locale, onChange, isSyncing = false, compact = false }) {
  const { t } = useLocale();
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef(null);

  const languages = [
    { code: 'es', label: 'ES', name: t('languages.spanish'), Flag: ES },
    { code: 'en', label: 'EN', name: t('languages.english'), Flag: GB },
  ];

  const currentLang = languages.find((lang) => lang.code === locale);

  const handleChange = (newLocale) => {
    onChange(newLocale);
    setIsOpen(false);
  };

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Determine styles based on context (dark or light background)
  const isDark = true; // Assumption: used mostly in dark landing, nav, etc.
  const bgClass = isDark ? 'bg-brand-gray border-brand-gray-light' : 'bg-white border-gray-200';
  const textClass = isDark ? 'text-brand-white' : 'text-gray-900';
  const hoverClass = isDark ? 'hover:border-brand-gold hover:text-brand-gold' : 'hover:text-indigo-600';
  const dropdownBgClass = isDark ? 'bg-brand-gray border-brand-gold/30' : 'bg-white border-gray-200';
  const dropdownTextClass = isDark ? 'text-brand-white hover:text-brand-gold hover:bg-brand-black/50' : 'text-gray-900 hover:bg-gray-100';
  const spinnerClass = isDark ? 'text-brand-gold' : 'text-indigo-600';

  return (
    <div
      ref={containerRef}
      className="relative"
    >
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={isSyncing}
        className={`flex items-center gap-2 px-3 py-2 border rounded-none font-mono text-sm transition-colors ${bgClass} ${textClass} ${!isSyncing && hoverClass} ${isSyncing ? 'opacity-60 cursor-not-allowed' : 'cursor-pointer'}`}
        title={currentLang?.name}
        aria-label={t('nav.changeLanguage')}
      >
        <currentLang.Flag className="w-4 h-3 rounded-sm" />
        <span>{currentLang?.label}</span>
        {isSyncing && (
          <svg
            className={`w-3 h-3 animate-spin ${spinnerClass}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M4 12a8 8 0 018-8v0m0 0a8 8 0 018 8v0m-16 0a8 8 0 008 8v0m0 0a8 8 0 008-8v0"
            />
          </svg>
        )}
      </button>

      {isOpen && !isSyncing && (
        <div className={`absolute top-full right-0 mt-2 py-2 border rounded-none shadow-lg ${dropdownBgClass} z-50 min-w-40`}>
          {languages.map((lang) => (
            <button
              key={lang.code}
              onClick={() => handleChange(lang.code)}
              className={`w-full flex items-center gap-3 px-4 py-2 text-sm font-mono transition-colors ${dropdownTextClass} ${locale === lang.code ? 'font-bold text-brand-gold' : ''}`}
              title={lang.name}
            >
              <lang.Flag className="w-4 h-3 rounded-sm" />
              <span>{lang.label}</span>
              <span className="text-xs opacity-60 ml-auto">{lang.name}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
