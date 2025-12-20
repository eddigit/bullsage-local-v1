import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { useAuth } from "../App";
import { Button } from "../components/ui/button";
import { Card, CardContent } from "../components/ui/card";
import { Progress } from "../components/ui/progress";
import { Badge } from "../components/ui/badge";
import { ScrollArea } from "../components/ui/scroll-area";
import {
  ChevronRight,
  ChevronLeft,
  Check,
  Sparkles,
  Rocket
} from "lucide-react";

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Step indicator component
function StepIndicator({ currentStep, totalSteps }) {
  return (
    <div className="flex items-center justify-center gap-2 mb-8">
      {Array.from({ length: totalSteps }).map((_, index) => (
        <div
          key={index}
          className={`h-2 rounded-full transition-all duration-300 ${
            index === currentStep
              ? "w-8 bg-primary"
              : index < currentStep
              ? "w-2 bg-primary/60"
              : "w-2 bg-white/20"
          }`}
        />
      ))}
    </div>
  );
}

// Selection card component
function SelectionCard({ item, selected, onClick, size = "normal" }) {
  const isSelected = selected;
  
  return (
    <button
      onClick={onClick}
      className={`
        relative p-4 rounded-2xl border-2 transition-all duration-200 text-left w-full
        ${size === "small" ? "p-3" : "p-4"}
        ${isSelected 
          ? "border-primary bg-primary/10 shadow-lg shadow-primary/20" 
          : "border-white/10 bg-white/5 hover:border-white/20 hover:bg-white/10 active:scale-[0.98]"
        }
      `}
    >
      {isSelected && (
        <div className="absolute top-2 right-2 w-6 h-6 rounded-full bg-primary flex items-center justify-center">
          <Check className="w-4 h-4 text-black" />
        </div>
      )}
      <div className={`text-2xl mb-2 ${size === "small" ? "text-xl mb-1" : ""}`}>{item.icon}</div>
      <h3 className={`font-semibold ${size === "small" ? "text-sm" : ""}`}>{item.name}</h3>
      {item.description && (
        <p className={`text-muted-foreground mt-1 ${size === "small" ? "text-xs" : "text-sm"}`}>
          {item.description}
        </p>
      )}
      {item.symbol && (
        <Badge variant="outline" className="mt-2 text-xs">
          {item.symbol}
        </Badge>
      )}
    </button>
  );
}

// Step 1: Experience Level
function ExperienceStep({ options, value, onChange }) {
  return (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold mb-2">Quel est ton niveau ? 🎯</h2>
        <p className="text-muted-foreground">
          Dis-moi où tu en es, je m&apos;adapte à toi !
        </p>
      </div>
      
      <div className="grid gap-4">
        {options.map((level) => (
          <SelectionCard
            key={level.id}
            item={level}
            selected={value === level.id}
            onClick={() => onChange(level.id)}
          />
        ))}
      </div>
    </div>
  );
}

// Step 2: Markets
function MarketsStep({ options, values, onChange }) {
  const toggleMarket = (marketId) => {
    if (values.includes(marketId)) {
      onChange(values.filter(m => m !== marketId));
    } else {
      onChange([...values, marketId]);
    }
  };

  return (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold mb-2">Quels marchés t&apos;intéressent ? 📊</h2>
        <p className="text-muted-foreground">
          Sélectionne tous ceux qui te plaisent
        </p>
      </div>
      
      <div className="grid grid-cols-2 gap-3">
        {options.map((market) => (
          <SelectionCard
            key={market.id}
            item={market}
            selected={values.includes(market.id)}
            onClick={() => market.id !== "defi" && toggleMarket(market.id)}
            size="small"
          />
        ))}
      </div>
      
      <p className="text-xs text-center text-muted-foreground">
        Tu pourras modifier ça plus tard dans les paramètres
      </p>
    </div>
  );
}

// Step 3: Goals
function GoalsStep({ options, values, onChange }) {
  const toggleGoal = (goalId) => {
    if (values.includes(goalId)) {
      onChange(values.filter(g => g !== goalId));
    } else {
      onChange([...values, goalId]);
    }
  };

  return (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold mb-2">Quels sont tes objectifs ? 🎯</h2>
        <p className="text-muted-foreground">
          Que cherches-tu à accomplir ?
        </p>
      </div>
      
      <div className="space-y-3">
        {options.map((goal) => (
          <SelectionCard
            key={goal.id}
            item={goal}
            selected={values.includes(goal.id)}
            onClick={() => toggleGoal(goal.id)}
          />
        ))}
      </div>
    </div>
  );
}

