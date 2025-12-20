import { useState, useEffect } from "react";
import { API } from "../App";
import axios from "axios";
import { toast } from "sonner";
import {
  Signal,
  TrendingUp,
  TrendingDown,
  Clock,
  Target,
  CheckCircle,
  XCircle,
  AlertCircle,
  Trash2,
  RefreshCw,
  Loader2,
  BarChart3,
  Zap,
  ArrowUpRight,
  ArrowDownRight
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
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

const getSignalTypeColor = (type) => {
  switch (type) {
    case "BUY": return "bg-emerald-500/20 text-emerald-500";
    case "SELL": return "bg-rose-500/20 text-rose-500";
    default: return "bg-yellow-500/20 text-yellow-500";
  }
};

const getStatusColor = (status) => {
  switch (status) {
    case "hit_tp1": 
    case "hit_tp2": return "bg-emerald-500/20 text-emerald-500";
    case "hit_sl": return "bg-rose-500/20 text-rose-500";
    case "expired": return "bg-gray-500/20 text-gray-500";
    default: return "bg-blue-500/20 text-blue-500";
  }
};

const getStatusLabel = (status) => {
  switch (status) {
    case "active": return "Actif";
    case "hit_tp1": return "TP1 Atteint";
    case "hit_tp2": return "TP2 Atteint";
    case "hit_sl": return "SL Touché";
    case "expired": return "Expiré";
    default: return status;
  }
};

const getStatusIcon = (status) => {
  switch (status) {
    case "hit_tp1":
    case "hit_tp2":
      return <CheckCircle className="w-3 h-3 mr-1" />;
    case "hit_sl":
      return <XCircle className="w-3 h-3 mr-1" />;
    case "active":
      return <AlertCircle className="w-3 h-3 mr-1" />;
    default:
      return null;
  }
};

const getConfidenceColor = (confidence) => {
  switch (confidence) {
    case "high": return "text-emerald-500";
    case "medium": return "text-yellow-500";
    default: return "text-rose-500";
  }
};

export default function SignalsPage() {
  const [signals, setSignals] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [evaluating, setEvaluating] = useState(false);
  const [evaluationResults, setEvaluationResults] = useState(null);
  const [filter, setFilter] = useState("all");

  const fetchData = async () => {
    try {
      const [signalsRes, statsRes] = await Promise.all([
        axios.get(`${API}/signals`),
        axios.get(`${API}/signals/stats`)
      ]);
      setSignals(signalsRes.data);
      setStats(statsRes.data);
    } catch (error) {
      console.error("Error fetching signals:", error);
      toast.error("Erreur lors du chargement des signaux");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchData();
    toast.success("Données actualisées");
  };

  const handleEvaluate = async () => {
    setEvaluating(true);
    setEvaluationResults(null);
    try {
      const response = await axios.post(`${API}/signals/evaluate`);
      setEvaluationResults(response.data);
      
      if (response.data.updated > 0) {
        toast.success(`${response.data.updated} signal(s) mis à jour automatiquement`);
        fetchData(); // Refresh to show new statuses
      } else {
        toast.info("Aucun signal n'a atteint ses objectifs ou stop-loss");
      }
    } catch (error) {
      console.error("Error evaluating signals:", error);
      toast.error("Erreur lors de l'évaluation des signaux");
    } finally {
      setEvaluating(false);
    }
  };

  const handleUpdateStatus = async (signalId, newStatus) => {
    try {
      await axios.put(`${API}/signals/${signalId}/status?status=${newStatus}`);
      toast.success(`Signal mis à jour: ${getStatusLabel(newStatus)}`);
      fetchData();
    } catch (error) {
      toast.error("Erreur lors de la mise à jour");
    }
  };

  const handleDelete = async (signalId) => {
    try {
      await axios.delete(`${API}/signals/${signalId}`);
      toast.success("Signal supprimé");
      fetchData();
    } catch (error) {
      toast.error("Erreur lors de la suppression");
    }
  };

  const filteredSignals = signals.filter(s => {
    if (filter === "all") return true;
    if (filter === "active") return s.status === "active";
    if (filter === "wins") return s.status === "hit_tp1" || s.status === "hit_tp2";
    if (filter === "losses") return s.status === "hit_sl";
    return true;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-12 h-12 animate-spin text-primary" />
          <p className="text-muted-foreground">Chargement des signaux...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="signals-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-orange-500 to-red-500 flex items-center justify-center">
            <Signal className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl md:text-3xl font-bold font-manrope">Mes Signaux</h1>
            <p className="text-sm text-muted-foreground">Historique et performance de vos signaux de trading</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={handleEvaluate}
            disabled={evaluating || stats?.active === 0}
            className="bg-gradient-to-r from-violet-500 to-fuchsia-500 hover:from-violet-600 hover:to-fuchsia-600 text-white"
            data-testid="evaluate-btn"
          >
            <Zap className={`w-4 h-4 mr-2 ${evaluating ? "animate-pulse" : ""}`} />
            {evaluating ? "Évaluation..." : "Évaluer les signaux"}
          </Button>
          <Button
            variant="outline"
            onClick={handleRefresh}
            disabled={refreshing}
            className="border-white/10 hover:bg-white/5"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? "animate-spin" : ""}`} />
            Actualiser
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <Card className="glass border-white/5">
            <CardContent className="pt-4 pb-4 text-center">
              <p className="text-3xl font-bold font-mono">{stats.total_signals}</p>
              <p className="text-xs text-muted-foreground">Total Signaux</p>
            </CardContent>
          </Card>
          
          <Card className="glass border-white/5">
            <CardContent className="pt-4 pb-4 text-center">
              <p className="text-3xl font-bold font-mono text-blue-500">{stats.active}</p>
              <p className="text-xs text-muted-foreground">Actifs</p>
            </CardContent>
          </Card>
          
          <Card className="glass border-white/5">
            <CardContent className="pt-4 pb-4 text-center">
              <p className="text-3xl font-bold font-mono text-emerald-500">{stats.hit_tp1 + stats.hit_tp2}</p>
              <p className="text-xs text-muted-foreground">Gagnants</p>
            </CardContent>
          </Card>
          
          <Card className="glass border-white/5">
            <CardContent className="pt-4 pb-4 text-center">
              <p className="text-3xl font-bold font-mono text-rose-500">{stats.hit_sl}</p>
              <p className="text-xs text-muted-foreground">Perdants</p>
            </CardContent>
          </Card>
          
          <Card className={`glass border-2 ${stats.win_rate >= 50 ? "border-emerald-500/30" : "border-rose-500/30"}`}>
            <CardContent className="pt-4 pb-4 text-center">
              <p className={`text-3xl font-bold font-mono ${stats.win_rate >= 50 ? "text-emerald-500" : "text-rose-500"}`}>
                {stats.win_rate}%
              </p>
              <p className="text-xs text-muted-foreground">Win Rate</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Evaluation Results */}
      {evaluationResults && evaluationResults.results.length > 0 && (
        <Card className="glass border-violet-500/20">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg flex items-center gap-2">
                <Zap className="w-5 h-5 text-violet-500" />
                Résultats de l&apos;évaluation
              </CardTitle>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setEvaluationResults(null)}
                className="text-muted-foreground hover:text-foreground"
              >
                Fermer
              </Button>
            </div>
            <CardDescription>{evaluationResults.message}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {evaluationResults.results.map((result, idx) => (
                <div
                  key={idx}
                  className={`p-3 rounded-lg flex items-center justify-between ${
                    result.new_status === "hit_tp1" || result.new_status === "hit_tp2"
                      ? "bg-emerald-500/10 border border-emerald-500/20"
                      : result.new_status === "hit_sl"
                      ? "bg-rose-500/10 border border-rose-500/20"
                      : result.status === "active"
                      ? "bg-white/5"
                      : "bg-yellow-500/10 border border-yellow-500/20"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                      result.signal_type === "BUY" ? "bg-emerald-500/20" : "bg-rose-500/20"
                    }`}>
                      {result.signal_type === "BUY" ? (
                        <ArrowUpRight className="w-4 h-4 text-emerald-500" />
                      ) : (
                        <ArrowDownRight className="w-4 h-4 text-rose-500" />
                      )}
                    </div>
                    <div>
                      <p className="font-medium">{result.symbol}</p>
                      <p className="text-xs text-muted-foreground">
                        Entrée: {formatPrice(result.entry_price)} → Actuel: {formatPrice(result.current_price)}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    {result.new_status ? (
                      <>
                        <Badge className={getStatusColor(result.new_status)}>
                          {getStatusIcon(result.new_status)}
                          {getStatusLabel(result.new_status)}
                        </Badge>
                        <p className={`text-sm font-mono mt-1 ${result.pnl_percent >= 0 ? "text-emerald-500" : "text-rose-500"}`}>
                          {result.pnl_percent >= 0 ? "+" : ""}{result.pnl_percent}%
                        </p>
                      </>
                    ) : (
                      <>
                        <p className="text-xs text-muted-foreground">P&L non réalisé</p>
                        <p className={`text-sm font-mono ${result.unrealized_pnl >= 0 ? "text-emerald-500" : "text-rose-500"}`}>
                          {result.unrealized_pnl >= 0 ? "+" : ""}{result.unrealized_pnl}%
                        </p>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filters */}
      <div className="flex items-center gap-4">
        <Select value={filter} onValueChange={setFilter}>
          <SelectTrigger className="w-48 bg-black/20 border-white/10">
            <SelectValue placeholder="Filtrer" />
          </SelectTrigger>
          <SelectContent className="glass border-white/10">
            <SelectItem value="all">Tous les signaux</SelectItem>
            <SelectItem value="active">Actifs seulement</SelectItem>
            <SelectItem value="wins">Gagnants</SelectItem>
            <SelectItem value="losses">Perdants</SelectItem>
          </SelectContent>
        </Select>
        <p className="text-sm text-muted-foreground">
          {filteredSignals.length} signal(s)
        </p>
      </div>

      {/* Signals List */}
      <Card className="glass border-white/5">
        <CardHeader>
          <CardTitle className="text-lg">Historique des Signaux</CardTitle>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[500px]">
            {filteredSignals.length > 0 ? (
              <div className="space-y-4">
                {filteredSignals.map((signal) => (
                  <div
                    key={signal.id}
                    className="p-4 rounded-lg bg-white/5 border border-white/10"
                    data-testid={`signal-${signal.id}`}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <Badge className={getSignalTypeColor(signal.signal_type)}>
                          {signal.signal_type === "BUY" ? (
                            <><TrendingUp className="w-3 h-3 mr-1" /> ACHAT</>
                          ) : signal.signal_type === "SELL" ? (
                            <><TrendingDown className="w-3 h-3 mr-1" /> VENTE</>
                          ) : (
                            <><Clock className="w-3 h-3 mr-1" /> ATTENDRE</>
                          )}
                        </Badge>
                        <div>
                          <p className="font-bold">{signal.symbol_name}</p>
                          <p className="text-xs text-muted-foreground">
                            {new Date(signal.created_at).toLocaleString("fr-FR")} • {signal.timeframe}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge className={`flex items-center ${getStatusColor(signal.status)}`}>
                          {getStatusIcon(signal.status)}
                          {getStatusLabel(signal.status)}
                        </Badge>
                        <AlertDialog>
                          <AlertDialogTrigger asChild>
                            <Button variant="ghost" size="icon" className="hover:bg-rose-500/10 hover:text-rose-500">
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </AlertDialogTrigger>
                          <AlertDialogContent className="glass border-white/10">
                            <AlertDialogHeader>
                              <AlertDialogTitle>Supprimer ce signal?</AlertDialogTitle>
                              <AlertDialogDescription>
                                Cette action est irréversible.
                              </AlertDialogDescription>
                            </AlertDialogHeader>
                            <AlertDialogFooter>
                              <AlertDialogCancel className="border-white/10">Annuler</AlertDialogCancel>
                              <AlertDialogAction
                                onClick={() => handleDelete(signal.id)}
                                className="bg-destructive hover:bg-destructive/90"
                              >
                                Supprimer
                              </AlertDialogAction>
                            </AlertDialogFooter>
                          </AlertDialogContent>
                        </AlertDialog>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-3">
                      <div className="p-2 rounded bg-black/20">
                        <p className="text-xs text-muted-foreground">Prix Signal</p>
                        <p className="font-mono font-bold">{formatPrice(signal.price_at_signal)}</p>
                      </div>
                      <div className="p-2 rounded bg-black/20">
                        <p className="text-xs text-muted-foreground">Entrée</p>
                        <p className="font-mono font-bold text-blue-400">{formatPrice(signal.entry_price)}</p>
                      </div>
                      <div className="p-2 rounded bg-black/20">
                        <p className="text-xs text-muted-foreground">Stop-Loss</p>
                        <p className="font-mono font-bold text-rose-400">{formatPrice(signal.stop_loss)}</p>
                      </div>
                      <div className="p-2 rounded bg-black/20">
                        <p className="text-xs text-muted-foreground">TP1</p>
                        <p className="font-mono font-bold text-emerald-400">{formatPrice(signal.take_profit_1)}</p>
                      </div>
                      {signal.take_profit_2 && (
                        <div className="p-2 rounded bg-black/20">
                          <p className="text-xs text-muted-foreground">TP2</p>
                          <p className="font-mono font-bold text-emerald-400">{formatPrice(signal.take_profit_2)}</p>
                        </div>
                      )}
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4 text-sm">
                        <span className={`${getConfidenceColor(signal.confidence)}`}>
                          Confiance: {signal.confidence?.toUpperCase()}
                        </span>
                        <span className="text-muted-foreground">
                          {signal.reason}
                        </span>
                      </div>
                      
                      {signal.status === "active" && (
                        <div className="flex items-center gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            className="border-emerald-500/30 text-emerald-500 hover:bg-emerald-500/10"
                            onClick={() => handleUpdateStatus(signal.id, "hit_tp1")}
                          >
                            <CheckCircle className="w-3 h-3 mr-1" /> TP1
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            className="border-emerald-500/30 text-emerald-500 hover:bg-emerald-500/10"
                            onClick={() => handleUpdateStatus(signal.id, "hit_tp2")}
                          >
                            <CheckCircle className="w-3 h-3 mr-1" /> TP2
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            className="border-rose-500/30 text-rose-500 hover:bg-rose-500/10"
                            onClick={() => handleUpdateStatus(signal.id, "hit_sl")}
                          >
                            <XCircle className="w-3 h-3 mr-1" /> SL
                          </Button>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-16">
                <Signal className="w-16 h-16 text-muted-foreground/30 mb-4" />
                <h3 className="text-lg font-medium mb-2">Aucun signal</h3>
                <p className="text-muted-foreground text-center max-w-md">
                  Analysez des cryptos depuis le Dashboard pour générer des signaux de trading.
                </p>
              </div>
            )}
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}
