import { Link } from 'react-router-dom';
import { Zap, BarChart3, FileText, Download } from 'lucide-react';
import { Footer } from '../../../shared/components';

export function LandingPage() {
  const features = [
    { icon: FileText, title: 'Upload Your CV', desc: 'Securely store your resume for instant analysis' },
    { icon: BarChart3, title: 'Smart Analysis', desc: 'AI-powered evaluation of job offers against your profile' },
    { icon: Zap, title: 'Quick Screening', desc: 'Intelligent filtering to find truly relevant opportunities' },
    { icon: Download, title: 'Adapted CVs', desc: 'Tailored versions for each promising offer' },
  ];

  return (
    <div className="flex flex-col min-h-screen bg-gradient-to-b from-indigo-50 to-white">
      <nav className="flex justify-between items-center p-6 bg-white border-b border-gray-200">
        <h1 className="text-2xl font-bold text-indigo-700">OptiCV</h1>
        <div className="flex gap-4">
          <Link to="/auth/login" className="px-4 py-2 text-indigo-600 hover:bg-gray-100 rounded">
            Login
          </Link>
          <Link to="/auth/register" className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700">
            Register
          </Link>
        </div>
      </nav>

      <div className="flex-1">
        <section className="text-center py-20 px-6">
          <h2 className="text-5xl font-bold text-gray-900 mb-4">
            Intelligent Job Offer Analysis
          </h2>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            Upload your CV once, analyze any job offer instantly, and receive perfectly tailored versions for positions that truly match your profile.
          </p>
          <Link
            to="/auth/register"
            className="inline-block px-8 py-3 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700"
          >
            Get Started Free
          </Link>
        </section>

        <section className="py-16 px-6 max-w-6xl mx-auto">
          <h3 className="text-3xl font-bold text-center mb-12">Why OptiCV?</h3>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, idx) => {
              const Icon = feature.icon;
              return (
                <div key={idx} className="bg-white p-6 rounded-lg shadow-md text-center">
                  <Icon size={32} className="mx-auto text-indigo-600 mb-4" />
                  <h4 className="font-semibold text-gray-800 mb-2">{feature.title}</h4>
                  <p className="text-gray-600 text-sm">{feature.desc}</p>
                </div>
              );
            })}
          </div>
        </section>
      </div>

      <Footer />
    </div>
  );
}
