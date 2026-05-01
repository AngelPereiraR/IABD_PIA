import { useNavigate } from 'react-router-dom';
import useStore from '../../stores/globalStore';
import { useLocale } from '../../hooks/useLocale';
import { LogOut, Home, Menu } from 'lucide-react';
import { LanguageSwitcher } from './LanguageSwitcher';

export function Navbar({ onMenuClick, sidebarOpen }) {
  const navigate = useNavigate();
  const { user, logout } = useStore((state) => ({
    user: state.auth.user,
    logout: state.authActions.logout,
  }));
  const { t, locale, changeLocale, isSyncing } = useLocale();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const handleHome = () => {
    navigate('/');
  };

  return (
    <nav className="flex justify-between items-center p-4 bg-brand-black border-b border-brand-gold/30">
      <div className="flex items-center gap-4">
        <button
          onClick={onMenuClick}
          className="lg:hidden flex items-center justify-center p-2 text-brand-gold hover:text-brand-white transition"
          title={t('nav.toggleMenu')}
        >
          <Menu size={24} />
        </button>
        <button
          onClick={handleHome}
          className="text-xl font-display font-black text-brand-gold hover:text-brand-white transition"
        >
          OptiCV
        </button>
      </div>
      <div className="flex items-center gap-4">
        <span className="text-sm text-brand-white/70 hidden sm:inline font-mono">{user?.email}</span>

        <LanguageSwitcher locale={locale} onChange={changeLocale} isSyncing={isSyncing} />

        <button
          onClick={handleHome}
          className="flex items-center gap-2 px-3 py-2 text-sm border border-brand-gray-light text-brand-white hover:border-brand-gold hover:text-brand-gold transition font-mono"
          title={t('nav.goHome')}
        >
          <Home size={18} />
        </button>
        <button
          onClick={handleLogout}
          className="flex items-center gap-2 px-3 py-2 text-sm border border-brand-gray-light text-brand-white hover:border-brand-gold hover:text-brand-gold transition font-mono"
        >
          <LogOut size={18} />
          <span className="hidden sm:inline">{t('nav.logout')}</span>
        </button>
      </div>
    </nav>
  );
}
