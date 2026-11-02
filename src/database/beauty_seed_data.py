"""Indian Skincare and Makeup Demo Dataset for PriceWise AI Beauty (Phase 2).
Provides realistic, transparently labeled demo products, verified ingredients,
and multi-retailer offers across Nykaa, Tira, Purplle, Amazon India, and Myntra.
"""

DEMO_BEAUTY_STORES = [
    {
        "name": "Nykaa (Demo)",
        "domain": "nykaa.com",
        "rating": 4.8,
        "shipping_policy": "Free shipping on orders over ₹499. Standard delivery 2-4 days.",
    },
    {
        "name": "Tira (Demo)",
        "domain": "tirabeauty.com",
        "rating": 4.7,
        "shipping_policy": "Free shipping on orders over ₹499. Express delivery 1-3 days.",
    },
    {
        "name": "Purplle (Demo)",
        "domain": "purplle.com",
        "rating": 4.6,
        "shipping_policy": "Free shipping on orders over ₹399. Standard delivery 3-5 days.",
    },
    {
        "name": "Amazon India (Demo)",
        "domain": "amazon.in",
        "rating": 4.7,
        "shipping_policy": "Free delivery for Prime members. Standard delivery 1-2 days.",
    },
    {
        "name": "Myntra (Demo)",
        "domain": "myntra.com",
        "rating": 4.6,
        "shipping_policy": "Free shipping on orders over ₹799. Standard delivery 2-4 days.",
    },
]

