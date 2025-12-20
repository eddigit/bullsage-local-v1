import { useState, useEffect } from "react";
import { API, useAuth } from "../App";
import axios from "axios";
import { toast } from "sonner";
import {
  Wallet,
  TrendingUp,
  TrendingDown,
  ArrowUpRight,
  ArrowDownRight,
  RefreshCw,
  History,
  PieChart,
  DollarSign,
  RotateCcw,
  Plus,
  Minus
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Badge } from "../components/ui/badge";
import { ScrollArea } from "../components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "../components/ui/alert-dialog";

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

export default function PaperTradingPage() {
  const { user } = useAuth();
  const [portfolio, setPortfolio] = useState({ balance: 10000, portfolio: {} });
  const [trades, setTrades] = useState([]);
  const [markets, setMarkets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [tradeDialogOpen, setTradeDialogOpen] = useState(false);
  
  // Trade form state
  const [selectedCoin, setSelectedCoin] = useState("");
  const [tradeType, setTradeType] = useState("buy");
  const [tradeAmount, setTradeAmount] = useState("");
  const [submitting, setSubmitting] = useState(false);
  
  // Stats state
  const [tradingStats, setTradingStats] = useState(null);
  const [loadingStats, setLoadingStats] = useState(false);

  const fetchData = async () => {
    try {
      const [portfolioRes, tradesRes, marketsRes] = await Promise.all([
        axios.get(`${API}/paper-trading/portfolio`),
        axios.get(`${API}/paper-trading/trades`),
        axios.get(`${API}/market/crypto`)
      ]);
      
      setPortfolio(portfolioRes.data);
      setTrades(tradesRes.data);
      setMarkets(marketsRes.data || []);
    } catch (error) {
      console.error("Error fetching data:", error);
      toast.error("Erreur lors du chargement des données");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const fetchStats = async () => {
    setLoadingStats(true);
    try {
      const response = await axios.get(`${API}/paper-trading/stats`);
      setTradingStats(response.data);
    } catch (error) {
      console.error("Error fetching stats:", error);
    } finally {
      setLoadingStats(false);
    }
  };

  useEffect(() => {
    fetchData();
    fetchStats();
    const interval = setInterval(fetchData, 60000);
    return () => clearInterval(interval);
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchData();
    toast.success("Données actualisées");
  };

  const handleTrade = async () => {
    if (!selectedCoin || !tradeAmount || parseFloat(tradeAmount) <= 0) {
      toast.error("Veuillez remplir tous les champs correctement");
      return;
    }

    const coin = markets.find(c => c.id === selectedCoin);
    if (!coin) {
      toast.error("Crypto non trouvée");
      return;
    }

    setSubmitting(true);
    try {
      await axios.post(`${API}/paper-trading/trade`, {
        symbol: selectedCoin,
        type: tradeType,
        amount: parseFloat(tradeAmount),
        price: coin.current_price
      });

      toast.success(`${tradeType === "buy" ? "Achat" : "Vente"} exécuté avec succès!`);
      setTradeDialogOpen(false);
      setSelectedCoin("");
      setTradeAmount("");
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erreur lors de l'exécution du trade");
    } finally {
      setSubmitting(false);
    }
  };

  const handleReset = async () => {
    try {
      await axios.post(`${API}/paper-trading/reset`);
      toast.success("Portfolio réinitialisé");
      fetchData();
    } catch (error) {
      toast.error("Erreur lors de la réinitialisation");
    }
  };

  // Calculate portfolio value
  const calculatePortfolioValue = () => {
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

  // Get current price for selected coin
  const selectedCoinData = markets.find(c => c.id === selectedCoin);
  const tradeValue = selectedCoinData && tradeAmount 
    ? parseFloat(tradeAmount) * selectedCoinData.current_price 
    : 0;

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-48 bg-white/5 rounded animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-32 bg-white/5 rounded-xl animate-pulse" />
          ))}
        </div>
        <div className="h-96 bg-white/5 rounded-xl animate-pulse" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="paper-trading-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold font-manrope">Paper Trading</h1>
          <p className="text-muted-foreground">
            Pratiquez le trading sans risque avec un capital virtuel
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={handleRefresh}
            disabled={refreshing}
            className="border-white/10 hover:bg-white/5"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? "animate-spin" : ""}`} />
            Actualiser
          </Button>
          
          <Dialog open={tradeDialogOpen} onOpenChange={setTradeDialogOpen}>
            <DialogTrigger asChild>
              <Button className="bg-primary hover:bg-primary/90 text-black font-bold" data-testid="new-trade-btn">
                <Plus className="w-4 h-4 mr-2" />
                Nouveau Trade
              </Button>
            </DialogTrigger>
            <DialogContent className="glass border-white/10">
              <DialogHeader>
                <DialogTitle>Nouveau Trade</DialogTitle>
                <DialogDescription>
                  Exécutez un trade sur votre portfolio virtuel
                </DialogDescription>
              </DialogHeader>
              
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label>Type de trade</Label>
                  <div className="grid grid-cols-2 gap-2">
                    <Button
                      type="button"
                      variant={tradeType === "buy" ? "default" : "outline"}
                      onClick={() => setTradeType("buy")}
                      className={tradeType === "buy" ? "bg-emerald-500 hover:bg-emerald-600" : "border-white/10"}
                      data-testid="trade-buy-btn"
                    >
                      <ArrowUpRight className="w-4 h-4 mr-2" />
                      Acheter
                    </Button>
                    <Button
                      type="button"
                      variant={tradeType === "sell" ? "default" : "outline"}
                      onClick={() => setTradeType("sell")}
                      className={tradeType === "sell" ? "bg-rose-500 hover:bg-rose-600" : "border-white/10"}
                      data-testid="trade-sell-btn"
                    >
                      <ArrowDownRight className="w-4 h-4 mr-2" />
                      Vendre
                    </Button>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Cryptomonnaie</Label>
                  <Select value={selectedCoin} onValueChange={setSelectedCoin}>
                    <SelectTrigger className="bg-black/20 border-white/10" data-testid="coin-select">
                      <SelectValue placeholder="Sélectionner une crypto" />
                    </SelectTrigger>
                    <SelectContent className="glass border-white/10 max-h-64">
                      {markets.slice(0, 30).map(coin => (
                        <SelectItem key={coin.id} value={coin.id}>
                          <div className="flex items-center gap-2">
                            <img src={coin.image} alt={coin.name} className="w-5 h-5 rounded-full" />
                            <span>{coin.name}</span>
                            <span className="text-muted-foreground">({coin.symbol.toUpperCase()})</span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {selectedCoinData && (
                    <p className="text-sm text-muted-foreground">
                      Prix actuel: <span className="font-mono text-primary">{formatPrice(selectedCoinData.current_price)}</span>
                    </p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label>Quantité</Label>
                  <Input
                    type="number"
                    value={tradeAmount}
                    onChange={(e) => setTradeAmount(e.target.value)}
                    placeholder="0.00"
                    className="bg-black/20 border-white/10 font-mono"
                    step="0.0001"
                    min="0"
                    data-testid="trade-amount"
                  />
                  {tradeValue > 0 && (
                    <p className="text-sm text-muted-foreground">
                      Valeur totale: <span className="font-mono text-primary">{formatPrice(tradeValue)}</span>
                    </p>
                  )}
                </div>

                <div className="p-3 rounded-lg bg-white/5 border border-white/10">
                  <p className="text-sm text-muted-foreground">
                    Solde disponible: <span className="font-mono text-foreground">{formatPrice(portfolio.balance)}</span>
                  </p>
                </div>
              </div>

              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => setTradeDialogOpen(false)}
                  className="border-white/10"
                >
                  Annuler
                </Button>
                <Button
                  onClick={handleTrade}
                  disabled={submitting || !selectedCoin || !tradeAmount}
                  className={tradeType === "buy" ? "bg-emerald-500 hover:bg-emerald-600" : "bg-rose-500 hover:bg-rose-600"}
                  data-testid="execute-trade-btn"
                >
                  {submitting ? "Exécution..." : tradeType === "buy" ? "Acheter" : "Vendre"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="glass border-white/5">
          <CardContent className="pt-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Valeur du Portfolio</p>
                <p className="text-2xl font-bold font-mono mt-1" data-testid="total-value">
                  {formatPrice(portfolioValue)}
                </p>
                <div className={`flex items-center gap-1 mt-1 ${portfolioChange >= 0 ? "text-emerald-500" : "text-rose-500"}`}>
                  {portfolioChange >= 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                  <span className="text-sm font-mono">{formatPercent(portfolioChange)}</span>
                </div>
              </div>
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                <PieChart className="w-5 h-5 text-primary" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="glass border-white/5">
          <CardContent className="pt-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Solde Disponible</p>
                <p className="text-2xl font-bold font-mono mt-1" data-testid="available-balance">
                  {formatPrice(portfolio.balance)}
                </p>
                <p className="text-sm text-muted-foreground mt-1">Cash disponible</p>
              </div>
              <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
                <DollarSign className="w-5 h-5 text-blue-500" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="glass border-white/5">
          <CardContent className="pt-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Capital Initial</p>
                <p className="text-2xl font-bold font-mono mt-1">$10,000.00</p>
                <AlertDialog>
                  <AlertDialogTrigger asChild>
                    <Button variant="link" className="p-0 h-auto text-sm text-muted-foreground hover:text-destructive">
                      <RotateCcw className="w-3 h-3 mr-1" />
                      Réinitialiser
                    </Button>
                  </AlertDialogTrigger>
                  <AlertDialogContent className="glass border-white/10">
                    <AlertDialogHeader>
                      <AlertDialogTitle>Réinitialiser le portfolio?</AlertDialogTitle>
                      <AlertDialogDescription>
                        Cette action supprimera tous vos trades et réinitialisera votre solde à $10,000.
                      </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel className="border-white/10">Annuler</AlertDialogCancel>
                      <AlertDialogAction onClick={handleReset} className="bg-destructive hover:bg-destructive/90">
                        Réinitialiser
                      </AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
              </div>
              <div className="w-10 h-10 rounded-lg bg-yellow-500/10 flex items-center justify-center">
                <Wallet className="w-5 h-5 text-yellow-500" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="portfolio" className="space-y-4">
        <TabsList className="bg-black/20 border border-white/10">
          <TabsTrigger value="portfolio" className="data-[state=active]:bg-primary data-[state=active]:text-black">
            <Wallet className="w-4 h-4 mr-2" />
            Portfolio
          </TabsTrigger>
          <TabsTrigger value="stats" className="data-[state=active]:bg-primary data-[state=active]:text-black">
            <PieChart className="w-4 h-4 mr-2" />
            Stats
          </TabsTrigger>
          <TabsTrigger value="history" className="data-[state=active]:bg-primary data-[state=active]:text-black">
            <History className="w-4 h-4 mr-2" />
            Historique
          </TabsTrigger>
        </TabsList>

        <TabsContent value="portfolio">
          <Card className="glass border-white/5">
            <CardHeader>
              <CardTitle className="text-lg">Mes Positions</CardTitle>
              <CardDescription>Vos positions actuelles en crypto</CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[400px]">
                {Object.keys(portfolio.portfolio || {}).length > 0 ? (
                  <div className="space-y-3">
                    {Object.entries(portfolio.portfolio).map(([symbol, holding]) => {
                      const coin = markets.find(c => c.id === symbol);
                      const currentValue = coin ? holding.amount * coin.current_price : 0;
                      const costBasis = holding.amount * holding.avg_price;
                      const pnl = currentValue - costBasis;
                      const pnlPercent = costBasis > 0 ? (pnl / costBasis) * 100 : 0;

                      return (
                        <div
                          key={symbol}
                          className="p-4 rounded-lg bg-white/5 border border-white/10"
                          data-testid={`position-${symbol}`}
                        >
                          <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center gap-3">
                              {coin && <img src={coin.image} alt={coin.name} className="w-10 h-10 rounded-full" />}
                              <div>
                                <p className="font-medium">{coin?.name || symbol}</p>
                                <p className="text-sm text-muted-foreground uppercase">{symbol}</p>
                              </div>
                            </div>
                            <Badge className={pnl >= 0 ? "bg-emerald-500/20 text-emerald-500" : "bg-rose-500/20 text-rose-500"}>
                              {formatPercent(pnlPercent)} P&L
                            </Badge>
                          </div>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                            <div>
                              <p className="text-muted-foreground">Quantité</p>
                              <p className="font-mono font-medium">{holding.amount.toFixed(6)}</p>
                            </div>
                            <div>
                              <p className="text-muted-foreground">Prix moyen</p>
                              <p className="font-mono font-medium">{formatPrice(holding.avg_price)}</p>
                            </div>
                            <div>
                              <p className="text-muted-foreground">Valeur actuelle</p>
                              <p className="font-mono font-medium">{formatPrice(currentValue)}</p>
                            </div>
                            <div>
                              <p className="text-muted-foreground">P&L</p>
                              <p className={`font-mono font-medium ${pnl >= 0 ? "text-emerald-500" : "text-rose-500"}`}>
                                {pnl >= 0 ? "+" : ""}{formatPrice(pnl)}
                              </p>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center h-full py-12">
                    <Wallet className="w-16 h-16 text-muted-foreground/30 mb-4" />
                    <p className="text-muted-foreground text-center">
                      Aucune position ouverte
                    </p>
                    <p className="text-sm text-muted-foreground text-center mt-1">
                      Commencez par acheter une crypto
                    </p>
                  </div>
                )}
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="stats">
          <div className="space-y-4">
            {/* Performance Overview */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Card className="glass border-white/5">
                <CardContent className="pt-4 pb-4 text-center">
                  <p className="text-xs text-muted-foreground">Trades Total</p>
                  <p className="text-2xl font-bold font-mono">{tradingStats?.total_trades || 0}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {tradingStats?.buy_trades || 0} achats / {tradingStats?.sell_trades || 0} ventes
                  </p>
                </CardContent>
              </Card>
              
              <Card className="glass border-white/5">
                <CardContent className="pt-4 pb-4 text-center">
                  <p className="text-xs text-muted-foreground">Volume Total</p>
                  <p className="text-2xl font-bold font-mono">{formatPrice(tradingStats?.total_volume || 0)}</p>
                </CardContent>
              </Card>
              
              <Card className={`glass border-2 ${(tradingStats?.total_pnl || 0) >= 0 ? "border-emerald-500/30" : "border-rose-500/30"}`}>
                <CardContent className="pt-4 pb-4 text-center">
                  <p className="text-xs text-muted-foreground">P&L Total</p>
                  <p className={`text-2xl font-bold font-mono ${(tradingStats?.total_pnl || 0) >= 0 ? "text-emerald-500" : "text-rose-500"}`}>
                    {(tradingStats?.total_pnl || 0) >= 0 ? "+" : ""}{formatPrice(tradingStats?.total_pnl || 0)}
                  </p>
                  <p className={`text-xs font-mono ${(tradingStats?.total_pnl_percent || 0) >= 0 ? "text-emerald-500" : "text-rose-500"}`}>
                    {(tradingStats?.total_pnl_percent || 0) >= 0 ? "+" : ""}{(tradingStats?.total_pnl_percent || 0).toFixed(2)}%
                  </p>
                </CardContent>
              </Card>
              
              <Card className="glass border-white/5">
                <CardContent className="pt-4 pb-4 text-center">
                  <p className="text-xs text-muted-foreground">Valeur Portfolio</p>
                  <p className="text-2xl font-bold font-mono">{formatPrice(tradingStats?.portfolio_value || 10000)}</p>
                </CardContent>
              </Card>
            </div>
            
            {/* Best/Worst & Most Traded */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card className="glass border-white/5">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <ArrowUpRight className="w-4 h-4 text-emerald-500" />
                    Meilleur Trade
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {tradingStats?.best_trade ? (
                    <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                      <p className="font-medium">{tradingStats.best_trade.symbol}</p>
                      <p className="text-lg font-mono text-emerald-500">
                        +{formatPrice(tradingStats.best_trade.pnl)} ({tradingStats.best_trade.pnl_percent}%)
                      </p>
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">Aucun trade réalisé</p>
                  )}
                </CardContent>
              </Card>
              
              <Card className="glass border-white/5">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <ArrowDownRight className="w-4 h-4 text-rose-500" />
                    Pire Trade
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {tradingStats?.worst_trade ? (
                    <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20">
                      <p className="font-medium">{tradingStats.worst_trade.symbol}</p>
                      <p className="text-lg font-mono text-rose-500">
                        {formatPrice(tradingStats.worst_trade.pnl)} ({tradingStats.worst_trade.pnl_percent}%)
                      </p>
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">Aucun trade réalisé</p>
                  )}
                </CardContent>
              </Card>
              
              <Card className="glass border-white/5">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-primary" />
                    Crypto Favorite
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {tradingStats?.most_traded ? (
                    <div className="p-3 rounded-lg bg-primary/10 border border-primary/20">
                      <p className="font-medium capitalize">{tradingStats.most_traded.replace("-", " ")}</p>
                      <p className="text-sm text-muted-foreground">La plus tradée</p>
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">Aucun trade</p>
                  )}
                </CardContent>
              </Card>
            </div>
            
            {/* Recent Activity */}
            <Card className="glass border-white/5">
              <CardHeader>
                <CardTitle className="text-lg">Activité Récente</CardTitle>
              </CardHeader>
              <CardContent>
                {tradingStats?.trading_history?.length > 0 ? (
                  <div className="space-y-2">
                    {tradingStats.trading_history.map((trade, idx) => (
                      <div key={idx} className="flex items-center justify-between p-3 rounded-lg bg-white/5">
                        <div className="flex items-center gap-3">
                          <Badge className={trade.type === "buy" ? "bg-emerald-500/20 text-emerald-400" : "bg-rose-500/20 text-rose-400"}>
                            {trade.type === "buy" ? "ACHAT" : "VENTE"}
                          </Badge>
                          <span className="font-medium capitalize">{trade.symbol.replace("-", " ")}</span>
                        </div>
                        <div className="text-right">
                          <p className="font-mono">{formatPrice(trade.value)}</p>
                          <p className="text-xs text-muted-foreground">{trade.timestamp}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-center text-muted-foreground py-8">Aucune activité récente</p>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="history">
          <Card className="glass border-white/5">
            <CardHeader>
              <CardTitle className="text-lg">Historique des Trades</CardTitle>
              <CardDescription>Vos transactions récentes</CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[400px]">
                {trades.length > 0 ? (
                  <div className="space-y-2">
                    {trades.map((trade) => {
                      const coin = markets.find(c => c.id === trade.symbol);
                      return (
                        <div
                          key={trade.id}
                          className="flex items-center justify-between p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
                          data-testid={`trade-${trade.id}`}
                        >
                          <div className="flex items-center gap-3">
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                              trade.type === "buy" ? "bg-emerald-500/20" : "bg-rose-500/20"
                            }`}>
                              {trade.type === "buy" ? (
                                <Plus className="w-4 h-4 text-emerald-500" />
                              ) : (
                                <Minus className="w-4 h-4 text-rose-500" />
                              )}
                            </div>
                            <div>
                              <p className="font-medium">
                                {trade.type === "buy" ? "Achat" : "Vente"} {coin?.name || trade.symbol}
                              </p>
                              <p className="text-xs text-muted-foreground">
                                {new Date(trade.timestamp).toLocaleString("fr-FR")}
                              </p>
                            </div>
                          </div>
                          <div className="text-right">
                            <p className="font-mono font-medium">
                              {trade.amount.toFixed(6)} {trade.symbol.toUpperCase()}
                            </p>
                            <p className="text-sm text-muted-foreground font-mono">
                              @ {formatPrice(trade.price)}
                            </p>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center h-full py-12">
                    <History className="w-16 h-16 text-muted-foreground/30 mb-4" />
                    <p className="text-muted-foreground text-center">
                      Aucun trade effectué
                    </p>
                  </div>
                )}
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
