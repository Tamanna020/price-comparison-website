import React from 'react';
import { Heart, ShieldAlert, ArrowUp } from 'lucide-react';

export const Footer: React.FC = () => {
  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <footer className="bg-espresso-900 text-ivory-100 pt-16 pb-12 border-t border-espresso-800 relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Top Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-10 pb-12 border-b border-espresso-800/80">
          {/* Brand Info */}
          <div className="lg:col-span-2 space-y-4">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-rose-400 to-rose-600 flex items-center justify-center text-ivory font-serif font-bold text-lg">
                P
              </div>
              <span className="font-editorial text-2xl font-bold tracking-tight text-ivory">
                PriceWise <span className="font-serif italic font-normal text-rose-300">Beauty</span>
              </span>
            </div>

            <p className="text-sm text-espresso-200/80 max-w-sm font-light leading-relaxed">
              India’s dedicated luxury and affordable beauty price comparison platform. We empower shoppers to discover holy-grail skincare and makeup, analyze formula dupes, and find verified market prices across top retailers.
            </p>

            <div className="text-xs text-champagne-300/90 font-medium">
              Tagline: <em>Your beauty. Your budget. Your best match.</em>
            </div>
          </div>

          {/* Skincare Column */}
          <div>
            <h4 className="font-editorial text-base font-bold text-champagne-300 uppercase tracking-wider mb-3">
              Skincare
            </h4>
            <ul className="space-y-2 text-xs text-espresso-200/70">
              <li><a href="#categories" className="hover:text-rose-300 transition-colors">Face Wash & Cleansers</a></li>
              <li><a href="#categories" className="hover:text-rose-300 transition-colors">Ceramide Moisturisers</a></li>
              <li><a href="#categories" className="hover:text-rose-300 transition-colors">PA++++ Sunscreens</a></li>
              <li><a href="#categories" className="hover:text-rose-300 transition-colors">Targeted Active Serums</a></li>
              <li><a href="#categories" className="hover:text-rose-300 transition-colors">Exfoliating Toners</a></li>
              <li><a href="#categories" className="hover:text-rose-300 transition-colors">Overnight Lip Care</a></li>
            </ul>
          </div>

          {/* Makeup Column */}
          <div>
            <h4 className="font-editorial text-base font-bold text-champagne-300 uppercase tracking-wider mb-3">
              Makeup
            </h4>
            <ul className="space-y-2 text-xs text-espresso-200/70">
              <li><a href="#categories" className="hover:text-rose-300 transition-colors">Warm Undertone Foundations</a></li>
              <li><a href="#categories" className="hover:text-rose-300 transition-colors">Crease-Proof Concealers</a></li>
              <li><a href="#categories" className="hover:text-rose-300 transition-colors">Transfer-Proof Lipsticks</a></li>
              <li><a href="#categories" className="hover:text-rose-300 transition-colors">Dewy Liquid Blushes</a></li>
              <li><a href="#categories" className="hover:text-rose-300 transition-colors">Humidity-Resistant Mascaras</a></li>
              <li><a href="#categories" className="hover:text-rose-300 transition-colors">Eyeshadow Palettes</a></li>
            </ul>
          </div>

          {/* Academic & Disclosures */}
          <div>
            <h4 className="font-editorial text-base font-bold text-champagne-300 uppercase tracking-wider mb-3">
              Legal & Disclosures
            </h4>
            <ul className="space-y-2 text-xs text-espresso-200/70">
              <li><span className="hover:text-rose-300 cursor-pointer">About Project</span></li>
              <li><span className="hover:text-rose-300 cursor-pointer">Academic Methodology</span></li>
              <li><span className="hover:text-rose-300 cursor-pointer">Privacy Policy</span></li>
              <li><span className="hover:text-rose-300 cursor-pointer">Data Sources & Attribution</span></li>
              <li><span className="hover:text-rose-300 cursor-pointer">Affiliate Transparency Disclosure</span></li>
            </ul>
          </div>
        </div>

        {/* Academic Ethics & Disclaimer Callout */}
        <div className="py-6 border-b border-espresso-800 text-xs text-espresso-300/80 leading-relaxed flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-start space-x-2">
            <ShieldAlert className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
            <div>
              <strong>ACADEMIC PROTOTYPE NOTICE:</strong> All product listings, brand names (Dot & Key, Minimalist, Cetaphil, MAC, Charlotte Tilbury, etc.), retailer references (Nykaa, Tira, Purplle, Amazon India, Myntra), and price points are curated sample data for academic demonstration purposes and clearly designated as <strong>DEMO DATA</strong>. No automated live scraping is performed.
            </div>
          </div>

          <button
            onClick={scrollToTop}
            aria-label="Scroll to top"
            className="p-2.5 rounded-full bg-espresso-800 hover:bg-rose-500 text-ivory transition-colors shrink-0 self-end md:self-auto"
          >
            <ArrowUp className="w-4 h-4" />
          </button>
        </div>

        {/* Bottom Copyright */}
        <div className="pt-6 flex flex-col sm:flex-row items-center justify-between text-xs text-espresso-400 gap-2">
          <div>
            © 2026 PriceWise Beauty India. Phase 1 Academic Frontend Release.
          </div>
          <div className="flex items-center space-x-1">
            <span>Crafted with</span>
            <Heart className="w-3.5 h-3.5 text-rose-400 fill-rose-400 inline" />
            <span>for Indian Beauty Enthusiasts</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