DEMO_BEAUTY_PRODUCTS = [
    # -------------------------------------------------------------
    # 1. SUNSCREEN
    # -------------------------------------------------------------
    {
        "sku": "BEAUTY-DOTKEY-SUN-50",
        "title": "Dot & Key Watermelon Cooling Sunscreen SPF 50+ PA++++",
        "brand": "Dot & Key",
        "category": "Sunscreens",
        "description": "Ultra-lightweight fluid sunscreen infused with Watermelon and Hyaluronic acid that instantly cools skin temperature by 6°C with zero white cast and no greasy residue.",
        "specs": {
            "Product Type": "Fluid Sunscreen",
            "Net Quantity": "50 g",
            "Key Ingredients": "Watermelon Extract, Hyaluronic Acid, Tinosorb M, Uvinul A Plus, Beetroot Extract",
            "Skin Type": "All Skin Types, Oily, Combination",
            "Routine": "AM",
            "Intended Use": "Broad spectrum UVA/UVB protection, cooling hydration",
            "Brand Tier": "Affordable",
        },
        "image_url": "https://images.unsplash.com/photo-1598440947619-2c35fc9aa908?auto=format&fit=crop&w=600&q=80",
        "offers": [
            {"store_name": "Nykaa (Demo)", "current_price": 465.0, "original_price": 595.0, "shipping_cost": 0.0, "availability": "In Stock", "variant_name": "50 g / Standard", "trend_type": "all_time_low"},
            {"store_name": "Tira (Demo)", "current_price": 495.0, "original_price": 595.0, "shipping_cost": 0.0, "availability": "In Stock", "variant_name": "50 g / Standard", "trend_type": "moderate_deal"},
            {"store_name": "Purplle (Demo)", "current_price": 489.0, "original_price": 595.0, "shipping_cost": 49.0, "availability": "In Stock", "variant_name": "50 g / Standard", "trend_type": "normal"},
            {"store_name": "Amazon India (Demo)", "current_price": 475.0, "original_price": 595.0, "shipping_cost": 0.0, "availability": "In Stock", "variant_name": "50 g / Standard", "trend_type": "normal"},
        ],
    },
    {
        "sku": "BEAUTY-DERMACO-SUN-50",
        "title": "The Derma Co 1% Hyaluronic Sunscreen Aqua Gel SPF 50 PA++++",
        "brand": "The Derma Co",
        "category": "Sunscreens",
        "description": "Dermatologist-formulated light aqua gel with Hyaluronic Acid and Vitamin E. Absorbs like water with zero pilling under makeup and broad spectrum blue-light defense.",
        "specs": {
            "Product Type": "Aqua Gel Sunscreen",
            "Net Quantity": "50 g",
            "Key Ingredients": "Hyaluronic Acid 1%, Vitamin E, Titanium Dioxide, Zinc Oxide",
            "Skin Type": "Acne-Prone, Normal, Sensitive",
            "Routine": "AM",
            "Intended Use": "Sun defense, blue-light protection, lightweight hydration",
            "Brand Tier": "Affordable",
        },
        "image_url": "https://images.unsplash.com/photo-1556228720-195a672e8a03?auto=format&fit=crop&w=600&q=80",
        "offers": [
            {"store_name": "Nykaa (Demo)", "current_price": 449.0, "original_price": 499.0, "shipping_cost": 0.0, "availability": "In Stock", "variant_name": "50 g / Standard", "trend_type": "moderate_deal"},
            {"store_name": "Amazon India (Demo)", "current_price": 469.0, "original_price": 499.0, "shipping_cost": 0.0, "availability": "In Stock", "variant_name": "50 g / Standard", "trend_type": "normal"},
            {"store_name": "Purplle (Demo)", "current_price": 479.0, "original_price": 499.0, "shipping_cost": 49.0, "availability": "In Stock", "variant_name": "50 g / Standard", "trend_type": "normal"},
        ],
    },

    # -------------------------------------------------------------
    # 2. SERUMS
    # -------------------------------------------------------------
    {
        "sku": "BEAUTY-MIN-NIAC-30",
        "title": "Minimalist 10% Niacinamide Face Serum with Zinc PCA",
        "brand": "Minimalist",
        "category": "Serums",
        "description": "Clinical-strength 10% pure Niacinamide paired with EUK-134 and Zinc PCA to visibly reduce sebum, fade post-acne blemishes, and refine skin texture.",
        "specs": {
            "Product Type": "Active Face Serum",
            "Net Quantity": "30 ml",
            "Key Ingredients": "Niacinamide (Vitamin B3) 10%, Zinc PCA 1%, EUK-134, Aloe Vera Juice",
            "Skin Type": "Blemish-Prone, Oily, Uneven Texture, All Skin Types",
            "Routine": "AM & PM",
            "Intended Use": "Sebum control, blemish fading, barrier support",
            "Brand Tier": "Affordable",
        },
        "image_url": "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?auto=format&fit=crop&w=600&q=80",
        "offers": [
            {"store_name": "Nykaa (Demo)", "current_price": 569.0, "original_price": 599.0, "shipping_cost": 0.0, "availability": "In Stock", "variant_name": "30 ml / Dropper", "trend_type": "moderate_deal"},
            {"store_name": "Purplle (Demo)", "current_price": 599.0, "original_price": 599.0, "shipping_cost": 49.0, "availability": "In Stock", "variant_name": "30 ml / Dropper", "trend_type": "normal"},
            {"store_name": "Tira (Demo)", "current_price": 569.0, "original_price": 599.0, "shipping_cost": 0.0, "availability": "In Stock", "variant_name": "30 ml / Dropper", "trend_type": "normal"},
            {"store_name": "Amazon India (Demo)", "current_price": 559.0, "original_price": 599.0, "shipping_cost": 0.0, "availability": "In Stock", "variant_name": "30 ml / Dropper", "trend_type": "all_time_low"},
        ],
    },
    {
        "sku": "BEAUTY-PLUM-VITC-30",
        "title": "Plum 15% Vitamin C Glow Face Serum with Mandarin",
        "brand": "Plum",
        "category": "Serums",
        "description": "Pure Ethyl Ascorbic Acid 15% formulated with Japanese Mandarin extract and Rosehip to boost collagen, enhance skin radiance, and combat hyperpigmentation.",
        "specs": {
            "Product Type": "Glow Face Serum",
            "Net Quantity": "30 ml",
            "Key Ingredients": "Ethyl Ascorbic Acid (Vitamin C) 15%, Japanese Mandarin Extract, Rosehip Oil",
            "Skin Type": "Dull, Normal, Combination, Hyperpigmented",
            "Routine": "AM",
            "Intended Use": "Radiance enhancement, dark spot reduction, antioxidant protection",
            "Brand Tier": "Affordable",
        },
        "image_url": "https://images.unsplash.com/photo-1608248597359-52410a747e93?auto=format&fit=crop&w=600&q=80",
        "offers": [
            {"store_name": "Nykaa (Demo)", "current_price": 675.0, "original_price": 790.0, "shipping_cost": 0.0, "availability": "In Stock", "variant_name": "30 ml / Dark Glass Bottle", "trend_type": "all_time_low"},
            {"store_name": "Tira (Demo)", "current_price": 710.0, "original_price": 790.0, "shipping_cost": 0.0, "availability": "In Stock", "variant_name": "30 ml / Dark Glass Bottle", "trend_type": "normal"},
            {"store_name": "Purplle (Demo)", "current_price": 690.0, "original_price": 790.0, "shipping_cost": 49.0, "availability": "In Stock", "variant_name": "30 ml / Dark Glass Bottle", "trend_type": "moderate_deal"},
        ],
    },
    {
        "sku": "BEAUTY-COSRX-SNAIL-100",
        "title": "COSRX Advanced Snail 96 Mucin Power Essence",
        "brand": "COSRX",
        "category": "Serums",
        "description": "Celebrated K-beauty essence containing 96% snail secretion filtrate to deeply hydrate, soothe damaged skin barriers, and deliver glass-skin glow.",
        "specs": {
            "Product Type": "Repair Essence / Serum",
            "Net Quantity": "100 ml",
            "Key Ingredients": "Snail Secretion Filtrate 96.3%, Sodium Hyaluronate, Allantoin, Panthenol, Arginine",
            "Skin Type": "Dehydrated, Sensitive, Dry, Acne-Prone",
            "Routine": "AM & PM",
            "Intended Use": "Deep hydration, barrier repair, soothing redness",
            "Brand Tier": "Premium",
        },
        "image_url": "https://images.unsplash.com/photo-1616683693504-3ea7e9ad6fec?auto=format&fit=crop&w=600&q=80",
        "offers": [
            {"store_name": "Nykaa (Demo)", "current_price": 1450.0, "original_price": 1450.0, "shipping_cost": 0.0, "availability": "In Stock", "variant_name": "100 ml / Pump Bottle", "trend_type": "normal"},
            {"store_name": "Tira (Demo)", "current_price": 1375.0, "original_price": 1450.0, "shipping_cost": 0.0, "availability": "In Stock", "variant_name": "100 ml / Pump Bottle", "trend_type": "great_deal"},
            {"store_name": "Myntra (Demo)", "current_price": 1410.0, "original_price": 1450.0, "shipping_cost": 0.0, "availability": "In Stock", "variant_name": "100 ml / Pump Bottle", "trend_type": "normal"},
        ],
    },

    # -------------------------------------------------------------
    # 3. FACE CLEANSERS
    # -------------------------------------------------------------
    {
        "sku": "BEAUTY-CETAPHIL-CLN-125",
        "title": "Cetaphil Gentle Skin Cleanser Hydrating Formula",
        "brand": "Cetaphil",
        "category": "Face cleansers",
        "description": "Award-winning soap-free and fragrance-free dermatological cleanser with Niacinamide and Panthenol that preserves skin moisture during cleansing.",
        "specs": {
            "Product Type": "Cream Cleanser",
            "Net Quantity": "125 ml",
            "Key Ingredients": "Niacinamide (Vitamin B3), Panthenol (Pro-Vitamin B5), Hydrating Glycerin",
            "Skin Type": "Dry, Normal, Sensitive",
            "Routine": "AM & PM",
            "Intended Use": "Gentle daily non-stripping facial cleansing",
            "Brand Tier": "Affordable",
        },
        "image_url": "https://images.unsplash.com/photo-1556228720-195a672e8a03?auto=format&fit=crop&w=600&q=80",
        "offers": [
            {"store_name": "Nykaa (Demo)", "current_price": 333.0, "original_price": 370.0, "shipping_cost": 0.0, "availability": "In Stock", "variant_name": "125 ml / Standard", "trend_type": "all_time_low"},
            {"store_name": "Amazon India (Demo)", "current_price": 349.0, "original_price": 370.0, "shipping_cost": 0.0, "availability": "In Stock", "variant_name": "125 ml / Standard", "trend_type": "normal"},
            {"store_name": "Purplle (Demo)", "current_price": 355.0, "original_price": 370.0, "shipping_cost": 49.0, "availability": "In Stock", "variant_name": "125 ml / Standard", "trend_type": "normal"},
        ],
    },
    {
        "sku": "BEAUTY-FE-SAFFRON-CLN-200",
        "title": "Forest Essentials Delicate Facial Cleanser Kashmiri Saffron & Neem",
        "brand": "Forest Essentials",
        "category": "Face cleansers",
        "description": "Pure Ayurvedic cleanser infused with Kashmiri Saffron extract and clarifying Neem leaf water to gently purify, balance oil, and clarify skin tone.",
        "specs": {
            "Product Type": "Gel Cleanser",
            "Net Quantity": "200 ml",
            "Key Ingredients": "Kashmiri Saffron, Organic Neem Water, Rose Flower Water, Kewda Infusion",
            "Skin Type": "Normal, Oily, Combination, Sensitive",
            "Routine": "AM & PM",
            "Intended Use": "Ayurvedic botanical cleansing, pore clarification",
            "Brand Tier": "Luxury",
        },
        "image_url": "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?auto=format&fit=crop&w=600&q=80",
        "offers": [
            {"store_name": "Nykaa (Demo)", "current_price": 1550.0, "original_price": 1550.0, "shipping_cost": 0.0, "availability": "In Stock", "variant_name": "200 ml / Dispenser", "trend_type": "normal"},
            {"store_name": "Tira (Demo)", "current_price": 1475.0, "original_price": 1550.0, "shipping_cost": 0.0, "availability": "In Stock", "variant_name": "200 ml / Dispenser", "trend_type": "great_deal"},
        ],
    },

    # -------------------------------------------------------------
    # 4. MOISTURIZERS
    # -------------------------------------------------------------
    {
        "sku": "BEAUTY-CLINIQUE-100H-50",
        "title": "Clinique Moisture Surge 100H Auto-Replenishing Hydrator",
        "brand": "Clinique",
        "category": "Moisturizers",
        "description": "Iconic oil-free gel-cream with exclusive Aloe Bio-Ferment and Hyaluronic Acid that penetrates 10+ layers deep for 100 hours of continuous hydration.",
        "specs": {
            "Product Type": "Gel-Cream Moisturizer",
            "Net Quantity": "50 ml",
            "Key Ingredients": "Aloe Bio-Ferment, Hyaluronic Acid, Activated Aloe Water, Caffeine",
            "Skin Type": "All Skin Types, Dehydrated, Sensitive, Combination",
            "Routine": "AM & PM",
            "Intended Use": "Continuous 100-hour plumping hydration, barrier quench",
            "Brand Tier": "Luxury",
        },
        "image_url": "https://images.unsplash.com/photo-1608248597359-52410a747e93?auto=format&fit=crop&w=600&q=80",
        "offers": [
            {"store_name": "Nykaa (Demo)", "current_price": 2950.0, "original_price": 2950.0, "shipping_cost": 0.0, "availability": "In Stock", "variant_name": "50 ml / Glass Jar", "trend_type": "normal"},
            {"store_name": "Tira (Demo)", "current_price": 2790.0, "original_price": 2950.0, "shipping_cost": 0.0, "availability": "In Stock", "variant_name": "50 ml / Glass Jar", "trend_type": "great_deal"},
            {"store_name": "Myntra (Demo)", "current_price": 2850.0, "original_price": 2950.0, "shipping_cost": 0.0, "availability": "In Stock", "variant_name": "50 ml / Glass Jar", "trend_type": "normal"},
        ],
    },
    {
        "sku": "BEAUTY-DOTKEY-CERAM-50",
        "title": "Dot & Key Ceramides & Hyaluronic Skin Barrier Repair Face Cream",
        "brand": "Dot & Key",
        "category": "Moisturizers",
        "description": "Rich nourishing barrier cream loaded with 5 essential ceramides, Hyaluronic Acid, and Probiotics to heal compromised skin barriers and soothe dryness.",
        "specs": {
            "Product Type": "Barrier Cream Moisturizer",
            "Net Quantity": "50 g",
            "Key Ingredients": "Ceramides (NP, AP, EOP), Hyaluronic Acid, Japanese Rice Water, Probiotics",
            "Skin Type": "Dry, Normal, Compromised Barrier, Sensitive",
            "Routine": "AM & PM",
            "Intended Use": "Barrier restoration, deep nourishment, flaky skin relief",
            "Brand Tier": "Affordable",
        },
        "image_url": "https://images.unsplash.com/photo-1556228720-195a672e8a03?auto=format&fit=crop&w=600&q=80",
        "offers": [
            {"store_name": "Nykaa (Demo)", "current_price": 395.0, "original_price": 495.0, "shipping_cost": 0.0, "availability": "In Stock", "variant_name": "50 g / Tub", "trend_type": "all_time_low"},
            {"store_name": "Amazon India (Demo)", "current_price": 420.0, "original_price": 495.0, "shipping_cost": 0.0, "availability": "In Stock", "variant_name": "50 g / Tub", "trend_type": "normal"},
            {"store_name": "Purplle (Demo)", "current_price": 415.0, "original_price": 495.0, "shipping_cost": 49.0, "availability": "In Stock", "variant_name": "50 g / Tub", "trend_type": "normal"},
        ],
    },

    # -------------------------------------------------------------
    # 5. LIPSTICKS
    # -------------------------------------------------------------
    {
        "sku": "BEAUTY-MAC-RUBY-3",
        "title": "M.A.C Retro Matte Lipstick - Ruby Woo",
        "brand": "M.A.C",
        "category": "Lipsticks",
        "description": "The globally iconic vivid blue-red shade with an intense, non-feathering matte finish and full-coverage wear lasting up to 8 hours.",
        "specs": {
            "Product Type": "Bullet Lipstick",
            "Net Quantity": "3 g",
            "Shade": "Ruby Woo (Vivid Blue-Red)",
            "Finish": "Ultra-Matte",
            "Intended Use": "Iconic high-pigment longwear lip color",
            "Brand Tier": "Luxury",
        },
        "image_url": "https://images.unsplash.com/photo-1586495777744-4413f21062fa?auto=format&fit=crop&w=600&q=80",
        "offers": [
            {"store_name": "Nykaa (Demo)", "current_price": 2300.0, "original_price": 2300.0, "shipping_cost": 0.0, "availability": "In Stock", "variant_name": "3 g / Bullet", "trend_type": "normal"},
            {"store_name": "Tira (Demo)", "current_price": 2185.0, "original_price": 2300.0, "shipping_cost": 0.0, "availability": "In Stock", "variant_name": "3 g / Bullet", "trend_type": "great_deal"},
            {"store_name": "Myntra (Demo)", "current_price": 2300.0, "original_price": 2300.0, "shipping_cost": 0.0, "availability": "In Stock", "variant_name": "3 g / Bullet", "trend_type": "normal"},
        ],
    },
    {
        "sku": "BEAUTY-KAY-MATTE-3",
        "title": "Kay Beauty Matteinee Matte Lipstick - Reconstruct",
        "brand": "Kay Beauty",
        "category": "Lipsticks",
        "description": "Comfortable ultra-matte bullet enriched with Chamomile and Marula oil to nourish lips while delivering rich, high-intensity color payoff designed for Indian skin tones.",
        "specs": {
            "Product Type": "Bullet Lipstick",
            "Net Quantity": "3.5 g",
            "Shade": "Reconstruct (Deep True Red)",
            "Finish": "Velvet Matte",
            "Key Ingredients": "Chamomile Oil, Marula Oil, Vitamin E",
            "Intended Use": "Hydrating matte everyday and occasion lip color",
            "Brand Tier": "Affordable",
        },
        "image_url": "https://images.unsplash.com/photo-1586495777744-4413f21062fa?auto=format&fit=crop&w=600&q=80",
        "offers": [
            {"store_name": "Nykaa (Demo)", "current_price": 799.0, "original_price": 899.0, "shipping_cost": 0.0, "availability": "In Stock", "variant_name": "3.5 g / Bullet", "trend_type": "moderate_deal"},
            {"store_name": "Amazon India (Demo)", "current_price": 849.0, "original_price": 899.0, "shipping_cost": 0.0, "availability": "In Stock", "variant_name": "3.5 g / Bullet", "trend_type": "normal"},
        ],
    },

    # -------------------------------------------------------------
    # 6. FOUNDATIONS
    # -------------------------------------------------------------
    {
        "sku": "BEAUTY-MAYB-FITME-30",
        "title": "Maybelline Fit Me Matte + Poreless Liquid Foundation - 128 Warm Nude",
        "brand": "Maybelline",
        "category": "Foundations",
        "description": "India's bestselling lightweight liquid foundation with micro-powders that control shine, blur pores, and seamlessly match Indian skin undertones with SPF 22.",
        "specs": {
            "Product Type": "Liquid Foundation",
            "Net Quantity": "30 ml",
            "Shade": "128 Warm Nude",
            "Finish": "Natural Matte",
            "Skin Type": "Normal, Oily, Combination",
            "Intended Use": "Medium buildable coverage, pore blurring, oil control",
            "Brand Tier": "Affordable",
        },
        "image_url": "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?auto=format&fit=crop&w=600&q=80",
        "offers": [
            {"store_name": "Nykaa (Demo)", "current_price": 549.0, "original_price": 699.0, "shipping_cost": 0.0, "availability": "In Stock", "variant_name": "30 ml / Pump", "trend_type": "all_time_low"},
            {"store_name": "Purplle (Demo)", "current_price": 579.0, "original_price": 699.0, "shipping_cost": 49.0, "availability": "In Stock", "variant_name": "30 ml / Pump", "trend_type": "normal"},
            {"store_name": "Amazon India (Demo)", "current_price": 535.0, "original_price": 699.0, "shipping_cost": 0.0, "availability": "In Stock", "variant_name": "30 ml / Pump", "trend_type": "all_time_low"},
            {"store_name": "Myntra (Demo)", "current_price": 599.0, "original_price": 699.0, "shipping_cost": 0.0, "availability": "In Stock", "variant_name": "30 ml / Pump", "trend_type": "normal"},
        ],
    },

    # -------------------------------------------------------------
    # 7. BLUSHES
    # -------------------------------------------------------------
    {
        "sku": "BEAUTY-RARE-BLUSH-7",
        "title": "Rare Beauty Soft Pinch Liquid Blush - Encourage",
        "brand": "Rare Beauty",
        "category": "Blushes",
        "description": "Weightless, long-lasting liquid blush infused with lotus, gardenia, and white water lily that blends effortlessly for a soft, healthy flush.",
        "specs": {
            "Product Type": "Liquid Blush",
            "Net Quantity": "7.5 ml",
            "Shade": "Encourage (Soft Neutral Pink)",
            "Finish": "Dewy Luminous",
            "Skin Type": "All Skin Types",
            "Intended Use": "All-day high-pigment pinch of natural flush",
            "Brand Tier": "Luxury",
        },
        "image_url": "https://images.unsplash.com/photo-1512496015851-a90fb38ba796?auto=format&fit=crop&w=600&q=80",
        "offers": [
            {"store_name": "Tira (Demo)", "current_price": 2400.0, "original_price": 2400.0, "shipping_cost": 0.0, "availability": "In Stock", "variant_name": "7.5 ml / Standard", "trend_type": "normal"},
            {"store_name": "Nykaa (Demo)", "current_price": 2400.0, "original_price": 2400.0, "shipping_cost": 0.0, "availability": "In Stock", "variant_name": "7.5 ml / Standard", "trend_type": "normal"},
        ],
    },
    {
        "sku": "BEAUTY-KAY-CREME-BLUSH-4",
        "title": "Kay Beauty Creme Blush - Sweetheart Pink",
        "brand": "Kay Beauty",
        "category": "Blushes",
        "description": "Melt-on-skin creamy blush enriched with berry antioxidants that blends like butter without disturbing base makeup, leaving radiant color.",
        "specs": {
            "Product Type": "Cream Blush",
            "Net Quantity": "4 g",
            "Shade": "Sweetheart Pink",
            "Finish": "Dewy Glow",
            "Key Ingredients": "Berry Extracts, Avocado Oil, Vitamin E",
            "Intended Use": "Natural flush and cheek radiance for Indian skin tones",
            "Brand Tier": "Affordable",
        },
        "image_url": "https://images.unsplash.com/photo-1512496015851-a90fb38ba796?auto=format&fit=crop&w=600&q=80",
        "offers": [
            {"store_name": "Nykaa (Demo)", "current_price": 799.0, "original_price": 899.0, "shipping_cost": 0.0, "availability": "In Stock", "variant_name": "4 g / Pot", "trend_type": "moderate_deal"},
            {"store_name": "Amazon India (Demo)", "current_price": 820.0, "original_price": 899.0, "shipping_cost": 0.0, "availability": "In Stock", "variant_name": "4 g / Pot", "trend_type": "normal"},
        ],
    },

    # -------------------------------------------------------------
    # 8. MASCARA & EYELINER
    # -------------------------------------------------------------
    {
        "sku": "BEAUTY-MAYB-SKYHIGH-7",
        "title": "Maybelline Lash Sensational Sky High Waterproof Mascara",
        "brand": "Maybelline",
        "category": "Mascaras",
        "description": "Viral mascara with exclusive Flex Tower brush that extends every lash from root to tip. Infused with bamboo extract and fibers for lightweight, limitless length.",
        "specs": {
            "Product Type": "Waterproof Mascara",
            "Net Quantity": "7.2 ml",
            "Shade": "Very Black",
            "Key Ingredients": "Bamboo Extract, Lash Extending Fibers",
            "Intended Use": "All-day limitless lash length, smudgeproof volume",
            "Brand Tier": "Affordable",
        },
        "image_url": "https://images.unsplash.com/photo-1596462502278-27bfdc403348?auto=format&fit=crop&w=600&q=80",
        "offers": [
            {"store_name": "Nykaa (Demo)", "current_price": 799.0, "original_price": 899.0, "shipping_cost": 0.0, "availability": "In Stock", "variant_name": "7.2 ml / Waterproof", "trend_type": "moderate_deal"},
            {"store_name": "Amazon India (Demo)", "current_price": 749.0, "original_price": 899.0, "shipping_cost": 0.0, "availability": "In Stock", "variant_name": "7.2 ml / Waterproof", "trend_type": "all_time_low"},
            {"store_name": "Purplle (Demo)", "current_price": 820.0, "original_price": 899.0, "shipping_cost": 49.0, "availability": "In Stock", "variant_name": "7.2 ml / Waterproof", "trend_type": "normal"},
        ],
    },
    {
        "sku": "BEAUTY-KAY-KAJAL-03",
        "title": "Kay Beauty 24HR Waterproof Metallic Gel Kajal Eyeliner",
        "brand": "Kay Beauty",
        "category": "Eyeliners",
        "description": "Ultra-pigmented gel kajal that glides on smoothly, sets to a transfer-proof finish, and withstands heat and humidity for up to 24 hours.",
        "specs": {
            "Product Type": "Gel Kajal Eyeliner",
            "Net Quantity": "0.35 g",
            "Shade": "Midnight Black",
            "Key Ingredients": "Ceramides, Chamomile, Waterproof Film Formers",
            "Intended Use": "24HR smudgeproof waterline and lid definition",
            "Brand Tier": "Affordable",
        },
        "image_url": "https://images.unsplash.com/photo-1596462502278-27bfdc403348?auto=format&fit=crop&w=600&q=80",
        "offers": [
            {"store_name": "Nykaa (Demo)", "current_price": 299.0, "original_price": 349.0, "shipping_cost": 0.0, "availability": "In Stock", "variant_name": "0.35 g / Retractable", "trend_type": "all_time_low"},
            {"store_name": "Purplle (Demo)", "current_price": 320.0, "original_price": 349.0, "shipping_cost": 49.0, "availability": "In Stock", "variant_name": "0.35 g / Retractable", "trend_type": "normal"},
        ],
    },

    # -------------------------------------------------------------
    # 9. LIP CARE
    # -------------------------------------------------------------
    {
        "sku": "BEAUTY-LANEIGE-LIP-20",
        "title": "Laneige Lip Sleeping Mask Berry",
        "brand": "Laneige",
        "category": "Lip care",
        "description": "Cult-favorite overnight lip mask with Moisture Wrap technology and Berry Fruit Complex that melts away dead skin cells for baby-soft lips by morning.",
        "specs": {
            "Product Type": "Lip Sleeping Mask",
            "Net Quantity": "20 g",
            "Key Ingredients": "Berry Fruit Complex, Vitamin C, Coconut Oil, Shea Butter",
            "Intended Use": "Overnight dead cell removal, intense hydration",
            "Brand Tier": "Premium",
        },
        "image_url": "https://images.unsplash.com/photo-1586495777744-4413f21062fa?auto=format&fit=crop&w=600&q=80",
        "offers": [
            {"store_name": "Nykaa (Demo)", "current_price": 600.0, "original_price": 600.0, "shipping_cost": 0.0, "availability": "In Stock", "variant_name": "20 g / Berry", "trend_type": "normal"},
            {"store_name": "Tira (Demo)", "current_price": 570.0, "original_price": 600.0, "shipping_cost": 0.0, "availability": "In Stock", "variant_name": "20 g / Berry", "trend_type": "moderate_deal"},
            {"store_name": "Myntra (Demo)", "current_price": 585.0, "original_price": 600.0, "shipping_cost": 0.0, "availability": "In Stock", "variant_name": "20 g / Berry", "trend_type": "normal"},
        ],
    },
    {
        "sku": "BEAUTY-DOTKEY-LIP-12",
        "title": "Dot & Key Vitamin C + E Lip Sleeping Mask",
        "brand": "Dot & Key",
        "category": "Lip care",
        "description": "Rich nourishing lip butter infused with Vitamin C and Shea Butter that repairs dry, chapped, and pigmented lips overnight.",
        "specs": {
            "Product Type": "Lip Sleeping Mask",
            "Net Quantity": "12 g",
            "Key Ingredients": "Vitamin C, Vitamin E, Shea Butter, Lingonberry",
            "Intended Use": "Intensive overnight lip repair, flakiness treatment",
            "Brand Tier": "Affordable",
        },
        "image_url": "https://images.unsplash.com/photo-1586495777744-4413f21062fa?auto=format&fit=crop&w=600&q=80",
        "offers": [
            {"store_name": "Nykaa (Demo)", "current_price": 275.0, "original_price": 325.0, "shipping_cost": 0.0, "availability": "In Stock", "variant_name": "12 g / Tub", "trend_type": "all_time_low"},
            {"store_name": "Amazon India (Demo)", "current_price": 290.0, "original_price": 325.0, "shipping_cost": 0.0, "availability": "In Stock", "variant_name": "12 g / Tub", "trend_type": "normal"},
        ],
    },

    # -------------------------------------------------------------
    # 10. MAKEUP REMOVERS, HAIRCARE & BODY CARE
    # -------------------------------------------------------------
    {
        "sku": "BEAUTY-SIMPLE-MICELLAR-200",
        "title": "Simple Kind to Skin Micellar Cleansing Water",
        "brand": "Simple",
        "category": "Makeup removers",
        "description": "Triple-purified water and Vitamin B3/C formula that gently lifts away stubborn makeup and unclogs pores without rinsing, stinging, or residue.",
        "specs": {
            "Product Type": "Micellar Makeup Remover",
            "Net Quantity": "200 ml",
            "Key Ingredients": "Triple Purified Water, Niacinamide (Vitamin B3), Vitamin C",
            "Skin Type": "Sensitive, All Skin Types",
            "Routine": "PM",
            "Intended Use": "Gentle waterproof makeup removal, zero irritation",
            "Brand Tier": "Affordable",
        },
        "image_url": "https://images.unsplash.com/photo-1556228720-195a672e8a03?auto=format&fit=crop&w=600&q=80",
        "offers": [
            {"store_name": "Nykaa (Demo)", "current_price": 385.0, "original_price": 450.0, "shipping_cost": 0.0, "availability": "In Stock", "variant_name": "200 ml / Bottle", "trend_type": "all_time_low"},
            {"store_name": "Amazon India (Demo)", "current_price": 399.0, "original_price": 450.0, "shipping_cost": 0.0, "availability": "In Stock", "variant_name": "200 ml / Bottle", "trend_type": "normal"},
            {"store_name": "Purplle (Demo)", "current_price": 410.0, "original_price": 450.0, "shipping_cost": 49.0, "availability": "In Stock", "variant_name": "200 ml / Bottle", "trend_type": "normal"},
        ],
    },
    {
        "sku": "BEAUTY-MIN-MALEIC-50",
        "title": "Minimalist Maleic Bond Repair Complex 5% Hair Serum",
        "brand": "Minimalist",
        "category": "Haircare",
        "description": "Patent-pending pre-shampoo bond repair treatment with Maleic Acid, Transglutaminase, and Amino Acids that repairs disulfide bonds broken by heat and coloring.",
        "specs": {
            "Product Type": "Bond Repair Hair Treatment",
            "Net Quantity": "50 ml",
            "Key Ingredients": "Maleic Acid 5%, Transglutaminase, Amino Acids, Argan Oil",
            "Hair Type": "Damaged, Color-Treated, Frizzy, Heat-Styled",
            "Routine": "Weekly Pre-Shampoo",
            "Intended Use": "Hair bond repair, breakage reduction, frizz control",
            "Brand Tier": "Affordable",
        },
        "image_url": "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?auto=format&fit=crop&w=600&q=80",
        "offers": [
            {"store_name": "Nykaa (Demo)", "current_price": 599.0, "original_price": 599.0, "shipping_cost": 0.0, "availability": "In Stock", "variant_name": "50 ml / Dropper", "trend_type": "normal"},
            {"store_name": "Amazon India (Demo)", "current_price": 569.0, "original_price": 599.0, "shipping_cost": 0.0, "availability": "In Stock", "variant_name": "50 ml / Dropper", "trend_type": "all_time_low"},
            {"store_name": "Purplle (Demo)", "current_price": 599.0, "original_price": 599.0, "shipping_cost": 49.0, "availability": "In Stock", "variant_name": "50 ml / Dropper", "trend_type": "normal"},
        ],
    },
    {
        "sku": "BEAUTY-CAP-BODYWASH-250",
        "title": "Chemist at Play Exfoliating Lactic Acid Body Wash",
        "brand": "Chemist at Play",
        "category": "Body care",
        "description": "Ceramide-infused daily exfoliating body wash with 2% Lactic Acid and Zemea to buff away strawberry skin, rough bumps, and back acne gently.",
        "specs": {
            "Product Type": "Exfoliating Body Wash",
            "Net Quantity": "250 ml",
            "Key Ingredients": "Lactic Acid 2%, Essential Ceramides, Zemea, Vitamin E",
            "Skin Type": "Rough Bumpy Skin, Strawberry Legs, Normal",
            "Routine": "Daily Body Routine",
            "Intended Use": "Keratosis pilaris reduction, skin smoothing, barrier hydration",
            "Brand Tier": "Affordable",
        },
        "image_url": "https://images.unsplash.com/photo-1556228720-195a672e8a03?auto=format&fit=crop&w=600&q=80",
        "offers": [
            {"store_name": "Nykaa (Demo)", "current_price": 399.0, "original_price": 499.0, "shipping_cost": 0.0, "availability": "In Stock", "variant_name": "250 ml / Pump", "trend_type": "all_time_low"},
            {"store_name": "Amazon India (Demo)", "current_price": 419.0, "original_price": 499.0, "shipping_cost": 0.0, "availability": "In Stock", "variant_name": "250 ml / Pump", "trend_type": "normal"},
            {"store_name": "Purplle (Demo)", "current_price": 429.0, "original_price": 499.0, "shipping_cost": 49.0, "availability": "In Stock", "variant_name": "250 ml / Pump", "trend_type": "normal"},
        ],
    },
]

