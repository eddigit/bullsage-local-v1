import { useState, useEffect } from "react";
import { API } from "../App";
import axios from "axios";
import { toast } from "sonner";
import {
  Target,
  Plus,
  Trash2,
  TrendingUp,
  TrendingDown,
  Shield,
  Zap,
  Clock,
  Play,
  Info
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Badge } from "../components/ui/badge";
import { ScrollArea } from "../components/ui/scroll-area";
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import { Checkbox } from "../components/ui/checkbox";

const INDICATORS = [
  { id: "rsi", name: "RSI (Relative Strength Index)", description: "Mesure la force du mouvement" },
  { id: "macd", name: "MACD", description: "Convergence/Divergence de moyennes mobiles" },
  { id: "sma", name: "SMA (Simple Moving Average)", description: "Moyenne mobile simple" },
  { id: "ema", name: "EMA (Exponential Moving Average)", description: "Moyenne mobile exponentielle" },
  { id: "bollinger", name: "Bandes de Bollinger", description: "Volatilité et niveaux de prix" },
  { id: "volume", name: "Volume", description: "Volume des échanges" },
  { id: "support_resistance", name: "Support/Résistance", description: "Niveaux clés de prix" },
  { id: "fibonacci", name: "Fibonacci", description: "Retracements de Fibonacci" },
];

