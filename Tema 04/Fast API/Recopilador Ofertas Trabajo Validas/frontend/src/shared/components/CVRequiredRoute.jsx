import { Navigate } from 'react-router-dom';
import useStore from '../../stores/globalStore';

export function CVRequiredRoute({ children }) {
  const { currentCV } = useStore((state) => state.cv);
  if (!currentCV) return <Navigate to="/dashboard/cv" replace />;
  return children;
}
