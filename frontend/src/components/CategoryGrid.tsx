import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { CATEGORIES_DATA } from '../data/categories';
import type { Subcategory, ProductCategory } from '../types';
import { ArrowRight } from 'lucide-react';

interface CategoryGridProps {
  onSelectSubcategory: (sub: Subcategory) => void;
  selectedSubcategory: Subcategory | 'all';
}

export const CategoryGrid: React.FC<CategoryGridProps> = ({
  onSelectSubcategory,
  selectedSubcategory,
}) => {
  const [activeTab, setActiveTab] = useState<ProductCategory | 'all'>('all');

  const filteredCategories = CATEGORIES_DATA.filter((cat) => {
    if (activeTab === 'all') return true;
    return cat.category === activeTab;
  });

  return (
    <section id="categories" className="py-16 bg-white/60 border-y border-rose-100/80 relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Heading */}
        <div className="text-center max-w-2xl mx-auto mb-10">
          <span className="text-xs font-bold tracking-widest uppercase text-rose-500 mb-2 inline-block">
            Curated Beauty Departments
          </span>
          <h2 className="font-editorial text-3xl sm:text-4xl font-bold text-espresso-800 tracking-tight">
            Explore by Category
          </h2>
          <p className="text-espresso-600 text-sm sm:text-base mt-2">
            Navigate through focused skincare, makeup, haircare, and body care departments crafted for Indian skin concerns and climates.
          </p>

          {/* Department Tabs */}
          <div className="inline-flex flex-wrap items-center justify-center p-1 bg-ivory rounded-full border border-rose-200/80 mt-6 shadow-xs">
            <button
              onClick={() => setActiveTab('all')}
              className={`px-4 sm:px-5 py-2 rounded-full text-xs font-semibold tracking-wide transition-all ${
                activeTab === 'all'
                  ? 'bg-espresso-700 text-ivory shadow-xs'
                  : 'text-espresso-600 hover:text-espresso-800'
              }`}
            >
              All Categories ({CATEGORIES_DATA.length})
            </button>
            <button
              onClick={() => setActiveTab('skincare')}
              className={`px-4 sm:px-5 py-2 rounded-full text-xs font-semibold tracking-wide transition-all flex items-center space-x-1.5 ${
                activeTab === 'skincare'
                  ? 'bg-rose-500 text-ivory shadow-xs'
                  : 'text-espresso-600 hover:text-espresso-800'
              }`}
            >
              <span>Skincare</span>
            </button>
            <button
              onClick={() => setActiveTab('makeup')}
              className={`px-4 sm:px-5 py-2 rounded-full text-xs font-semibold tracking-wide transition-all flex items-center space-x-1.5 ${
                activeTab === 'makeup'
                  ? 'bg-champagne-500 text-ivory shadow-xs'
                  : 'text-espresso-600 hover:text-espresso-800'
              }`}
            >
              <span>Makeup</span>
            </button>
          </div>
        </div>

        {/* Categories Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-4 gap-4 sm:gap-6">
          {filteredCategories.map((cat, idx) => {
            const isSelected = selectedSubcategory === cat.name;

            return (
              <motion.div
                key={cat.name}
                initial={{ opacity: 0, y: 15 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: idx * 0.04 }}
                onClick={() => onSelectSubcategory(cat.name)}
                className={`group cursor-pointer rounded-2xl overflow-hidden border transition-all duration-300 relative bg-white shadow-soft-lift hover:shadow-luxury-card ${
                  isSelected
                    ? 'border-rose-400 ring-2 ring-rose-300/40'
                    : 'border-rose-100/80 hover:border-rose-300'
                }`}
              >
                {/* Category Thumbnail */}
                <div className="relative h-36 sm:h-44 overflow-hidden bg-ivory">
                  <img
                    src={cat.image}
                    alt={cat.name}
                    className="w-full h-full object-cover object-center group-hover:scale-105 transition-transform duration-500"
                    loading="lazy"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-espresso-900/60 via-transparent to-transparent opacity-80 group-hover:opacity-60 transition-opacity" />

                  {/* Badge */}
                  <div className="absolute top-3 left-3">
                    <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-white/90 backdrop-blur-xs text-espresso-700">
                      {cat.category}
                    </span>
                  </div>

                  {/* Title overlay */}
                  <div className="absolute bottom-3 left-3 right-3 text-white">
                    <h3 className="font-editorial text-lg sm:text-xl font-bold leading-tight group-hover:text-rose-200 transition-colors">
                      {cat.name}
                    </h3>
                  </div>
                </div>

                {/* Subtitle & Action */}
                <div className="p-3 sm:p-4 bg-white flex items-center justify-between text-xs">
                  <span className="text-espresso-400 font-medium">
                    {cat.itemCount} items tracked
                  </span>
                  <div className="flex items-center text-rose-500 font-semibold group-hover:translate-x-1 transition-transform">
                    <span className="text-[11px] mr-1">Shop</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
};
