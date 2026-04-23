import { useNavigate } from 'react-router-dom';
import useStore from '../../stores/globalStore';
import { LogOut } from 'lucide-react';

export function Navbar() {
  const navigate = useNavigate();
  const { user, logout } = useStore((state) => ({
    user: state.auth.user,
    logout: state.authActions.logout,
  }));

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <nav className="flex justify-between items-center p-4 bg-white border-b border-gray-200">
      <div className="text-xl font-bold text-indigo-700">OptiCV</div>
      <div className="flex items-center gap-4">
        <span className="text-sm text-gray-600">{user?.email}</span>
        <button
          onClick={handleLogout}
          className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded"
        >
          <LogOut size={18} />
          Logout
        </button>
      </div>
    </nav>
  );
}
