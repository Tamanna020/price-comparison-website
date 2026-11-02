import type { Subcategory, ProductCategory } from '../types';

export interface CategoryInfo {
  name: Subcategory;
  category: ProductCategory;
  description: string;
  image: string;
  itemCount: number;
}

export const CATEGORIES_DATA: CategoryInfo[] = [
  // Skincare (8)
  {
    name: 'Face Wash',
    category: 'skincare',
    description: 'Gentle, pH-balanced cleansers to purify without stripping the moisture barrier.',
    image: 'https://images.unsplash.com/photo-1556228720-195a672e8a03?auto=format&fit=crop&w=600&q=80',
    itemCount: 42,
  },
  {
    name: 'Moisturiser',
    category: 'skincare',
    description: 'Ceramide-rich creams, gel hydrators and barrier-repair formulas for glowing skin.',
    image: 'https://images.unsplash.com/photo-1608248597359-52410a747e93?auto=format&fit=crop&w=600&q=80',
    itemCount: 58,
  },
  {
    name: 'Sunscreen',
    category: 'skincare',
    description: 'Broad-spectrum PA++++ sun protections with zero white cast and light matte finishes.',
    image: 'https://images.unsplash.com/photo-1598440947619-2c35fc9aa908?auto=format&fit=crop&w=600&q=80',
    itemCount: 36,
  },
  {
    name: 'Serums',
    category: 'skincare',
    description: 'Targeted actives including Niacinamide, Vitamin C, Retinol, and Hyaluronic Acid.',
    image: 'https://images.unsplash.com/photo-1620916566398-39f1143ab7be?auto=format&fit=crop&w=600&q=80',
    itemCount: 64,
  },
  {
    name: 'Toners',
    category: 'skincare',
    description: 'Hydrating essences and gentle exfoliating waters to prep and balance pH.',
    image: 'https://images.unsplash.com/photo-1616683693504-3ea7e9ad6fec?auto=format&fit=crop&w=600&q=80',
    itemCount: 28,
  },
  {
    name: 'Face Masks',
    category: 'skincare',
    description: 'Deep detoxifying clay treatments, revitalising sheet masks, and overnight jellies.',
    image: 'https://images.unsplash.com/photo-1567928815116-2483664d50c1?auto=format&fit=crop&w=600&q=80',
    itemCount: 22,
  },
  {
    name: 'Eye Care',
    category: 'skincare',
    description: 'Caffeine peptides and botanical eye balms for dark circles and morning puffiness.',
    image: 'https://images.unsplash.com/photo-1512290900672-1f4f65c97f48?auto=format&fit=crop&w=600&q=80',
    itemCount: 18,
  },
  {
    name: 'Lip Care',
    category: 'skincare',
    description: 'Nourishing peptide butter balms, overnight sleeping masks, and SPF lip oils.',
    image: 'https://images.unsplash.com/photo-1586495777744-4413f21062fa?auto=format&fit=crop&w=600&q=80',
    itemCount: 24,
  },

  // Makeup (8)
  {
    name: 'Foundation',
    category: 'makeup',
    description: 'Second-skin liquid, cream, and powder bases matched to Indian undertones.',
    image: 'https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?auto=format&fit=crop&w=600&q=80',
    itemCount: 46,
  },
  {
    name: 'Concealer',
    category: 'makeup',
    description: 'Crease-proof high-coverage concealers for blemish correction and under-eye brighten.',
    image: 'https://images.unsplash.com/photo-1596462502278-27bfdc403348?auto=format&fit=crop&w=600&q=80',
    itemCount: 32,
  },
  {
    name: 'Lipstick',
    category: 'makeup',
    description: 'Hydrating matte bullets, transfers-proof liquid pigments, and sheer tinted balms.',
    image: 'https://images.unsplash.com/photo-1586495777744-4413f21062fa?auto=format&fit=crop&w=600&q=80',
    itemCount: 78,
  },
  {
    name: 'Blush',
    category: 'makeup',
    description: 'Dewy liquid drops, velvet mousse, and baked powder flushes for warm radiance.',
    image: 'https://images.unsplash.com/photo-1512496015851-a90fb38ba796?auto=format&fit=crop&w=600&q=80',
    itemCount: 35,
  },
  {
    name: 'Mascara',
    category: 'makeup',
    description: 'Humidity-resistant, non-clumping lash lift formulas for length and intense volume.',
    image: 'https://images.unsplash.com/photo-1503236823255-94609f598e71?auto=format&fit=crop&w=600&q=80',
    itemCount: 26,
  },
  {
    name: 'Eyeliner',
    category: 'makeup',
    description: 'Smudge-proof kajal pencils, waterproof dip ink pens, and gel pot liners.',
    image: 'https://images.unsplash.com/photo-1597225244660-1cd128c64284?auto=format&fit=crop&w=600&q=80',
    itemCount: 30,
  },
  {
    name: 'Highlighter',
    category: 'makeup',
    description: 'Champagne and rose gold liquid strobes and ultra-fine pressed glow powders.',
    image: 'https://images.unsplash.com/photo-1516975080664-ed2fc6a32937?auto=format&fit=crop&w=600&q=80',
    itemCount: 24,
  },
  {
    name: 'Makeup Palettes',
    category: 'makeup',
    description: 'Versatile warm nude, terracotta and festival shimmer eyeshadow collections.',
    image: 'https://images.unsplash.com/photo-1512496015851-a90fb38ba796?auto=format&fit=crop&w=600&q=80',
    itemCount: 19,
  },
  {
    name: 'Makeup Remover',
    category: 'skincare',
    description: 'Nourishing cleansing balms, bifocal waters, and gentle micellar liquids for clean skin.',
    image: 'https://images.unsplash.com/photo-1556228720-195a672e8a03?auto=format&fit=crop&w=600&q=80',
    itemCount: 16,
  },
  {
    name: 'Haircare',
    category: 'haircare',
    description: 'Bond-repair hair serums, peptide scalp density drops, and nourishing hair masks.',
    image: 'https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?auto=format&fit=crop&w=600&q=80',
    itemCount: 28,
  },
  {
    name: 'Body Care',
    category: 'bodycare',
    description: 'Exfoliating AHA/BHA body washes, ceramide skin smoothing lotions, and body sunscreens.',
    image: 'https://images.unsplash.com/photo-1556228720-195a672e8a03?auto=format&fit=crop&w=600&q=80',
    itemCount: 31,
  },
];
