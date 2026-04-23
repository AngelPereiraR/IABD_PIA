import { Link, useLocation } from 'react-router-dom';
import useStore from '../../stores/globalStore';
import { LayoutDashboard, FileText, BarChart3, Zap, CheckCircle, User } from 'lucide-react';

export function Sidebar() {
  const location = useLocation();
  const { currentCV } = useStore((state) => state.cv);

  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/dashboard/cv', label: 'My CV', icon: FileText },
    { path: '/dashboard/analysis', label: 'Analysis', icon: BarChart3 },
    { path: '/dashboard/adaptations', label: 'My Adaptations', icon: Zap },
    { path: '/dashboard/profile', label: 'My Profile', icon: User },
  ];

  const isActive = (path) => location.pathname === path;

  return (
    <aside className="w-64 bg-gray-50 border-r border-gray-200 min-h-screen flex flex-col">
      <nav className="flex-1 p-4">
        <div className="space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-4 py-2 rounded ${
                  isActive(item.path)
                    ? 'bg-indigo-600 text-white'
                    : 'text-gray-700 hover:bg-gray-200'
                }`}
              >
                <Icon size={20} />
                {item.label}
              </Link>
            );
          })}
        </div>
      </nav>

      <div className="p-4 border-t border-gray-200">
        <div className="flex items-center gap-2 text-sm">
          {currentCV ? (
            <>
              <CheckCircle size={18} className="text-green-600" />
              <span className="text-gray-700">CV Uploaded</span>
            </>
          ) : (
            <>
              <FileText size={18} className="text-gray-400" />
              <span className="text-gray-500">No CV</span>
            </>
          )}
        </div>
      </div>
    </aside>
  );
}
