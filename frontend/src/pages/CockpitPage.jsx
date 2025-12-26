import { useState, useEffect } from "react";
import { useAuth, API } from "../App";
import axios from "axios";
import { toast } from "sonner";
import { useNavigate } from "react-router-dom";
import {
  Sun,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Zap,
  Brain,
  RefreshCw,
  Loader2,
  ArrowUpRight,
  ArrowDownRight,
  Target,
  DollarSign,
  BarChart3,
  Coins,
  LineChart,
  Building2,
  CheckCircle,
  XCircle,
  History
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { ScrollArea } from "../components/ui/scroll-area";

const formatPrice = (price, decimals = 2) => {
  if (!price && price !== 0) return "$0.00";
  if (price >= 1000) return `$${price.toLocaleString("en-US", { maximumFractionDigits: 0 })}`;
  if (price >= 1) return `$${price.toFixed(decimals)}`;
  return `$${price.toFixed(6)}`;
};

const getMarketIcon = (type) => {
  switch (type) {
    case "crypto": return <Coins className="w-4 h-4" />;
    case "forex": return <DollarSign className="w-4 h-4" />;
    case "indices": return <BarChart3 className="w-4 h-4" />;
    case "stocks": return <Building2 className="w-4 h-4" />;
    default: return <LineChart className="w-4 h-4" />;
  }
};

const getMarketLabel = (type) => {
  switch (type) {
    case "crypto": return "Crypto";
    case "forex": return "Forex";
    case "indices": return "Indice";
    case "stocks": return "Action";
    default: return type;
  }
};

export default function CockpitPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [briefing, setBriefing] = useState(null);
  const [signals, setSignals] = useState(null);
  const [signalsHistory, setSignalsHistory] = useState([]);
  const [signalsStats, setSignalsStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadingSignals, setLoadingSignals] = useState(false);
  const [activeTab, setActiveTab] = useState("signals");

  const fetchBriefing = async () => {
    try {
      const response = await axios.get(`${API}/briefing/daily`);
      setBriefing(response.data);
    } catch (error) {
      console.error("Error fetching briefing:", error);
    }
  };

  const fetchSignals = async () => {
    setLoadingSignals(true);
    try {
      const response = await axios.get(`${API}/signals/ai-trading`);
      setSignals(response.data);
    } catch (error) {
      console.error("Error fetching signals:", error);
      toast.error("Erreur lors de la génération des signaux");
    } finally {
      setLoadingSignals(false);
    }
  };

  const fetchHistory = async () => {
    try {
      const response = await axios.get(`${API}/signals/history?limit=20`);
      setSignalsHistory(Array.isArray(response.data) ? response.data : []);
    } catch (error) {
      console.error("Error fetching history:", error);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/signals/stats`);
      setSignalsStats(response.data);
    } catch (error) {
      console.error("Error fetching stats:", error);
    }
  };

  const updateSignalResult = async (signalId, result, pnl) => {
    try {
      await axios.post(`${API}/signals/${signalId}/result?result=${result}&pnl_percent=${pnl}`);
      toast.success("Résultat enregistré");
      fetchHistory();
      fetchStats();
    } catch (error) {
      toast.error("Erreur lors de la mise à jour");
    }
  };

  useEffect(() => {
    const init = async () => {
      await Promise.all([fetchBriefing(), fetchSignals(), fetchHistory(), fetchStats()]);
      setLoading(false);
    };
    init();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-12 h-12 animate-spin text-primary" />
          <p className="text-muted-foreground">Bull Sage analyse les marchés...</p>
        </div>
      </div>
    );
  }

  const getSentimentColor = (sentiment) => {
    if (sentiment === "bullish") return "text-emerald-500";
    if (sentiment === "bearish") return "text-rose-500";
    return "text-yellow-500";
  };

  const getSentimentBg = (sentiment) => {
    if (sentiment === "bullish") return "bg-emerald-500/10 border-emerald-500/20";
    if (sentiment === "bearish") return "bg-rose-500/10 border-rose-500/20";
    return "bg-yellow-500/10 border-yellow-500/20";
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center">
            <Sun className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl md:text-3xl font-bold font-manrope">Cockpit Trading</h1>
            <p className="text-sm text-muted-foreground">
              Signaux IA Multi-Marchés • Crypto, Forex, Indices, Actions
            </p>
          </div>
        </div>
        
        <Button
          onClick={fetchSignals}
          disabled={loadingSignals}
          className="bg-primary hover:bg-primary/90 text-black font-bold"
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${loadingSignals ? "animate-spin" : ""}`} />
          {loadingSignals ? "Analyse en cours..." : "Analyser les Marchés"}
        </Button>
      </div>

      {/* Market Overview */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Card className="glass border-white/5">
          <CardContent className="pt-4 pb-4 text-center">
            <p className="text-xs text-muted-foreground">Fear & Greed</p>
            <p className={`text-2xl font-bold ${
              (signals?.fear_greed?.value || briefing?.fear_greed) < 30 ? "text-rose-500" :
              (signals?.fear_greed?.value || briefing?.fear_greed) > 70 ? "text-emerald-500" : "text-yellow-500"
            }`}>
              {signals?.fear_greed?.value || briefing?.fear_greed || "—"}
            </p>
            <p className="text-xs text-muted-foreground">
              {signals?.fear_greed?.label || briefing?.fear_greed_label || "—"}
            </p>
          </CardContent>
        </Card>

        <Card className={`glass border ${getSentimentBg(signals?.market_sentiment || briefing?.sentiment)}`}>
          <CardContent className="pt-4 pb-4 text-center">
            <p className="text-xs text-muted-foreground">Sentiment</p>
            <p className={`text-2xl font-bold capitalize ${getSentimentColor(signals?.market_sentiment || briefing?.sentiment)}`}>
              {signals?.market_sentiment || briefing?.sentiment || "Neutral"}
            </p>
            <p className="text-xs text-muted-foreground">Marché global</p>
          </CardContent>
        </Card>

        <Card className="glass border-white/5">
          <CardContent className="pt-4 pb-4 text-center">
            <p className="text-xs text-muted-foreground">Signaux Actifs</p>
            <p className="text-2xl font-bold text-primary">
              {signals?.signals?.length || 0}
            </p>
            <p className="text-xs text-muted-foreground">Opportunités</p>
          </CardContent>
        </Card>

        <Card className="glass border-white/5">
          <CardContent className="pt-4 pb-4 text-center">
            <p className="text-xs text-muted-foreground">Win Rate</p>
            <p className={`text-2xl font-bold ${(signalsStats?.win_rate || 0) >= 50 ? "text-emerald-500" : "text-rose-500"}`}>
              {signalsStats?.win_rate || 0}%
            </p>
            <p className="text-xs text-muted-foreground">{signalsStats?.total_signals || 0} trades</p>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="bg-black/20 border border-white/10">
          <TabsTrigger value="signals" className="data-[state=active]:bg-primary data-[state=active]:text-black">
            <Zap className="w-4 h-4 mr-2" />
            Signaux du Jour
          </TabsTrigger>
          <TabsTrigger value="history" className="data-[state=active]:bg-primary data-[state=active]:text-black">
            <History className="w-4 h-4 mr-2" />
            Historique
          </TabsTrigger>
        </TabsList>

        {/* Signaux du jour */}
        <TabsContent value="signals" className="space-y-4">
          {/* Warning */}
          {signals?.warning && (
            <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-500 mt-0.5 flex-shrink-0" />
              <p className="text-sm text-amber-200">{signals.warning}</p>
            </div>
          )}

          {/* Signaux */}
          {loadingSignals ? (
            <div className="flex items-center justify-center py-16">
              <div className="flex flex-col items-center gap-4">
                <Loader2 className="w-12 h-12 animate-spin text-primary" />
                <p className="text-muted-foreground">Grok analyse les marchés...</p>
                <p className="text-xs text-muted-foreground">Crypto • Forex • Indices • Actions</p>
              </div>
            </div>
          ) : signals?.signals?.length > 0 ? (
            <div className="space-y-4">
              {signals.signals.map((signal, idx) => (
                <Card 
                  key={idx} 
                  className={`glass border-2 ${
                    signal.direction === "ACHAT" 
                      ? "border-emerald-500/30 bg-gradient-to-r from-emerald-500/5 to-transparent" 
                      : "border-rose-500/30 bg-gradient-to-r from-rose-500/5 to-transparent"
                  }`}
                >
                  <CardContent className="pt-4 pb-4">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                      {/* Left: Asset info */}
                      <div className="flex items-center gap-4">
                        <div className={`w-14 h-14 rounded-xl flex items-center justify-center ${
                          signal.direction === "ACHAT" ? "bg-emerald-500/20" : "bg-rose-500/20"
                        }`}>
                          {signal.direction === "ACHAT" ? (
                            <ArrowUpRight className="w-8 h-8 text-emerald-500" />
                          ) : (
                            <ArrowDownRight className="w-8 h-8 text-rose-500" />
                          )}
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <h3 className="text-xl font-bold">{signal.asset}</h3>
                            <Badge variant="outline" className="border-white/20">
                              {getMarketIcon(signal.market_type)}
                              <span className="ml-1">{getMarketLabel(signal.market_type)}</span>
                            </Badge>
                          </div>
                          <p className="text-sm text-muted-foreground">{signal.asset_name}</p>
                          <div className="flex items-center gap-2 mt-1">
                            <Badge className={`${
                              signal.direction === "ACHAT" 
                                ? "bg-emerald-500 text-white" 
                                : "bg-rose-500 text-white"
                            }`}>
                              {signal.direction}
                            </Badge>
                            <span className="text-sm font-mono">
                              @ {signal.entry_price ? formatPrice(signal.entry_price) : "Market"}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Center: Metrics */}
                      <div className="grid grid-cols-4 gap-4 flex-1 max-w-xl">
                        <div className="text-center p-2 rounded-lg bg-white/5">
                          <p className="text-xs text-muted-foreground">Confiance</p>
                          <p className={`text-lg font-bold ${
                            signal.confidence >= 80 ? "text-emerald-500" :
                            signal.confidence >= 60 ? "text-yellow-500" : "text-rose-500"
                          }`}>
                            {signal.confidence}%
                          </p>
                        </div>
                        <div className="text-center p-2 rounded-lg bg-white/5">
                          <p className="text-xs text-muted-foreground">Durée</p>
                          <p className="text-lg font-bold text-blue-400">
                            {signal.duration}
                          </p>
                        </div>
                        <div className="text-center p-2 rounded-lg bg-emerald-500/10">
                          <p className="text-xs text-muted-foreground">Take Profit</p>
                          <p className="text-lg font-bold text-emerald-500">
                            +{signal.take_profit}%
                          </p>
                        </div>
                        <div className="text-center p-2 rounded-lg bg-rose-500/10">
                          <p className="text-xs text-muted-foreground">Stop Loss</p>
                          <p className="text-lg font-bold text-rose-500">
                            -{signal.stop_loss}%
                          </p>
                        </div>
                      </div>

                      {/* Right: Actions */}
                      <div className="flex flex-col gap-2">
                        <Button 
                          size="sm"
                          onClick={() => navigate(`/chart?symbol=${signal.asset}`)}
                          className="bg-white/10 hover:bg-white/20"
                        >
                          <LineChart className="w-4 h-4 mr-1" />
                          Graphique
                        </Button>
                        <Button 
                          size="sm"
                          onClick={() => navigate(`/paper-trading`)}
                          className={signal.direction === "ACHAT" ? "bg-emerald-500 hover:bg-emerald-600" : "bg-rose-500 hover:bg-rose-600"}
                        >
                          <Target className="w-4 h-4 mr-1" />
                          Simuler
                        </Button>
                      </div>
                    </div>

                    {/* Reason */}
                    <div className="mt-4 p-3 rounded-lg bg-white/5 border border-white/10">
                      <div className="flex items-start gap-2">
                        <Brain className="w-4 h-4 text-violet-400 mt-0.5 flex-shrink-0" />
                        <p className="text-sm">{signal.reason}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}

              {/* Markets analyzed */}
              {signals.markets_analyzed && (
                <div className="flex items-center justify-center gap-4 text-xs text-muted-foreground pt-4">
                  <span>📊 Marchés analysés:</span>
                  <span>{signals.markets_analyzed.crypto} cryptos</span>
                  <span>•</span>
                  <span>{signals.markets_analyzed.forex} forex</span>
                  <span>•</span>
                  <span>{signals.markets_analyzed.indices} indices</span>
                  <span>•</span>
                  <span>{signals.markets_analyzed.stocks} actions</span>
                </div>
              )}
            </div>
          ) : (
            <Card className="glass border-white/5">
              <CardContent className="py-16 text-center">
                <Brain className="w-16 h-16 text-muted-foreground/30 mx-auto mb-4" />
                <p className="text-muted-foreground">Aucun signal disponible</p>
                <p className="text-sm text-muted-foreground/70 mt-1">
                  Cliquez sur &quot;Analyser les Marchés&quot; pour générer des signaux
                </p>
              </CardContent>
            </Card>
          )}

          {/* Briefing Summary */}
          {briefing && (
            <Card className="glass border-amber-500/20 bg-gradient-to-r from-amber-500/5 to-transparent">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Sun className="w-4 h-4 text-amber-500" />
                  Briefing du {new Date().toLocaleDateString("fr-FR", { weekday: "long", day: "numeric", month: "long" })}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm">{briefing.summary}</p>
                {briefing.main_action && (
                  <div className="mt-3 p-2 rounded bg-violet-500/10 border border-violet-500/20">
                    <p className="text-xs text-violet-400 font-medium">
                      💡 {briefing.main_action}
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Historique */}
        <TabsContent value="history">
          <Card className="glass border-white/5">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <History className="w-5 h-5" />
                Historique des Signaux
              </CardTitle>
              <CardDescription>
                Marquez vos trades comme gagnants ou perdants pour suivre votre track record
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[400px]">
                {signalsHistory.length > 0 ? (
                  <div className="space-y-2">
                    {signalsHistory.map((signal) => (
                      <div
                        key={signal.id}
                        className={`p-3 rounded-lg border flex items-center justify-between ${
                          signal.status === "closed" 
                            ? signal.result === "win" 
                              ? "bg-emerald-500/10 border-emerald-500/20"
                              : signal.result === "loss"
                                ? "bg-rose-500/10 border-rose-500/20"
                                : "bg-white/5 border-white/10"
                            : "bg-white/5 border-white/10"
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <div className={`w-8 h-8 rounded flex items-center justify-center ${
                            signal.direction === "ACHAT" ? "bg-emerald-500/20" : "bg-rose-500/20"
                          }`}>
                            {signal.direction === "ACHAT" ? (
                              <ArrowUpRight className="w-4 h-4 text-emerald-500" />
                            ) : (
                              <ArrowDownRight className="w-4 h-4 text-rose-500" />
                            )}
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-medium">{signal.asset}</span>
                              <Badge variant="outline" className="text-xs">
                                {getMarketLabel(signal.market_type)}
                              </Badge>
                              <Badge className={signal.direction === "ACHAT" ? "bg-emerald-500/20 text-emerald-400" : "bg-rose-500/20 text-rose-400"}>
                                {signal.direction}
                              </Badge>
                            </div>
                            <p className="text-xs text-muted-foreground">
                              {new Date(signal.created_at).toLocaleString("fr-FR")} • {signal.duration}
                            </p>
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          {signal.status === "closed" ? (
                            <Badge className={
                              signal.result === "win" 
                                ? "bg-emerald-500 text-white"
                                : signal.result === "loss"
                                  ? "bg-rose-500 text-white"
                                  : "bg-gray-500 text-white"
                            }>
                              {signal.result === "win" ? "✓ Gagné" : signal.result === "loss" ? "✗ Perdu" : "= Breakeven"}
                              {signal.pnl_percent ? ` (${signal.pnl_percent > 0 ? "+" : ""}${signal.pnl_percent}%)` : ""}
                            </Badge>
                          ) : (
                            <div className="flex gap-1">
                              <Button
                                size="sm"
                                variant="ghost"
                                className="h-7 text-emerald-500 hover:bg-emerald-500/20"
                                onClick={() => updateSignalResult(signal.id, "win", signal.take_profit || 2)}
                              >
                                <CheckCircle className="w-4 h-4" />
                              </Button>
                              <Button
                                size="sm"
                                variant="ghost"
                                className="h-7 text-rose-500 hover:bg-rose-500/20"
                                onClick={() => updateSignalResult(signal.id, "loss", -(signal.stop_loss || 1))}
                              >
                                <XCircle className="w-4 h-4" />
                              </Button>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <History className="w-12 h-12 text-muted-foreground/30 mx-auto mb-4" />
                    <p className="text-muted-foreground">Aucun signal dans l&apos;historique</p>
                  </div>
                )}
              </ScrollArea>
            </CardContent>
          </Card>

          {/* Stats */}
          {signalsStats && signalsStats.total_signals > 0 && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4">
              <Card className="glass border-white/5">
                <CardContent className="pt-4 pb-4 text-center">
                  <p className="text-xs text-muted-foreground">Total Signaux</p>
                  <p className="text-2xl font-bold">{signalsStats.total_signals}</p>
                </CardContent>
              </Card>
              <Card className="glass border-emerald-500/20">
                <CardContent className="pt-4 pb-4 text-center">
                  <p className="text-xs text-muted-foreground">Gagnants</p>
                  <p className="text-2xl font-bold text-emerald-500">{signalsStats.wins}</p>
                </CardContent>
              </Card>
              <Card className="glass border-rose-500/20">
                <CardContent className="pt-4 pb-4 text-center">
                  <p className="text-xs text-muted-foreground">Perdants</p>
                  <p className="text-2xl font-bold text-rose-500">{signalsStats.losses}</p>
                </CardContent>
              </Card>
              <Card className={`glass border-2 ${signalsStats.total_pnl >= 0 ? "border-emerald-500/30" : "border-rose-500/30"}`}>
                <CardContent className="pt-4 pb-4 text-center">
                  <p className="text-xs text-muted-foreground">P&L Total</p>
                  <p className={`text-2xl font-bold ${signalsStats.total_pnl >= 0 ? "text-emerald-500" : "text-rose-500"}`}>
                    {signalsStats.total_pnl >= 0 ? "+" : ""}{signalsStats.total_pnl}%
                  </p>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
