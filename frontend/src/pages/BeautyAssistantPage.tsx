import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Send,
  Copy,
  AlertTriangle,
  MessageSquare,
  Heart,
  Brain,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import {
  matchSkinConcerns,
  findProductAlternatives,
  generateBeautyRoutine,
  analyzeProductIngredients,
  type AlternativeProduct,
  type RoutineRecommendationResponse,
  type SkinConcernMatch,
  type IngredientAnalysisResponse,
} from '../utils/api';
import type { Product } from '../types';
import { PRODUCTS_DATA } from '../data/products';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  type?: 'text' | 'product_card' | 'routine' | 'alternatives' | 'concern_matches' | 'ingredients';
  data?: unknown;
}

const SUGGESTED_PROMPTS = [
  "Find a serum for oily skin",
  "Explain this product's ingredients",
  "Find a cheaper alternative",
  "Build an AM skincare routine",
  "Build a PM skincare routine",
  "Which serum is best for oily, acne-prone skin under ₹1000?",
];

const RoutineDisplay: React.FC<{ data: RoutineRecommendationResponse }> = ({ data }) => {
  if (!data || !data.steps) return null;
  return (
    <div className="space-y-3 pt-1">
      <div className="flex items-center justify-between gap-2 border-b border-rose-100 pb-2">
        <span className="text-xs font-semibold text-rose-700 uppercase tracking-wider">
          {data.routine_type} Routine • {data.skin_type} Skin
        </span>
        <span className="text-[10px] px-2 py-0.5 rounded-full bg-rose-50 text-rose-600 font-medium border border-rose-200">
          {data.generation_source === 'gemini_model' ? '🧠 AI Powered' : '⚡ Smart Rules'}
        </span>
      </div>

      <div className="space-y-2">
        {data.steps.map((step) => (
          <div key={step.step_number} className="p-2.5 rounded-xl bg-rose-50/60 border border-rose-100 text-xs">
            <div className="flex items-center justify-between mb-1">
              <span className="font-bold text-espresso-900">
                Step {step.step_number}: {step.step_name}
              </span>
              <span className="text-[10px] text-espresso-500">{step.frequency}</span>
            </div>
            {step.product_name && (
              <p className="font-medium text-rose-800">
                {step.product_name} {step.brand ? `by ${step.brand}` : ''}
              </p>
            )}
            <p className="text-espresso-600 mt-1">{step.usage_instructions}</p>
            {step.key_ingredients && step.key_ingredients.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-1.5">
                {step.key_ingredients.map((ing, i) => (
                  <span key={i} className="px-1.5 py-0.5 rounded bg-white text-[10px] text-espresso-700 border border-rose-100">
                    {ing}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {data.sunscreen_required && (
        <div className="p-2 rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-[11px] flex items-center gap-1.5">
          <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
          <span>Sunscreen SPF 50+ is mandatory for this routine.</span>
        </div>
      )}

      {data.total_estimated_cost ? (
        <p className="text-right text-xs font-semibold text-espresso-700">
          Estimated Total: ₹{data.total_estimated_cost.toLocaleString('en-IN')}
        </p>
      ) : null}
    </div>
  );
};

const AlternativesDisplay: React.FC<{
  data: { originalProduct: Product; alternatives: AlternativeProduct[] };
}> = ({ data }) => {
  if (!data || !data.alternatives) return null;
  const { originalProduct, alternatives } = data;
  return (
    <div className="space-y-3 pt-1">
      {originalProduct && (
        <div className="text-xs text-espresso-700 pb-1 border-b border-rose-100">
          Comparing alternatives to <span className="font-semibold text-espresso-900">{originalProduct.name}</span> (₹{originalProduct.price.toLocaleString('en-IN')})
        </div>
      )}

      <div className="space-y-2">
        {alternatives.map((alt, idx) => (
          <div key={idx} className="p-3 rounded-xl bg-rose-50/60 border border-rose-100 text-xs space-y-1.5">
            <div className="flex items-start justify-between gap-2">
              <div>
                <p className="font-bold text-espresso-900">{alt.alternative_product_name}</p>
                <p className="text-[11px] text-espresso-500">{alt.alternative_brand}</p>
              </div>
              <div className="text-right shrink-0">
                <span className="font-bold text-rose-600 text-sm">
                  ₹{(alt.alternative_price || 0).toLocaleString('en-IN')}
                </span>
                {alt.price_difference_pct != null && alt.price_difference_pct > 0 && (
                  <span className="block text-[10px] text-emerald-600 font-semibold">
                    Save {Math.round(alt.price_difference_pct)}%
                  </span>
                )}
              </div>
            </div>

            <p className="text-espresso-700 text-[11px] leading-relaxed">{alt.explanation}</p>

            {alt.matched_attributes && alt.matched_attributes.length > 0 && (
              <div className="flex flex-wrap gap-1 pt-1">
                {alt.matched_attributes.map((attr, i) => (
                  <span key={i} className="px-1.5 py-0.5 rounded bg-white text-[10px] text-espresso-600 border border-rose-100">
                    ✓ {attr}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

const ConcernMatchesDisplay: React.FC<{
  data: { concerns: string[]; skinType?: string; matches: SkinConcernMatch[] };
}> = ({ data }) => {
  if (!data || !data.matches) return null;
  const { concerns, skinType, matches } = data;
  return (
    <div className="space-y-3 pt-1">
      <div className="text-xs text-espresso-700 border-b border-rose-100 pb-1.5">
        Targeting: <span className="font-semibold text-rose-700">{concerns.join(', ')}</span>
        {skinType ? ` for ${skinType} skin` : ''}
      </div>

      <div className="space-y-2">
        {matches.map((item, idx) => (
          <div key={idx} className="p-2.5 rounded-xl bg-rose-50/60 border border-rose-100 text-xs space-y-1">
            <div className="flex items-start justify-between gap-2">
              <div>
                <p className="font-bold text-espresso-900">{item.product_name}</p>
                <p className="text-[11px] text-espresso-500">{item.brand} • {item.category}</p>
              </div>
              {item.price ? (
                <span className="font-semibold text-rose-600 shrink-0">
                  ₹{item.price.toLocaleString('en-IN')}
                </span>
              ) : null}
            </div>

            <p className="text-espresso-700 text-[11px] leading-relaxed">{item.explanation}</p>

            {item.matched_ingredients && item.matched_ingredients.length > 0 && (
              <div className="flex flex-wrap gap-1 pt-0.5">
                {item.matched_ingredients.map((ing, i) => (
                  <span key={i} className="px-1.5 py-0.5 rounded bg-white text-[10px] text-espresso-600 border border-rose-100">
                    {ing}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

const IngredientsDisplay: React.FC<{ data: IngredientAnalysisResponse }> = ({ data }) => {
  if (!data) return null;
  return (
    <div className="space-y-3 pt-1">
      <div className="flex items-center justify-between gap-2 border-b border-rose-100 pb-1.5">
        <span className="text-xs font-semibold text-espresso-900 truncate">
          {data.product_name}
        </span>
        <span className="text-[10px] px-2 py-0.5 rounded-full bg-rose-50 text-rose-600 font-medium border border-rose-200 shrink-0">
          {data.extraction_source === 'gemini_model' ? '🧠 AI Analyzed' : '⚡ Heuristic'}
        </span>
      </div>

      {data.key_actives && data.key_actives.length > 0 && (
        <div>
          <p className="text-[11px] font-bold text-rose-700 mb-1">Key Actives:</p>
          <div className="flex flex-wrap gap-1">
            {data.key_actives.map((act, i) => (
              <span key={i} className="px-2 py-0.5 rounded-full bg-rose-100/70 text-rose-800 text-[10px] font-medium">
                ★ {act}
              </span>
            ))}
          </div>
        </div>
      )}

      {data.ingredients && data.ingredients.length > 0 && (
        <div className="space-y-1.5 max-h-56 overflow-y-auto pr-1">
          {data.ingredients.slice(0, 8).map((ing, idx) => (
            <div key={idx} className="p-2 rounded-lg bg-rose-50/50 border border-rose-100 text-[11px]">
              <div className="flex justify-between items-center">
                <span className="font-semibold text-espresso-900">{ing.name}</span>
                <span className="text-[10px] text-espresso-500">{ing.function}</span>
              </div>
              {ing.benefits && ing.benefits.length > 0 && (
                <p className="text-espresso-600 text-[10px] mt-0.5">
                  Benefits: {ing.benefits.join(', ')}
                </p>
              )}
            </div>
          ))}
          {data.ingredients.length > 8 && (
            <p className="text-[10px] text-espresso-400 text-center pt-1">
              + {data.ingredients.length - 8} more ingredients
            </p>
          )}
        </div>
      )}

      {data.potential_conflicts && data.potential_conflicts.length > 0 && (
        <div className="p-2 rounded-lg bg-amber-50 border border-amber-200 text-[11px] text-amber-800 flex items-start gap-1.5">
          <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold">Potential Conflicts: </span>
            {data.potential_conflicts.join(', ')}
          </div>
        </div>
      )}
    </div>
  );
};

export const BeautyAssistantPage: React.FC = () => {
  const { user, openAuthModal } = useAuth();
  const navigate = useNavigate();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(true);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const addMessage = (message: Omit<ChatMessage, 'id' | 'timestamp'>) => {
    const newMessage: ChatMessage = {
      ...message,
      id: Math.random().toString(36).substring(2, 11),
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, newMessage]);
    setShowSuggestions(false);
  };

  const handleSuggestionClick = (prompt: string) => {
    setInput(prompt);
    inputRef.current?.focus();
  };

  const getBasicRoutine = (type: 'AM' | 'PM', skinType: string): string => {
    if (type === 'AM') {
      return `**AM Routine for ${skinType} skin:**
1. **Cleanse** - Gentle, pH-balanced cleanser
2. **Tone** - Hydrating toner (hyaluronic acid, ceramides)
3. **Treat** - Vitamin C serum (antioxidant protection)
4. **Moisturize** - Lightweight, non-comedogenic moisturizer
5. **☀️ SUNSCREEN SPF 50+** - **NON-NEGOTIABLE**`;
    }
    return `**PM Routine for ${skinType} skin:**
1. **Cleanse** - Double cleanse if wearing sunscreen/makeup
2. **Tone** - Hydrating/balancing toner
3. **Treat** - Retinol (2-3x/week) or AHA/BHA exfoliant
4. **Moisturize** - Richer night cream with barrier repair`;
  };

  const handleRoutineQuery = async (query: string): Promise<Omit<ChatMessage, 'id' | 'timestamp'>> => {
    const skinTypes = ['oily', 'dry', 'combination', 'normal', 'sensitive'];
    const concerns = ['acne', 'pigmentation', 'dullness', 'dryness', 'aging', 'pores', 'redness', 'sun damage'];

    let detectedSkinType = 'combination';
    const detectedConcerns: string[] = [];
    let routineType: 'AM' | 'PM' = 'AM';

    for (const st of skinTypes) {
      if (query.toLowerCase().includes(st)) {
        detectedSkinType = st;
        break;
      }
    }

    for (const c of concerns) {
      if (query.toLowerCase().includes(c)) {
        detectedConcerns.push(c);
      }
    }

    if (query.toLowerCase().includes('pm') || query.toLowerCase().includes('evening') || query.toLowerCase().includes('night')) {
      routineType = 'PM';
    } else if (query.toLowerCase().includes('am') || query.toLowerCase().includes('morning')) {
      routineType = 'AM';
    }

    const res = await generateBeautyRoutine(routineType, {
      skin_type: detectedSkinType,
      skin_concerns: detectedConcerns.length > 0 ? detectedConcerns : ['general'],
      budget_range: [300, 3000],
    });

    if (res.success && res.data) {
      const routine = res.data;
      return {
        role: 'assistant',
        content: `I've created a personalized ${routineType} routine for ${detectedSkinType} skin targeting ${detectedConcerns.join(', ') || 'general care'}:`,
        type: 'routine',
        data: routine,
      };
    }

    return {
      role: 'assistant',
      content: `I couldn't generate a routine right now. Here's a basic ${routineType} framework for ${detectedSkinType} skin:\n\n${getBasicRoutine(routineType, detectedSkinType)}`,
      type: 'text',
    };
  };

  const handleAlternativesQuery = async (query: string): Promise<Omit<ChatMessage, 'id' | 'timestamp'>> => {
    let matchedProduct: Product | undefined;

    for (const product of PRODUCTS_DATA) {
      if (query.toLowerCase().includes(product.name.toLowerCase()) ||
          query.toLowerCase().includes(product.brand.toLowerCase())) {
        matchedProduct = product;
        break;
      }
    }

    if (!matchedProduct) {
      return {
        role: 'assistant',
        content: `I'd love to help find alternatives! Could you specify which product you're looking to replace? For example:
• "Cheaper alternative to The Ordinary Niacinamide 10%"
• "Dupe for Minimalist 2% Salicylic Acid"
• "Affordable version of Plum Vitamin C Serum"`,
        type: 'text',
      };
    }

    const res = await findProductAlternatives(matchedProduct.id as unknown as number, {
      max_price_ratio: 0.8,
      min_similarity: 0.6,
    });

    if (res.success && res.data && res.data.alternatives.length > 0) {
      return {
        role: 'assistant',
        content: `Found ${res.data.alternatives.length} alternatives for ${matchedProduct.name} (${matchedProduct.brand}) priced at ₹${matchedProduct.price.toLocaleString('en-IN')}:`,
        type: 'alternatives',
        data: {
          originalProduct: matchedProduct,
          alternatives: res.data.alternatives.slice(0, 3),
        },
      };
    }

    return {
      role: 'assistant',
      content: `I couldn't find close alternatives for ${matchedProduct.name} within 80% of its price. You could try:
• Expanding the price range to 90-100%
• Lowering similarity threshold to 50%
• Checking if a different variant exists`,
      type: 'text',
    };
  };

  const handleConcernsQuery = async (query: string): Promise<Omit<ChatMessage, 'id' | 'timestamp'>> => {
    const concerns = ['acne', 'pigmentation', 'dryness', 'oily', 'dullness', 'sensitivity', 'dehydration', 'pores', 'aging', 'redness', 'sun damage'];
    const detected = concerns.filter((c) => query.toLowerCase().includes(c));

    if (detected.length === 0) {
      return {
        role: 'assistant',
        content: `I can help match products to specific skin concerns. Which concern would you like to address?

**Common concerns:**
• Acne & Breakouts
• Hyperpigmentation & Dark Spots
• Dryness & Dehydration
• Oily Skin & Excess Sebum
• Dullness & Uneven Tone
• Sensitivity & Redness
• Enlarged Pores
• Fine Lines & Aging`,
        type: 'text',
      };
    }

    let skinType: string | undefined;
    const skinTypes = ['oily', 'dry', 'combination', 'normal', 'sensitive'];
    for (const st of skinTypes) {
      if (query.toLowerCase().includes(st)) {
        skinType = st;
        break;
      }
    }

    const res = await matchSkinConcerns(detected, skinType, [300, 5000]);

    if (res.success && res.data && res.data.matches.length > 0) {
      const skinTypeSuffix = skinType ? ` for ${skinType} skin` : '';
      return {
        role: 'assistant',
        content: `Based on your concerns (${detected.join(', ')})${skinTypeSuffix}:`,
        type: 'concern_matches',
        data: {
          concerns: detected,
          skinType,
          matches: res.data.matches.slice(0, 4),
        },
      };
    }

    return {
      role: 'assistant',
      content: `I couldn't find specific product matches for ${detected.join(', ')} right now. This could be because:
• The catalog doesn't have products targeting these concerns
• Budget range is too narrow

Try adjusting your budget or let me know your price range!`,
      type: 'text',
    };
  };

  const handleIngredientsQuery = async (query: string): Promise<Omit<ChatMessage, 'id' | 'timestamp'>> => {
    let matchedProduct: Product | undefined;

    for (const product of PRODUCTS_DATA) {
      if (query.toLowerCase().includes(product.name.toLowerCase()) ||
          query.toLowerCase().includes(product.brand.toLowerCase())) {
        matchedProduct = product;
        break;
      }
    }

    if (!matchedProduct) {
      return {
        role: 'assistant',
        content: "I can analyze ingredients for any product in our catalog. Which product would you like me to analyze? For example:\n• \"Analyze ingredients in The Ordinary Niacinamide 10%\"\n• \"What's in Minimalist Vitamin C Serum?\"\n• \"Break down Plum Green Tea Moisturizer ingredients\"",
        type: 'text',
      };
    }

    const res = await analyzeProductIngredients(matchedProduct.id as unknown as number, false);

    if (res.success && res.data) {
      const analysis = res.data;
      const sourceBadge = analysis.extraction_source === 'gemini_model' ? '🧠 AI Analyzed' : '⚡ Heuristic Fallback';
      return {
        role: 'assistant',
        content: `**Ingredient Analysis for ${matchedProduct.name}** (${sourceBadge}):`,
        type: 'ingredients',
        data: analysis,
      };
    }

    return {
      role: 'assistant',
      content: `I couldn't analyze ${matchedProduct.name} right now. The product may not have detailed ingredient data in our catalog.`,
      type: 'text',
    };
  };

  const generateGeneralResponse = (_query: string): string => {
    return `I'm your PriceWise AI Beauty Assistant! I can help you with:

**🧴 Routine Building** - "Build an AM routine for oily skin with pigmentation"
**💰 Cheaper Alternatives** - "Find a dupe for The Ordinary Niacinamide"
**🎯 Skin Concern Matching** - "What products help with acne and dryness?"
**🔬 Ingredient Analysis** - "Analyze ingredients in Minimalist Vitamin C Serum"
**📚 General Beauty Q&A** - "Can I use Vitamin C and Retinol together?"

Try one of the suggested prompts below, or ask me anything about Indian beauty products, ingredients, routines, or price comparisons!`;
  };

  const processBeautyQuery = async (query: string): Promise<Omit<ChatMessage, 'id' | 'timestamp'>> => {
    const lowerQuery = query.toLowerCase();

    if (
      lowerQuery.includes('routine') ||
      lowerQuery.includes('am routine') ||
      lowerQuery.includes('pm routine') ||
      lowerQuery.includes('morning routine') ||
      lowerQuery.includes('evening routine') ||
      lowerQuery.includes('build a routine')
    ) {
      return await handleRoutineQuery(query);
    }

    if (
      lowerQuery.includes('cheaper') ||
      lowerQuery.includes('alternative') ||
      lowerQuery.includes('dupe') ||
      lowerQuery.includes('affordable') ||
      lowerQuery.includes('similar to') ||
      lowerQuery.includes('compare')
    ) {
      return await handleAlternativesQuery(query);
    }

    if (
      lowerQuery.includes('concern') ||
      lowerQuery.includes('acne') ||
      lowerQuery.includes('dry') ||
      lowerQuery.includes('pigment') ||
      lowerQuery.includes('dark spot') ||
      lowerQuery.includes('sensitive') ||
      lowerQuery.includes('dull') ||
      lowerQuery.includes('dehydrat') ||
      lowerQuery.includes('ingredient')
    ) {
      return await handleConcernsQuery(query);
    }

    if (
      lowerQuery.includes('analyze') ||
      lowerQuery.includes('what is in') ||
      lowerQuery.includes('contains')
    ) {
      return await handleIngredientsQuery(query);
    }

    return {
      role: 'assistant',
      content: generateGeneralResponse(query),
      type: 'text',
    };
  };

  const handleSend = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    if (!user) {
      openAuthModal('login');
      return;
    }

    const userMessage = input.trim();
    setInput('');
    setIsLoading(true);

    addMessage({ role: 'user', content: userMessage });

    try {
      const response = await processBeautyQuery(userMessage);
      addMessage(response);
    } catch {
      addMessage({
        role: 'assistant',
        content: 'I apologize, but I encountered an error processing your request. Please try again or rephrase your question.',
        type: 'text',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
  };

  const renderMessageContent = (msg: ChatMessage) => {
    switch (msg.type) {
      case 'routine':
        return <RoutineDisplay data={msg.data as RoutineRecommendationResponse} />;
      case 'alternatives':
        return <AlternativesDisplay data={msg.data as { originalProduct: Product; alternatives: AlternativeProduct[] }} />;
      case 'concern_matches':
        return <ConcernMatchesDisplay data={msg.data as { concerns: string[]; skinType?: string; matches: SkinConcernMatch[] }} />;
      case 'ingredients':
        return <IngredientsDisplay data={msg.data as IngredientAnalysisResponse} />;
      default:
        return <div className="prose prose-sm text-espresso-800 whitespace-pre-wrap">{msg.content}</div>;
    }
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-ivory flex items-center justify-center p-4">
        <div className="bg-white/80 border border-rose-200/80 rounded-3xl p-10 sm:p-14 shadow-soft-lift glass-panel max-w-xl w-full text-center">
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-rose-200 to-rose-400 mx-auto flex items-center justify-center text-ivory mb-5 shadow-xs">
            <MessageSquare className="w-8 h-8" />
          </div>
          <h2 className="font-editorial text-3xl font-bold text-espresso-900 mb-2">
            Beauty Assistant
          </h2>
          <p className="text-sm text-espresso-600 mb-8 leading-relaxed">
            Sign in to chat with your personal beauty intelligence assistant. Get personalized routine recommendations, ingredient analysis, cheaper alternatives, and skin concern matching.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            <button
              onClick={() => openAuthModal('login')}
              className="w-full sm:w-auto px-6 py-3 rounded-xl bg-rose-500 hover:bg-rose-600 text-ivory text-sm font-shadow md-shadow-md transition-all cursor-pointer"
            >
              Sign In to Chat
            </button>
            <button
              onClick={() => openAuthModal('register')}
              className="w-full sm:w-auto px-6 py-3 rounded-xl bg-white border border-rose-200 hover:border-rose-400 text-espresso-700 text-sm font-shadow md-shadow-md transition-all cursor-pointer"
            >
              Create Free Account
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-ivory flex flex-col">
      {/* Header */}
      <header className="border-b border-rose-100 bg-white/60 backdrop-blur-xs sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex items-center justify-between">
          <nav className="flex items-center space-x-2 text-xs text-espresso-500">
            <button
              onClick={() => navigate('/')}
              className="hover:text-rose-600 transition-colors flex items-center space-x-1 cursor-pointer"
            >
              <span>←</span>
              <span>Discovery</span>
            </button>
            <span>/</span>
            <span className="font-semibold text-espresso-800">Beauty Assistant</span>
          </nav>
        </div>
      </header>

      {/* Chat Area */}
      <main className="flex-1 max-w-4xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-6 flex flex-col">
        {/* Suggested Prompts */}
        {showSuggestions && messages.length === 0 && (
          <div className="mb-6 animate-fade-in">
            <p className="text-xs font-bold uppercase tracking-wider text-rose-600 mb-3">Try asking me</p>
            <div className="flex flex-wrap gap-2">
              {SUGGESTED_PROMPTS.map((prompt, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSuggestionClick(prompt)}
                  className="px-3.5 py-2 rounded-xl bg-white border border-rose-200 text-espresso-700 text-xs font-medium hover:bg-rose-50 hover:border-rose-300 transition-all text-left cursor-pointer"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto space-y-4 pb-4" id="chat-messages">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-3 animate-slide-up ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
            >
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                  msg.role === 'user'
                    ? 'bg-gradient-to-br from-rose-200 to-rose-400 text-ivory'
                    : 'bg-gradient-to-br from-rose-50 to-rose-100 text-rose-600 border border-rose-200'
                }`}
              >
                {msg.role === 'user' ? (
                  <Heart className="w-4 h-4" />
                ) : (
                  <Brain className="w-4 h-4" />
                )}
              </div>
              <div
                className={`max-w-[85%] p-4 rounded-2xl ${
                  msg.role === 'user'
                    ? 'bg-rose-500 text-ivory rounded-br-none'
                    : 'bg-white border border-rose-100 text-espresso-800 rounded-bl-none shadow-2xs'
                }`}
              >
                <div className="space-y-2">
                  {renderMessageContent(msg)}
                  <div className="flex items-center justify-end space-x-2 text-[10px] text-espresso-400 pt-1">
                    <span>{formatTime(msg.timestamp)}</span>
                    {msg.role === 'assistant' && (
                      <button
                        className="p-1 rounded hover:bg-rose-50 transition-colors cursor-pointer"
                        onClick={() => navigator.clipboard.writeText(msg.content)}
                        title="Copy"
                      >
                        <Copy className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex gap-3 animate-pulse">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-rose-50 to-rose-100 text-rose-600 border border-rose-200 flex items-center justify-center shrink-0">
                <Brain className="w-4 h-4" />
              </div>
              <div className="max-w-[85%] p-4 rounded-2xl bg-white border border-rose-100 rounded-bl-none shadow-2xs">
                <div className="space-y-2">
                  <div className="h-4 bg-rose-100 rounded w-3/4" />
                  <div className="h-4 bg-rose-100 rounded w-1/2" />
                  <div className="h-4 bg-rose-100 rounded w-2/3" />
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="border-t border-rose-100 pt-4 mt-auto">
          <form onSubmit={handleSend} className="space-y-2">
            <div className="flex items-end gap-2">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask me about routines, ingredients, alternatives, skin concerns..."
                className="flex-1 px-4 py-3 bg-white border border-rose-200 rounded-2xl text-sm text-espresso-900 placeholder-espresso-400 focus:outline-hidden focus:border-rose-400 resize-none min-h-[52px] max-h-32"
                rows={1}
                disabled={isLoading}
              />
              <button
                type="submit"
                disabled={!input.trim() || isLoading}
                className="p-3 rounded-xl bg-rose-500 hover:bg-rose-600 text-ivory disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-md flex-shrink-0 cursor-pointer"
                aria-label="Send message"
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
            <p className="text-xs text-espresso-400 text-center">
              Powered by Gemini AI • Heuristic fallback available • No medical advice
            </p>
          </form>
        </div>
      </main>
    </div>
  );
};
