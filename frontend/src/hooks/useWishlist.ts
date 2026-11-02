import { useState, useEffect } from 'react';

const WISHLIST_STORAGE_KEY = 'pricewise_beauty_wishlist';

export function useWishlist() {
  const [wishlist, setWishlist] = useState<string[]>(() => {
    try {
      const stored = localStorage.getItem(WISHLIST_STORAGE_KEY);
      return stored ? JSON.parse(stored) : ['prod-01', 'prod-12', 'prod-17']; // Initial pre-saved demo favorites
    } catch {
      return ['prod-01', 'prod-12', 'prod-17'];
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem(WISHLIST_STORAGE_KEY, JSON.stringify(wishlist));
    } catch (e) {
      console.warn('Could not save wishlist to localStorage', e);
    }
  }, [wishlist]);

  const toggleWishlist = (id: string) => {
    setWishlist((prev) => 
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const isWishlisted = (id: string) => wishlist.includes(id);

  const clearWishlist = () => setWishlist([]);

  return {
    wishlist,
    toggleWishlist,
    isWishlisted,
    clearWishlist,
    wishlistCount: wishlist.length,
  };
}

