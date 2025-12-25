import { useState, useEffect, useRef } from "react";
import { useAuth, API } from "../App";
import axios from "axios";
import { toast } from "sonner";
import {
  Target,
  TrendingUp,
  TrendingDown,
  Activity,
  BarChart3,
  Clock,
  Zap,
  RefreshCw,
  Loader2,
  Volume2,
  VolumeX,
  AlertTriangle,
  CheckCircle,
  XCircle,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
  ChevronUp,
  ChevronDown,
  Crosshair,
  Gauge,
  LineChart,
  HelpCircle,
  Info,
  Globe,
  Newspaper
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Progress } from "../components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "../components/ui/tooltip";

// Tooltips content for education
const TOOLTIPS = {
  rsi: {
    title: "RSI (Relative Strength Index)",
    content: "Mesure la vitesse et l'amplitude des mouvements de prix. RSI < 30 = survente (signal d'achat potentiel). RSI > 70 = surachat (signal de vente potentiel)."
  },
  macd: {
    title: "MACD (Moving Average Convergence Divergence)",
    content: "Indicateur de momentum qui montre la relation entre deux moyennes mobiles. Un MACD positif indique une tendance haussière, négatif = baissière."
  },
  bollinger: {
    title: "Bandes de Bollinger",
    content: "Mesure la volatilité du marché. Prix près de la bande haute = surachat. Prix près de la bande basse = survente. Utile pour identifier les retournements."
  },
  ma: {
    title: "Moyennes Mobiles (MA)",
    content: "Lissent les données de prix. MA20 > MA50 > MA200 = tendance haussière forte. L'inverse = tendance baissière. Croisements = signaux de trading."
  },
  support: {
    title: "Support",
    content: "Niveau de prix où la demande est suffisamment forte pour empêcher le prix de baisser davantage. Bon niveau pour placer des ordres d'achat."
  },
  resistance: {
    title: "Résistance", 
    content: "Niveau de prix où l'offre est suffisamment forte pour empêcher le prix de monter davantage. Bon niveau pour prendre des profits."
  },
  entry: {
    title: "Prix d'Entrée",
    content: "Prix recommandé pour ouvrir votre position. Basé sur l'analyse des niveaux de support/résistance et des indicateurs techniques."
  },
  stopLoss: {
    title: "Stop-Loss (SL)",
    content: "Niveau de prix où vous devez couper vos pertes. ESSENTIEL pour la gestion du risque. Ne jamais trader sans stop-loss !"
  },
  takeProfit: {
    title: "Take-Profit (TP)",
    content: "Niveau de prix où vous prenez vos gains. TP1 = objectif conservateur (prendre une partie). TP2 = objectif optimiste (laisser courir)."
  },
  scalping: {
    title: "Scalping (1H)",
    content: "Trades très courts (minutes à heures). Petits gains fréquents. Nécessite une grande attention et des frais bas. Risque élevé."
  },
  intraday: {
    title: "Intraday (4H)",
    content: "Positions ouvertes et fermées dans la journée. Équilibre entre fréquence et taille des gains. Bon pour les traders actifs."
  },
  swing: {
    title: "Swing Trading (1D)",
    content: "Positions tenues plusieurs jours à semaines. Capture les mouvements de prix plus importants. Moins stressant, adapté aux débutants."
  },
  confidence: {
    title: "Niveau de Confiance",
    content: "HIGH = plusieurs indicateurs alignés, signal fort. MEDIUM = signal modéré, prudence. LOW = signaux contradictoires, attendre."
  },
  candlesticks: {
    title: "Patterns Chandeliers",
    content: "Formations de prix qui prédisent les mouvements futurs. Doji = indécision. Marteau = retournement haussier. Étoile filante = retournement baissier."
  },
  fearGreed: {
    title: "Fear & Greed Index",
    content: "Mesure le sentiment du marché crypto (0-100). <25 = Peur Extrême (opportunité d'achat). >75 = Cupidité Extrême (prudence/vente). Indicateur contrarien."
  },
  vix: {
    title: "VIX (Indice de Volatilité)",
    content: "Mesure la volatilité attendue du S&P 500. VIX élevé (>25) = marché nerveux, risque élevé. VIX bas (<15) = marché calme. Influence les cryptos."
  },
  fedRate: {
    title: "Taux Directeur Fed",
    content: "Taux d'intérêt de la Réserve Fédérale US. Taux élevé = dollar fort, actifs risqués sous pression. Taux bas = liquidité, favorable aux cryptos."
  },
  eurusd: {
    title: "EUR/USD",
    content: "Taux de change Euro/Dollar. EUR/USD haut = dollar faible = généralement positif pour Bitcoin. Indicateur de la force du dollar."
  },
  unemployment: {
    title: "Taux de Chômage US",
    content: "Indicateur de santé économique. Chômage bas = économie forte. Chômage élevé = récession possible, la Fed pourrait baisser les taux (positif crypto)."
  }
};

