import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Link } from 'react-router-dom';
import useStore from '../../../stores/globalStore';
import { TermsModal } from './TermsModal';
import { PrivacyModal } from './PrivacyModal';
import { Mail, Lock, User, Eye, EyeOff } from 'lucide-react';
import { useLocale } from '../../../hooks/useLocale';

const schema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters'),
  email: z.string().email('Invalid email'),
  password: z.string().min(8, 'Min 8 characters'),
  confirmPassword: z.string().min(8, 'Min 8 characters'),
  acceptTerms: z.boolean().refine((val) => val === true, {
    message: 'You must accept the Terms and Conditions',
  }),
  acceptPrivacy: z.boolean().refine((val) => val === true, {
    message: 'You must accept the Privacy Policy',
  }),
});

export function RegisterForm({ onSuccess }) {
  const { t } = useLocale();
  const { registerUser } = useStore((state) => state.authActions);
  const [apiError, setApiError] = useState(null);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [termsModalOpen, setTermsModalOpen] = useState(false);
  const [privacyModalOpen, setPrivacyModalOpen] = useState(false);
  const { register, handleSubmit, formState: { errors, isSubmitting }, watch, setError, clearErrors } = useForm({
    resolver: zodResolver(schema),
  });
  const password = watch('password');
  const confirmPassword = watch('confirmPassword');

  useEffect(() => {
    if (password && confirmPassword && password !== confirmPassword) {
      setError('confirmPassword', {
        type: 'manual',
        message: t('auth.passwordsMismatch'),
      });
    } else if (password === confirmPassword) {
      clearErrors('confirmPassword');
    }
  }, [password, confirmPassword, setError, clearErrors, t]);

  const onSubmit = async (data) => {
    setApiError(null);
    const { confirmPassword, ...submitData } = data;
    const result = await registerUser(submitData.email, submitData.password, submitData.name);
    if (result.success) {
      onSuccess?.();
    } else {
      setApiError(result.error);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-5 w-full">
      <div>
        <label className="flex items-center gap-2 text-base font-medium text-brand-white/80 mb-2 font-mono">
          <User size={16} className="text-brand-gold" /> {t('auth.name')}
        </label>
        <input
          {...register('name')}
          type="text"
          className="w-full px-4 py-3 bg-brand-black border-2 border-brand-gray-light text-brand-white placeholder-brand-white/40 focus:outline-none focus:border-brand-gold transition font-mono"
          placeholder="Your name"
        />
        {errors.name && <p className="text-brand-rust text-sm mt-2 font-mono">{errors.name.message}</p>}
      </div>

      <div>
        <label className="flex items-center gap-2 text-base font-medium text-brand-white/80 mb-2 font-mono">
          <Mail size={16} className="text-brand-gold" /> {t('auth.email')}
        </label>
        <input
          {...register('email')}
          type="email"
          className="w-full px-4 py-3 bg-brand-black border-2 border-brand-gray-light text-brand-white placeholder-brand-white/40 focus:outline-none focus:border-brand-gold transition font-mono"
          placeholder="you@example.com"
        />
        {errors.email && <p className="text-brand-rust text-sm mt-2 font-mono">{errors.email.message}</p>}
      </div>

      <div>
        <label className="flex items-center gap-2 text-base font-medium text-brand-white/80 mb-2 font-mono">
          <Lock size={16} className="text-brand-gold" /> {t('auth.password')}
        </label>
        <div className="relative">
          <input
            {...register('password')}
            type={showPassword ? 'text' : 'password'}
            className="w-full px-4 py-3 bg-brand-black border-2 border-brand-gray-light text-brand-white placeholder-brand-white/40 focus:outline-none focus:border-brand-gold transition font-mono pr-12"
            placeholder="••••••••"
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-brand-white/60 hover:text-brand-gold transition flex-shrink-0"
            aria-label={showPassword ? 'Hide password' : 'Show password'}
          >
            {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
          </button>
        </div>
        {errors.password && <p className="text-brand-rust text-sm mt-2 font-mono">{errors.password.message}</p>}
      </div>

      <div>
        <label className="flex items-center gap-2 text-base font-medium text-brand-white/80 mb-2 font-mono">
          <Lock size={16} className="text-brand-gold" /> {t('auth.confirmPassword')}
        </label>
        <div className="relative">
          <input
            {...register('confirmPassword')}
            type={showConfirmPassword ? 'text' : 'password'}
            className="w-full px-4 py-3 bg-brand-black border-2 border-brand-gray-light text-brand-white placeholder-brand-white/40 focus:outline-none focus:border-brand-gold transition font-mono pr-12"
            placeholder="••••••••"
          />
          <button
            type="button"
            onClick={() => setShowConfirmPassword(!showConfirmPassword)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-brand-white/60 hover:text-brand-gold transition flex-shrink-0"
            aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
          >
            {showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
          </button>
        </div>
        {errors.confirmPassword && <p className="text-brand-rust text-sm mt-2 font-mono">{errors.confirmPassword.message}</p>}
      </div>

      {apiError && <div className="p-4 bg-brand-rust/20 border-2 border-brand-rust text-brand-rust text-sm font-mono">{apiError}</div>}

      <div className="space-y-3 pt-2">
        <div className="flex items-center gap-3">
          <input
            {...register('acceptTerms')}
            type="checkbox"
            id="acceptTerms"
            className="w-5 h-5 border-2 border-brand-gray-light bg-brand-black cursor-pointer accent-brand-gold flex-shrink-0"
          />
          <label htmlFor="acceptTerms" className="text-base text-brand-white/70 cursor-pointer font-mono">
            {t('auth.acceptTerms')}{' '}
            <button
              type="button"
              onClick={() => setTermsModalOpen(true)}
              className="text-brand-gold font-bold hover:text-brand-white transition"
            >
              {t('auth.termsTitle')}
            </button>
          </label>
        </div>
        {errors.acceptTerms && <p className="text-brand-rust text-sm font-mono">{errors.acceptTerms.message}</p>}

        <div className="flex items-center gap-3">
          <input
            {...register('acceptPrivacy')}
            type="checkbox"
            id="acceptPrivacy"
            className="w-5 h-5 border-2 border-brand-gray-light bg-brand-black cursor-pointer accent-brand-gold flex-shrink-0"
          />
          <label htmlFor="acceptPrivacy" className="text-base text-brand-white/70 cursor-pointer font-mono">
            {t('auth.acceptPrivacy')}{' '}
            <button
              type="button"
              onClick={() => setPrivacyModalOpen(true)}
              className="text-brand-gold font-bold hover:text-brand-white transition"
            >
              {t('auth.privacyTitle')}
            </button>
          </label>
        </div>
        {errors.acceptPrivacy && <p className="text-brand-rust text-sm font-mono">{errors.acceptPrivacy.message}</p>}
      </div>

      <TermsModal isOpen={termsModalOpen} onClose={() => setTermsModalOpen(false)} />
      <PrivacyModal isOpen={privacyModalOpen} onClose={() => setPrivacyModalOpen(false)} />

      <button
        type="submit"
        disabled={isSubmitting}
        className="w-full px-4 py-3 bg-brand-gold text-brand-black font-display font-bold border-2 border-brand-gold hover:bg-brand-black hover:text-brand-gold transition duration-300 disabled:opacity-50 cursor-pointer"
      >
        {isSubmitting ? t('auth.registering') : t('auth.register')}
      </button>
    </form>
  );
}