// Step 4: Favorite Assets
function AssetsStep({ markets, allAssets, values, onChange }) {
  const toggleAsset = (marketId, assetId) => {
    const currentMarketAssets = values[marketId] || [];
    let newMarketAssets;
    
    if (currentMarketAssets.includes(assetId)) {
      newMarketAssets = currentMarketAssets.filter(a => a !== assetId);
    } else {
      newMarketAssets = [...currentMarketAssets, assetId];
    }
    
    onChange({
      ...values,
      [marketId]: newMarketAssets
    });
  };

  const marketLabels = {
    crypto: "🪙 Cryptomonnaies",
    forex: "💱 Forex",
    stocks: "📊 Actions",
    indices: "📈 Indices",
    commodities: "🥇 Matières Premières"
  };

  return (
    <div className="space-y-6">
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold mb-2">Tes actifs favoris ⭐</h2>
        <p className="text-muted-foreground">
          Sélectionne ceux que tu veux suivre
        </p>
      </div>
      
      <ScrollArea className="h-[400px] pr-4">
        {markets.map((marketId) => {
          const assets = allAssets[marketId] || [];
          if (assets.length === 0) return null;
          
          return (
            <div key={marketId} className="mb-6">
              <h3 className="font-semibold text-sm text-muted-foreground mb-3">
                {marketLabels[marketId] || marketId}
              </h3>
              <div className="grid grid-cols-2 gap-2">
                {assets.map((asset) => {
                  const isSelected = (values[marketId] || []).includes(asset.id);
                  return (
                    <button
                      key={asset.id}
                      onClick={() => toggleAsset(marketId, asset.id)}
                      className={`
                        flex items-center gap-2 p-3 rounded-xl border transition-all
                        ${isSelected 
                          ? "border-primary bg-primary/10" 
                          : "border-white/10 bg-white/5 hover:bg-white/10"
                        }
                      `}
                    >
                      {isSelected && <Check className="w-4 h-4 text-primary flex-shrink-0" />}
                      <span className="text-lg flex-shrink-0">{asset.icon || "📈"}</span>
                      <div className="text-left min-w-0">
                        <p className="font-medium text-sm truncate">{asset.name}</p>
                        <p className="text-xs text-muted-foreground">{asset.symbol}</p>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}
      </ScrollArea>
    </div>
  );
}

// Final Step: Summary
function SummaryStep({ data, options }) {
  const levelInfo = options?.experience_levels?.find(l => l.id === data.experience_level);
  
  return (
    <div className="space-y-6 text-center">
      <div className="w-20 h-20 mx-auto rounded-full bg-gradient-to-br from-primary to-emerald-400 flex items-center justify-center mb-4">
        <Rocket className="w-10 h-10 text-black" />
      </div>
      
      <div>
        <h2 className="text-2xl font-bold mb-2">Tu es prêt ! 🎉</h2>
        <p className="text-muted-foreground">
          Ton profil personnalisé est configuré
        </p>
      </div>
      
      <Card className="glass border-white/10 text-left">
        <CardContent className="p-4 space-y-4">
          <div className="flex items-center gap-3">
            <span className="text-2xl">{levelInfo?.icon}</span>
            <div>
              <p className="text-sm text-muted-foreground">Niveau</p>
              <p className="font-semibold">{levelInfo?.name}</p>
            </div>
          </div>
          
          <div>
            <p className="text-sm text-muted-foreground mb-2">Marchés sélectionnés</p>
            <div className="flex flex-wrap gap-2">
              {data.preferred_markets.map((m) => {
                const market = options?.markets?.find(x => x.id === m);
                return (
                  <Badge key={m} variant="outline" className="text-xs">
                    {market?.icon} {market?.name}
                  </Badge>
                );
              })}
            </div>
          </div>
          
          <div>
            <p className="text-sm text-muted-foreground mb-2">Objectifs</p>
            <div className="flex flex-wrap gap-2">
              {data.trading_goals.map((g) => {
                const goal = options?.goals?.find(x => x.id === g);
                return (
                  <Badge key={g} variant="outline" className="text-xs">
                    {goal?.icon} {goal?.name}
                  </Badge>
                );
              })}
            </div>
          </div>
        </CardContent>
      </Card>
      
      <div className="pt-4">
        <div className="flex items-center justify-center gap-2 text-primary">
          <Sparkles className="w-5 h-5" />
          <span className="font-medium">BULL SAGE est prêt pour toi !</span>
        </div>
      </div>
    </div>
  );
}

export default function OnboardingPage() {
  const navigate = useNavigate();
  const { user, updateUser } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [step, setStep] = useState(0);
  const [options, setOptions] = useState(null);
  
  // Form state
  const [experienceLevel, setExperienceLevel] = useState("");
  const [preferredMarkets, setPreferredMarkets] = useState([]);
  const [tradingGoals, setTradingGoals] = useState([]);
  const [favoriteAssets, setFavoriteAssets] = useState({});

  // Determine total steps based on markets selected
  const hasAssetStep = preferredMarkets.length > 0;
  const totalSteps = hasAssetStep ? 5 : 4;

  useEffect(() => {
    fetchOptions();
  }, []);

  const fetchOptions = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/onboarding/options`);
      setOptions(response.data);
    } catch (error) {
      console.error("Error fetching onboarding options:", error);
    } finally {
      setLoading(false);
    }
  };

  const canProceed = () => {
    switch (step) {
      case 0: return experienceLevel !== "";
      case 1: return preferredMarkets.length > 0;
      case 2: return tradingGoals.length > 0;
      case 3: return true; // Assets are optional
      case 4: return true; // Summary
      default: return false;
    }
  };

  const handleNext = () => {
    if (step < totalSteps - 1) {
      // Skip assets step if no markets with assets selected
      if (step === 2 && !hasAssetStep) {
        setStep(4);
      } else {
        setStep(step + 1);
      }
    }
  };

  const handleBack = () => {
    if (step > 0) {
      // Skip assets step when going back if no markets
      if (step === 4 && !hasAssetStep) {
        setStep(2);
      } else {
        setStep(step - 1);
      }
    }
  };

  const handleComplete = async () => {
    setSaving(true);
    try {
      const token = localStorage.getItem("token");
      const response = await axios.post(
        `${API_URL}/api/onboarding/complete`,
        {
          experience_level: experienceLevel,
          preferred_markets: preferredMarkets,
          trading_goals: tradingGoals,
          favorite_assets: favoriteAssets
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      // Update user in context
      if (updateUser && response.data.user) {
        updateUser(response.data.user);
      }
      
      // Redirect based on profile
      if (experienceLevel === "beginner" || tradingGoals.includes("learn")) {
        navigate("/academy");
      } else {
        navigate("/");
      }
    } catch (error) {
      console.error("Error completing onboarding:", error);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Préparation...</p>
        </div>
      </div>
    );
  }

  const getStepContent = () => {
    switch (step) {
      case 0:
        return (
          <ExperienceStep
            options={options?.experience_levels || []}
            value={experienceLevel}
            onChange={setExperienceLevel}
          />
        );
      case 1:
        return (
          <MarketsStep
            options={options?.markets || []}
            values={preferredMarkets}
            onChange={setPreferredMarkets}
          />
        );
      case 2:
        return (
          <GoalsStep
            options={options?.goals || []}
            values={tradingGoals}
            onChange={setTradingGoals}
          />
        );
      case 3:
        return (
          <AssetsStep
            markets={preferredMarkets}
            allAssets={options?.assets || {}}
            values={favoriteAssets}
            onChange={setFavoriteAssets}
          />
        );
      case 4:
        return (
          <SummaryStep
            data={{
              experience_level: experienceLevel,
              preferred_markets: preferredMarkets,
              trading_goals: tradingGoals,
              favorite_assets: favoriteAssets
            }}
            options={options}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <header className="p-4 flex items-center justify-between safe-area-top">
        <div className="flex items-center gap-2">
          <img src="/logo.png" alt="BULL SAGE" className="w-8 h-8 rounded-lg" />
          <span className="font-bold">BULL SAGE</span>
        </div>
        {step > 0 && (
          <Button variant="ghost" size="sm" onClick={handleBack}>
            <ChevronLeft className="w-4 h-4 mr-1" />
            Retour
          </Button>
        )}
      </header>

      {/* Progress */}
      <div className="px-4">
        <Progress value={((step + 1) / totalSteps) * 100} className="h-1" />
      </div>

      {/* Content */}
      <main className="flex-1 p-4 overflow-auto">
        <StepIndicator currentStep={step} totalSteps={totalSteps} />
        {getStepContent()}
      </main>

      {/* Footer */}
      <footer className="p-4 safe-area-bottom">
        {step < totalSteps - 1 ? (
          <Button
            onClick={handleNext}
            disabled={!canProceed()}
            className="w-full h-14 text-lg rounded-2xl bg-primary hover:bg-primary/90"
          >
            Continuer
            <ChevronRight className="w-5 h-5 ml-2" />
          </Button>
        ) : (
          <Button
            onClick={handleComplete}
            disabled={saving}
            className="w-full h-14 text-lg rounded-2xl bg-gradient-to-r from-primary to-emerald-400 hover:opacity-90"
          >
            {saving ? (
              <>
                <div className="w-5 h-5 border-2 border-black border-t-transparent rounded-full animate-spin mr-2" />
                Préparation...
              </>
            ) : (
              <>
                <Rocket className="w-5 h-5 mr-2" />
                C&apos;est parti !
              </>
            )}
          </Button>
        )}
      </footer>
    </div>
  );
}