// Reusable Tooltip component
const InfoTooltip = ({ tooltipKey, children, className = "" }) => {
  const tip = TOOLTIPS[tooltipKey];
  if (!tip) return children;
  
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span className={`inline-flex items-center gap-1 cursor-help ${className}`}>
          {children}
          <HelpCircle className="w-3.5 h-3.5 text-muted-foreground/50 hover:text-primary transition-colors" />
        </span>
      </TooltipTrigger>
      <TooltipContent side="top" className="max-w-xs bg-black/95 border-white/10 p-3">
        <p className="font-semibold text-primary mb-1">{tip.title}</p>
        <p className="text-xs text-muted-foreground leading-relaxed">{tip.content}</p>
      </TooltipContent>
    </Tooltip>
  );
};

const TIMEFRAMES = [
  { value: "1h", label: "1H", description: "Scalping", icon: Zap, tooltip: "scalping" },
  { value: "4h", label: "4H", description: "Intraday", icon: Clock, tooltip: "intraday" },
  { value: "daily", label: "1D", description: "Swing", icon: Target, tooltip: "swing" },
];

const TRADING_STYLES = [
  { value: "scalping", label: "Scalping", description: "Trades rapides, petits gains" },
  { value: "intraday", label: "Intraday", description: "Dans la journée" },
  { value: "swing", label: "Swing Trading", description: "Quelques jours" },
];

const formatPrice = (price) => {
  if (!price) return "$0.00";
  if (price >= 1000) return `$${price.toLocaleString("en-US", { maximumFractionDigits: 2 })}`;
  if (price >= 1) return `$${price.toFixed(2)}`;
  return `$${price.toFixed(6)}`;
};

const formatPercent = (value) => {
  if (!value && value !== 0) return "0.00%";
  const formatted = Math.abs(value).toFixed(2);
  return value >= 0 ? `+${formatted}%` : `-${formatted}%`;
};

// Alert sound
const playAlertSound = () => {
  try {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    oscillator.frequency.value = 800;
    oscillator.type = "sine";
    gainNode.gain.value = 0.3;
    
    oscillator.start();
    
    // Create a pleasant "ding" pattern
    setTimeout(() => { oscillator.frequency.value = 1000; }, 100);
    setTimeout(() => { oscillator.frequency.value = 1200; }, 200);
    setTimeout(() => { 
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
      setTimeout(() => oscillator.stop(), 300);
    }, 300);
  } catch (e) {
    console.log("Audio not supported");
  }
};

const RSIGauge = ({ value }) => {
  const getColor = () => {
    if (value < 30) return "text-emerald-500";
    if (value > 70) return "text-rose-500";
    return "text-yellow-500";
  };
  
  const getLabel = () => {
    if (value < 30) return "SURVENTE";
    if (value > 70) return "SURACHAT";
    if (value < 45) return "Bas";
    if (value > 55) return "Haut";
    return "Neutre";
  };

  return (
    <div className="text-center">
      <div className="relative w-24 h-24 mx-auto">
        <svg className="w-24 h-24 transform -rotate-90" viewBox="0 0 100 100">
          <circle
            cx="50" cy="50" r="40"
            fill="none"
            stroke="rgba(255,255,255,0.1)"
            strokeWidth="8"
          />
          <circle
            cx="50" cy="50" r="40"
            fill="none"
            stroke="currentColor"
            strokeWidth="8"
            strokeDasharray={`${(value / 100) * 251.2} 251.2`}
            className={getColor()}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center flex-col">
          <span className={`text-2xl font-bold font-mono ${getColor()}`}>{value}</span>
        </div>
      </div>
      <p className={`text-xs font-medium mt-1 ${getColor()}`}>{getLabel()}</p>
    </div>
  );
};

