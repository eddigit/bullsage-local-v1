import { useState, useEffect } from "react";
import axios from "axios";
import { toast } from "sonner";
import {
  Search,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  Loader2,
  Zap,
  DollarSign,
  BarChart3,
  Bitcoin,
  Building2,
  LineChart,
  ArrowUpRight,
  ArrowDownRight,
  Target,
  Brain,
  Sparkles,
  Filter,
  CheckCircle,
  Rocket,
  HelpCircle,
  Info,
  Clock,
  ShieldAlert,
  TrendingUp as TrendUp
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Switch } from "../components/ui/switch";
import { Label } from "../components/ui/label";
import { API, useAuth } from "../App";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "../components/ui/tooltip";

const TYPE_ICONS = {
  crypto: Bitcoin,
  stock: Building2,
  index: LineChart
};

const TYPE_COLORS = {
  crypto: "from-amber-500/20 to-orange-500/20 border-amber-500/30",
  stock: "from-blue-500/20 to-cyan-500/20 border-blue-500/30",
  index: "from-purple-500/20 to-pink-500/20 border-purple-500/30"
};

const ACTION_STYLES = {
  BUY: { bg: "bg-emerald-500/20", text: "text-emerald-400", border: "border-emerald-500/30" },
  SELL: { bg: "bg-red-500/20", text: "text-red-400", border: "border-red-500/30" },
  WATCH: { bg: "bg-yellow-500/20", text: "text-yellow-400", border: "border-yellow-500/30" }
};

// Descriptions des actions pour les tooltips
const ACTION_DESCRIPTIONS = {
  BUY: {
    title: "🟢 Signal d'ACHAT",
    description: "Les indicateurs suggèrent une opportunité d'achat. Le prix pourrait monter.",
    advice: "Envisagez d'ouvrir une position LONG (achat)"
  },
  SELL: {
    title: "🔴 Signal de VENTE",
    description: "Les indicateurs suggèrent une opportunité de vente. Le prix pourrait baisser.",
    advice: "Envisagez d'ouvrir une position SHORT (vente) ou de prendre vos profits"
  },
  WATCH: {
    title: "🟡 À SURVEILLER",
    description: "Pas de signal clair pour le moment. L'actif montre des signes intéressants.",
    advice: "Patientez et surveillez l'évolution avant de prendre position"
  }
};

// Descriptions des scores
const getScoreDescription = (score) => {
  if (score >= 4) return { level: "Excellent", color: "text-emerald-400", desc: "Signal très fort avec plusieurs confirmations" };
  if (score >= 2) return { level: "Bon", color: "text-green-400", desc: "Signal correct avec quelques confirmations" };
  if (score >= 0) return { level: "Neutre", color: "text-yellow-400", desc: "Signaux mitigés, prudence recommandée" };
  if (score >= -2) return { level: "Faible", color: "text-orange-400", desc: "Signaux négatifs, éviter ou attendre" };
  return { level: "Négatif", color: "text-red-400", desc: "Signaux fortement baissiers" };
};

