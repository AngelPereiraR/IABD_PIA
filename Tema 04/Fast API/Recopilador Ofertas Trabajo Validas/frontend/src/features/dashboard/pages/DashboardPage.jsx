import { Layout } from '../../../shared/components';
import useStore from '../../../stores/globalStore';
import { useLocale } from '../../../hooks/useLocale';
import { Link } from 'react-router-dom';
import { BarChart3, FileText, Zap, History } from 'lucide-react';

export function DashboardPage() {
  const { t } = useLocale();
  const { user, currentCV } = useStore((state) => ({
    user: state.auth.user,
    currentCV: state.cv.currentCV,
  }));

  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-display font-black text-brand-white mb-2">{t('dashboard.welcome')}, {user?.email}</h1>
        <p className="text-brand-white/70 mb-8 font-mono">{t('pages.dashboard.manage')} {t('sidebar.myCV')} {t('pages.analysis.analyze')}</p>

        <div className="grid md:grid-cols-2 gap-6">
          <Link
            to="/dashboard/cv"
            className="bg-brand-gray p-6 border-2 border-brand-gray-light hover:border-brand-gold transition"
          >
            <FileText size={32} className="text-brand-gold mb-4" />
            <h3 className="text-lg font-semibold text-brand-white mb-2">{t('pages.cv.myCV')}</h3>
            <p className="text-sm text-brand-white/70 font-mono">
              {currentCV ? `✓ ${t('sidebar.cvUploaded')}` : t('pages.cv.uploadDescription')}
            </p>
          </Link>

          <Link
            to="/dashboard/analysis"
            className="bg-brand-gray p-6 border-2 border-brand-gray-light hover:border-brand-gold transition"
          >
            <BarChart3 size={32} className="text-brand-gold mb-4" />
            <h3 className="text-lg font-semibold text-brand-white mb-2">{t('pages.dashboard.analyzeOffer')}</h3>
            <p className="text-sm text-brand-white/70 font-mono">{t('analysis.description')}</p>
          </Link>

          <Link
            to="/dashboard/analysis/history"
            className="bg-brand-gray p-6 border-2 border-brand-gray-light hover:border-brand-gold transition"
          >
            <History size={32} className="text-brand-gold mb-4" />
            <h3 className="text-lg font-semibold text-brand-white mb-2">{t('sidebar.analysisHistory')}</h3>
            <p className="text-sm text-brand-white/70 font-mono">{t('pages.dashboard.analysisHistory')}</p>
          </Link>

          <Link
            to="/dashboard/adaptations"
            className="bg-brand-gray p-6 border-2 border-brand-gray-light hover:border-brand-gold transition"
          >
            <Zap size={32} className="text-brand-gold mb-4" />
            <h3 className="text-lg font-semibold text-brand-white mb-2">{t('pages.adaptations.myAdaptations')}</h3>
            <p className="text-sm text-brand-white/70 font-mono">{t('adaptations.description')}</p>
          </Link>
        </div>
      </div>
    </Layout>
  );
}