export default function TradingModePage() {
  const { user } = useAuth();
  const [markets, setMarkets] = useState([]);
  const [selectedCoin, setSelectedCoin] = useState(null);
  const [timeframe, setTimeframe] = useState("4h");
  const [tradingStyle, setTradingStyle] = useState("swing");
  const [analysis, setAnalysis] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [alerts, setAlerts] = useState([]);
  const [marketContext, setMarketContext] = useState(null);
  const [loadingContext, setLoadingContext] = useState(false);
  
  // Fetch global market context
  const fetchMarketContext = async () => {
    setLoadingContext(true);
    try {
      const [fearGreedRes, macroRes, newsRes, forexRes] = await Promise.all([
        axios.get(`${API}/market/fear-greed`).catch(() => ({ data: null })),
        axios.get(`${API}/market/macro-overview`).catch(() => ({ data: null })),
        axios.get(`${API}/market/news?category=crypto`).catch(() => ({ data: [] })),
        axios.get(`${API}/market/forex/EUR/USD`).catch(() => ({ data: null }))
      ]);
      
      const newsData = Array.isArray(newsRes.data) ? newsRes.data : [];
      setMarketContext({
        fearGreed: fearGreedRes.data?.data?.[0] || null,
        macro: macroRes.data || null,
        news: newsData.slice(0, 5),
        eurusd: forexRes.data?.["Realtime Currency Exchange Rate"] || null
      });
    } catch (error) {
      console.error("Error fetching market context:", error);
    } finally {
      setLoadingContext(false);
    }
  };

  // Fetch news impact
  const [newsImpact, setNewsImpact] = useState(null);
  const [loadingNews, setLoadingNews] = useState(false);
  
  const fetchNewsImpact = async () => {
    setLoadingNews(true);
    try {
      const response = await axios.get(`${API}/market/news-impact`);
      setNewsImpact(response.data);
    } catch (error) {
      console.error("Error fetching news impact:", error);
    } finally {
      setLoadingNews(false);
    }
  };
  
  // Fetch watchlist coins
  useEffect(() => {
    const fetchMarkets = async () => {
      try {
        const response = await axios.get(`${API}/market/crypto`);
        const marketsData = Array.isArray(response.data) ? response.data : [];
        setMarkets(marketsData);
        
        // Auto-select first watchlist coin
        if (user?.watchlist?.length > 0 && marketsData.length > 0) {
          const firstWatchlistCoin = marketsData.find(c => c.id === user.watchlist[0]);
          if (firstWatchlistCoin) {
            setSelectedCoin(firstWatchlistCoin);
          }
        }
      } catch (error) {
        console.error("Error fetching markets:", error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchMarkets();
    fetchMarketContext();
    fetchNewsImpact(); // Load news impact on mount
  }, [user]);

  // Filter watchlist coins
  const watchlistCoins = markets.filter(coin => 
    user?.watchlist?.includes(coin.id)
  );

  // Analyze selected coin
  const analyzeNow = async () => {
    if (!selectedCoin) {
      toast.error("Sélectionnez une crypto d'abord");
      return;
    }
    
    setAnalyzing(true);
    setAnalysis(null);
    
    try {
      const response = await axios.post(`${API}/trading/analyze`, {
        coin_id: selectedCoin.id,
        timeframe: timeframe,
        trading_style: tradingStyle
      });
      
      setAnalysis(response.data);
      
      // Play sound if alert-worthy
      if (response.data.is_alert && soundEnabled) {
        playAlertSound();
        toast.success(`Signal ${response.data.recommendation.action} détecté !`, {
          duration: 5000
        });
      }
    } catch (error) {
      console.error("Error analyzing:", error);
      toast.error("Erreur lors de l'analyse. Réessayez.");
    } finally {
      setAnalyzing(false);
    }
  };

  // Scan watchlist for opportunities
  const scanOpportunities = async () => {
    setScanning(true);
    setAlerts([]);
    
    try {
      const response = await axios.get(`${API}/trading/scan-opportunities`);
      const data = response.data || {};
      const alertsData = Array.isArray(data.alerts) ? data.alerts : [];
      setAlerts(alertsData);
      
      if (alertsData.length > 0 && soundEnabled) {
        playAlertSound();
        toast.success(`${alertsData.length} opportunité(s) détectée(s) !`);
      } else {
        toast.info("Aucune opportunité forte détectée");
      }
    } catch (error) {
      console.error("Error scanning:", error);
      toast.error("Erreur lors du scan");
    } finally {
      setScanning(false);
    }
  };

  // Save signal
  const saveSignal = async () => {
    if (!analysis || !selectedCoin) return;
    
    try {
      await axios.post(`${API}/signals`, {
        symbol: selectedCoin.id,
        symbol_name: selectedCoin.name,
        signal_type: analysis.recommendation.action.includes("BUY") ? "BUY" : 
                     analysis.recommendation.action.includes("SELL") ? "SELL" : "WAIT",
        entry_price: analysis.levels.entry,
        stop_loss: analysis.levels.stop_loss,
        take_profit_1: analysis.levels.take_profit_1,
        take_profit_2: analysis.levels.take_profit_2,
        timeframe: timeframe,
        confidence: analysis.recommendation.confidence,
        reason: analysis.recommendation.reasons.slice(0, 2).join("; "),
        price_at_signal: analysis.current_price
      });
      
      toast.success("Signal sauvegardé dans l'historique");
    } catch (error) {
      toast.error("Erreur lors de la sauvegarde");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-12 h-12 animate-spin text-primary" />
          <p className="text-muted-foreground">Chargement du mode trading...</p>
        </div>
      </div>
    );
  }

  return (
    <TooltipProvider>
    <div className="space-y-6" data-testid="trading-mode-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center">
            <Crosshair className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl md:text-3xl font-bold font-manrope">Mode Trading</h1>
            <p className="text-sm text-muted-foreground">
              Analyse technique approfondie avec indicateurs professionnels
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="icon"
            onClick={() => setSoundEnabled(!soundEnabled)}
            className="border-white/10"
          >
            {soundEnabled ? (
              <Volume2 className="w-4 h-4 text-primary" />
            ) : (
              <VolumeX className="w-4 h-4 text-muted-foreground" />
            )}
          </Button>
          
          <Button
            onClick={scanOpportunities}
            disabled={scanning}
            variant="outline"
            className="border-white/10"
          >
            <Zap className={`w-4 h-4 mr-2 ${scanning ? "animate-pulse" : ""}`} />
            {scanning ? "Scan..." : "Scanner Watchlist"}
          </Button>
        </div>
      </div>

      {/* Alerts */}
      {alerts.length > 0 && (
        <Card className="glass border-violet-500/30 bg-violet-500/5">
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 mb-3">
              <AlertTriangle className="w-5 h-5 text-violet-500" />
              <span className="font-medium text-violet-400">Opportunités détectées</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {alerts.map((alert, idx) => (
                <Badge
                  key={idx}
                  className={`cursor-pointer ${
                    alert.alert_type.includes("BUY") 
                      ? "bg-emerald-500/20 text-emerald-500 hover:bg-emerald-500/30" 
                      : "bg-rose-500/20 text-rose-500 hover:bg-rose-500/30"
                  }`}
                  onClick={() => {
                    const coin = markets.find(c => c.id === alert.coin_id);
                    if (coin) setSelectedCoin(coin);
                  }}
                >
                  {alert.alert_type.includes("BUY") ? <ArrowUpRight className="w-3 h-3 mr-1" /> : <ArrowDownRight className="w-3 h-3 mr-1" />}
                  {alert.coin_id.toUpperCase()} - {alert.alert_type} (RSI: {alert.rsi})
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Global Market Context */}
      <Card className="glass border-white/5">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg flex items-center gap-2">
              <Globe className="w-5 h-5 text-blue-500" />
              Contexte Marché Global
            </CardTitle>
            <Button
              variant="ghost"
              size="sm"
              onClick={fetchMarketContext}
              disabled={loadingContext}
              className="text-muted-foreground hover:text-foreground"
            >
              <RefreshCw className={`w-4 h-4 ${loadingContext ? "animate-spin" : ""}`} />
            </Button>
          </div>
          <CardDescription>Données économiques réelles influençant les cryptos</CardDescription>
        </CardHeader>
        <CardContent>
          {loadingContext && !marketContext ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-primary" />
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              {/* Fear & Greed */}
              <div className="p-3 rounded-lg bg-white/5 text-center">
                <InfoTooltip tooltipKey="fearGreed">
                  <p className="text-xs text-muted-foreground mb-1">Fear & Greed</p>
                </InfoTooltip>
                {marketContext?.fearGreed ? (
                  <>
                    <p className={`text-2xl font-bold font-mono ${
                      parseInt(marketContext.fearGreed.value) < 30 ? "text-rose-500" :
                      parseInt(marketContext.fearGreed.value) > 70 ? "text-emerald-500" :
                      "text-yellow-500"
                    }`}>
                      {marketContext.fearGreed.value}
                    </p>
                    <p className={`text-xs ${
                      parseInt(marketContext.fearGreed.value) < 30 ? "text-rose-400" :
                      parseInt(marketContext.fearGreed.value) > 70 ? "text-emerald-400" :
                      "text-yellow-400"
                    }`}>
                      {marketContext.fearGreed.value_classification}
                    </p>
                  </>
                ) : (
                  <p className="text-muted-foreground">-</p>
                )}
              </div>

              {/* VIX */}
              <div className="p-3 rounded-lg bg-white/5 text-center">
                <InfoTooltip tooltipKey="vix">
                  <p className="text-xs text-muted-foreground mb-1">VIX (Volatilité)</p>
                </InfoTooltip>
                {marketContext?.macro?.vix ? (
                  <>
                    <p className={`text-2xl font-bold font-mono ${
                      parseFloat(marketContext.macro.vix.value) > 25 ? "text-rose-500" :
                      parseFloat(marketContext.macro.vix.value) < 15 ? "text-emerald-500" :
                      "text-yellow-500"
                    }`}>
                      {parseFloat(marketContext.macro.vix.value).toFixed(1)}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {parseFloat(marketContext.macro.vix.value) > 25 ? "Élevé" :
                       parseFloat(marketContext.macro.vix.value) < 15 ? "Bas" : "Normal"}
                    </p>
                  </>
                ) : (
                  <p className="text-muted-foreground">-</p>
                )}
              </div>

              {/* Fed Rate */}
              <div className="p-3 rounded-lg bg-white/5 text-center">
                <InfoTooltip tooltipKey="fedRate">
                  <p className="text-xs text-muted-foreground mb-1">Taux Fed</p>
                </InfoTooltip>
                {marketContext?.macro?.fed_rate ? (
                  <>
                    <p className="text-2xl font-bold font-mono text-blue-400">
                      {parseFloat(marketContext.macro.fed_rate.value).toFixed(2)}%
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {marketContext.macro.fed_rate.date}
                    </p>
                  </>
                ) : (
                  <p className="text-muted-foreground">-</p>
                )}
              </div>

              {/* EUR/USD */}
              <div className="p-3 rounded-lg bg-white/5 text-center">
                <InfoTooltip tooltipKey="eurusd">
                  <p className="text-xs text-muted-foreground mb-1">EUR/USD</p>
                </InfoTooltip>
                {marketContext?.eurusd ? (
                  <>
                    <p className="text-2xl font-bold font-mono text-violet-400">
                      {parseFloat(marketContext.eurusd["5. Exchange Rate"]).toFixed(4)}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Dollar {parseFloat(marketContext.eurusd["5. Exchange Rate"]) > 1.10 ? "faible" : "fort"}
                    </p>
                  </>
                ) : (
                  <p className="text-muted-foreground">-</p>
                )}
              </div>

              {/* Unemployment */}
              <div className="p-3 rounded-lg bg-white/5 text-center">
                <InfoTooltip tooltipKey="unemployment">
                  <p className="text-xs text-muted-foreground mb-1">Chômage US</p>
                </InfoTooltip>
                {marketContext?.macro?.unemployment ? (
                  <>
                    <p className={`text-2xl font-bold font-mono ${
                      parseFloat(marketContext.macro.unemployment.value) > 5 ? "text-rose-400" :
                      parseFloat(marketContext.macro.unemployment.value) < 4 ? "text-emerald-400" :
                      "text-yellow-400"
                    }`}>
                      {parseFloat(marketContext.macro.unemployment.value).toFixed(1)}%
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {marketContext.macro.unemployment.date}
                    </p>
                  </>
                ) : (
                  <p className="text-muted-foreground">-</p>
                )}
              </div>
            </div>
          )}

          {/* News Impact AI Summary */}
          <div className="mt-4 pt-4 border-t border-white/5">
            <div className="flex items-center justify-between mb-2">
              <p className="text-xs text-muted-foreground flex items-center gap-1">
                <Newspaper className="w-3 h-3" />
                Actualités Impact (IA)
              </p>
              <Button
                variant="ghost"
                size="sm"
                onClick={fetchNewsImpact}
                disabled={loadingNews}
                className="h-6 px-2 text-xs text-muted-foreground hover:text-foreground"
              >
                <RefreshCw className={`w-3 h-3 ${loadingNews ? "animate-spin" : ""}`} />
              </Button>
            </div>
            {loadingNews && !newsImpact ? (
              <div className="flex items-center justify-center py-3">
                <Loader2 className="w-4 h-4 animate-spin text-primary" />
              </div>
            ) : newsImpact?.summary?.length > 0 ? (
              <div className="space-y-1.5">
                {newsImpact.summary.slice(0, 4).map((item, idx) => (
                  <div
                    key={idx}
                    className={`p-2 rounded text-xs flex items-start gap-2 ${
                      item.impact === "HAUSSIER" ? "bg-emerald-500/10" :
                      item.impact === "BAISSIER" ? "bg-rose-500/10" :
                      "bg-white/5"
                    }`}
                  >
                    <span className="flex-shrink-0">
                      {item.impact === "HAUSSIER" ? "📈" : item.impact === "BAISSIER" ? "📉" : "➡️"}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="leading-tight">{item.news}</p>
                      <p className={`text-xs mt-0.5 font-medium ${
                        item.impact === "HAUSSIER" ? "text-emerald-400" :
                        item.impact === "BAISSIER" ? "text-rose-400" :
                        "text-yellow-400"
                      }`}>
                        → {item.action}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-muted-foreground text-center py-2">Chargement des actualités...</p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Selection Panel */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Coin Selection */}
        <Card className="glass border-white/5">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm text-muted-foreground">Crypto à analyser</CardTitle>
          </CardHeader>
          <CardContent>
            <Select
              value={selectedCoin?.id || ""}
              onValueChange={(value) => {
                const coin = markets.find(c => c.id === value);
                setSelectedCoin(coin);
                setAnalysis(null);
              }}
            >
              <SelectTrigger className="bg-black/20 border-white/10">
                <SelectValue placeholder="Sélectionner..." />
              </SelectTrigger>
              <SelectContent className="glass border-white/10">
                {watchlistCoins.length > 0 ? (
                  watchlistCoins.map(coin => (
                    <SelectItem key={coin.id} value={coin.id}>
                      <div className="flex items-center gap-2">
                        <img src={coin.image} alt={coin.name} className="w-5 h-5 rounded-full" />
                        <span>{coin.name}</span>
                        <span className="text-muted-foreground">({coin.symbol.toUpperCase()})</span>
                      </div>
                    </SelectItem>
                  ))
                ) : (
                  <SelectItem value="none" disabled>
                    Ajoutez des cryptos à votre watchlist
                  </SelectItem>
                )}
              </SelectContent>
            </Select>
            
            {selectedCoin && (
              <div className="mt-3 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <img src={selectedCoin.image} alt={selectedCoin.name} className="w-8 h-8 rounded-full" />
                  <div>
                    <p className="font-bold">{formatPrice(selectedCoin.current_price)}</p>
                    <p className={`text-xs ${selectedCoin.price_change_percentage_24h >= 0 ? "text-emerald-500" : "text-rose-500"}`}>
                      {formatPercent(selectedCoin.price_change_percentage_24h)} 24h
                    </p>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Timeframe Selection */}
        <Card className="glass border-white/5">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm text-muted-foreground">Timeframe</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-2">
              {TIMEFRAMES.map(tf => (
                <Button
                  key={tf.value}
                  variant={timeframe === tf.value ? "default" : "outline"}
                  className={`flex-1 ${timeframe === tf.value ? "bg-primary text-black" : "border-white/10"}`}
                  onClick={() => {
                    setTimeframe(tf.value);
                    setAnalysis(null);
                  }}
                >
                  <tf.icon className="w-4 h-4 mr-1" />
                  {tf.label}
                </Button>
              ))}
            </div>
            <p className="text-xs text-muted-foreground text-center mt-2">
              <InfoTooltip tooltipKey={TIMEFRAMES.find(t => t.value === timeframe)?.tooltip || "swing"}>
                <span>{TIMEFRAMES.find(t => t.value === timeframe)?.description}</span>
              </InfoTooltip>
            </p>
          </CardContent>
        </Card>

        {/* Trading Style */}
        <Card className="glass border-white/5">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm text-muted-foreground">Style de Trading</CardTitle>
          </CardHeader>
          <CardContent>
            <Select value={tradingStyle} onValueChange={(v) => { setTradingStyle(v); setAnalysis(null); }}>
              <SelectTrigger className="bg-black/20 border-white/10">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="glass border-white/10">
                {TRADING_STYLES.map(style => (
                  <SelectItem key={style.value} value={style.value}>
                    <div>
                      <span className="font-medium">{style.label}</span>
                      <span className="text-xs text-muted-foreground ml-2">({style.description})</span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </CardContent>
        </Card>
      </div>

      {/* Analyze Button */}
      <Button
        onClick={analyzeNow}
        disabled={analyzing || !selectedCoin}
        className="w-full h-14 text-lg bg-gradient-to-r from-violet-500 to-fuchsia-500 hover:from-violet-600 hover:to-fuchsia-600 text-white font-bold"
        data-testid="analyze-trading-btn"
      >
        {analyzing ? (
          <>
            <Loader2 className="w-5 h-5 mr-2 animate-spin" />
            Analyse en cours...
          </>
        ) : (
          <>
            <Crosshair className="w-5 h-5 mr-2" />
            ANALYSER {selectedCoin?.symbol?.toUpperCase() || ""}
          </>
        )}
      </Button>

      {/* Analysis Results */}
      {analysis && (
        <div className="space-y-4">
          {/* Main Recommendation */}
          <Card className={`glass border-2 ${
            analysis.recommendation.action.includes("BUY") ? "border-emerald-500/30 bg-emerald-500/5" :
            analysis.recommendation.action.includes("SELL") ? "border-rose-500/30 bg-rose-500/5" :
            "border-yellow-500/30 bg-yellow-500/5"
          }`}>
            <CardContent className="pt-6">
              <div className="flex flex-col md:flex-row items-center justify-between gap-4">
                <div className="flex items-center gap-4">
                  <div className={`w-16 h-16 rounded-full flex items-center justify-center ${
                    analysis.recommendation.action.includes("BUY") ? "bg-emerald-500/20" :
                    analysis.recommendation.action.includes("SELL") ? "bg-rose-500/20" :
                    "bg-yellow-500/20"
                  }`}>
                    {analysis.recommendation.action.includes("BUY") ? (
                      <ArrowUpRight className="w-8 h-8 text-emerald-500" />
                    ) : analysis.recommendation.action.includes("SELL") ? (
                      <ArrowDownRight className="w-8 h-8 text-rose-500" />
                    ) : (
                      <Minus className="w-8 h-8 text-yellow-500" />
                    )}
                  </div>
                  <div>
                    <p className={`text-2xl font-bold ${
                      analysis.recommendation.action.includes("BUY") ? "text-emerald-500" :
                      analysis.recommendation.action.includes("SELL") ? "text-rose-500" :
                      "text-yellow-500"
                    }`}>
                      {analysis.recommendation.message}
                    </p>
                    <p className="text-muted-foreground">
                      <InfoTooltip tooltipKey="confidence">
                        <span>Confiance: <span className="font-medium">{analysis.recommendation.confidence.toUpperCase()}</span></span>
                      </InfoTooltip>
                      {" • "}Score: {analysis.recommendation.score}/10
                    </p>
                  </div>
                </div>
                
                <Button onClick={saveSignal} variant="outline" className="border-white/10">
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Sauvegarder Signal
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Indicators Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {/* RSI */}
            <Card className="glass border-white/5">
              <CardContent className="pt-4">
                <InfoTooltip tooltipKey="rsi">
                  <p className="text-xs text-muted-foreground text-center mb-2">RSI (14)</p>
                </InfoTooltip>
                <RSIGauge value={analysis.indicators.rsi} />
              </CardContent>
            </Card>

            {/* MACD */}
            <Card className="glass border-white/5">
              <CardContent className="pt-4">
                <InfoTooltip tooltipKey="macd">
                  <p className="text-xs text-muted-foreground text-center mb-2">MACD</p>
                </InfoTooltip>
                <div className="text-center">
                  <div className={`text-2xl font-bold font-mono ${
                    analysis.indicators.macd.trend === "bullish" ? "text-emerald-500" : "text-rose-500"
                  }`}>
                    {analysis.indicators.macd.histogram > 0 ? "+" : ""}{analysis.indicators.macd.histogram.toFixed(2)}
                  </div>
                  <div className="flex items-center justify-center gap-1 mt-1">
                    {analysis.indicators.macd.trend === "bullish" ? (
                      <ChevronUp className="w-4 h-4 text-emerald-500" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-rose-500" />
                    )}
                    <span className={`text-xs ${
                      analysis.indicators.macd.trend === "bullish" ? "text-emerald-500" : "text-rose-500"
                    }`}>
                      {analysis.indicators.macd.trend === "bullish" ? "HAUSSIER" : "BAISSIER"}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Bollinger */}
            <Card className="glass border-white/5">
              <CardContent className="pt-4">
                <InfoTooltip tooltipKey="bollinger">
                  <p className="text-xs text-muted-foreground text-center mb-2">Bollinger</p>
                </InfoTooltip>
                <div className="text-center">
                  <div className={`text-lg font-bold ${
                    analysis.indicators.bollinger.position === "oversold" ? "text-emerald-500" :
                    analysis.indicators.bollinger.position === "overbought" ? "text-rose-500" :
                    "text-yellow-500"
                  }`}>
                    {analysis.indicators.bollinger.position === "oversold" ? "SURVENTE" :
                     analysis.indicators.bollinger.position === "overbought" ? "SURACHAT" :
                     analysis.indicators.bollinger.position === "upper_half" ? "HAUT" :
                     analysis.indicators.bollinger.position === "lower_half" ? "BAS" : "MILIEU"}
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">
                    <span className="text-rose-400">{formatPrice(analysis.indicators.bollinger.upper)}</span>
                    {" / "}
                    <span className="text-emerald-400">{formatPrice(analysis.indicators.bollinger.lower)}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Trend */}
            <Card className="glass border-white/5">
              <CardContent className="pt-4">
                <InfoTooltip tooltipKey="ma">
                  <p className="text-xs text-muted-foreground text-center mb-2">Tendance MA</p>
                </InfoTooltip>
                <div className="text-center">
                  <div className={`text-lg font-bold ${
                    analysis.indicators.moving_averages.trend.includes("bullish") ? "text-emerald-500" :
                    analysis.indicators.moving_averages.trend.includes("bearish") ? "text-rose-500" :
                    "text-yellow-500"
                  }`}>
                    {analysis.indicators.moving_averages.trend === "strong_bullish" ? "TRÈS HAUSSIER" :
                     analysis.indicators.moving_averages.trend === "bullish" ? "HAUSSIER" :
                     analysis.indicators.moving_averages.trend === "strong_bearish" ? "TRÈS BAISSIER" :
                     analysis.indicators.moving_averages.trend === "bearish" ? "BAISSIER" : "NEUTRE"}
                  </div>
                  <div className="flex justify-center gap-1 mt-1">
                    {analysis.indicators.moving_averages.trend.includes("bullish") ? (
                      <TrendingUp className="w-4 h-4 text-emerald-500" />
                    ) : analysis.indicators.moving_averages.trend.includes("bearish") ? (
                      <TrendingDown className="w-4 h-4 text-rose-500" />
                    ) : (
                      <Activity className="w-4 h-4 text-yellow-500" />
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Price Levels */}
          <Card className="glass border-white/5">
            <CardHeader className="pb-2">
              <CardTitle className="text-lg flex items-center gap-2">
                <Target className="w-5 h-5 text-primary" />
                Niveaux de Prix
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <div className="p-3 rounded-lg bg-white/5 text-center">
                  <p className="text-xs text-muted-foreground">Prix Actuel</p>
                  <p className="text-lg font-bold font-mono">{formatPrice(analysis.current_price)}</p>
                </div>
                <div className="p-3 rounded-lg bg-blue-500/10 text-center">
                  <InfoTooltip tooltipKey="entry">
                    <p className="text-xs text-blue-400">Entrée</p>
                  </InfoTooltip>
                  <p className="text-lg font-bold font-mono text-blue-400">{formatPrice(analysis.levels.entry)}</p>
                </div>
                <div className="p-3 rounded-lg bg-rose-500/10 text-center">
                  <InfoTooltip tooltipKey="stopLoss">
                    <p className="text-xs text-rose-400">Stop-Loss</p>
                  </InfoTooltip>
                  <p className="text-lg font-bold font-mono text-rose-400">{formatPrice(analysis.levels.stop_loss)}</p>
                  <p className="text-xs text-muted-foreground">
                    {(((analysis.levels.entry - analysis.levels.stop_loss) / analysis.levels.entry) * 100).toFixed(1)}%
                  </p>
                </div>
                <div className="p-3 rounded-lg bg-emerald-500/10 text-center">
                  <InfoTooltip tooltipKey="takeProfit">
                    <p className="text-xs text-emerald-400">TP1</p>
                  </InfoTooltip>
                  <p className="text-lg font-bold font-mono text-emerald-400">{formatPrice(analysis.levels.take_profit_1)}</p>
                  <p className="text-xs text-muted-foreground">
                    +{(((analysis.levels.take_profit_1 - analysis.levels.entry) / analysis.levels.entry) * 100).toFixed(1)}%
                  </p>
                </div>
                <div className="p-3 rounded-lg bg-emerald-500/10 text-center">
                  <InfoTooltip tooltipKey="takeProfit">
                    <p className="text-xs text-emerald-400">TP2</p>
                  </InfoTooltip>
                  <p className="text-lg font-bold font-mono text-emerald-400">{formatPrice(analysis.levels.take_profit_2)}</p>
                  <p className="text-xs text-muted-foreground">
                    +{(((analysis.levels.take_profit_2 - analysis.levels.entry) / analysis.levels.entry) * 100).toFixed(1)}%
                  </p>
                </div>
              </div>
              
              {/* Support/Resistance */}
              <div className="mt-4 flex items-center justify-between text-sm">
                <InfoTooltip tooltipKey="support">
                  <span className="text-emerald-400">
                    Support: {formatPrice(analysis.indicators.support_resistance.support)}
                  </span>
                </InfoTooltip>
                <InfoTooltip tooltipKey="resistance">
                  <span className="text-rose-400">
                    Résistance: {formatPrice(analysis.indicators.support_resistance.resistance)}
                  </span>
                </InfoTooltip>
              </div>
            </CardContent>
          </Card>

          {/* Reasons */}
          <Card className="glass border-white/5">
            <CardHeader className="pb-2">
              <CardTitle className="text-lg flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-violet-500" />
                Raisons de la Recommandation
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {analysis.recommendation.reasons.map((reason, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-sm">
                    <CheckCircle className="w-4 h-4 text-primary mt-0.5 flex-shrink-0" />
                    <span>{reason}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>

          {/* AI Analysis */}
          <Card className="glass border-violet-500/20">
            <CardHeader className="pb-2">
              <CardTitle className="text-lg flex items-center gap-2">
                <Zap className="w-5 h-5 text-violet-500" />
                Analyse IA Détaillée
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="prose prose-sm prose-invert max-w-none">
                <div className="p-4 rounded-lg bg-black/20 whitespace-pre-wrap text-sm">
                  {analysis.ai_analysis}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Empty State */}
      {!analysis && !analyzing && (
        <Card className="glass border-white/5">
          <CardContent className="py-16">
            <div className="flex flex-col items-center text-center">
              <Crosshair className="w-16 h-16 text-muted-foreground/30 mb-4" />
              <h3 className="text-lg font-medium mb-2">Prêt à analyser</h3>
              <p className="text-muted-foreground max-w-md">
                Sélectionnez une crypto de votre watchlist, choisissez le timeframe et le style de trading, 
                puis cliquez sur <span className="text-primary font-medium">ANALYSER</span> pour obtenir 
                une analyse technique complète avec recommandation.
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
    </TooltipProvider>
  );
}
