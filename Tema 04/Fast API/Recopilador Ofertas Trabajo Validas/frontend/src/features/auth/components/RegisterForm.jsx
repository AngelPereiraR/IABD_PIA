import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Link } from 'react-router-dom';
import useStore from '../../../stores/globalStore';
import { TermsModal } from './TermsModal';
import { PrivacyModal } from './PrivacyModal';
import { Mail, Lock, User } from 'lucide-react';

const schema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters'),
  email: z.string().email('Invalid email'),
  password: z.string().min(8, 'Min 8 characters'),
  acceptTerms: z.boolean().refine((val) => val === true, {
    message: 'You must accept the Terms and Conditions',
  }),
  acceptPrivacy: z.boolean().refine((val) => val === true, {
    message: 'You must accept the Privacy Policy',
  }),
});

export function RegisterForm({ onSuccess }) {
  const { registerUser } = useStore((state) => state.authActions);
  const [apiError, setApiError] = useState(null);
  const [termsModalOpen, setTermsModalOpen] = useState(false);
  const [privacyModalOpen, setPrivacyModalOpen] = useState(false);
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data) => {
    setApiError(null);
    const result = await registerUser(data.email, data.password, data.name);
    if (result.success) {
      onSuccess?.();
    } else {
      setApiError(result.error);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 w-full max-w-sm">
      <div>
        <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-1">
          <User size={16} /> Name
        </label>
        <input
          {...register('name')}
          type="text"
          className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-indigo-500"
          placeholder="Your name"
        />
        {errors.name && <p className="text-red-500 text-sm mt-1">{errors.name.message}</p>}
      </div>

      <div>
        <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-1">
          <Mail size={16} /> Email
        </label>
        <input
          {...register('email')}
          type="email"
          className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-indigo-500"
          placeholder="you@example.com"
        />
        {errors.email && <p className="text-red-500 text-sm mt-1">{errors.email.message}</p>}
      </div>

      <div>
        <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-1">
          <Lock size={16} /> Password
        </label>
        <input
          {...register('password')}
          type="password"
          className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-indigo-500"
          placeholder="••••••••"
        />
        {errors.password && <p className="text-red-500 text-sm mt-1">{errors.password.message}</p>}
      </div>

      {apiError && <div className="p-3 bg-red-50 text-red-700 text-sm rounded">{apiError}</div>}

      <div className="space-y-3">
        <div className="flex items-start gap-2">
          <input
            {...register('acceptTerms')}
            type="checkbox"
            id="acceptTerms"
            className="mt-1 w-4 h-4 rounded cursor-pointer"
          />
          <label htmlFor="acceptTerms" className="text-sm text-gray-700 cursor-pointer">
            I accept the{' '}
            <button
              type="button"
              onClick={() => setTermsModalOpen(true)}
              className="text-indigo-600 font-medium hover:underline"
            >
              Terms and Conditions
            </button>
          </label>
        </div>
        {errors.acceptTerms && <p className="text-red-500 text-sm">{errors.acceptTerms.message}</p>}

        <div className="flex items-start gap-2">
          <input
            {...register('acceptPrivacy')}
            type="checkbox"
            id="acceptPrivacy"
            className="mt-1 w-4 h-4 rounded cursor-pointer"
          />
          <label htmlFor="acceptPrivacy" className="text-sm text-gray-700 cursor-pointer">
            I accept the{' '}
            <button
              type="button"
              onClick={() => setPrivacyModalOpen(true)}
              className="text-indigo-600 font-medium hover:underline"
            >
              Privacy Policy
            </button>
          </label>
        </div>
        {errors.acceptPrivacy && <p className="text-red-500 text-sm">{errors.acceptPrivacy.message}</p>}
      </div>

      <TermsModal isOpen={termsModalOpen} onClose={() => setTermsModalOpen(false)} />
      <PrivacyModal isOpen={privacyModalOpen} onClose={() => setPrivacyModalOpen(false)} />

      <button
        type="submit"
        disabled={isSubmitting}
        className="w-full px-4 py-2 bg-indigo-600 text-white rounded font-medium hover:bg-indigo-700 disabled:bg-gray-400"
      >
        {isSubmitting ? 'Registering...' : 'Register'}
      </button>
    </form>
  );
}
