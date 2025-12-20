import { useState, useEffect } from "react";
import { useAuth, API } from "../App";
import { Link } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import {
  TrendingUp,
  TrendingDown,
  Wallet,
  ArrowUpRight,
  ArrowDownRight,
  Zap,
  Eye,
  RefreshCw,
  Sparkles,
  Loader2,
  Plus,
  Star,
  StarOff,
  Clock,
  Target,
  Search,
  X,
  ChevronDown,
  Newspaper,
  AlertCircle
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { ScrollArea } from "../components/ui/scroll-area";
import { Input } from "../components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer
} from "recharts";

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

const TIMEFRAMES = [
  { value: "1h", label: "1 Heure", description: "Scalping / Day trading" },
  { value: "4h", label: "4 Heures", description: "Intraday" },
  { value: "daily", label: "Journalier", description: "Swing trading" },
];

const CustomTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    return (
      <div className="glass rounded-lg px-3 py-2 text-sm">
        <p className="font-mono font-medium text-primary">
          ${payload[0].value?.toLocaleString()}
        </p>
      </div>
    );
  }
  return null;
};

export default function DashboardPage() {
  const { user, updateUser } = useAuth();
  const [markets, setMarkets] = useState([]);
  const [fearGreed, setFearGreed] = useState(null);
  const [portfolio, setPortfolio] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [newsImpact, setNewsImpact] = useState(null);
  const [loadingNews, setLoadingNews] = useState(false);
  
  // Analysis state
  const [selectedCoin, setSelectedCoin] = useState(null);
  const [selectedTimeframe, setSelectedTimeframe] = useState("4h");
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [analysisDialogOpen, setAnalysisDialogOpen] = useState(false);
  
  // Add to watchlist state
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

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

  const fetchData = async () => {
    try {
      const [marketsRes, fgRes, portfolioRes] = await Promise.all([
        axios.get(`${API}/market/crypto`),
        axios.get(`${API}/market/fear-greed`),
        axios.get(`${API}/paper-trading/portfolio`)
      ]);
      setMarkets(marketsRes.data || []);
      if (fgRes.data?.data?.[0]) {
        setFearGreed(fgRes.data.data[0]);
      }
      setPortfolio(portfolioRes.data);
    } catch (error) {
      console.error("Error fetching data:", error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
    fetchNewsImpact();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchData();
    toast.success("Données actualisées");
  };

  // Filter watchlist coins
  const watchlistCoins = markets.filter(coin => 
    user?.watchlist?.includes(coin.id)
  );

  // Filter available coins for adding
  const availableCoins = markets.filter(coin => 
    !user?.watchlist?.includes(coin.id) &&
    (searchQuery === "" || 
     coin.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
     coin.symbol.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  // Add to watchlist
  const addToWatchlist = async (coinId) => {
    try {
      const response = await axios.post(`${API}/watchlist/${coinId}`);
      updateUser({ watchlist: response.data.watchlist });
      toast.success("Ajouté à votre watchlist");
    } catch (error) {
      toast.error("Erreur lors de l'ajout");
    }
  };

  // Remove from watchlist
  const removeFromWatchlist = async (coinId) => {
    try {
      const response = await axios.delete(`${API}/watchlist/${coinId}`);
      updateUser({ watchlist: response.data.watchlist });
      toast.success("Retiré de la watchlist");
    } catch (error) {
      toast.error("Erreur lors de la suppression");
    }
  };

  // Analyze coin with AI
  const analyzeCoin = async (coin) => {
    setSelectedCoin(coin);
    setAnalysisDialogOpen(true);
    setAnalyzing(true);
    setAnalysisResult(null);

    try {
      const response = await axios.post(`${API}/assistant/chat`, {
        message: `ANALYSE TRADING RAPIDE pour ${coin.name} (${coin.symbol.toUpperCase()}/USD).

Timeframe: ${selectedTimeframe}
Prix actuel: $${coin.current_price}
Variation 24h: ${coin.price_change_percentage_24h?.toFixed(2)}%
High 24h: $${coin.high_24h}
Low 24h: $${coin.low_24h}

DONNE MOI EN FORMAT STRUCTURÉ:
1. SIGNAL: [ACHAT] ou [VENTE] ou [ATTENDRE]
2. ENTRÉE: prix exact recommandé
3. STOP-LOSS: prix exact
4. TP1: premier objectif
5. TP2: deuxième objectif
6. CONFIANCE: Faible/Moyen/Élevé
7. RAISON: explication en 1 phrase

Sois PRÉCIS avec des prix exacts basés sur les données actuelles.`
      });
      
      setAnalysisResult(response.data.response);
      
      // Try to parse and save the signal
      try {
        const text = response.data.response;
        let signalType = "WAIT";
        if (text.toLowerCase().includes("achat") || text.includes("[ACHAT]")) signalType = "BUY";
        else if (text.toLowerCase().includes("vente") || text.includes("[VENTE]")) signalType = "SELL";
        
        // Extract prices using regex
        const extractPrice = (pattern) => {
          const match = text.match(pattern);
          if (match) {
            const priceStr = match[1].replace(/[,$\s]/g, '');
            return parseFloat(priceStr);
          }
          return null;
        };
        
        const entryPrice = extractPrice(/entr[ée]e?\s*:?\s*\$?([\d,]+\.?\d*)/i) || coin.current_price;
        const stopLoss = extractPrice(/stop[- ]?loss\s*:?\s*\$?([\d,]+\.?\d*)/i) || coin.current_price * 0.95;
        const tp1 = extractPrice(/tp1\s*:?\s*\$?([\d,]+\.?\d*)/i) || coin.current_price * 1.05;
        const tp2 = extractPrice(/tp2\s*:?\s*\$?([\d,]+\.?\d*)/i) || coin.current_price * 1.10;
        
        let confidence = "medium";
        if (text.toLowerCase().includes("élevé") || text.toLowerCase().includes("high")) confidence = "high";
        else if (text.toLowerCase().includes("faible") || text.toLowerCase().includes("low")) confidence = "low";
        
        // Extract reason
        const reasonMatch = text.match(/raison\s*:?\s*(.+?)(?:\n|$)/i);
        const reason = reasonMatch ? reasonMatch[1].trim().substring(0, 100) : "Analyse IA";
        
        // Save the signal
        await axios.post(`${API}/signals`, {
          symbol: coin.id,
          symbol_name: coin.name,
          signal_type: signalType,
          entry_price: entryPrice,
          stop_loss: stopLoss,
          take_profit_1: tp1,
          take_profit_2: tp2,
          timeframe: selectedTimeframe,
          confidence: confidence,
          reason: reason,
          price_at_signal: coin.current_price
        });
        
        toast.success("Signal sauvegardé dans l'historique");
      } catch (parseError) {
        console.log("Could not auto-save signal:", parseError);
      }
    } catch (error) {
      toast.error("Erreur lors de l'analyse");
      setAnalysisResult("Erreur lors de l'analyse. Veuillez réessayer.");
    } finally {
      setAnalyzing(false);
    }
  };

  // Calculate portfolio value
  const calculatePortfolioValue = () => {
    if (!portfolio || !markets.length) return portfolio?.balance || 10000;
    let totalValue = portfolio.balance;
    Object.entries(portfolio.portfolio || {}).forEach(([symbol, holding]) => {
      const coin = markets.find(c => c.id === symbol);
      if (coin) {
        totalValue += holding.amount * coin.current_price;
      }
    });
    return totalValue;
  };

  const portfolioValue = calculatePortfolioValue();
  const portfolioChange = ((portfolioValue - 10000) / 10000) * 100;

  // Get sparkline data for chart
  const getSparklineData = (coin) => {
    if (!coin?.sparkline_in_7d?.price) return [];
    const prices = coin.sparkline_in_7d.price;
    return prices.filter((_, i) => i % Math.ceil(prices.length / 20) === 0).map((price, i) => ({
      price
    }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-12 h-12 animate-spin text-primary" />
          <p className="text-muted-foreground">Chargement des données marché...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="dashboard">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold font-manrope">
            Bonjour, {user?.name?.split(" ")[0]} 👋
          </h1>
          <p className="text-muted-foreground">
            Sélectionnez une crypto et cliquez sur <span className="text-primary font-medium">Analyser</span> pour obtenir un signal de trading
          </p>
        </div>
        <div className="flex gap-2">
          <Select value={selectedTimeframe} onValueChange={setSelectedTimeframe}>
            <SelectTrigger className="w-40 bg-black/20 border-white/10">
              <Clock className="w-4 h-4 mr-2" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="glass border-white/10">
              {TIMEFRAMES.map(tf => (
                <SelectItem key={tf.value} value={tf.value}>
                  <div>
                    <span className="font-medium">{tf.label}</span>
                    <span className="text-xs text-muted-foreground ml-2">({tf.description})</span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button
            variant="outline"
            onClick={handleRefresh}
            disabled={refreshing}
            className="border-white/10 hover:bg-white/5"
            data-testid="refresh-btn"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin" : ""}`} />
          </Button>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Portfolio */}
        <Card className="glass border-white/5">
          <CardContent className="pt-4 pb-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground">Portfolio Virtuel</p>
                <p className="text-xl font-bold font-mono">{formatPrice(portfolioValue)}</p>
                <p className={`text-xs font-mono ${portfolioChange >= 0 ? "text-emerald-500" : "text-rose-500"}`}>
                  {formatPercent(portfolioChange)}
                </p>
              </div>
              <Wallet className="w-8 h-8 text-primary/50" />
            </div>
          </CardContent>
        </Card>

        {/* Fear & Greed */}
        <Card className="glass border-white/5">
          <CardContent className="pt-4 pb-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground">Fear & Greed</p>
                <p className="text-xl font-bold font-mono">{fearGreed?.value || "-"}</p>
                <p className={`text-xs ${
                  parseInt(fearGreed?.value) <= 25 ? "text-rose-500" :
                  parseInt(fearGreed?.value) >= 75 ? "text-emerald-500" : "text-yellow-500"
                }`}>
                  {fearGreed?.value_classification || "-"}
                </p>
              </div>
              <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                parseInt(fearGreed?.value) <= 25 ? "bg-rose-500/10" :
                parseInt(fearGreed?.value) >= 75 ? "bg-emerald-500/10" : "bg-yellow-500/10"
              }`}>
                {parseInt(fearGreed?.value) <= 25 ? (
                  <TrendingDown className="w-5 h-5 text-rose-500" />
                ) : parseInt(fearGreed?.value) >= 75 ? (
                  <TrendingUp className="w-5 h-5 text-emerald-500" />
                ) : (
                  <TrendingUp className="w-5 h-5 text-yellow-500" />
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* BTC Quick */}
        <Card className="glass border-white/5">
          <CardContent className="pt-4 pb-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground">Bitcoin</p>
                <p className="text-xl font-bold font-mono">
                  {formatPrice(markets.find(c => c.id === "bitcoin")?.current_price)}
                </p>
                <p className={`text-xs font-mono ${
                  (markets.find(c => c.id === "bitcoin")?.price_change_percentage_24h || 0) >= 0 
                    ? "text-emerald-500" : "text-rose-500"
                }`}>
                  {formatPercent(markets.find(c => c.id === "bitcoin")?.price_change_percentage_24h)}
                </p>
              </div>
              <img src={markets.find(c => c.id === "bitcoin")?.image} alt="BTC" className="w-8 h-8" />
            </div>
          </CardContent>
        </Card>

        {/* Watchlist count */}
        <Card className="glass border-white/5">
          <CardContent className="pt-4 pb-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground">Ma Watchlist</p>
                <p className="text-xl font-bold font-mono">{watchlistCoins.length}</p>
                <p className="text-xs text-muted-foreground">cryptos suivies</p>
              </div>
              <Star className="w-8 h-8 text-yellow-500/50" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* News Impact Section */}
      <Card className="glass border-white/5">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base flex items-center gap-2">
              <Newspaper className="w-4 h-4 text-violet-500" />
              Actualités Impact Marché
            </CardTitle>
            <Button
              variant="ghost"
              size="sm"
              onClick={fetchNewsImpact}
              disabled={loadingNews}
              className="text-xs text-muted-foreground hover:text-foreground"
            >
              <RefreshCw className={`w-3 h-3 mr-1 ${loadingNews ? "animate-spin" : ""}`} />
              Actualiser
            </Button>
          </div>
        </CardHeader>
        <CardContent className="pt-0">
          {loadingNews && !newsImpact ? (
            <div className="flex items-center justify-center py-4">
              <Loader2 className="w-5 h-5 animate-spin text-primary" />
            </div>
          ) : newsImpact?.summary?.length > 0 ? (
            <div className="space-y-2">
              {newsImpact.summary.map((item, idx) => (
                <div
                  key={idx}
                  className={`p-2.5 rounded-lg flex items-start gap-3 ${
                    item.impact === "HAUSSIER" ? "bg-emerald-500/5 border border-emerald-500/10" :
                    item.impact === "BAISSIER" ? "bg-rose-500/5 border border-rose-500/10" :
                    "bg-white/5 border border-white/5"
                  }`}
                >
                  <div className={`mt-0.5 flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-sm ${
                    item.impact === "HAUSSIER" ? "bg-emerald-500/20" :
                    item.impact === "BAISSIER" ? "bg-rose-500/20" :
                    "bg-yellow-500/20"
                  }`}>
                    {item.impact === "HAUSSIER" ? "📈" : item.impact === "BAISSIER" ? "📉" : "➡️"}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm leading-tight">{item.news}</p>
                    <p className={`text-xs mt-1 font-medium ${
                      item.impact === "HAUSSIER" ? "text-emerald-400" :
                      item.impact === "BAISSIER" ? "text-rose-400" :
                      "text-yellow-400"
                    }`}>
                      {item.action}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground text-center py-4">
              Aucune actualité disponible
            </p>
          )}
        </CardContent>
      </Card>

      {/* Main Watchlist Section */}
      <Card className="glass border-white/5">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-xl flex items-center gap-2">
                <Star className="w-5 h-5 text-yellow-500" />
                Ma Watchlist Trading
              </CardTitle>
              <CardDescription>
                Cliquez sur <span className="text-primary">Analyser</span> pour obtenir un signal IA en timeframe {TIMEFRAMES.find(t => t.value === selectedTimeframe)?.label}
              </CardDescription>
            </div>
            
            {/* Add to Watchlist Button */}
            <Dialog open={addDialogOpen} onOpenChange={setAddDialogOpen}>
              <DialogTrigger asChild>
                <Button className="bg-primary hover:bg-primary/90 text-black" data-testid="add-watchlist-btn">
                  <Plus className="w-4 h-4 mr-2" />
                  Ajouter
                </Button>
              </DialogTrigger>
              <DialogContent className="glass border-white/10 max-w-lg">
                <DialogHeader>
                  <DialogTitle>Ajouter à ma Watchlist</DialogTitle>
                  <DialogDescription>
                    Sélectionnez les cryptos que vous souhaitez suivre
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <Input
                      placeholder="Rechercher une crypto..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-10 bg-black/20 border-white/10"
                    />
                  </div>
                  <ScrollArea className="h-[300px]">
                    <div className="space-y-2">
                      {availableCoins.slice(0, 20).map(coin => (
                        <div
                          key={coin.id}
                          className="flex items-center justify-between p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors cursor-pointer"
                          onClick={() => {
                            addToWatchlist(coin.id);
                          }}
                        >
                          <div className="flex items-center gap-3">
                            <img src={coin.image} alt={coin.name} className="w-8 h-8 rounded-full" />
                            <div>
                              <p className="font-medium">{coin.name}</p>
                              <p className="text-xs text-muted-foreground uppercase">{coin.symbol}</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-3">
                            <div className="text-right">
                              <p className="font-mono text-sm">{formatPrice(coin.current_price)}</p>
                              <p className={`text-xs font-mono ${coin.price_change_percentage_24h >= 0 ? "text-emerald-500" : "text-rose-500"}`}>
                                {formatPercent(coin.price_change_percentage_24h)}
                              </p>
                            </div>
                            <Plus className="w-5 h-5 text-primary" />
                          </div>
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </CardHeader>
        <CardContent>
          {watchlistCoins.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {watchlistCoins.map((coin) => {
                const sparklineData = getSparklineData(coin);
                const isPositive = coin.price_change_percentage_24h >= 0;
                
                return (
                  <Card 
                    key={coin.id} 
                    className="glass border-white/10 overflow-hidden group hover:border-primary/30 transition-all"
                    data-testid={`watchlist-card-${coin.id}`}
                  >
                    <CardContent className="p-4">
                      {/* Header */}
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <img src={coin.image} alt={coin.name} className="w-10 h-10 rounded-full" />
                          <div>
                            <p className="font-bold">{coin.name}</p>
                            <p className="text-xs text-muted-foreground uppercase">{coin.symbol}/USD</p>
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => removeFromWatchlist(coin.id)}
                          className="opacity-0 group-hover:opacity-100 transition-opacity hover:bg-rose-500/10 hover:text-rose-500"
                          data-testid={`remove-${coin.id}`}
                        >
                          <X className="w-4 h-4" />
                        </Button>
                      </div>

                      {/* Price & Change */}
                      <div className="flex items-end justify-between mb-3">
                        <div>
                          <p className="text-2xl font-bold font-mono">{formatPrice(coin.current_price)}</p>
                          <div className={`flex items-center gap-1 ${isPositive ? "text-emerald-500" : "text-rose-500"}`}>
                            {isPositive ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
                            <span className="font-mono text-sm">{formatPercent(coin.price_change_percentage_24h)}</span>
                            <span className="text-xs text-muted-foreground">24h</span>
                          </div>
                        </div>
                        
                        {/* Mini Chart */}
                        {sparklineData.length > 0 && (
                          <div className="w-20 h-12">
                            <ResponsiveContainer width="100%" height="100%">
                              <AreaChart data={sparklineData}>
                                <defs>
                                  <linearGradient id={`gradient-${coin.id}`} x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor={isPositive ? "#10B981" : "#F43F5E"} stopOpacity={0.3} />
                                    <stop offset="95%" stopColor={isPositive ? "#10B981" : "#F43F5E"} stopOpacity={0} />
                                  </linearGradient>
                                </defs>
                                <Area
                                  type="monotone"
                                  dataKey="price"
                                  stroke={isPositive ? "#10B981" : "#F43F5E"}
                                  strokeWidth={1.5}
                                  fill={`url(#gradient-${coin.id})`}
                                />
                              </AreaChart>
                            </ResponsiveContainer>
                          </div>
                        )}
                      </div>

                      {/* High/Low */}
                      <div className="flex items-center justify-between text-xs text-muted-foreground mb-4">
                        <span>Low: <span className="font-mono text-rose-400">{formatPrice(coin.low_24h)}</span></span>
                        <span>High: <span className="font-mono text-emerald-400">{formatPrice(coin.high_24h)}</span></span>
                      </div>

                      {/* Analyze Button */}
                      <Button
                        onClick={() => analyzeCoin(coin)}
                        className="w-full bg-gradient-to-r from-violet-500 to-fuchsia-500 hover:from-violet-600 hover:to-fuchsia-600 text-white font-bold"
                        data-testid={`analyze-${coin.id}`}
                      >
                        <Sparkles className="w-4 h-4 mr-2" />
                        Analyser ({TIMEFRAMES.find(t => t.value === selectedTimeframe)?.label})
                      </Button>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-16">
              <Star className="w-16 h-16 text-muted-foreground/30 mb-4" />
              <h3 className="text-lg font-medium mb-2">Votre watchlist est vide</h3>
              <p className="text-muted-foreground text-center max-w-md mb-4">
                Ajoutez des cryptomonnaies pour les suivre et obtenir des analyses de trading personnalisées.
              </p>
              <Button onClick={() => setAddDialogOpen(true)} className="bg-primary hover:bg-primary/90 text-black">
                <Plus className="w-4 h-4 mr-2" />
                Ajouter des cryptos
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Analysis Dialog */}
      <Dialog open={analysisDialogOpen} onOpenChange={setAnalysisDialogOpen}>
        <DialogContent className="glass border-white/10 max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-3">
              {selectedCoin && (
                <>
                  <img src={selectedCoin.image} alt={selectedCoin.name} className="w-8 h-8 rounded-full" />
                  <span>Analyse {selectedCoin.name}</span>
                  <Badge variant="secondary" className="ml-2">
                    {TIMEFRAMES.find(t => t.value === selectedTimeframe)?.label}
                  </Badge>
                </>
              )}
            </DialogTitle>
            <DialogDescription>
              Signal de trading généré par l'IA BULL SAGE
            </DialogDescription>
          </DialogHeader>
          
          <div className="mt-4">
            {analyzing ? (
              <div className="flex flex-col items-center justify-center py-12">
                <Loader2 className="w-12 h-12 animate-spin text-violet-500 mb-4" />
                <p className="text-muted-foreground">Analyse en cours...</p>
                <p className="text-xs text-muted-foreground mt-1">
                  Récupération des données temps réel et génération du signal
                </p>
              </div>
            ) : analysisResult ? (
              <div className="prose prose-sm prose-invert max-w-none">
                <div className="p-4 rounded-lg bg-black/20 border border-white/10 whitespace-pre-wrap">
                  {analysisResult}
                </div>
                
                {/* Quick Info */}
                {selectedCoin && (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4">
                    <div className="p-3 rounded-lg bg-white/5">
                      <p className="text-xs text-muted-foreground">Prix actuel</p>
                      <p className="font-mono font-bold">{formatPrice(selectedCoin.current_price)}</p>
                    </div>
                    <div className="p-3 rounded-lg bg-white/5">
                      <p className="text-xs text-muted-foreground">24h Change</p>
                      <p className={`font-mono font-bold ${selectedCoin.price_change_percentage_24h >= 0 ? "text-emerald-500" : "text-rose-500"}`}>
                        {formatPercent(selectedCoin.price_change_percentage_24h)}
                      </p>
                    </div>
                    <div className="p-3 rounded-lg bg-white/5">
                      <p className="text-xs text-muted-foreground">24h Low</p>
                      <p className="font-mono font-bold text-rose-400">{formatPrice(selectedCoin.low_24h)}</p>
                    </div>
                    <div className="p-3 rounded-lg bg-white/5">
                      <p className="text-xs text-muted-foreground">24h High</p>
                      <p className="font-mono font-bold text-emerald-400">{formatPrice(selectedCoin.high_24h)}</p>
                    </div>
                  </div>
                )}
                
                <div className="flex gap-2 mt-4">
                  <Button
                    onClick={() => analyzeCoin(selectedCoin)}
                    variant="outline"
                    className="flex-1 border-white/10"
                  >
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Nouvelle analyse
                  </Button>
                  <Link to="/assistant" className="flex-1">
                    <Button className="w-full bg-violet-500 hover:bg-violet-600">
                      <Sparkles className="w-4 h-4 mr-2" />
                      Discussion détaillée
                    </Button>
                  </Link>
                </div>
              </div>
            ) : null}
          </div>
        </DialogContent>
      </Dialog>

      {/* Quick Actions */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Link to="/markets">
          <Card className="glass border-white/5 card-hover cursor-pointer">
            <CardContent className="pt-6 text-center">
              <TrendingUp className="w-8 h-8 mx-auto text-blue-500 mb-2" />
              <p className="font-medium">Tous les Marchés</p>
              <p className="text-xs text-muted-foreground">50+ cryptos</p>
            </CardContent>
          </Card>
        </Link>
        <Link to="/paper-trading">
          <Card className="glass border-white/5 card-hover cursor-pointer">
            <CardContent className="pt-6 text-center">
              <Wallet className="w-8 h-8 mx-auto text-primary mb-2" />
              <p className="font-medium">Paper Trading</p>
              <p className="text-xs text-muted-foreground">S'entraîner</p>
            </CardContent>
          </Card>
        </Link>
        <Link to="/strategies">
          <Card className="glass border-white/5 card-hover cursor-pointer">
            <CardContent className="pt-6 text-center">
              <Target className="w-8 h-8 mx-auto text-yellow-500 mb-2" />
              <p className="font-medium">Stratégies</p>
              <p className="text-xs text-muted-foreground">Mes règles</p>
            </CardContent>
          </Card>
        </Link>
        <Link to="/assistant">
          <Card className="glass border-violet-500/20 card-hover cursor-pointer">
            <CardContent className="pt-6 text-center">
              <Sparkles className="w-8 h-8 mx-auto text-violet-400 mb-2" />
              <p className="font-medium">Assistant IA</p>
              <p className="text-xs text-muted-foreground">Chat complet</p>
            </CardContent>
          </Card>
        </Link>
      </div>
    </div>
  );
}
