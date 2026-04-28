import { Link, useLocation } from 'react-router-dom';
import useStore from '../../stores/globalStore';
import { LayoutDashboard, FileText, BarChart3, Zap, History, CheckCircle, User } from 'lucide-react';

export function Sidebar({ isOpen, isDesktop }) {
  const location = useLocation();
  const { currentCV } = useStore((state) => state.cv);

  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/dashboard/cv', label: 'My CV', icon: FileText },
    { path: '/dashboard/analysis', label: 'Analysis', icon: BarChart3 },
    { path: '/dashboard/analysis/history', label: 'Analysis History', icon: History },
    { path: '/dashboard/adaptations', label: 'My Adaptations', icon: Zap },
    { path: '/dashboard/profile', label: 'My Profile', icon: User },
  ];

  const isActive = (path) => location.pathname === path;

  return (
    <aside
      className={`
        fixed lg:static inset-y-12 left-0 z-50 w-64 bg-gray-50 border-r border-gray-200 flex flex-col
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
                className={`flex items-center gap-3 px-4 py-2 rounded transition ${
                  isActive(item.path)
                    ? 'bg-indigo-600 text-white'
                    : 'text-gray-700 hover:bg-gray-200'
                }`}
              >
                <Icon size={20} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </div>
      </nav>

      <div className="p-4 border-t border-gray-200">
        <div className="flex items-center gap-2 text-sm">
          {currentCV ? (
            <>
              <CheckCircle size={18} className="text-green-600 flex-shrink-0" />
              <span className="text-gray-700">CV Uploaded</span>
            </>
          ) : (
            <>
              <FileText size={18} className="text-gray-400 flex-shrink-0" />
              <span className="text-gray-500">No CV</span>
            </>
          )}
        </div>
      </div>
    </aside>
  );
}
