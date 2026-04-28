import { useNavigate } from 'react-router-dom';
import useStore from '../../stores/globalStore';
import { LogOut, Home, Menu } from 'lucide-react';

export function Navbar({ onMenuClick, sidebarOpen }) {
  const navigate = useNavigate();
  const { user, logout } = useStore((state) => ({
    user: state.auth.user,
    logout: state.authActions.logout,
  }));

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const handleHome = () => {
    navigate('/');
  };

  return (
    <nav className="flex justify-between items-center p-4 bg-white border-b border-gray-200">
      <div className="flex items-center gap-4">
        <button
          onClick={onMenuClick}
          className="lg:hidden flex items-center justify-center p-2 text-gray-600 hover:bg-gray-100 rounded transition"
          title="Toggle menu"
        >
          <Menu size={24} />
        </button>
        <button
          onClick={handleHome}
          className="text-xl font-bold text-indigo-700 hover:opacity-80 transition"
        >
          OptiCV
        </button>
      </div>
      <div className="flex items-center gap-4">
        <span className="text-sm text-gray-600 hidden sm:inline">{user?.email}</span>
        <button
          onClick={handleHome}
          className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded transition"
          title="Go to home page"
        >
          <Home size={18} />
        </button>
        <button
          onClick={handleLogout}
          className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded transition"
        >
          <LogOut size={18} />
          <span className="hidden sm:inline">Logout</span>
        </button>
      </div>
    </nav>
  );
}
