import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Search, Sparkles, ArrowDown, ShieldCheck, CheckCircle2 } from 'lucide-react';

interface HeroProps {
  onSearch: (query: string) => void;
  onExploreClick: () => void;
  onDupesClick: () => void;
}

export const Hero: React.FC<HeroProps> = ({ onSearch, onExploreClick, onDupesClick }) => {
  const [searchInput, setSearchInput] = useState('');

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchInput.trim()) {
      onSearch(searchInput.trim());
      onExploreClick();
    }
  };

  const trendingTags = ['Sunscreen', 'Niacinamide', 'Ceramides', 'Lip Mask', 'Matte Foundation', 'Liquid Blush'];

  return (
    <section id="hero" className="relative pt-28 pb-16 sm:pt-36 sm:pb-24 overflow-hidden">
      {/* Background ambient lighting accents */}
      <div className="absolute top-10 left-1/2 -translate-x-1/2 w-full max-w-7xl h-[500px] pointer-events-none opacity-40">
        <div className="absolute top-10 left-10 w-96 h-96 rounded-full bg-rose-200/50 blur-3xl" />
        <div className="absolute top-20 right-10 w-80 h-80 rounded-full bg-champagne-200/60 blur-3xl" />
        <div className="absolute bottom-10 left-1/3 w-72 h-72 rounded-full bg-sage-200/40 blur-3xl" />
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center">
          {/* Left Column: Text & Editorial Intro */}
          <div className="lg:col-span-7 text-center lg:text-left space-y-6">
            {/* Tagline Badge */}
            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-rose-50 border border-rose-200/80 text-rose-700 text-xs font-semibold tracking-wider uppercase shadow-xs"
            >
              <Sparkles className="w-3.5 h-3.5 text-rose-500 animate-pulse" />
              <span>Your beauty. Your budget. Your best match.</span>
            </motion.div>

            {/* Headline */}
            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.1 }}
              className="font-editorial text-4xl sm:text-6xl lg:text-7xl font-bold tracking-tight text-espresso-800 leading-[1.08]"
            >
              Discover Beauty. <br className="hidden sm:inline" />
              <span className="font-serif italic font-normal text-rose-500">Compare Smarter.</span>
            </motion.h1>

            {/* Subtitle */}
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.2 }}
              className="text-base sm:text-lg text-espresso-600/90 max-w-xl mx-auto lg:mx-0 font-normal leading-relaxed"
            >
              Find your favourite skincare and makeup at the best available prices. We compare real-time offers across India’s premier beauty retailers so you never overpay for your glow.
            </motion.p>

            {/* Search Input Bar */}
            <motion.form
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.3 }}
              onSubmit={handleSearchSubmit}
              className="max-w-xl mx-auto lg:mx-0"
            >
              <div className="relative flex items-center shadow-soft-lift rounded-full bg-white p-1.5 border border-rose-200/90 focus-within:border-rose-400 focus-within:ring-2 focus-within:ring-rose-200/50 transition-all">
                <Search className="w-5 h-5 text-espresso-400 ml-3.5 shrink-0" />
                <input
                  type="text"
                  value={searchInput}
                  onChange={(e) => setSearchInput(e.target.value)}
                  placeholder="Search SPF, Niacinamide, Maybelline, Dot & Key..."
                  className="w-full bg-transparent px-3 py-2 text-sm text-espresso-800 placeholder-espresso-400 focus:outline-none"
                />
                <button
                  type="submit"
                  className="px-5 py-2.5 rounded-full bg-espresso-700 hover:bg-espresso-800 text-ivory text-xs sm:text-sm font-semibold tracking-wide transition-all shrink-0 hover:shadow-md"
                >
                  Search
                </button>
              </div>

              {/* Instant Search Tags */}
              <div className="mt-3 flex items-center justify-center lg:justify-start flex-wrap gap-1.5 text-xs text-espresso-500">
                <span className="text-[11px] font-medium text-espresso-400">Popular:</span>
                {trendingTags.map((tag) => (
                  <button
                    type="button"
                    key={tag}
                    onClick={() => {
                      setSearchInput(tag);
                      onSearch(tag);
                      onExploreClick();
                    }}
                    className="px-2.5 py-0.5 rounded-full bg-white/70 hover:bg-rose-100 hover:text-rose-700 border border-rose-100 transition-colors text-[11px]"
                  >
                    {tag}
                  </button>
                ))}
              </div>
            </motion.form>

            {/* CTAs */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.4 }}
              className="pt-2 flex flex-col sm:flex-row items-center justify-center lg:justify-start gap-4"
            >
              <button
                onClick={onExploreClick}
                className="w-full sm:w-auto px-8 py-3.5 rounded-full bg-rose-500 hover:bg-rose-600 text-ivory font-semibold text-sm tracking-wide shadow-md hover:shadow-lg transition-all flex items-center justify-center space-x-2 group"
              >
                <span>Explore Products</span>
                <ArrowDown className="w-4 h-4 group-hover:translate-y-0.5 transition-transform" />
              </button>

              <button
                onClick={onDupesClick}
                className="w-full sm:w-auto px-8 py-3.5 rounded-full bg-white hover:bg-champagne-50 text-espresso-700 border border-champagne-300 font-semibold text-sm tracking-wide transition-all flex items-center justify-center space-x-2 shadow-xs"
              >
                <Sparkles className="w-4 h-4 text-champagne-500" />
                <span>Find Luxury Dupes</span>
              </button>
            </motion.div>

            {/* Trust Badges */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.8, delay: 0.5 }}
              className="pt-4 flex items-center justify-center lg:justify-start space-x-6 text-xs text-espresso-500"
            >
              <div className="flex items-center space-x-1.5">
                <CheckCircle2 className="w-4 h-4 text-sage-500" />
                <span>5 Indian Retailers</span>
              </div>
              <div className="flex items-center space-x-1.5">
                <ShieldCheck className="w-4 h-4 text-rose-500" />
                <span>100% Authentic Listings</span>
              </div>
              <div className="flex items-center space-x-1.5">
                <span className="font-semibold text-champagne-600">₹</span>
                <span>Transparent Delivery Costs</span>
              </div>
            </motion.div>
          </div>

          {/* Right Column: Editorial Hero Campaign Visual */}
          <div className="lg:col-span-5 relative">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.9, delay: 0.2 }}
              className="relative mx-auto max-w-md lg:max-w-none"
            >
              {/* Outer decorative border frame */}
              <div className="absolute -inset-3 rounded-3xl border border-champagne-300/40 transform rotate-1 pointer-events-none" />

              {/* Main campaign image card */}
              <div className="relative rounded-2xl overflow-hidden shadow-2xl border border-rose-200/50 bg-white">
                <img
                  src="https://images.unsplash.com/photo-1596462502278-27bfdc403348?auto=format&fit=crop&w=1000&q=85"
                  alt="PriceWise Beauty Editorial Campaign - Glowing Skin"
                  className="w-full h-[440px] sm:h-[500px] object-cover object-center filter saturate-105"
                />

                {/* Editorial Overlay Pill */}
                <div className="absolute bottom-5 inset-x-5 glass-panel rounded-xl p-4 shadow-luxury-card">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="flex items-center space-x-1 text-[11px] font-bold tracking-wider text-rose-600 uppercase">
                        <Sparkles className="w-3 h-3 text-rose-500" />
                        <span>Today's Spotlight</span>
                      </div>
                      <h4 className="font-editorial text-lg font-bold text-espresso-800">
                        Dot & Key Watermelon Sunscreen
                      </h4>
                      <p className="text-xs text-espresso-500">Lowest on Nykaa Demo at ₹465 (MRP ₹595)</p>
                    </div>

                    <div className="text-right">
                      <span className="inline-block bg-rose-500 text-ivory text-xs font-bold px-2.5 py-1 rounded-full">
                        Save 22%
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </section>
  );
};

