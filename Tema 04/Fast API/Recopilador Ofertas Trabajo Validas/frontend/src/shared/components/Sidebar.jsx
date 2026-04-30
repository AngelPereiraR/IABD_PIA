import { Link, useLocation } from 'react-router-dom';
import useStore from '../../stores/globalStore';
import { LayoutDashboard, FileText, BarChart3, Zap, History, CheckCircle, User } from 'lucide-react';
import { useLocale } from '../../hooks/useLocale';

export function Sidebar({ isOpen, isDesktop }) {
  const { t } = useLocale();
  const location = useLocation();
  const { currentCV } = useStore((state) => state.cv);

  const navItems = [
    { path: '/dashboard', labelKey: 'sidebar.dashboard', icon: LayoutDashboard },
    { path: '/dashboard/cv', labelKey: 'sidebar.myCV', icon: FileText },
    { path: '/dashboard/analysis', labelKey: 'sidebar.analysis', icon: BarChart3 },
    { path: '/dashboard/analysis/history', labelKey: 'sidebar.analysisHistory', icon: History },
    { path: '/dashboard/adaptations', labelKey: 'sidebar.myAdaptations', icon: Zap },
    { path: '/dashboard/profile', labelKey: 'sidebar.myProfile', icon: User },
  ];

  const isActive = (path) => location.pathname === path;

  return (
    <aside
      className={`
        fixed lg:static inset-y-12 left-0 z-50 w-64 bg-brand-black border-r border-brand-gold/30 flex flex-col
        transition-transform duration-300 ease-in-out
        ${isDesktop ? 'translate-x-0' : isOpen ? 'translate-x-0' : '-translate-x-full'}
        lg:translate-x-0
      `}
    >
      <nav className="flex-1 p-4">
        <div className="space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-4 py-2 transition border-l-4 font-mono ${
                  isActive(item.path)
                    ? 'border-brand-gold text-brand-gold bg-brand-gray/30'
                    : 'border-transparent text-brand-white/70 hover:border-brand-gold/50 hover:text-brand-gold'
                }`}
              >
                <Icon size={20} />
                <span>{t(item.labelKey)}</span>
              </Link>
            );
          })}
        </div>
      </nav>

      <div className="p-4 border-t border-brand-gold/30">
        <div className="flex items-center gap-2 text-sm font-mono">
          {currentCV ? (
            <>
              <CheckCircle size={18} className="text-brand-gold flex-shrink-0" />
              <span className="text-brand-white/70">{t('sidebar.cvUploaded')}</span>
            </>
          ) : (
            <>
              <FileText size={18} className="text-brand-white/40 flex-shrink-0" />
              <span className="text-brand-white/40">{t('sidebar.noCV')}</span>
            </>
          )}
        </div>
      </div>
    </aside>
  );
}
