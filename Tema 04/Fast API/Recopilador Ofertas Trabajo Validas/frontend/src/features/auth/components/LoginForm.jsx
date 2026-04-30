import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import useStore from '../../../stores/globalStore';
import { Mail, Lock, Eye, EyeOff } from 'lucide-react';
import { useLocale } from '../../../hooks/useLocale';

const schema = z.object({
  email: z.string().email('Invalid email'),
  password: z.string().min(8, 'Min 8 characters'),
});

export function LoginForm({ onSuccess }) {
  const { t } = useLocale();
  const { login } = useStore((state) => state.authActions);
  const [apiError, setApiError] = useState(null);
  const [showPassword, setShowPassword] = useState(false);
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data) => {
    setApiError(null);
    try {
      const result = await login(data.email, data.password);
      if (result.success) {
        onSuccess?.();
      } else {
        setApiError(result.error || t('auth.loginError'));
      }
    } catch (err) {
      setApiError(t('auth.unexpectedError'));
      console.error('Login error:', err);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-5 w-full">
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

      {apiError && <div className="p-4 bg-brand-rust/20 border-2 border-brand-rust text-brand-rust text-sm font-mono">{apiError}</div>}

      <button
        type="submit"
        disabled={isSubmitting}
        className="w-full px-4 py-3 bg-brand-gold text-brand-black font-display font-bold border-2 border-brand-gold hover:bg-brand-black hover:text-brand-gold transition duration-300 disabled:opacity-50 cursor-pointer"
      >
        {isSubmitting ? t('auth.loggingIn') : t('auth.login')}
      </button>
    </form>
  );
}
