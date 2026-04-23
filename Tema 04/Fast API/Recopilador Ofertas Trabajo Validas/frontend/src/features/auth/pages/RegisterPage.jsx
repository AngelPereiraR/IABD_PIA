import { useNavigate, Link } from 'react-router-dom';
import { RegisterForm } from '../components/RegisterForm';
import { ArrowLeft } from 'lucide-react';

export function RegisterPage() {
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
        <h2 className="text-3xl font-bold text-gray-800 mb-8">Register</h2>
        <RegisterForm onSuccess={handleSuccess} />
        <p className="text-center text-sm text-gray-600 mt-8">
          Already have an account?{' '}
          <Link to="/auth/login" className="text-indigo-600 font-medium hover:underline">
            Login here
          </Link>
        </p>
      </div>
    </div>
  );
}
