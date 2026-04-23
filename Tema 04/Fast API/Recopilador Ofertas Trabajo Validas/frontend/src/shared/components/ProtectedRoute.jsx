import { Navigate } from 'react-router-dom';
import useStore from '../../stores/globalStore';

export function ProtectedRoute({ children }) {
  const { token } = useStore((state) => state.auth);
  if (!token) return <Navigate to="/auth/login" replace />;
  return children;
}
