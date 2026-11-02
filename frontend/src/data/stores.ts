export interface StoreInfo {
  id: string;
  name: 'Nykaa' | 'Tira' | 'Purplle' | 'Amazon India' | 'Myntra';
  domain: string;
  rating: number;
  freeShippingAbove: number; // in INR
  standardDeliveryDays: string;
  badge: string;
  description: string;
}

export const STORES_DATA: Record<string, StoreInfo> = {
  nykaa: {
    id: 'nykaa',
    name: 'Nykaa',
    domain: 'nykaa.com',
    rating: 4.8,
    freeShippingAbove: 499,
    standardDeliveryDays: '2-4 Days',
    badge: '100% Authentic Guarantee',
    description: "India's premier multi-brand beauty and cosmetics destination.",
  },
  tira: {
    id: 'tira',
    name: 'Tira',
    domain: 'tirabeauty.com',
    rating: 4.7,
    freeShippingAbove: 499,
    standardDeliveryDays: '1-3 Days',
    badge: 'Reliance Beauty Luxe',
    description: "Curated luxury and contemporary skincare by Reliance Retail.",
  },
  purplle: {
    id: 'purplle',
    name: 'Purplle',
    domain: 'purplle.com',
    rating: 4.6,
    freeShippingAbove: 399,
    standardDeliveryDays: '3-5 Days',
    badge: 'Best Budget Offers',
    description: 'Affordable, popular indie brands and daily beauty discounts.',
  },
  amazon: {
    id: 'amazon',
    name: 'Amazon India',
    domain: 'amazon.in',
    rating: 4.7,
    freeShippingAbove: 499,
    standardDeliveryDays: '1-2 Days (Prime)',
    badge: 'Fastest Delivery',
    description: 'Fast fulfillment with verified brand flagship stores.',
  },
  myntra: {
    id: 'myntra',
    name: 'Myntra',
    domain: 'myntra.com',
    rating: 4.6,
    freeShippingAbove: 799,
    standardDeliveryDays: '2-4 Days',
    badge: 'Fashion & Beauty Insider',
    description: 'Verified beauty and trend curation with insider perks.',
  },
};

