import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, Sparkles } from 'lucide-react';

export const NotFoundPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-[75vh] flex flex-col items-center justify-center p-6 text-center max-w-2xl mx-auto space-y-6">
      <div className="w-20 h-20 rounded-full bg-rose-50 border border-rose-200 flex items-center justify-center text-rose-500 shadow-soft-lift">
        <Sparkles className="w-10 h-10 text-rose-400" />
      </div>

      <div className="space-y-2">
        <span className="text-xs font-bold uppercase tracking-widest text-rose-600 block">
          404 • Page Not Found
        </span>
        <h1 className="font-editorial text-4xl sm:text-5xl font-bold text-espresso-950">
          The Beauty Match You're Looking For Isn't Here
        </h1>
        <p className="text-sm text-espresso-600 leading-relaxed max-w-md mx-auto pt-1">
          The product route or page you requested doesn't exist or may have been updated in our curated Indian beauty catalog.
        </p>
      </div>

      <div className="pt-2 flex flex-col sm:flex-row items-center gap-3">
        <button
          onClick={() => navigate('/')}
          className="px-6 py-3 rounded-2xl bg-espresso-800 hover:bg-espresso-950 text-ivory text-xs font-bold tracking-wide transition-all shadow-xs flex items-center space-x-2"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Return to Product Discovery</span>
        </button>

        <Link
          to="/watchlist"
          className="px-6 py-3 rounded-2xl bg-white hover:bg-rose-50/60 text-espresso-800 border border-rose-200 text-xs font-bold tracking-wide transition-all"
        >
          View Your Watchlist
        </Link>
      </div>

      {/* Suggested Categories */}
      <div className="pt-6 border-t border-rose-100 w-full max-w-md">
        <span className="text-xs text-espresso-400 block mb-3 font-semibold uppercase tracking-wider">
          Popular Departments
        </span>
        <div className="flex flex-wrap justify-center gap-2">
          {['Sunscreens', 'Serums', 'Moisturisers', 'Lipsticks', 'Eyeliners', 'Haircare'].map((cat) => (
            <Link
              key={cat}
              to={`/?category=${cat.toLowerCase()}`}
              className="px-3 py-1 rounded-full bg-white border border-rose-100 text-xs text-espresso-700 hover:border-rose-300 hover:text-rose-600 transition-colors shadow-2xs"
            >
              {cat}
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
};