export default function StrategiesPage() {
  const [strategies, setStrategies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Form state
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [selectedIndicators, setSelectedIndicators] = useState([]);
  const [entryRules, setEntryRules] = useState("");
  const [exitRules, setExitRules] = useState("");
  const [riskPercentage, setRiskPercentage] = useState("2");

  const fetchStrategies = async () => {
    try {
      const response = await axios.get(`${API}/strategies`);
      setStrategies(response.data);
    } catch (error) {
      console.error("Error fetching strategies:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStrategies();
  }, []);

  const handleCreate = async () => {
    if (!name || !description || selectedIndicators.length === 0) {
      toast.error("Veuillez remplir tous les champs obligatoires");
      return;
    }

    setSubmitting(true);
    try {
      await axios.post(`${API}/strategies`, {
        name,
        description,
        indicators: selectedIndicators,
        entry_rules: entryRules,
        exit_rules: exitRules,
        risk_percentage: parseFloat(riskPercentage)
      });

      toast.success("Stratégie créée avec succès!");
      setDialogOpen(false);
      resetForm();
      fetchStrategies();
    } catch (error) {
      toast.error("Erreur lors de la création de la stratégie");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id) => {
    try {
      await axios.delete(`${API}/strategies/${id}`);
      toast.success("Stratégie supprimée");
      fetchStrategies();
    } catch (error) {
      toast.error("Erreur lors de la suppression");
    }
  };

  const resetForm = () => {
    setName("");
    setDescription("");
    setSelectedIndicators([]);
    setEntryRules("");
    setExitRules("");
    setRiskPercentage("2");
  };

  const toggleIndicator = (indicatorId) => {
    setSelectedIndicators(prev =>
      prev.includes(indicatorId)
        ? prev.filter(id => id !== indicatorId)
        : [...prev, indicatorId]
    );
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-48 bg-white/5 rounded animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="h-48 bg-white/5 rounded-xl animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="strategies-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold font-manrope">Stratégies</h1>
          <p className="text-muted-foreground">
            Créez et gérez vos stratégies de trading
          </p>
        </div>
        
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button className="bg-primary hover:bg-primary/90 text-black font-bold" data-testid="new-strategy-btn">
              <Plus className="w-4 h-4 mr-2" />
              Nouvelle Stratégie
            </Button>
          </DialogTrigger>
          <DialogContent className="glass border-white/10 max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Créer une Stratégie</DialogTitle>
              <DialogDescription>
                Définissez les paramètres de votre stratégie de trading
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-6 py-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Nom de la stratégie *</Label>
                  <Input
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Ma stratégie RSI"
                    className="bg-black/20 border-white/10"
                    data-testid="strategy-name"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Risque par trade (%)</Label>
                  <Select value={riskPercentage} onValueChange={setRiskPercentage}>
                    <SelectTrigger className="bg-black/20 border-white/10">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="glass border-white/10">
                      <SelectItem value="1">1% (Conservateur)</SelectItem>
                      <SelectItem value="2">2% (Modéré)</SelectItem>
                      <SelectItem value="3">3% (Agressif)</SelectItem>
                      <SelectItem value="5">5% (Très agressif)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Description *</Label>
                <Textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Décrivez votre stratégie..."
                  className="bg-black/20 border-white/10 min-h-[80px]"
                  data-testid="strategy-description"
                />
              </div>

              <div className="space-y-2">
                <Label>Indicateurs techniques *</Label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  {INDICATORS.map(indicator => (
                    <div
                      key={indicator.id}
                      className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                        selectedIndicators.includes(indicator.id)
                          ? "bg-primary/10 border-primary/30"
                          : "bg-white/5 border-white/10 hover:border-white/20"
                      }`}
                      onClick={() => toggleIndicator(indicator.id)}
                    >
                      <Checkbox
                        checked={selectedIndicators.includes(indicator.id)}
                        className="mt-0.5"
                      />
                      <div>
                        <p className="font-medium text-sm">{indicator.name}</p>
                        <p className="text-xs text-muted-foreground">{indicator.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="space-y-2">
                <Label>Règles d&apos;entrée</Label>
                <Textarea
                  value={entryRules}
                  onChange={(e) => setEntryRules(e.target.value)}
                  placeholder="Ex: Acheter quand RSI < 30 et MACD croise à la hausse..."
                  className="bg-black/20 border-white/10 min-h-[80px]"
                  data-testid="entry-rules"
                />
              </div>

              <div className="space-y-2">
                <Label>Règles de sortie</Label>
                <Textarea
                  value={exitRules}
                  onChange={(e) => setExitRules(e.target.value)}
                  placeholder="Ex: Vendre quand RSI > 70 ou stop-loss à -5%..."
                  className="bg-black/20 border-white/10 min-h-[80px]"
                  data-testid="exit-rules"
                />
              </div>
            </div>

            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setDialogOpen(false)}
                className="border-white/10"
              >
                Annuler
              </Button>
              <Button
                onClick={handleCreate}
                disabled={submitting}
                className="bg-primary hover:bg-primary/90 text-black"
                data-testid="create-strategy-btn"
              >
                {submitting ? "Création..." : "Créer la stratégie"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Strategies Grid */}
      {strategies.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {strategies.map((strategy) => (
            <Card key={strategy.id} className="glass border-white/5 card-hover" data-testid={`strategy-${strategy.id}`}>
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
                      <Target className="w-5 h-5 text-blue-500" />
                    </div>
                    <div>
                      <CardTitle className="text-lg">{strategy.name}</CardTitle>
                      <p className="text-xs text-muted-foreground">
                        Créée le {new Date(strategy.created_at).toLocaleDateString("fr-FR")}
                      </p>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleDelete(strategy.id)}
                    className="text-muted-foreground hover:text-destructive"
                    data-testid={`delete-strategy-${strategy.id}`}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-muted-foreground">{strategy.description}</p>
                
                <div className="flex flex-wrap gap-2">
                  {strategy.indicators.map(ind => (
                    <Badge key={ind} variant="secondary" className="bg-white/5">
                      {INDICATORS.find(i => i.id === ind)?.name || ind}
                    </Badge>
                  ))}
                </div>

                <div className="flex items-center gap-4 pt-2 border-t border-white/5">
                  <div className="flex items-center gap-2 text-sm">
                    <Shield className="w-4 h-4 text-yellow-500" />
                    <span>Risque: {strategy.risk_percentage}%</span>
                  </div>
                </div>

                {(strategy.entry_rules || strategy.exit_rules) && (
                  <div className="space-y-2 pt-2 border-t border-white/5">
                    {strategy.entry_rules && (
                      <div>
                        <p className="text-xs text-muted-foreground flex items-center gap-1">
                          <TrendingUp className="w-3 h-3 text-emerald-500" /> Entrée
                        </p>
                        <p className="text-sm">{strategy.entry_rules}</p>
                      </div>
                    )}
                    {strategy.exit_rules && (
                      <div>
                        <p className="text-xs text-muted-foreground flex items-center gap-1">
                          <TrendingDown className="w-3 h-3 text-rose-500" /> Sortie
                        </p>
                        <p className="text-sm">{strategy.exit_rules}</p>
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card className="glass border-white/5">
          <CardContent className="flex flex-col items-center justify-center py-16">
            <Target className="w-16 h-16 text-muted-foreground/30 mb-4" />
            <h3 className="text-lg font-medium mb-2">Aucune stratégie</h3>
            <p className="text-muted-foreground text-center max-w-md mb-4">
              Créez votre première stratégie de trading pour définir vos règles d&apos;entrée et de sortie.
            </p>
            <Button onClick={() => setDialogOpen(true)} className="bg-primary hover:bg-primary/90 text-black">
              <Plus className="w-4 h-4 mr-2" />
              Créer une stratégie
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Backtesting Section */}
      <Card className="glass border-white/5 mt-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-violet-500" />
            🧪 Backtesting Rapide
          </CardTitle>
          <CardDescription>
            Testez des stratégies prédéfinies sur l&apos;historique des prix
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
            <div className="space-y-2">
              <Label>Crypto</Label>
              <Select value={backtestCoin} onValueChange={setBacktestCoin}>
                <SelectTrigger className="bg-black/20 border-white/10">
                  <SelectValue placeholder="Choisir..." />
                </SelectTrigger>
                <SelectContent className="glass border-white/10">
                  <SelectItem value="bitcoin">Bitcoin (BTC)</SelectItem>
                  <SelectItem value="ethereum">Ethereum (ETH)</SelectItem>
                  <SelectItem value="solana">Solana (SOL)</SelectItem>
                  <SelectItem value="ripple">XRP</SelectItem>
                  <SelectItem value="cardano">Cardano (ADA)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label>Stratégie</Label>
              <Select value={backtestStrategy} onValueChange={setBacktestStrategy}>
                <SelectTrigger className="bg-black/20 border-white/10">
                  <SelectValue placeholder="Choisir..." />
                </SelectTrigger>
                <SelectContent className="glass border-white/10">
                  <SelectItem value="rsi_oversold">RSI Survente (&lt;30)</SelectItem>
                  <SelectItem value="rsi_overbought">RSI Surachat (&gt;70)</SelectItem>
                  <SelectItem value="ma_crossover">MA Crossover</SelectItem>
                  <SelectItem value="bollinger_bounce">Bollinger Bounce</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label>Période</Label>
              <Select value={backtestDays} onValueChange={setBacktestDays}>
                <SelectTrigger className="bg-black/20 border-white/10">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="glass border-white/10">
                  <SelectItem value="30">30 jours</SelectItem>
                  <SelectItem value="60">60 jours</SelectItem>
                  <SelectItem value="90">90 jours</SelectItem>
                  <SelectItem value="180">6 mois</SelectItem>
                  <SelectItem value="365">1 an</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label>&nbsp;</Label>
              <Button 
                onClick={runBacktest}
                disabled={backtesting || !backtestCoin || !backtestStrategy}
                className="w-full bg-violet-600 hover:bg-violet-700"
              >
                {backtesting ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Play className="w-4 h-4 mr-2" />
                )}
                Lancer le Backtest
              </Button>
            </div>
          </div>
          
          {/* Backtest Results */}
          {backtestResult && (
            <div className="mt-6 space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="font-semibold">Résultats du Backtest</h4>
                <Badge className={backtestResult.strategy_vs_buyhold >= 0 ? "bg-emerald-500/20 text-emerald-400" : "bg-rose-500/20 text-rose-400"}>
                  {backtestResult.strategy_vs_buyhold >= 0 ? "+" : ""}{backtestResult.strategy_vs_buyhold}% vs Buy&Hold
                </Badge>
              </div>
              
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                <div className="p-3 rounded-lg bg-white/5 text-center">
                  <p className="text-xs text-muted-foreground">Capital Final</p>
                  <p className="text-lg font-bold font-mono">${backtestResult.final_value?.toLocaleString()}</p>
                </div>
                <div className={`p-3 rounded-lg text-center ${backtestResult.total_return >= 0 ? "bg-emerald-500/10" : "bg-rose-500/10"}`}>
                  <p className="text-xs text-muted-foreground">Rendement</p>
                  <p className={`text-lg font-bold font-mono ${backtestResult.total_return >= 0 ? "text-emerald-500" : "text-rose-500"}`}>
                    {backtestResult.total_return >= 0 ? "+" : ""}{backtestResult.total_return}%
                  </p>
                </div>
                <div className="p-3 rounded-lg bg-white/5 text-center">
                  <p className="text-xs text-muted-foreground">Trades</p>
                  <p className="text-lg font-bold font-mono">{backtestResult.total_trades}</p>
                </div>
                <div className={`p-3 rounded-lg text-center ${backtestResult.win_rate >= 50 ? "bg-emerald-500/10" : "bg-rose-500/10"}`}>
                  <p className="text-xs text-muted-foreground">Win Rate</p>
                  <p className={`text-lg font-bold font-mono ${backtestResult.win_rate >= 50 ? "text-emerald-500" : "text-rose-500"}`}>
                    {backtestResult.win_rate}%
                  </p>
                </div>
                <div className="p-3 rounded-lg bg-blue-500/10 text-center">
                  <p className="text-xs text-muted-foreground">Buy & Hold</p>
                  <p className="text-lg font-bold font-mono text-blue-400">
                    {backtestResult.buy_hold_return >= 0 ? "+" : ""}{backtestResult.buy_hold_return}%
                  </p>
                </div>
              </div>
              
              <div className="flex items-center gap-2 p-3 rounded-lg bg-violet-500/10 border border-violet-500/20">
                <Info className="w-5 h-5 text-violet-400 flex-shrink-0" />
                <p className="text-sm">{backtestResult.message}</p>
              </div>
              
              {/* Trade History */}
              {backtestResult.trades_sample?.length > 0 && (
                <div className="space-y-2">
                  <p className="text-sm font-medium">Derniers trades simulés:</p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-40 overflow-y-auto">
                    {backtestResult.trades_sample.map((trade, idx) => (
                      <div key={idx} className={`p-2 rounded text-xs flex justify-between items-center ${
                        trade.type === "buy" ? "bg-emerald-500/10" : "bg-rose-500/10"
                      }`}>
                        <span className={trade.type === "buy" ? "text-emerald-400" : "text-rose-400"}>
                          {trade.type === "buy" ? "ACHAT" : "VENTE"} @ ${trade.price?.toLocaleString()}
                        </span>
                        {trade.pnl !== undefined && (
                          <span className={trade.pnl >= 0 ? "text-emerald-400" : "text-rose-400"}>
                            {trade.pnl >= 0 ? "+" : ""}{trade.pnl_percent}%
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
