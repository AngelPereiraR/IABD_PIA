import { Navigate } from 'react-router-dom';
import { Spinner } from './Spinner';
import useStore from '../../stores/globalStore';
import { useLocale } from '../../hooks/useLocale';

export function CVRequiredRoute({ children }) {
  const { t } = useLocale();
  const { currentCV, isLoading } = useStore((state) => state.cv);

  // While loading CV, show loading state (don't redirect)
  if (isLoading) {
    return <Spinner message={t('common.loading')} fullHeight />;
  }

  // If CV doesn't exist after loading, redirect
  if (!currentCV) return <Navigate to="/dashboard/cv" replace />;

  return children;
}
