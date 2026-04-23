import { useNavigate, Link } from 'react-router-dom';
import { LoginForm } from '../components/LoginForm';
import { ArrowLeft } from 'lucide-react';

export function LoginPage() {
  const navigate = useNavigate();

  const handleSuccess = () => {
    navigate('/dashboard');
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 px-4">
      <button
        onClick={() => navigate('/')}
        className="absolute top-6 left-6 flex items-center gap-2 text-gray-600 hover:text-gray-900 transition"
      >
        <ArrowLeft size={20} /> Back to Home
      </button>

      <div className="text-center mb-12">
        <button
          onClick={() => navigate('/')}
          className="text-center hover:opacity-80 transition"
        >
          <h1 className="text-5xl font-bold text-indigo-700 mb-2">OptiCV</h1>
          <p className="text-lg text-gray-600">Intelligent Job Offer Analysis</p>
        </button>
      </div>

      <div className="bg-white p-12 rounded-lg shadow-lg w-full max-w-md">
        <h2 className="text-3xl font-bold text-gray-800 mb-8">Login</h2>
        <LoginForm onSuccess={handleSuccess} />
        <p className="text-center text-sm text-gray-600 mt-8">
          Don't have an account?{' '}
          <Link to="/auth/register" className="text-indigo-600 font-medium hover:underline">
            Register here
          </Link>
        </p>
      </div>
    </div>
  );
}
