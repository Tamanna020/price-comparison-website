# PriceWise Beauty — Phase 1: Premium Frontend
> *"Your beauty. Your budget. Your best match."*

A luxury Indian beauty and skincare product discovery and price-intelligence platform inspired by editorial beauty magazines.

---

## 🎨 Design Identity & Palette

Crafted with high-fashion typography (*Playfair Display*, *Cormorant Garamond*, *Plus Jakarta Sans*) and warm editorial tones:

| Tone | Hex Code | Description |
| :--- | :--- | :--- |
| **Warm Ivory** | `#FAF7F2` | Page background and radiant surfaces |
| **Dusty Rose** | `#C98991` | Primary accents, interactive states, badges |
| **Soft Sage** | `#A8B5A0` | Natural skincare accents, organic indicators |
| **Deep Espresso** | `#302724` | High-contrast editorial headers and body typography |
| **Champagne** | `#D6BC8A` | Luxury highlights, star ratings, borders |
| **White** | `#FFFFFF` | Elevated cards, dialog overlays |

---

## 💄 Scope & Features (Phase 1 Frontend)

- **Target Market**: India (`₹` INR currency, retail comparisons across Nykaa, Tira, Purplle, Amazon India, Myntra).
- **Product Scope**: Skincare and Makeup exclusively (Affordable Drugstore to Luxury).
- **Homepage Sections**:
  1. **Navbar**: Sticky glassmorphic navigation, department selectors, real-time search trigger, wishlist count badge, mobile menu.
  2. **Hero Section**: Campaign visuals, animated typography, quick search input, popular tags, trust badges, smooth scroll triggers.
  3. **Categories (16 Departments)**:
     - *Skincare*: Face Wash, Moisturiser, Sunscreen, Serums, Toners, Face Masks, Eye Care, Lip Care.
     - *Makeup*: Foundation, Concealer, Lipstick, Blush, Mascara, Eyeliner, Highlighter, Makeup Palettes.
  4. **Trending Products**: Dynamic product catalog with brand filtering, category filtering, search keyword highlighting, price sorting, wishlist toggle, and quick detail modal.
  5. **Today's Best Deals**: Featured discount cards comparing store prices with percentage savings and verified store tags.
  6. **Affordable Alternatives (Dupes)**: Side-by-side comparison of luxury items vs budget formulations with cost per ml/g and formula similarity breakdown.
  7. **How To Use (Routines)**: AM & PM routine order, application guidance, usage frequency, and dermatologist precautions.
  8. **Multi-Platform Reviews**: Verified customer feedback attributed to source retailers with rating breakdowns.
  9. **Footer**: Brand statement, market notices, affiliate disclosure, data source explanation, and DEMO DATA disclaimer.
- **Product Detail Modal**:
  - Full-screen glassmorphic modal with image preview and zoom.
  - Verified key ingredients and skin suitability badges.
  - Multi-retailer price comparison table (Nykaa, Tira, Purplle, Amazon, Myntra) with lowest price callout and savings calculation.
  - Configurable "Buy Now" links to retailer landing pages.
  - Direct dupe alternative link.
- **Wishlist Drawer**: LocalStorage-persisted slide-out drawer with cumulative cart value and potential savings.
- **Interactions & Accessibility**:
  - Custom fluid cursor with interactive magnetic effects.
  - Reduced-motion media query support (`useReducedMotion` hook).
  - Responsive layouts (mobile, tablet, desktop).
  - Semantic HTML and keyboard-navigable dialogs.

---

## 📁 Project Architecture

```
frontend/
├── public/                 # Favicons and public assets
├── src/
│   ├── assets/             # SVG and styling assets
│   ├── components/         # Modular React components
│   │   ├── CategoryGrid.tsx        # 16-department grid
│   │   ├── CustomCursor.tsx        # Fluid editorial cursor
│   │   ├── DealSection.tsx         # Best deals with savings badges
│   │   ├── DupesSection.tsx        # Affordable dupe comparison
│   │   ├── Footer.tsx              # Editorial footer and disclosures
│   │   ├── Hero.tsx                # Campaign hero and animated search
│   │   ├── HowToUseSection.tsx     # AM/PM ritual guides & precautions
│   │   ├── Navbar.tsx              # Glassmorphic header & wishlist toggle
│   │   ├── ProductCard.tsx         # Responsive product cards
│   │   ├── ProductDetailModal.tsx  # Multi-store price comparison dialog
│   │   ├── ReviewShowcase.tsx      # Multi-platform reviews
│   │   └── WishlistDrawer.tsx      # Slide-out saved items drawer
│   ├── data/               # Local JSON / TypeScript demo data
│   │   ├── alternatives.ts         # Luxury vs drugstore dupe pairs
│   │   ├── categories.ts           # 16 beauty departments metadata
│   │   ├── products.ts             # 20+ authentic Indian beauty products
│   │   ├── reviews.ts              # Multi-retailer customer reviews
│   │   ├── routines.ts             # AM/PM beauty steps & precautions
│   │   └── stores.ts               # Indian retailer metadata & delivery
│   ├── hooks/              # Custom React hooks
│   │   ├── useReducedMotion.ts     # A11y motion preference hook
│   │   └── useWishlist.ts          # LocalStorage wishlist persistence
│   ├── types/              # Strict TypeScript definitions
│   │   └── index.ts                # Interfaces for products, deals, dupes
│   ├── App.tsx             # Master application coordinator
│   ├── index.css           # Tailwind directives & editorial scrollbars
│   └── main.tsx            # Application entry point
├── index.html              # HTML shell with Google Fonts
├── package.json            # Dependencies & build scripts
├── tailwind.config.js      # Custom theme, colors, typography
├── tsconfig.json           # TypeScript configuration
└── vite.config.ts          # Vite configuration
```

---

## 🚀 Running the Frontend

### Prerequisites
- Node.js `v18+` (Installed: `v26.13.0`)
- npm `v9+` (Installed: `11.20.0`)

### Development Server
```bash
cd frontend
npm run dev
```
Available locally at: **`http://localhost:5173/`**

### Production Build & Preview
```bash
cd frontend
npm run build
npm run preview
```

---

## 🔒 Demo Data Disclosure
All prices, discounts, retailer comparisons, reviews, and product attributes in Phase 1 are illustrative sample data for discovery and design validation. Phase 2 will introduce live API integrations and price crawlers.
