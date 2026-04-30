import { useNavigate, Link } from 'react-router-dom';
import { RegisterForm } from '../components/RegisterForm';
import { ArrowLeft } from 'lucide-react';
import { useLocale } from '../../../hooks/useLocale';

const scrollbarStyles = `
  body {
    scrollbar-color: #3D3D3D #0A0A0A;
    scrollbar-width: thin;
  }
  ::-webkit-scrollbar {
    width: 8px;
  }
  ::-webkit-scrollbar-track {
    background: #0A0A0A;
  }
  ::-webkit-scrollbar-thumb {
    background: #3D3D3D;
    border-radius: 0;
  }
  ::-webkit-scrollbar-thumb:hover {
    background: #C9A84C;
  }
`;

export function RegisterPage() {
  const navigate = useNavigate();
  const { t } = useLocale();

  const handleSuccess = () => {
    navigate('/dashboard');
  };

  return (
    <>
      <style>{scrollbarStyles}</style>
      <div className="min-h-screen bg-brand-black text-brand-white flex flex-col">
      {/* Header */}
      <nav className="border-b border-brand-gold/30 px-6 md:px-8 py-6">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <button
            onClick={() => navigate('/')}
            className="flex items-center gap-2 px-3 py-2 border border-brand-gray-light text-brand-white hover:border-brand-gold hover:text-brand-gold transition font-mono text-sm"
          >
            <ArrowLeft size={18} /> {t('nav.back')}
          </button>
          <button
            onClick={() => navigate('/')}
            className="hover:opacity-90 transition"
          >
            <h1 className="text-2xl font-display font-black text-brand-gold">OptiCV</h1>
          </button>
        </div>
      </nav>

      {/* Main Content */}
      <div className="flex-1 px-6 md:px-8 py-16 md:py-24 flex items-center justify-center">
        <div className="w-full max-w-2xl">
          <div className="mb-12 text-center">
            <h2 className="text-5xl font-display font-black text-brand-white mb-3">{t('auth.register')}</h2>
            <p className="text-brand-white/70 font-mono text-sm max-w-lg mx-auto">{t('landing.subtitle')}</p>
          </div>

          <div className="bg-brand-gray border-2 border-brand-gray-light p-12 md:p-16">
            <RegisterForm onSuccess={handleSuccess} />
          </div>

          <p className="text-sm text-brand-white/70 mt-8 font-mono text-center">
            {t('auth.haveAccount')}{' '}
            <Link to="/auth/login" className="text-brand-gold font-bold hover:text-brand-white transition">
              {t('auth.login')}
            </Link>
          </p>
        </div>
      </div>
    </div>
    </>
  );
}
