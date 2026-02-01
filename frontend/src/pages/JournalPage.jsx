import { useState, useEffect } from "react";
import { useAuth, API } from "../App";
import axios from "axios";
import { toast } from "sonner";
import {
  BookOpen,
  Plus,
  TrendingUp,
  TrendingDown,
  Calendar,
  Target,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  BarChart3,
  Brain,
  Heart,
  Loader2,
  RefreshCw,
  ChevronDown,
  X,
  Award,
  Flame,
  Zap,
  PiggyBank
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
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

const EMOTIONS = [
  { value: "calm", label: "Calme 😌", color: "text-emerald-500" },
  { value: "confident", label: "Confiant 💪", color: "text-blue-500" },
  { value: "excited", label: "Excité 🔥", color: "text-orange-500" },
  { value: "anxious", label: "Anxieux 😰", color: "text-yellow-500" },
  { value: "fearful", label: "Peur 😨", color: "text-rose-500" },
];

const TIMEFRAMES = ["1h", "4h", "1d", "1w"];

const formatPrice = (price) => {
  if (!price) return "$0.00";
  if (price >= 1000) return `$${price.toLocaleString("en-US", { maximumFractionDigits: 2 })}`;
  if (price >= 1) return `$${price.toFixed(2)}`;
  return `$${price.toFixed(6)}`;
};

const formatDate = (dateStr) => {
  if (!dateStr) return "-";
  const date = new Date(dateStr);
  return date.toLocaleDateString("fr-FR", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });
};

