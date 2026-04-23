import { Layout } from '../../../shared/components';
import useStore from '../../../stores/globalStore';
import { Link } from 'react-router-dom';
import { BarChart3, FileText, Zap, History } from 'lucide-react';

export function DashboardPage() {
  const { user, currentCV } = useStore((state) => ({
    user: state.auth.user,
    currentCV: state.cv.currentCV,
  }));

  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">Welcome, {user?.email}</h1>
        <p className="text-gray-600 mb-8">Manage your CV and analyze job offers</p>

        <div className="grid md:grid-cols-2 gap-6">
          <Link
            to="/dashboard/cv"
            className="bg-gradient-to-br from-blue-50 to-blue-100 p-6 rounded-lg border border-blue-200 hover:shadow-md transition"
          >
            <FileText size={32} className="text-blue-600 mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">My CV</h3>
            <p className="text-sm text-gray-700">
              {currentCV ? '✓ CV Uploaded' : 'Upload your CV to get started'}
            </p>
          </Link>

          <Link
            to="/dashboard/analysis"
            className="bg-gradient-to-br from-purple-50 to-purple-100 p-6 rounded-lg border border-purple-200 hover:shadow-md transition"
          >
            <BarChart3 size={32} className="text-purple-600 mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Analyze Offer</h3>
            <p className="text-sm text-gray-700">Analyze any job offer in seconds</p>
          </Link>

          <Link
            to="/dashboard/analysis/history"
            className="bg-gradient-to-br from-green-50 to-green-100 p-6 rounded-lg border border-green-200 hover:shadow-md transition"
          >
            <History size={32} className="text-green-600 mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Analysis History</h3>
            <p className="text-sm text-gray-700">View your previous analyses</p>
          </Link>

          <Link
            to="/dashboard/adaptations"
            className="bg-gradient-to-br from-orange-50 to-orange-100 p-6 rounded-lg border border-orange-200 hover:shadow-md transition"
          >
            <Zap size={32} className="text-orange-600 mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">My Adaptations</h3>
            <p className="text-sm text-gray-700">Download your tailored CVs</p>
          </Link>
        </div>
      </div>
    </Layout>
  );
}
