import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import useStore from '../../../stores/globalStore';
import { useLocale } from '../../../hooks/useLocale';

export function GoogleCallbackPage() {
  const navigate = useNavigate();
  const { t } = useLocale();
  const [searchParams] = useSearchParams();
  const { googleCallback } = useStore((state) => state.authActions);

  useEffect(() => {
    const code = searchParams.get('code');
    if (!code) {
      navigate('/auth/login');
      return;
    }

    (async () => {
      const result = await googleCallback(code);
      if (result.success) {
        navigate('/dashboard');
      } else {
        navigate('/auth/login');
      }
    })();
  }, [searchParams, navigate, googleCallback]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-gray-800 mb-2">{t('auth.authenticating')}</h1>
        <p className="text-gray-600">{t('auth.googleSignInWait')}</p>
      </div>
    </div>
  );
}
