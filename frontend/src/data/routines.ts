export interface RoutineStepGuide {
  step: number;
  phase: 'AM' | 'PM';
  category: string;
  name: string;
  purpose: string;
  instructions: string;
  frequency: string;
  precautions: string;
  proTip: string;
}

export const AM_ROUTINE: RoutineStepGuide[] = [
  {
    step: 1,
    phase: 'AM',
    category: 'Face Wash',
    name: 'Gentle Cleansing',
    purpose: 'Remove overnight sweat and excess sebum without disturbing the lipid barrier.',
    instructions: 'Use lukewarm water and massage a dime-sized cleanser for 45-60 seconds before patting dry with a clean towel.',
    frequency: 'Daily (Every Morning)',
    precautions: 'Avoid aggressive foaming surfactants if your skin feels tight or parched.',
    proTip: 'For very dry skin types, a lukewarm water splash is often sufficient.',
  },
  {
    step: 2,
    phase: 'AM',
    category: 'Toners',
    name: 'Hydrating Prep Toner / Essence',
    purpose: 'Rebalance skin pH and create a damp sponge effect for maximum active absorption.',
    instructions: 'Pat 3-4 drops directly into skin with clean palms while skin is slightly damp.',
    frequency: 'Daily (Every Morning)',
    precautions: 'Do not use high-percentage chemical peeling toners in the morning before strong sun.',
    proTip: 'Apply on damp skin to lock in 3x more hydration.',
  },
  {
    step: 3,
    phase: 'AM',
    category: 'Serums',
    name: 'Antioxidant & Brightening Serum',
    purpose: 'Shield against environmental free-radical pollution and prevent UV hyperpigmentation.',
    instructions: 'Dispense 2-3 drops of Vitamin C or Niacinamide and tap into skin until completely absorbed.',
    frequency: 'Daily (Every Morning)',
    precautions: 'Always pair with sunscreen when using active brightening serums.',
    proTip: 'Vitamin C + SPF in the morning boosts UV protection by up to 40%.',
  },
  {
    step: 4,
    phase: 'AM',
    category: 'Moisturiser',
    name: 'Barrier Cream or Gel Hydrator',
    purpose: 'Replenish intercellular lipids (ceramides, cholesterol, fatty acids) to prevent transepidermal water loss.',
    instructions: 'Apply a pea-sized amount in upward lifting strokes across face and neck.',
    frequency: 'Daily (Every Morning)',
    precautions: 'Opt for lightweight gel hydrators in Indian summers to avoid midday oiliness.',
    proTip: 'Never skip moisturiser even if your skin is oily; dehydrated oily skin overproduces sebum.',
  },
  {
    step: 5,
    phase: 'AM',
    category: 'Sunscreen',
    name: 'Broad-Spectrum SPF 50+ PA++++',
    purpose: 'The ultimate non-negotiable step to prevent photoaging, melasma, and collagen breakdown.',
    instructions: 'Apply two full finger-lengths evenly over face, ears, and neck 15 minutes before stepping out.',
    frequency: 'Daily (365 Days a Year)',
    precautions: 'Reapply every 2-3 hours when in direct sunlight or after sweating/swimming.',
    proTip: 'Look for PA++++ rating for maximum UVA protection against Indian UV index.',
  },
];

export const PM_ROUTINE: RoutineStepGuide[] = [
  {
    step: 1,
    phase: 'PM',
    category: 'Face Wash',
    name: 'Double Cleanse (Oil Balm + Foaming Cleanser)',
    purpose: 'Melt water-resistant sunscreen, makeup, and urban grime effortlessly without scrubbing.',
    instructions: 'Massage cleansing oil on dry skin for 60 seconds, emulsify with water, rinse, then follow with water-based cleanser.',
    frequency: 'Daily (Every Evening)',
    precautions: 'Ensure you completely emulsify cleansing oil until it turns milky before rinsing.',
    proTip: 'Double cleansing prevents 90% of clogged pores caused by waterproof sunscreens.',
  },
  {
    step: 2,
    phase: 'PM',
    category: 'Serums',
    name: 'Cellular Repair & Exfoliation (Retinol / AHA)',
    purpose: 'Stimulate cellular turnover, boost collagen, and smooth stubborn uneven texture.',
    instructions: 'On completely dry skin, apply a pea-sized amount of Retinoid or gentle exfoliating acid.',
    frequency: '2-3 Times per Week',
    precautions: 'Never use Retinol and AHA/BHA in the same night. Introduce slowly (sandwich method).',
    proTip: 'Buffer Retinol between two layers of moisturiser if you experience initial sensitivity.',
  },
  {
    step: 3,
    phase: 'PM',
    category: 'Moisturiser',
    name: 'Deep Overnight Barrier Recovery Cream',
    purpose: 'Intensive overnight healing while your body is in its peak cellular regeneration cycle.',
    instructions: 'Generously press a rich ceramide cream or peptide emulsion over face, neck, and décolletage.',
    frequency: 'Daily (Every Evening)',
    precautions: 'Allow active serum to absorb for 2-3 minutes before sealing with cream.',
    proTip: 'Sleep on a silk or satin pillowcase to reduce friction and product absorption into fabric.',
  },
  {
    step: 4,
    phase: 'PM',
    category: 'Lip Care',
    name: 'Overnight Lip Sleeping Butter',
    purpose: 'Dissolve dry flakiness and infuse long-chain lipids for plump lips by morning.',
    instructions: 'Coat lips with a generous layer before sleeping.',
    frequency: 'Nightly',
    precautions: 'Gently wipe with a damp washcloth in the morning.',
    proTip: 'Also dab a tiny amount around dry orbital skin as a rich slugging barrier.',
  },
];

