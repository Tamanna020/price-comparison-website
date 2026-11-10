import React, { useState } from 'react';
import { generateProductPlaceholderSvg, isGenericStockImage } from '../utils/imageFallback';
import { ShieldCheck, Clock, AlertCircle } from 'lucide-react';

interface ProductImageProps {
  src?: string | null;
  alt: string;
  brand?: string;
  category?: string;
  status?: 'verified_exact' | 'permission_review' | 'unverified' | 'placeholder';
  className?: string;
  imageClassName?: string;
  showBadge?: boolean;
  priority?: boolean;
}

export const ProductImage: React.FC<ProductImageProps> = ({
  src,
  alt,
  brand = 'BEAUTY',
  category = 'SKINCARE',
  status = 'placeholder',
  className = 'w-full h-full',
  imageClassName = 'w-full h-full object-cover object-center',
  showBadge = false,
  priority = false,
}) => {
  // If the source is generic stock Unsplash or empty, start directly with the tailored placeholder
  const initialPlaceholder = generateProductPlaceholderSvg(brand, category, alt);
  const isGeneric = isGenericStockImage(src);
  
  const [currentSrc, setCurrentSrc] = useState<string>(isGeneric || !src ? initialPlaceholder : src);
  const [isLoaded, setIsLoaded] = useState<boolean>(isGeneric || !src);
  const [hasError, setHasError] = useState<boolean>(false);

  const handleError = () => {
    if (!hasError) {
      setHasError(true);
      setCurrentSrc(initialPlaceholder);
      setIsLoaded(true);
    }
  };

  const isVerifiedExact = status === 'verified_exact' && !hasError && !isGeneric;
  const isReview = status === 'permission_review' && !hasError && !isGeneric;

  return (
    <div className={`relative overflow-hidden bg-ivory-100 ${className}`}>
      {/* Skeleton / Shimmer during loading */}
      {!isLoaded && (
        <div className="absolute inset-0 bg-gradient-to-r from-ivory-100 via-rose-50/50 to-ivory-100 animate-pulse" />
      )}

      {/* Actual Image or Neutral Placeholder */}
      <img
        src={currentSrc}
        alt={alt}
        loading={priority ? 'eager' : 'lazy'}
        onLoad={() => setIsLoaded(true)}
        onError={handleError}
        className={`${imageClassName} transition-opacity duration-300 ${isLoaded ? 'opacity-100' : 'opacity-0'}`}
      />

      {/* Optional Verification Badge (for Product Detail / Admin) */}
      {showBadge && (
        <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between pointer-events-none">
          {isVerifiedExact ? (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-bold bg-emerald-950/80 backdrop-blur-md text-emerald-200 border border-emerald-500/40 shadow-sm">
              <ShieldCheck className="w-3 h-3 text-emerald-400" />
              Verified Packaging Photo (Open License)
            </span>
          ) : isReview ? (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-bold bg-amber-950/80 backdrop-blur-md text-amber-200 border border-amber-500/40 shadow-sm">
              <Clock className="w-3 h-3 text-amber-400" />
              Official Retailer Asset • Usage Review
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-bold bg-espresso-950/75 backdrop-blur-md text-sand-200 border border-sand-500/30 shadow-sm">
              <AlertCircle className="w-3 h-3 text-champagne-300" />
              Neutral Catalog Placeholder • Photo Verification Pending
            </span>
          )}
        </div>
      )}
    </div>
  );
};
