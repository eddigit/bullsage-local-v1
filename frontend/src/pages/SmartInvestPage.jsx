import { useState, useEffect } from "react";
import { API, useAuth } from "../App";
import axios from "axios";
import { toast } from "sonner";
import { Link } from "react-router-dom";
import {
  Zap,
  DollarSign,
  TrendingUp,
  ArrowRight,
  Loader2,
  CheckCircle,
  Target,
  Brain,
  Sparkles,
  RefreshCw,
  AlertTriangle,
  ArrowUpRight,
  Shield,
  Clock,
  BarChart3,
  Rocket,
  PartyPopper
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import { Progress } from "../components/ui/progress";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "../components/ui/dialog";

const INVESTMENT_PRESETS = [
  { amount: 20, label: "20€", description: "Petit investissement" },
  { amount: 50, label: "50€", description: "Investissement modéré" },
  { amount: 100, label: "100€", description: "Investissement standard" },
  { amount: 250, label: "250€", description: "Investissement sérieux" },
  { amount: 500, label: "500€", description: "Gros investissement" },
];

export default function SmartInvestPage() {
  const { user } = useAuth();
  const [step, setStep] = useState(1);
  const [investmentAmount, setInvestmentAmount] = useState("");
  const [customAmount, setCustomAmount] = useState("");
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [recommendation, setRecommendation] = useState(null);
  const [executing, setExecuting] = useState(false);
  const [executionResult, setExecutionResult] = useState(null);
  const [showSuccessDialog, setShowSuccessDialog] = useState(false);

  const formatPrice = (price) => {
    if (!price) return "$0.00";
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: price < 1 ? 6 : 2,
      maximumFractionDigits: price < 1 ? 6 : 2
    }).format(price);
  };

  const handleAmountSelect = (amount) => {
    setInvestmentAmount(amount);
    setCustomAmount("");
  };

  const handleCustomAmount = (value) => {
    setCustomAmount(value);
    setInvestmentAmount(parseFloat(value) || 0);
  };

  const getSmartRecommendation = async () => {
    const amount = investmentAmount || parseFloat(customAmount);
    if (!amount || amount < 10) {
      toast.error("Montant minimum: 10€");
      return;
    }

    setAnalyzing(true);
    setAnalysisProgress(0);
    setStep(2);

    // Simulate analysis progress
    const progressInterval = setInterval(() => {
      setAnalysisProgress(prev => {
        if (prev >= 90) return prev;
        return prev + Math.random() * 15;
      });
    }, 500);

    try {
      const response = await axios.post(`${API}/smart-invest/analyze`, {
        investment_amount: amount
      });

      clearInterval(progressInterval);
      setAnalysisProgress(100);
      
      await new Promise(resolve => setTimeout(resolve, 500));
      
      if (response.data.error) {
        toast.error(response.data.error);
        setStep(1);
      } else {
        setRecommendation(response.data);
        setStep(3);
      }
    } catch (error) {
      clearInterval(progressInterval);
      console.error("Analysis error:", error);
      toast.error("Erreur lors de l'analyse - réessayez");
      setStep(1);
    } finally {
      setAnalyzing(false);
    }
  };

  const executeInvestment = async () => {
    if (!recommendation) return;
    
    setExecuting(true);
    try {
      const response = await axios.post(`${API}/smart-invest/execute`, {
        coin_id: recommendation.coin_id,
        amount_usd: investmentAmount,
        entry_price: recommendation.current_price
      });

      if (response.data.success) {
        setExecutionResult(response.data);
        setShowSuccessDialog(true);
        toast.success("🎉 Investissement exécuté avec succès!");
      } else {
        toast.error(response.data.error || "Erreur lors de l'exécution");
      }
    } catch (error) {
      console.error("Execution error:", error);
      toast.error("Erreur lors de l'exécution du trade");
    } finally {
      setExecuting(false);
    }
  };

  const resetFlow = () => {
    setStep(1);
    setInvestmentAmount("");
    setCustomAmount("");
    setRecommendation(null);
    setExecutionResult(null);
    setShowSuccessDialog(false);
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="text-center py-6">
        <div className="inline-flex items-center justify-center p-3 bg-gradient-to-r from-violet-600 to-fuchsia-600 rounded-2xl mb-4">
          <Zap className="w-8 h-8 text-white" />
        </div>
        <h1 className="text-3xl md:text-4xl font-bold mb-2">
          🎯 Smart Invest
        </h1>
        <p className="text-muted-foreground max-w-md mx-auto">
          L&apos;IA BULL analyse le marché et investit pour vous au meilleur moment
        </p>
      </div>

      {/* Progress Steps */}
      <div className="flex items-center justify-center gap-2 mb-8">
        {[1, 2, 3].map((s) => (
          <div key={s} className="flex items-center">
            <div className={`
              w-10 h-10 rounded-full flex items-center justify-center font-bold transition-all
              ${step >= s 
                ? "bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white" 
                : "bg-white/10 text-muted-foreground"
              }
            `}>
              {step > s ? <CheckCircle className="w-5 h-5" /> : s}
            </div>
            {s < 3 && (
              <div className={`w-12 md:w-24 h-1 mx-2 rounded ${step > s ? "bg-violet-600" : "bg-white/10"}`} />
            )}
          </div>
        ))}
      </div>

      {/* Step 1: Choose Amount */}
      {step === 1 && (
        <Card className="glass border-white/10">
          <CardHeader className="text-center">
            <CardTitle className="flex items-center justify-center gap-2">
              <DollarSign className="w-5 h-5 text-emerald-500" />
              Combien souhaitez-vous investir ?
            </CardTitle>
            <CardDescription>
              Choisissez un montant prédéfini ou entrez un montant personnalisé
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Preset Amounts */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              {INVESTMENT_PRESETS.map((preset) => (
                <button
                  key={preset.amount}
                  onClick={() => handleAmountSelect(preset.amount)}
                  className={`
                    p-4 rounded-xl border-2 transition-all
                    ${investmentAmount === preset.amount && !customAmount
                      ? "border-violet-500 bg-violet-500/20"
                      : "border-white/10 hover:border-violet-500/50 hover:bg-white/5"
                    }
                  `}
                >
                  <p className="text-2xl font-bold">{preset.label}</p>
                  <p className="text-xs text-muted-foreground">{preset.description}</p>
                </button>
              ))}
            </div>

            {/* Custom Amount */}
            <div className="flex items-center gap-4">
              <div className="flex-1 h-px bg-white/10" />
              <span className="text-sm text-muted-foreground">ou</span>
              <div className="flex-1 h-px bg-white/10" />
            </div>

            <div className="flex items-center gap-3">
              <div className="relative flex-1">
                <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                <Input
                  type="number"
                  placeholder="Montant personnalisé"
                  value={customAmount}
                  onChange={(e) => handleCustomAmount(e.target.value)}
                  className="pl-10 bg-black/20 border-white/10 text-lg h-14"
                  min="10"
                />
              </div>
              <span className="text-muted-foreground">EUR</span>
            </div>

            {/* Info Box */}
            <div className="p-4 rounded-lg bg-violet-500/10 border border-violet-500/20">
              <div className="flex items-start gap-3">
                <Shield className="w-5 h-5 text-violet-400 mt-0.5" />
                <div>
                  <p className="font-medium text-violet-300">Mode Paper Trading</p>
                  <p className="text-sm text-muted-foreground">
                    Cet investissement sera simulé en Paper Trading. Aucun argent réel ne sera utilisé.
                  </p>
                </div>
              </div>
            </div>

            {/* CTA Button */}
            <Button
              onClick={getSmartRecommendation}
              disabled={!investmentAmount && !customAmount}
              className="w-full h-14 text-lg bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-500 hover:to-fuchsia-500"
            >
              <Brain className="w-5 h-5 mr-2" />
              Analyser le marché
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Step 2: Analyzing */}
      {step === 2 && (
        <Card className="glass border-white/10">
          <CardContent className="py-12">
            <div className="text-center space-y-6">
              <div className="relative inline-flex">
                <div className="w-24 h-24 rounded-full bg-gradient-to-r from-violet-600 to-fuchsia-600 flex items-center justify-center animate-pulse">
                  <Brain className="w-12 h-12 text-white" />
                </div>
                <div className="absolute inset-0 rounded-full bg-gradient-to-r from-violet-600 to-fuchsia-600 animate-ping opacity-20" />
              </div>
              
              <div>
                <h3 className="text-xl font-bold mb-2">BULL analyse le marché...</h3>
                <p className="text-muted-foreground">
                  Analyse de {user?.watchlist?.length || 5}+ actifs en cours
                </p>
              </div>

              <div className="max-w-md mx-auto space-y-2">
                <Progress value={analysisProgress} className="h-3" />
                <p className="text-sm text-muted-foreground">{Math.round(analysisProgress)}%</p>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div className={`p-3 rounded-lg ${analysisProgress > 20 ? "bg-emerald-500/20" : "bg-white/5"}`}>
                  <CheckCircle className={`w-4 h-4 mx-auto mb-1 ${analysisProgress > 20 ? "text-emerald-500" : "text-muted-foreground"}`} />
                  <span>RSI</span>
                </div>
                <div className={`p-3 rounded-lg ${analysisProgress > 40 ? "bg-emerald-500/20" : "bg-white/5"}`}>
                  <CheckCircle className={`w-4 h-4 mx-auto mb-1 ${analysisProgress > 40 ? "text-emerald-500" : "text-muted-foreground"}`} />
                  <span>MACD</span>
                </div>
                <div className={`p-3 rounded-lg ${analysisProgress > 60 ? "bg-emerald-500/20" : "bg-white/5"}`}>
                  <CheckCircle className={`w-4 h-4 mx-auto mb-1 ${analysisProgress > 60 ? "text-emerald-500" : "text-muted-foreground"}`} />
                  <span>Bollinger</span>
                </div>
                <div className={`p-3 rounded-lg ${analysisProgress > 80 ? "bg-emerald-500/20" : "bg-white/5"}`}>
                  <CheckCircle className={`w-4 h-4 mx-auto mb-1 ${analysisProgress > 80 ? "text-emerald-500" : "text-muted-foreground"}`} />
                  <span>Tendance</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 3: Recommendation */}
      {step === 3 && recommendation && (
        <div className="space-y-4">
          {/* Main Recommendation Card */}
          <Card className="glass border-2 border-emerald-500/30 overflow-hidden">
            <div className="bg-gradient-to-r from-emerald-600/20 to-teal-600/20 p-4 border-b border-emerald-500/20">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-emerald-400" />
                  <span className="font-bold text-emerald-400">RECOMMANDATION IA</span>
                </div>
                <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30">
                  Confiance: {recommendation.confidence}
                </Badge>
              </div>
            </div>
            
            <CardContent className="pt-6">
              <div className="flex flex-col md:flex-row items-center gap-6">
                {/* Coin Info */}
                <div className="text-center md:text-left">
                  <div className="flex items-center gap-3 mb-2">
                    <div className="w-16 h-16 rounded-full bg-gradient-to-r from-amber-500 to-orange-500 flex items-center justify-center text-2xl">
                      {recommendation.coin_id === "bitcoin" ? "₿" : 
                       recommendation.coin_id === "ethereum" ? "Ξ" : "◎"}
                    </div>
                    <div>
                      <h2 className="text-2xl font-bold capitalize">{recommendation.name}</h2>
                      <p className="text-muted-foreground">{recommendation.symbol?.toUpperCase()}</p>
                    </div>
                  </div>
                </div>

                {/* Arrow */}
                <ArrowRight className="w-8 h-8 text-emerald-500 hidden md:block" />

                {/* Investment Details */}
                <div className="flex-1 grid grid-cols-2 gap-4">
                  <div className="p-4 rounded-lg bg-white/5 text-center">
                    <p className="text-xs text-muted-foreground mb-1">Prix actuel</p>
                    <p className="text-xl font-bold font-mono">{formatPrice(recommendation.current_price)}</p>
                  </div>
                  <div className="p-4 rounded-lg bg-white/5 text-center">
                    <p className="text-xs text-muted-foreground mb-1">Vous obtenez</p>
                    <p className="text-xl font-bold font-mono text-emerald-400">
                      {recommendation.quantity_to_buy?.toFixed(6)} {recommendation.symbol?.toUpperCase()}
                    </p>
                  </div>
                </div>
              </div>

              {/* Analysis Summary */}
              <div className="mt-6 p-4 rounded-lg bg-black/30 space-y-3">
                <h4 className="font-semibold flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-violet-400" />
                  Pourquoi {recommendation.name} ?
                </h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <div className="p-2 rounded bg-white/5 text-center">
                    <p className="text-xs text-muted-foreground">RSI</p>
                    <p className={`font-bold ${recommendation.indicators?.rsi < 40 ? "text-emerald-500" : "text-amber-500"}`}>
                      {recommendation.indicators?.rsi?.toFixed(1)}
                    </p>
                  </div>
                  <div className="p-2 rounded bg-white/5 text-center">
                    <p className="text-xs text-muted-foreground">Score</p>
                    <p className={`font-bold ${recommendation.score > 0 ? "text-emerald-500" : "text-rose-500"}`}>
                      {recommendation.score > 0 ? "+" : ""}{recommendation.score}
                    </p>
                  </div>
                  <div className="p-2 rounded bg-white/5 text-center">
                    <p className="text-xs text-muted-foreground">Tendance</p>
                    <p className="font-bold text-xs capitalize">{recommendation.indicators?.trend || "N/A"}</p>
                  </div>
                  <div className="p-2 rounded bg-white/5 text-center">
                    <p className="text-xs text-muted-foreground">24h</p>
                    <p className={`font-bold ${recommendation.change_24h >= 0 ? "text-emerald-500" : "text-rose-500"}`}>
                      {recommendation.change_24h >= 0 ? "+" : ""}{recommendation.change_24h?.toFixed(2)}%
                    </p>
                  </div>
                </div>
                
                {/* Reasons */}
                <div className="space-y-1">
                  {recommendation.reasons?.slice(0, 3).map((reason, idx) => (
                    <div key={idx} className="flex items-center gap-2 text-sm">
                      <CheckCircle className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                      <span>{reason}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Target Levels */}
              {recommendation.levels && (
                <div className="mt-4 grid grid-cols-3 gap-3">
                  <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-center">
                    <p className="text-xs text-rose-400">Stop Loss</p>
                    <p className="font-mono font-bold">{formatPrice(recommendation.levels.stop_loss)}</p>
                    <p className="text-xs text-muted-foreground">
                      {(((recommendation.levels.stop_loss - recommendation.current_price) / recommendation.current_price) * 100).toFixed(1)}%
                    </p>
                  </div>
                  <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-center">
                    <p className="text-xs text-emerald-400">Target 1</p>
                    <p className="font-mono font-bold">{formatPrice(recommendation.levels.take_profit_1)}</p>
                    <p className="text-xs text-muted-foreground">
                      +{(((recommendation.levels.take_profit_1 - recommendation.current_price) / recommendation.current_price) * 100).toFixed(1)}%
                    </p>
                  </div>
                  <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-center">
                    <p className="text-xs text-emerald-400">Target 2</p>
                    <p className="font-mono font-bold">{formatPrice(recommendation.levels.take_profit_2)}</p>
                    <p className="text-xs text-muted-foreground">
                      +{(((recommendation.levels.take_profit_2 - recommendation.current_price) / recommendation.current_price) * 100).toFixed(1)}%
                    </p>
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="mt-6 flex flex-col md:flex-row gap-3">
                <Button
                  onClick={executeInvestment}
                  disabled={executing}
                  className="flex-1 h-14 text-lg bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500"
                >
                  {executing ? (
                    <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  ) : (
                    <Rocket className="w-5 h-5 mr-2" />
                  )}
                  Investir {investmentAmount}€ maintenant
                </Button>
                <Button
                  onClick={resetFlow}
                  variant="outline"
                  className="border-white/10 hover:bg-white/5"
                >
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Recommencer
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Risk Warning */}
          <div className="p-4 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-amber-400">Avertissement</p>
              <p className="text-sm text-muted-foreground">
                Les performances passées ne garantissent pas les résultats futurs. 
                Le trading comporte des risques. Ce mode utilise le Paper Trading (simulation).
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Success Dialog */}
      <Dialog open={showSuccessDialog} onOpenChange={setShowSuccessDialog}>
        <DialogContent className="glass border-white/10 text-center">
          <div className="py-6">
            <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-gradient-to-r from-emerald-500 to-teal-500 flex items-center justify-center">
              <PartyPopper className="w-10 h-10 text-white" />
            </div>
            <DialogHeader>
              <DialogTitle className="text-2xl">🎉 Investissement Réussi !</DialogTitle>
              <DialogDescription className="space-y-4 pt-4">
                <p>
                  Vous avez investi <strong>{investmentAmount}€</strong> dans <strong className="capitalize">{recommendation?.name}</strong>
                </p>
                {executionResult && (
                  <div className="p-4 rounded-lg bg-white/5 text-left space-y-2">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Quantité:</span>
                      <span className="font-mono font-bold">{executionResult.quantity?.toFixed(6)} {recommendation?.symbol?.toUpperCase()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Prix d&apos;entrée:</span>
                      <span className="font-mono">{formatPrice(executionResult.entry_price)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Nouveau solde:</span>
                      <span className="font-mono">{formatPrice(executionResult.new_balance)}</span>
                    </div>
                  </div>
                )}
              </DialogDescription>
            </DialogHeader>
            <div className="flex flex-col gap-2 mt-6">
              <Link to="/paper-trading" className="w-full">
                <Button className="w-full bg-violet-600 hover:bg-violet-700">
                  Voir mon Portfolio
                </Button>
              </Link>
              <Button variant="outline" onClick={resetFlow} className="border-white/10">
                Nouvel investissement
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