export default function OpportunityScannerPage() {
  const { user } = useAuth();
  const [opportunities, setOpportunities] = useState([]);
  const [aiRecommendation, setAiRecommendation] = useState(null);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [lastScan, setLastScan] = useState(null);
  const [applyingTrade, setApplyingTrade] = useState(null);
  
  // Filters
  const [includeCrypto, setIncludeCrypto] = useState(true);
  const [includeStocks, setIncludeStocks] = useState(true);
  const [includeIndices, setIncludeIndices] = useState(true);

  useEffect(() => {
    // Auto-scan on page load
    runScan();
  }, []);

  // Fonction pour appliquer un trade en Paper Trading
  const applyTrade = async (opp) => {
    const token = localStorage.getItem("token");
    if (!user || !token) {
      toast.error("Connectez-vous pour utiliser le Paper Trading");
      return;
    }
    
    setApplyingTrade(opp.symbol);
    try {
      const tradeType = opp.action === "BUY" ? "buy" : "sell";
      const amount = 100 / opp.price; // ~100$ de trade
      
      await axios.post(`${API}/paper-trading/trade`, {
        symbol: opp.symbol,
        type: tradeType,
        amount: amount,
        price: opp.price
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success(
        `🚀 Trade ${tradeType.toUpperCase()} ouvert sur ${opp.symbol}!\n` +
        `Prix: ${formatPrice(opp.price, opp.type)}`,
        { duration: 5000 }
      );
    } catch (error) {
      console.error("Trade error:", error);
      toast.error("Erreur lors de l'ouverture du trade");
    } finally {
      setApplyingTrade(null);
    }
  };

  const runScan = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API}/scanner/unified`, {
        include_crypto: includeCrypto,
        include_stocks: includeStocks,
        include_indices: includeIndices,
        max_results: 15
      });
      
      setOpportunities(response.data.opportunities || []);
      setAiRecommendation(response.data.ai_recommendation);
      setSummary(response.data.summary);
      setLastScan(new Date());
      
      toast.success(`🔍 Scan terminé - ${response.data.opportunities?.length || 0} opportunités trouvées`);
    } catch (error) {
      console.error("Scan error:", error);
      toast.error("Erreur lors du scan");
    } finally {
      setLoading(false);
    }
  };

  const formatPrice = (price, type) => {
    if (type === "crypto" && price < 1) {
      return `$${price.toFixed(6)}`;
    }
    return `$${price.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  return (
    <TooltipProvider delayDuration={200}>
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold font-manrope flex items-center gap-3">
            <div className="p-2 bg-gradient-to-br from-violet-600 to-fuchsia-600 rounded-xl">
              <Search className="w-6 h-6 text-white" />
            </div>
            Scanner IA Unifié
            <Tooltip>
              <TooltipTrigger asChild>
                <HelpCircle className="w-5 h-5 text-muted-foreground cursor-help" />
              </TooltipTrigger>
              <TooltipContent side="right" className="max-w-sm bg-slate-900 text-white p-3">
                <p className="font-bold mb-2">💡 Comment utiliser le Scanner</p>
                <ul className="text-sm space-y-1">
                  <li>• <span className="text-emerald-400">BUY</span> = Signal d'achat détecté</li>
                  <li>• <span className="text-red-400">SELL</span> = Signal de vente détecté</li>
                  <li>• <span className="text-yellow-400">WATCH</span> = À surveiller</li>
                  <li>• <span className="text-blue-400">Score</span> = Force du signal (-5 à +5)</li>
                </ul>
                <p className="text-xs text-muted-foreground mt-2">Survolez les éléments pour plus de détails</p>
              </TooltipContent>
            </Tooltip>
          </h1>
          <p className="text-muted-foreground mt-1">
            Analyse en temps réel des cryptos, actions et indices pour trouver les meilleures opportunités
          </p>
        </div>
        
        <Button 
          onClick={runScan} 
          disabled={loading}
          className="bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-500 hover:to-fuchsia-500"
        >
          {loading ? (
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
          ) : (
            <RefreshCw className="w-4 h-4 mr-2" />
          )}
          {loading ? "Scan en cours..." : "Lancer le scan"}
        </Button>
      </div>

      {/* Filters */}
      <Card className="glass border-white/10">
        <CardContent className="pt-4">
          <div className="flex flex-wrap items-center gap-6">
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-muted-foreground" />
              <span className="text-sm font-medium">Filtres:</span>
            </div>
            
            <div className="flex items-center space-x-2">
              <Switch id="crypto" checked={includeCrypto} onCheckedChange={setIncludeCrypto} />
              <Label htmlFor="crypto" className="flex items-center gap-1">
                <Bitcoin className="w-4 h-4 text-amber-500" />
                Cryptos
              </Label>
            </div>
            
            <div className="flex items-center space-x-2">
              <Switch id="stocks" checked={includeStocks} onCheckedChange={setIncludeStocks} />
              <Label htmlFor="stocks" className="flex items-center gap-1">
                <Building2 className="w-4 h-4 text-blue-500" />
                Actions
              </Label>
            </div>
            
            <div className="flex items-center space-x-2">
              <Switch id="indices" checked={includeIndices} onCheckedChange={setIncludeIndices} />
              <Label htmlFor="indices" className="flex items-center gap-1">
                <LineChart className="w-4 h-4 text-purple-500" />
                Indices
              </Label>
            </div>
            
            {lastScan && (
              <span className="text-xs text-muted-foreground ml-auto">
                Dernier scan: {lastScan.toLocaleTimeString("fr-FR")}
              </span>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Summary Stats */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <Card className="glass border-white/10">
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold">{summary.total_scanned}</p>
              <p className="text-xs text-muted-foreground">Actifs scannés</p>
            </CardContent>
          </Card>
          <Card className="glass border-white/10 border-amber-500/30">
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-amber-400">{summary.crypto_count}</p>
              <p className="text-xs text-muted-foreground">Cryptos</p>
            </CardContent>
          </Card>
          <Card className="glass border-white/10 border-blue-500/30">
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-blue-400">{summary.stock_count}</p>
              <p className="text-xs text-muted-foreground">Actions</p>
            </CardContent>
          </Card>
          <Card className="glass border-white/10 border-purple-500/30">
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-purple-400">{summary.index_count}</p>
              <p className="text-xs text-muted-foreground">Indices</p>
            </CardContent>
          </Card>
          <Card className="glass border-white/10 border-emerald-500/30">
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-emerald-400">{summary.buy_signals}</p>
              <p className="text-xs text-muted-foreground">Signaux BUY</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* AI Recommendation */}
      {aiRecommendation && (
        <Card className="glass border-2 border-violet-500/30 bg-gradient-to-br from-violet-500/10 to-fuchsia-500/10">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center gap-2">
              <Brain className="w-5 h-5 text-violet-400" />
              Analyse IA
              <Sparkles className="w-4 h-4 text-fuchsia-400" />
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="prose prose-invert prose-sm max-w-none whitespace-pre-wrap">
              {aiRecommendation}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Best Opportunity Highlight */}
      {summary?.best_opportunity && (
        <Card className="glass border-2 border-emerald-500/30 bg-gradient-to-br from-emerald-500/10 to-teal-500/10 overflow-hidden">
          <div className="absolute top-0 right-0 bg-emerald-500 text-black text-xs font-bold px-3 py-1 rounded-bl-lg">
            🏆 MEILLEURE OPPORTUNITÉ
          </div>
          <CardContent className="pt-8 pb-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-14 h-14 rounded-full bg-emerald-500/20 flex items-center justify-center text-2xl">
                  {summary.best_opportunity.icon}
                </div>
                <div>
                  <h3 className="text-xl font-bold">{summary.best_opportunity.name}</h3>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge variant="outline" className="text-xs">
                      {summary.best_opportunity.type.toUpperCase()}
                    </Badge>
                    <span className="text-sm text-muted-foreground">{summary.best_opportunity.symbol}</span>
                  </div>
                </div>
              </div>
              
              <div className="text-right">
                <p className="text-2xl font-bold font-mono">
                  {formatPrice(summary.best_opportunity.price, summary.best_opportunity.type)}
                </p>
                <p className={`text-sm flex items-center justify-end gap-1 ${summary.best_opportunity.change_24h >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                  {summary.best_opportunity.change_24h >= 0 ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
                  {summary.best_opportunity.change_24h >= 0 ? "+" : ""}{summary.best_opportunity.change_24h}%
                </p>
              </div>
            </div>
            
            <div className="flex flex-wrap gap-2 mt-4">
              {summary.best_opportunity.signals?.map((signal, idx) => (
                <Tooltip key={idx}>
                  <TooltipTrigger asChild>
                    <Badge variant="outline" className="text-emerald-400 border-emerald-500/30 cursor-help">
                      <CheckCircle className="w-3 h-3 mr-1" />
                      {signal}
                    </Badge>
                  </TooltipTrigger>
                  <TooltipContent side="top" className="bg-slate-900 text-white p-2">
                    <p className="text-sm">Signal technique confirmé</p>
                  </TooltipContent>
                </Tooltip>
              ))}
            </div>
            
            {/* CTA pour la meilleure opportunité */}
            {summary.best_opportunity.type === "crypto" && (
              <div className="mt-4 pt-4 border-t border-emerald-500/20">
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      className="w-full gap-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500"
                      onClick={() => applyTrade(summary.best_opportunity)}
                      disabled={applyingTrade === summary.best_opportunity.symbol}
                    >
                      {applyingTrade === summary.best_opportunity.symbol ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          Ouverture en cours...
                        </>
                      ) : (
                        <>
                          <Rocket className="w-4 h-4" />
                          🏆 Trader cette opportunité en Paper Trading
                        </>
                      )}
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent side="bottom" className="max-w-sm bg-slate-900 text-white p-3">
                    <p className="font-bold mb-1">🏆 Meilleure opportunité du scan</p>
                    <p className="text-sm">Ouvrir une position d'achat sur {summary.best_opportunity.symbol}</p>
                    <p className="text-xs text-blue-400 mt-2">💡 Le Paper Trading utilise de l'argent virtuel - Aucun risque réel !</p>
                  </TooltipContent>
                </Tooltip>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Opportunities Grid */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="text-center">
            <Loader2 className="w-12 h-12 animate-spin text-violet-500 mx-auto mb-4" />
            <p className="text-muted-foreground">Analyse des marchés en cours...</p>
            <p className="text-xs text-muted-foreground mt-1">Cryptos • Actions • Indices</p>
          </div>
        </div>
      ) : opportunities.length === 0 ? (
        <Card className="glass border-white/10">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Search className="w-12 h-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">Aucune opportunité trouvée</p>
            <p className="text-xs text-muted-foreground">Activez les filtres et relancez le scan</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {opportunities.map((opp, index) => {
            const TypeIcon = TYPE_ICONS[opp.type] || BarChart3;
            const actionStyle = ACTION_STYLES[opp.action] || ACTION_STYLES.WATCH;
            const actionDesc = ACTION_DESCRIPTIONS[opp.action] || ACTION_DESCRIPTIONS.WATCH;
            const scoreDesc = getScoreDescription(opp.score);
            const canTrade = opp.action === "BUY" || opp.action === "SELL";
            
            return (
              <Card 
                key={`${opp.symbol}-${index}`}
                className={`glass border bg-gradient-to-br ${TYPE_COLORS[opp.type]} hover:scale-[1.02] transition-transform`}
              >
                <CardContent className="p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <div className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center cursor-help">
                            {opp.icon ? (
                              <span className="text-lg">{opp.icon}</span>
                            ) : (
                              <TypeIcon className="w-5 h-5" />
                            )}
                          </div>
                        </TooltipTrigger>
                        <TooltipContent side="top" className="bg-slate-900 text-white p-2">
                          <p className="font-bold">{opp.type === "crypto" ? "🪙 Cryptomonnaie" : opp.type === "stock" ? "🏢 Action" : "📊 Indice"}</p>
                        </TooltipContent>
                      </Tooltip>
                      <div>
                        <h3 className="font-semibold">{opp.name}</h3>
                        <p className="text-xs text-muted-foreground">{opp.symbol} • {opp.type}</p>
                      </div>
                    </div>
                    
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Badge className={`${actionStyle.bg} ${actionStyle.text} ${actionStyle.border} cursor-help`}>
                          {opp.action}
                        </Badge>
                      </TooltipTrigger>
                      <TooltipContent side="top" className="max-w-xs bg-slate-900 text-white p-3">
                        <p className="font-bold mb-1">{actionDesc.title}</p>
                        <p className="text-sm">{actionDesc.description}</p>
                        <p className="text-sm text-blue-400 mt-2">💡 {actionDesc.advice}</p>
                      </TooltipContent>
                    </Tooltip>
                  </div>
                  
                  <div className="flex items-end justify-between mb-3">
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <div className="cursor-help">
                          <p className="text-xl font-bold font-mono">
                            {formatPrice(opp.price, opp.type)}
                          </p>
                          <p className={`text-sm flex items-center gap-1 ${opp.change_24h >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                            {opp.change_24h >= 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                            {opp.change_24h >= 0 ? "+" : ""}{opp.change_24h}%
                          </p>
                        </div>
                      </TooltipTrigger>
                      <TooltipContent side="top" className="bg-slate-900 text-white p-3">
                        <p className="font-bold mb-1">📈 Variation 24h</p>
                        <p className="text-sm">
                          {opp.change_24h >= 0 
                            ? `L'actif a gagné ${opp.change_24h}% sur les dernières 24h` 
                            : `L'actif a perdu ${Math.abs(opp.change_24h)}% sur les dernières 24h`}
                        </p>
                      </TooltipContent>
                    </Tooltip>
                    
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <div className="text-right cursor-help">
                          <p className="text-xs text-muted-foreground flex items-center gap-1">Score <Info className="w-3 h-3" /></p>
                          <p className={`text-lg font-bold ${scoreDesc.color}`}>
                            {opp.score > 0 ? "+" : ""}{opp.score}
                          </p>
                        </div>
                      </TooltipTrigger>
                      <TooltipContent side="top" className="max-w-xs bg-slate-900 text-white p-3">
                        <p className="font-bold mb-1">📊 Score de Signal : {scoreDesc.level}</p>
                        <p className="text-sm">{scoreDesc.desc}</p>
                        <div className="mt-2 text-xs">
                          <p>• +4 à +5 : Signal très fort</p>
                          <p>• +2 à +3 : Bon signal</p>
                          <p>• -1 à +1 : Neutre</p>
                          <p>• -2 à -5 : Signal négatif</p>
                        </div>
                      </TooltipContent>
                    </Tooltip>
                  </div>
                  
                  {/* Signals avec tooltip */}
                  <div className="flex flex-wrap gap-1 mb-3">
                    {opp.signals?.slice(0, 2).map((signal, idx) => (
                      <Tooltip key={idx}>
                        <TooltipTrigger asChild>
                          <span className="text-xs bg-white/5 px-2 py-0.5 rounded cursor-help">
                            {signal}
                          </span>
                        </TooltipTrigger>
                        <TooltipContent side="top" className="bg-slate-900 text-white p-2">
                          <p className="text-sm">Signal technique détecté par l'analyse</p>
                        </TooltipContent>
                      </Tooltip>
                    ))}
                  </div>
                  
                  {/* CTA Button pour Paper Trading */}
                  {canTrade && opp.type === "crypto" && (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button
                          size="sm"
                          className={`w-full gap-2 ${
                            opp.action === "BUY"
                              ? "bg-gradient-to-r from-emerald-600 to-green-600 hover:from-emerald-500 hover:to-green-500"
                              : "bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500"
                          }`}
                          onClick={() => applyTrade(opp)}
                          disabled={applyingTrade === opp.symbol}
                        >
                          {applyingTrade === opp.symbol ? (
                            <>
                              <Loader2 className="w-3 h-3 animate-spin" />
                              En cours...
                            </>
                          ) : (
                            <>
                              <Rocket className="w-3 h-3" />
                              {opp.action === "BUY" ? "🟢 ACHETER" : "🔴 VENDRE"} en Paper
                            </>
                          )}
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent side="bottom" className="max-w-sm bg-slate-900 text-white p-3">
                        <p className="font-bold mb-1">
                          {opp.action === "BUY" ? "🟢 Ouvrir un ACHAT" : "🔴 Ouvrir une VENTE"}
                        </p>
                        <p className="text-sm">
                          {opp.action === "BUY" 
                            ? "Vous achetez cet actif. Profit si le prix monte."
                            : "Vous vendez cet actif. Profit si le prix baisse."}
                        </p>
                        <p className="text-xs text-blue-400 mt-2">💡 Paper Trading = argent virtuel, sans risque réel</p>
                      </TooltipContent>
                    </Tooltip>
                  )}
                  
                  {/* Message si pas tradable */}
                  {(!canTrade || opp.type !== "crypto") && (
                    <div className="text-center">
                      <p className="text-xs text-muted-foreground">
                        {opp.type !== "crypto" 
                          ? "Paper Trading disponible uniquement pour les cryptos"
                          : "Aucune action recommandée pour le moment"}
                      </p>
                    </div>
                  )}
                  
                  <div className="mt-2 pt-2 border-t border-white/5">
                    <p className="text-xs text-muted-foreground">
                      Source: {opp.source}
                    </p>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
    </TooltipProvider>
  );
}
