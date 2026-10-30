"""About & Academic Methodology View for PriceWise AI."""

import streamlit as st
from src.config import APP_NAME, APP_VERSION


def render_about_view():
    """Renders academic project documentation, methodology, and database architecture."""
    st.markdown(
        f"""
        <div style="margin-bottom: 24px;">
            <h1 style="font-size: 2rem; font-weight: 800; color: #0f172a; margin-bottom: 8px;">
                About {APP_NAME} <span style="font-size: 1rem; color: #6366f1; vertical-align: middle;">v{APP_VERSION}</span>
            </h1>
            <p style="font-size: 1rem; color: #475569; margin: 0; line-height: 1.6;">
                Academic Project: <strong>Price Comparison Website with Real Deal Detector</strong>.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3, tab6, tab4, tab5 = st.tabs([
        "🧠 Real Deal Detector Methodology",
        "🧭 Smart Purchase Advisor (Phase 5)",
        "🔔 Price Tracking & Alerts (Phase 6)",
        "👤 Personalization & Wishlist (Phase 7)",
        "🗄️ Database Architecture",
        "📋 Academic Scope & Demo Data",
    ])

    with tab1:
        st.markdown(
            r"""
            ### Real Deal Detector™ Algorithm & Viva Methodology (Phase 4)
            
            Modern ecommerce platforms often employ dynamic pricing and artificial price inflation prior to sales events (such as inflating original list prices to exaggerate perceived discounts). **PriceWise AI** counteracts deceptive pricing tactics by evaluating current offers against timestamped historical price records across configurable time windows (30-day, 90-day, and all-time).

            #### 1. Price Benchmark Metrics
            For every product offer, the system calculates:
            - **Historical Minimum ($P_{min}$)**: The lowest recorded price within the selected observation window.
            - **Historical Maximum ($P_{max}$)**: The peak recorded price within the window.
            - **Historical Mean ($\mu_{hist}$)**: The arithmetic average of all recorded timestamped observations.
            - **Recent 7-Day Average ($\mu_{recent}$)**: Moving average over the past 7 days to identify immediate price direction.
            - **Current Price Difference vs Average ($\Delta_{avg}$)**: Current price minus historical average ($P_{curr} - \mu_{hist}$) and percentage deviation.
            - **Percentage Difference vs Minimum ($\Delta_{min}\%$)**: Percentage premium above recorded historical minimum: $\frac{P_{curr} - P_{min}}{P_{min}} \times 100\%$.
            - **Price Trend**: Categorized as *Falling* ($\le -3\%$), *Rising* ($\ge +3\%$), or *Stable*.

            #### 2. Deterministic Deal Scoring Formula (0 – 100)
            When sufficient evidence exists, the Deal Score is computed via a weighted multi-factor composite:
            
            1. **Historical Range Component (60% weight)**: Measures proximity to the historical minimum within the observed span $[P_{min}, P_{max}]$:
               $$S_{range} = 100 \times \left(1 - \frac{P_{curr} - P_{min}}{P_{max} - P_{min}}\right)$$
            2. **Historical Average Component (40% weight)**: Rewards prices below the historical mean and penalizes prices above:
               $$S_{avg} = 50 + 50 \times \left(\frac{\mu_{hist} - P_{curr}}{\mu_{hist} \times 0.20}\right)$$
            3. **Composite Score**:
               $$\text{Score} = \text{clamp}(0.60 \times S_{range} + 0.40 \times S_{avg}, 0, 100)$$
            4. **Bonus / Penalties**:
               - All-time low bonus: If $P_{curr} \le P_{min} + 0.01$, score is guaranteed at least 85.
               - Suspicious discount penalty: Clamped to maximum 40 if an unverified discount is detected.

            #### 3. 4-Tier Deal Classification
            - **80 – 100: EXCELLENT DEAL** (at or near historical minimum, significantly below historical average; `is_good_value = True`)
            - **65 – 79: GOOD DEAL** (noticeably below typical historical pricing; `is_good_value = True`)
            - **45 – 64: FAIR PRICE** (within standard historical range; `is_good_value = False`)
            - **0 – 44: POOR DEAL** (inflated price; shoppers are advised to wait; `is_good_value = False`)

            #### 4. Honest Handling of Insufficient Data
            If fewer than 3 timestamped observations are available or observations span less than 7 days, the system **withholds the numeric score** (`deal_score = None`) rather than fabricating a score of zero. A transparent **INSUFFICIENT DATA** verdict is shown, stating exactly how many observations are available and what evidence is required.

            #### 5. Transparent Suspicious Discount Detection
            Where an advertised discount is claimed against an `original_price`:
            - **Promotional Price Exceeds Average**: Flags when a "sale" price is actually higher than recorded historical averages.
            - **Unverified Reference Price**: Flags when an advertised MSRP is more than 15% above the highest price ever recorded.
            All alerts use measured, analytical language to inform shoppers without making unsubstantiated accusations of retailer fraud.

            #### 6. Variant & Currency Isolation
            To prevent statistical distortion, historical price series are strictly partitioned by canonical variant (e.g., 128GB vs 256GB) and currency (e.g., USD vs EUR). Offers of differing specifications are never combined into a single price analysis.
            """
        )

    with tab2:
        st.markdown(
            r"""
            ### Smart Purchase Advisor & Recommendation Methodology (Phase 5)

            The **Smart Purchase Advisor** provides transparent, explainable recommendations without relying on unpredictable or hallucinating external AI/LLM APIs. It applies deterministic constraint programming, technical specification verification, and mathematical multi-attribute utility theory.

            #### 1. Separation of Concerns: Suitability vs Price Attractiveness
            - **Recommendation Suitability Score ($R_{score} \in [0, 100]$)**: Measures how well a product matches the buyer's budget, use case, hardware specifications, and brand preference.
            - **Real Deal Score ($S_{deal} \in [0, 100]$)**: Measures price attractiveness relative to recorded historical observations.
            - **No Unexplained Score Merging**: The system intentionally keeps these two dimensions distinct so shoppers clearly see *why* an item fits their workflow independently of *how good* the current price is.

            #### 2. Recommendation Scoring Formulation
            For candidate products satisfying hard constraints (budget, category, stock availability, required specs):
            $$R_{score} = 0.40 \times S_{usecase} + 0.30 \times S_{spec} + 0.20 \times S_{budget} + 0.10 \times S_{brand}$$
            
            1. **Use-Case Suitability ($S_{usecase}$, 40% weight)**: Hardware synergy for the selected workflow:
               - *Programming*: Rewards high RAM ($\ge 16\text{GB}$ or $32\text{GB}$), multi-core CPUs, and 4K display connectivity.
               - *Gaming*: Rewards high-refresh displays ($120\text{Hz}$), discrete GeForce RTX GPUs, and console architecture.
               - *Photography*: Rewards full-frame sensors, OLED/wide-gamut panels, and multi-camera RAW arrays.
               - *Studying / Office*: Rewards Active Noise Cancellation (ANC), all-day battery runtime, and lightweight portability.
            2. **Specification Excellence ($S_{spec}$, 30% weight)**: Evaluates technical attributes against recorded specifications.
            3. **Budget Efficiency ($S_{budget}$, 20% weight)**: Rewards remaining headroom when under budget:
               $$S_{budget} = 60 + 40 \times \left(\frac{\text{Budget} - \text{Total Cost}}{\text{Budget}}\right)$$
            4. **Brand Preference ($S_{brand}$, 10% weight)**: Awards full score for matching manufacturer preferences.

            #### 3. Recommendation Categorization
            - **🌟 BEST OVERALL**: Candidate with the highest composite recommendation score ($R_{score}$).
            - **💰 BEST BUDGET**: Suitable candidate that maximizes budget savings (lowest total checkout cost) while satisfying all essential requirements.
            - **🏷️ BEST CURRENT DEAL**: Candidate with a verified historical Real Deal Score $\ge 65$ (`GOOD DEAL` or `EXCELLENT DEAL`). *A product is never labeled the best deal solely because it has the lowest nominal price.*

            #### 4. Hard Constraints & Missing Specification Safeguards
            - **Budget Overrun Protection**: Products above budget are never presented as compliant options.
            - **Total Cost with Shipping**: Total cost includes verified shipping fees (item price + shipping).
            - **Missing Specs Treated as Unknown**: Missing specs are never assumed to meet requirements. If a product lacks a recorded spec (e.g. unrecorded RAM), it fails hard spec requirements and flags an explicit missing spec warning.
            - **Closest Alternatives**: When no products satisfy all hard constraints, the advisor explains the failure and displays near-matches with exact overrun amounts and missing specs highlighted.
            """
        )

    with tab3:
        st.markdown(
            r"""
            ### Persistent Price Tracking & Alerts Methodology (Phase 6)

            The **Price Tracking & Alerts Engine** enables users to monitor target price conditions across canonical products and receive deterministic, explainable in-app alerts whenever recorded price observations satisfy trigger criteria.

            #### 1. Core Alert Evaluation Rules
            1. **Target Price Reached ($P_{curr} \le P_{target}$)**:
               - Triggers when the lowest active in-stock offer drops to or below the shopper's chosen threshold.
               - Calculates exact dollar savings below target ($P_{target} - P_{curr}$).
            2. **Meaningful Price Drop ($\Delta P_{drop}$)**:
               - Requires both an absolute reduction $\ge \$1.00$ AND a percentage drop $\ge 1.0\%$ relative to the previous observation:
                 $$\Delta P_{drop} = P_{prev} - P_{curr} \ge 1.00 \quad \land \quad \frac{\Delta P_{drop}}{P_{prev}} \ge 0.01$$
               - Filters out micro-cent rounding noise and minor fluctuations.
            3. **Tracking Status Gating**:
               - Monitored products can be actively running (`active`) or paused (`paused`). Paused trackers are strictly excluded from triggering notifications.
            4. **Stock Availability Safeguard**:
               - Offers labeled *Out of Stock*, *Unavailable*, or *Discontinued* are excluded from triggering price-based alerts.

            #### 2. Duplicate Alert Prevention Architecture
            To prevent spamming the user's notification feed during recurring evaluations or page refreshes:
            - **Tracking-Level Memory**: Tracks `last_alert_price` and `last_alert_type` directly on each record. If the current price is unchanged, no repeat alert is issued.
            - **Database-Level Idempotency**: Each alert generates a deterministic unique trigger key (e.g. `"<track_id>:target_reached:<price>"` or `"<track_id>:price_drop:<prev>-><curr>"`). The `price_alerts` table enforces `UNIQUE(trigger_key)` with `INSERT OR IGNORE`.
            - **Subsequent Price Change Re-Arming**: When a genuine subsequent price shift occurs, the new condition generates a distinct trigger key and safely creates a fresh notification.

            #### 3. In-App Notification Center
            - Stores all notifications in persistent SQLite storage (`price_alerts`).
            - Supports real-time filtering (all alerts vs. unread only), individual "Mark as Read", and batch "Mark All as Read".
            - No external email or SMS delivery is claimed or simulated; all notifications are transparently delivered within the application.
            """
        )

    with tab6:
        st.markdown(
            r"""
            ### User Accounts, Wishlist & Personalization Methodology (Phase 7)

            **Phase 7** introduces multi-tenant account isolation, persistent shopping wishlists, and user-tailored recommendation preferences while upholding strict academic standards and explainability.

            #### 1. Secure Authentication & Credential Architecture
            - **Salted PBKDF2 Password Hashing**: Passwords are hashed using NIST-compliant `PBKDF2-HMAC-SHA256` with 260,000 iterations and 16 bytes of cryptographically secure random salt (`secrets.token_bytes(16)`).
            - **Constant-Time Verification**: Password verification uses `secrets.compare_digest` to prevent timing attacks. Raw passwords are never stored in plaintext.
            - **Email Normalization & Validation**: Case-insensitive RFC-standard email normalization (`alice@domain.com` == `Alice@Domain.COM`).

            #### 2. Multi-User Isolation & Ownership Verification
            - **Database Ownership Foreign Keys**: `price_tracking` and `price_alerts` link directly to `users(id)` via nullable foreign keys (supporting backward compatibility with legacy guest records).
            - **Composite Uniqueness**: Each user can independently track the same product with distinct target prices via `UNIQUE(user_id, product_id)`.
            - **Service-Level Authorization Enforcement**: All mutation functions (`update_target_price`, `pause_tracking`, `remove_tracking`, `mark_alert_read`) perform caller verification to prevent cross-account tampering.

            #### 3. Persistent Personal Wishlist
            - Allows shoppers to curate saved items with custom annotations (`note`).
            - Automatically aggregates current lowest offers and active tracking indicators.
            - Guarantees idempotent item management via `UNIQUE(user_id, product_id)`.

            #### 4. Personalized Recommendation Engine
            - **Preference Synergies**: Integrates user-chosen manufacturer brands and category affinities into the Smart Purchase Advisor scoring pipeline.
            - **Hard Constraints Preserved**: User preferences *never* override hard budget ceilings, essential specifications, or in-stock availability. If an affinity item fails requirements, it is transparently categorized under *Closest Alternatives*.
            - **Optimization Priorities**: Supports `balanced`, `lowest_price` (maximum direct savings), and `best_deal` (highest verified Real Deal Score) ranking modes.
            """
        )

    with tab4:
        st.markdown(
            """
            ### Relational Database Schema (SQLite)
            
            The system employs a normalized relational schema with foreign key constraints, check constraints, and automated indexation for fast search and aggregation:

            - `users` (Phase 7): Member accounts with email, salted PBKDF2 password hashes, full names, and timestamps.
            - `wishlist` (Phase 7): Personal product wishlists linking users to products with custom notes and composite uniqueness.
            - `user_preferences` (Phase 7): Shopping profiles storing category/brand affinities (JSON arrays), budget ranges, preferred retailers, and ranking priorities.
            - `products`: Canonical product metadata (SKU, title, brand, category, technical specs JSON).
            - `stores`: Registered retail vendor profiles, trust ratings, and delivery policies.
            - `offers`: Cross-store offers tying products to stores with current prices, original MSRP, shipping fees, availability, and variants.
            - `price_history`: Immutable time-series ledger capturing timestamped price observations for historical analysis.
            - `price_tracking` (Phase 6 & 7): Persistent product monitoring records with target prices, monitoring status (`active` / `paused`), trigger type, evaluation state, and user ownership isolation.
            - `price_alerts` (Phase 6 & 7): Persistent in-app notifications with alert type (`target_reached` / `price_drop`), observed price, previous price, read status, unique trigger keys, and user ownership isolation.
            """
        )

    with tab5:
        st.markdown(
            """
            ### Academic Prototype Transparency Notice
            
            - **Curated Demo Dataset**: In compliance with academic evaluation standards, all products, stores (e.g. *TechMart Demo*, *ElectroHub Demo*), and price points are synthetic or curated sample data labeled as DEMO DATA.
            - **No Real-Time Background Scraping**: The prototype does not perform unannounced web scraping or run external background daemon daemons; evaluations run on-demand or upon recorded price updates.
            - **Modularity**: Application logic, data access, pricing intelligence, tracking, and UI components are strictly segregated into distinct Python packages without top-level monolithic mixing.
            """
        )