export default function JournalPage() {
  const { user } = useAuth();
  const [trades, setTrades] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [markets, setMarkets] = useState([]);
  const [filter, setFilter] = useState("all");
  
  // New trade dialog
  const [newTradeOpen, setNewTradeOpen] = useState(false);
  const [newTrade, setNewTrade] = useState({
    symbol: "",
    symbol_name: "",
    trade_type: "BUY",
    entry_price: "",
    quantity: "",
    timeframe: "4h",
    stop_loss: "",
    take_profit: "",
    emotion_before: "",
    strategy_used: "",
    reason_entry: ""
  });
  const [submitting, setSubmitting] = useState(false);
  
  // Close trade dialog
  const [closeTradeOpen, setCloseTradeOpen] = useState(false);
  const [selectedTrade, setSelectedTrade] = useState(null);
  const [closeTrade, setCloseTrade] = useState({
    exit_price: "",
    emotion_after: "",
    reason_exit: "",
    lessons_learned: ""
  });

  const fetchData = async () => {
    // Fetch each resource independently so one failure doesn't block others
    const results = await Promise.allSettled([
      axios.get(`${API}/journal/trades`),
      axios.get(`${API}/journal/stats`),
      axios.get(`${API}/market/crypto`)
    ]);

    if (results[0].status === "fulfilled") {
      setTrades(Array.isArray(results[0].value.data) ? results[0].value.data : []);
    } else {
      console.error("Error fetching trades:", results[0].reason);
    }

    if (results[1].status === "fulfilled") {
      setStats(results[1].value.data || {});
    } else {
      console.error("Error fetching stats:", results[1].reason);
      setStats({ total_trades: 0, win_rate: 0, total_pnl: 0, profit_factor: 0, average_rr: 0, current_streak: 0 });
    }

    if (results[2].status === "fulfilled") {
      setMarkets(Array.isArray(results[2].value.data) ? results[2].value.data : []);
    } else {
      console.error("Error fetching markets for journal:", results[2].reason);
    }

    setLoading(false);
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCreateTrade = async () => {
    if (!newTrade.symbol || !newTrade.entry_price || !newTrade.stop_loss || !newTrade.take_profit) {
      toast.error("Remplissez tous les champs obligatoires");
      return;
    }
    
    setSubmitting(true);
    try {
      await axios.post(`${API}/journal/trades`, {
        ...newTrade,
        entry_price: parseFloat(newTrade.entry_price),
        quantity: parseFloat(newTrade.quantity) || 1,
        stop_loss: parseFloat(newTrade.stop_loss),
        take_profit: parseFloat(newTrade.take_profit)
      });
      toast.success("Trade ajouté au journal");
      setNewTradeOpen(false);
      setNewTrade({
        symbol: "", symbol_name: "", trade_type: "BUY", entry_price: "",
        quantity: "", timeframe: "4h", stop_loss: "", take_profit: "",
        emotion_before: "", strategy_used: "", reason_entry: ""
      });
      fetchData();
    } catch (error) {
      toast.error("Erreur lors de l'ajout du trade");
    } finally {
      setSubmitting(false);
    }
  };

  const handleCloseTrade = async () => {
    if (!closeTrade.exit_price) {
      toast.error("Entrez le prix de sortie");
      return;
    }
    
    setSubmitting(true);
    try {
      const response = await axios.put(`${API}/journal/trades/${selectedTrade.id}/close`, {
        exit_price: parseFloat(closeTrade.exit_price),
        emotion_after: closeTrade.emotion_after,
        reason_exit: closeTrade.reason_exit,
        lessons_learned: closeTrade.lessons_learned
      });
      
      const pnl = response.data.pnl_percent;
      if (pnl > 0) {
        toast.success(`Trade clôturé avec +${pnl}% de profit ! 🎉`);
      } else if (pnl < 0) {
        toast.info(`Trade clôturé avec ${pnl}% de perte. Analysez ce qui n'a pas fonctionné.`);
      } else {
        toast.info("Trade clôturé à l'équilibre");
      }
      
      setCloseTradeOpen(false);
      setSelectedTrade(null);
      setCloseTrade({ exit_price: "", emotion_after: "", reason_exit: "", lessons_learned: "" });
      fetchData();
    } catch (error) {
      toast.error("Erreur lors de la clôture du trade");
    } finally {
      setSubmitting(false);
    }
  };

  const filteredTrades = trades.filter(t => {
    if (filter === "all") return true;
    if (filter === "open") return t.status === "open";
    if (filter === "profit") return t.status === "closed_profit";
    if (filter === "loss") return t.status === "closed_loss";
    return true;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center">
            <BookOpen className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl md:text-3xl font-bold font-manrope">Journal de Trading</h1>
            <p className="text-sm text-muted-foreground">Suivez et analysez vos performances</p>
          </div>
        </div>
        
        <Button
          onClick={() => setNewTradeOpen(true)}
          className="bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white"
        >
          <Plus className="w-4 h-4 mr-2" />
          Nouveau Trade
        </Button>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
          <Card className="glass border-white/5">
            <CardContent className="pt-4 text-center">
              <p className="text-xs text-muted-foreground">Total Trades</p>
              <p className="text-2xl font-bold">{stats.total_trades}</p>
            </CardContent>
          </Card>
          
          <Card className="glass border-white/5">
            <CardContent className="pt-4 text-center">
              <p className="text-xs text-muted-foreground">Win Rate</p>
              <p className={`text-2xl font-bold ${stats.win_rate >= 50 ? "text-emerald-500" : "text-rose-500"}`}>
                {stats.win_rate}%
              </p>
            </CardContent>
          </Card>
          
          <Card className="glass border-white/5">
            <CardContent className="pt-4 text-center">
              <p className="text-xs text-muted-foreground">P&L Total</p>
              <p className={`text-2xl font-bold ${stats.total_pnl >= 0 ? "text-emerald-500" : "text-rose-500"}`}>
                {stats.total_pnl >= 0 ? "+" : ""}{stats.total_pnl}%
              </p>
            </CardContent>
          </Card>
          
          <Card className="glass border-white/5">
            <CardContent className="pt-4 text-center">
              <p className="text-xs text-muted-foreground">Profit Factor</p>
              <p className={`text-2xl font-bold ${stats.profit_factor >= 1.5 ? "text-emerald-500" : stats.profit_factor >= 1 ? "text-yellow-500" : "text-rose-500"}`}>
                {stats.profit_factor}
              </p>
            </CardContent>
          </Card>
          
          <Card className="glass border-white/5">
            <CardContent className="pt-4 text-center">
              <p className="text-xs text-muted-foreground">R:R Moyen</p>
              <p className="text-2xl font-bold text-blue-500">{stats.average_rr}</p>
            </CardContent>
          </Card>
          
          <Card className="glass border-white/5">
            <CardContent className="pt-4 text-center">
              <p className="text-xs text-muted-foreground">Série</p>
              <p className={`text-2xl font-bold flex items-center justify-center gap-1 ${stats.current_streak > 0 ? "text-emerald-500" : stats.current_streak < 0 ? "text-rose-500" : "text-muted-foreground"}`}>
                {stats.current_streak > 0 ? <Flame className="w-4 h-4" /> : null}
                {stats.current_streak > 0 ? `+${stats.current_streak}` : stats.current_streak}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Advanced Stats */}
      {stats && stats.total_trades > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="glass border-white/5">
            <CardContent className="pt-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-emerald-500/20 flex items-center justify-center">
                  <TrendingUp className="w-5 h-5 text-emerald-500" />
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Meilleur Trade</p>
                  <p className="text-xl font-bold text-emerald-500">+{stats.best_trade}%</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="glass border-white/5">
            <CardContent className="pt-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-rose-500/20 flex items-center justify-center">
                  <TrendingDown className="w-5 h-5 text-rose-500" />
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Pire Trade</p>
                  <p className="text-xl font-bold text-rose-500">{stats.worst_trade}%</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="glass border-white/5">
            <CardContent className="pt-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-violet-500/20 flex items-center justify-center">
                  <Target className="w-5 h-5 text-violet-500" />
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Crypto Favorite</p>
                  <p className="text-xl font-bold text-violet-500">{stats.most_traded_symbol}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filter & Trades List */}
      <Card className="glass border-white/5">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Calendar className="w-5 h-5 text-primary" />
              Historique des Trades
            </CardTitle>
            <Select value={filter} onValueChange={setFilter}>
              <SelectTrigger className="w-40 bg-black/20 border-white/10">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="glass border-white/10">
                <SelectItem value="all">Tous</SelectItem>
                <SelectItem value="open">Ouverts</SelectItem>
                <SelectItem value="profit">Gagnants</SelectItem>
                <SelectItem value="loss">Perdants</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          {filteredTrades.length === 0 ? (
            <div className="text-center py-12">
              <BookOpen className="w-12 h-12 text-muted-foreground/30 mx-auto mb-4" />
              <p className="text-muted-foreground">Aucun trade enregistré</p>
              <p className="text-sm text-muted-foreground/70">Cliquez sur &quot;Nouveau Trade&quot; pour commencer</p>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredTrades.map((trade) => (
                <div
                  key={trade.id}
                  className={`p-4 rounded-lg border ${
                    trade.status === "open" ? "bg-blue-500/5 border-blue-500/20" :
                    trade.status === "closed_profit" ? "bg-emerald-500/5 border-emerald-500/20" :
                    trade.status === "closed_loss" ? "bg-rose-500/5 border-rose-500/20" :
                    "bg-white/5 border-white/10"
                  }`}
                >
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                        trade.trade_type === "BUY" ? "bg-emerald-500/20" : "bg-rose-500/20"
                      }`}>
                        {trade.trade_type === "BUY" ? (
                          <TrendingUp className="w-5 h-5 text-emerald-500" />
                        ) : (
                          <TrendingDown className="w-5 h-5 text-rose-500" />
                        )}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold">{trade.symbol_name}</span>
                          <Badge variant="outline" className={trade.trade_type === "BUY" ? "text-emerald-500" : "text-rose-500"}>
                            {trade.trade_type}
                          </Badge>
                          <Badge variant="outline" className="text-muted-foreground">{trade.timeframe}</Badge>
                        </div>
                        <p className="text-xs text-muted-foreground">
                          Entrée: {formatPrice(trade.entry_price)}
                          {trade.exit_price && ` → Sortie: ${formatPrice(trade.exit_price)}`}
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <p className="text-xs text-muted-foreground">{formatDate(trade.entry_date)}</p>
                        {trade.pnl_percent !== null && (
                          <p className={`font-bold ${trade.pnl_percent >= 0 ? "text-emerald-500" : "text-rose-500"}`}>
                            {trade.pnl_percent >= 0 ? "+" : ""}{trade.pnl_percent}%
                          </p>
                        )}
                      </div>
                      
                      {trade.status === "open" && (
                        <Button
                          size="sm"
                          variant="outline"
                          className="border-amber-500/50 text-amber-500 hover:bg-amber-500/10"
                          onClick={() => {
                            setSelectedTrade(trade);
                            setCloseTradeOpen(true);
                          }}
                        >
                          Clôturer
                        </Button>
                      )}
                      
                      {trade.status !== "open" && (
                        <Badge className={
                          trade.status === "closed_profit" ? "bg-emerald-500/20 text-emerald-500" :
                          trade.status === "closed_loss" ? "bg-rose-500/20 text-rose-500" :
                          "bg-yellow-500/20 text-yellow-500"
                        }>
                          {trade.status === "closed_profit" ? <CheckCircle className="w-3 h-3 mr-1" /> :
                           trade.status === "closed_loss" ? <XCircle className="w-3 h-3 mr-1" /> :
                           <Clock className="w-3 h-3 mr-1" />}
                          {trade.status === "closed_profit" ? "Gagné" :
                           trade.status === "closed_loss" ? "Perdu" : "Breakeven"}
                        </Badge>
                      )}
                    </div>
                  </div>
                  
                  {/* Trade details */}
                  {(trade.reason_entry || trade.lessons_learned) && (
                    <div className="mt-3 pt-3 border-t border-white/5 text-sm">
                      {trade.reason_entry && (
                        <p className="text-muted-foreground">
                          <span className="text-primary">Raison:</span> {trade.reason_entry}
                        </p>
                      )}
                      {trade.lessons_learned && (
                        <p className="text-amber-400 mt-1">
                          <span className="text-amber-500">💡 Leçon:</span> {trade.lessons_learned}
                        </p>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* New Trade Dialog */}
      <Dialog open={newTradeOpen} onOpenChange={setNewTradeOpen}>
        <DialogContent className="glass border-white/10 max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Plus className="w-5 h-5 text-primary" />
              Nouveau Trade
            </DialogTitle>
            <DialogDescription>
              Enregistrez votre trade pour suivre vos performances
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            {/* Symbol Selection */}
            <div className="space-y-2">
              <Label>Crypto *</Label>
              <Select
                value={newTrade.symbol}
                onValueChange={(value) => {
                  const coin = markets.find(m => m.id === value);
                  setNewTrade({
                    ...newTrade,
                    symbol: value,
                    symbol_name: coin?.name || value
                  });
                }}
              >
                <SelectTrigger className="bg-black/20 border-white/10">
                  <SelectValue placeholder="Sélectionner..." />
                </SelectTrigger>
                <SelectContent className="glass border-white/10 max-h-60">
                  {markets.slice(0, 30).map(coin => (
                    <SelectItem key={coin.id} value={coin.id}>
                      <div className="flex items-center gap-2">
                        <img src={coin.image} alt={coin.name} className="w-4 h-4 rounded-full" />
                        {coin.name}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            {/* Type & Timeframe */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Type *</Label>
                <Select value={newTrade.trade_type} onValueChange={(v) => setNewTrade({...newTrade, trade_type: v})}>
                  <SelectTrigger className="bg-black/20 border-white/10">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="glass border-white/10">
                    <SelectItem value="BUY">🟢 ACHAT (Long)</SelectItem>
                    <SelectItem value="SELL">🔴 VENTE (Short)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div className="space-y-2">
                <Label>Timeframe</Label>
                <Select value={newTrade.timeframe} onValueChange={(v) => setNewTrade({...newTrade, timeframe: v})}>
                  <SelectTrigger className="bg-black/20 border-white/10">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="glass border-white/10">
                    {TIMEFRAMES.map(tf => (
                      <SelectItem key={tf} value={tf}>{tf}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            {/* Prices */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Prix d&apos;entrée *</Label>
                <Input
                  type="number"
                  step="any"
                  placeholder="0.00"
                  value={newTrade.entry_price}
                  onChange={(e) => setNewTrade({...newTrade, entry_price: e.target.value})}
                  className="bg-black/20 border-white/10"
                />
              </div>
              
              <div className="space-y-2">
                <Label>Quantité</Label>
                <Input
                  type="number"
                  step="any"
                  placeholder="1"
                  value={newTrade.quantity}
                  onChange={(e) => setNewTrade({...newTrade, quantity: e.target.value})}
                  className="bg-black/20 border-white/10"
                />
              </div>
            </div>
            
            {/* SL & TP */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="text-rose-400">Stop-Loss *</Label>
                <Input
                  type="number"
                  step="any"
                  placeholder="0.00"
                  value={newTrade.stop_loss}
                  onChange={(e) => setNewTrade({...newTrade, stop_loss: e.target.value})}
                  className="bg-black/20 border-rose-500/30"
                />
              </div>
              
              <div className="space-y-2">
                <Label className="text-emerald-400">Take-Profit *</Label>
                <Input
                  type="number"
                  step="any"
                  placeholder="0.00"
                  value={newTrade.take_profit}
                  onChange={(e) => setNewTrade({...newTrade, take_profit: e.target.value})}
                  className="bg-black/20 border-emerald-500/30"
                />
              </div>
            </div>
            
            {/* Emotion */}
            <div className="space-y-2">
              <Label className="flex items-center gap-1">
                <Heart className="w-3 h-3" /> État émotionnel
              </Label>
              <Select value={newTrade.emotion_before} onValueChange={(v) => setNewTrade({...newTrade, emotion_before: v})}>
                <SelectTrigger className="bg-black/20 border-white/10">
                  <SelectValue placeholder="Comment vous sentez-vous ?" />
                </SelectTrigger>
                <SelectContent className="glass border-white/10">
                  {EMOTIONS.map(e => (
                    <SelectItem key={e.value} value={e.value}>{e.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            {/* Reason */}
            <div className="space-y-2">
              <Label>Raison du trade *</Label>
              <Textarea
                placeholder="Pourquoi prenez-vous ce trade ? (ex: RSI en survente, support touché...)"
                value={newTrade.reason_entry}
                onChange={(e) => setNewTrade({...newTrade, reason_entry: e.target.value})}
                className="bg-black/20 border-white/10 min-h-[80px]"
              />
            </div>
            
            <Button
              onClick={handleCreateTrade}
              disabled={submitting}
              className="w-full bg-gradient-to-r from-amber-500 to-orange-500"
            >
              {submitting ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Plus className="w-4 h-4 mr-2" />}
              Enregistrer le Trade
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Close Trade Dialog */}
      <Dialog open={closeTradeOpen} onOpenChange={setCloseTradeOpen}>
        <DialogContent className="glass border-white/10 max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Target className="w-5 h-5 text-amber-500" />
              Clôturer le Trade
            </DialogTitle>
            <DialogDescription>
              {selectedTrade?.symbol_name} - Entrée à {formatPrice(selectedTrade?.entry_price)}
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Prix de sortie *</Label>
              <Input
                type="number"
                step="any"
                placeholder="0.00"
                value={closeTrade.exit_price}
                onChange={(e) => setCloseTrade({...closeTrade, exit_price: e.target.value})}
                className="bg-black/20 border-white/10"
              />
            </div>
            
            <div className="space-y-2">
              <Label className="flex items-center gap-1">
                <Heart className="w-3 h-3" /> État émotionnel après
              </Label>
              <Select value={closeTrade.emotion_after} onValueChange={(v) => setCloseTrade({...closeTrade, emotion_after: v})}>
                <SelectTrigger className="bg-black/20 border-white/10">
                  <SelectValue placeholder="Comment vous sentez-vous ?" />
                </SelectTrigger>
                <SelectContent className="glass border-white/10">
                  {EMOTIONS.map(e => (
                    <SelectItem key={e.value} value={e.value}>{e.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label>Raison de sortie</Label>
              <Input
                placeholder="TP atteint, SL touché, changement de plan..."
                value={closeTrade.reason_exit}
                onChange={(e) => setCloseTrade({...closeTrade, reason_exit: e.target.value})}
                className="bg-black/20 border-white/10"
              />
            </div>
            
            <div className="space-y-2">
              <Label className="flex items-center gap-1">
                <Brain className="w-3 h-3" /> Leçon apprise
              </Label>
              <Textarea
                placeholder="Qu'avez-vous appris de ce trade ?"
                value={closeTrade.lessons_learned}
                onChange={(e) => setCloseTrade({...closeTrade, lessons_learned: e.target.value})}
                className="bg-black/20 border-white/10"
              />
            </div>
            
            <Button
              onClick={handleCloseTrade}
              disabled={submitting}
              className="w-full bg-gradient-to-r from-amber-500 to-orange-500"
            >
              {submitting ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <CheckCircle className="w-4 h-4 mr-2" />}
              Clôturer le Trade
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
