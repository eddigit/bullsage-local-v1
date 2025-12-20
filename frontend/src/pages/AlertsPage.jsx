import { useState, useEffect } from "react";
import { API } from "../App";
import axios from "axios";
import { toast } from "sonner";
import {
  Bell,
  Plus,
  Trash2,
  TrendingUp,
  TrendingDown,
  ArrowUp,
  ArrowDown,
  CheckCircle,
  XCircle
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
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

export default function AlertsPage() {
  const [alerts, setAlerts] = useState([]);
  const [markets, setMarkets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Form state
  const [selectedCoin, setSelectedCoin] = useState("");
  const [targetPrice, setTargetPrice] = useState("");
  const [condition, setCondition] = useState("above");
  const [alertName, setAlertName] = useState("");

  const fetchData = async () => {
    try {
      const [alertsRes, marketsRes] = await Promise.all([
        axios.get(`${API}/alerts`),
        axios.get(`${API}/market/crypto`)
      ]);
      setAlerts(alertsRes.data);
      setMarkets(marketsRes.data || []);
    } catch (error) {
      console.error("Error fetching data:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCreate = async () => {
    if (!selectedCoin || !targetPrice) {
      toast.error("Veuillez remplir tous les champs obligatoires");
      return;
    }

    setSubmitting(true);
    try {
      await axios.post(`${API}/alerts`, {
        symbol: selectedCoin,
        target_price: parseFloat(targetPrice),
        condition,
        name: alertName || null
      });

      toast.success("Alerte créée avec succès!");
      setDialogOpen(false);
      resetForm();
      fetchData();
    } catch (error) {
      toast.error("Erreur lors de la création de l'alerte");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id) => {
    try {
      await axios.delete(`${API}/alerts/${id}`);
      toast.success("Alerte supprimée");
      fetchData();
    } catch (error) {
      toast.error("Erreur lors de la suppression");
    }
  };

  const resetForm = () => {
    setSelectedCoin("");
    setTargetPrice("");
    setCondition("above");
    setAlertName("");
  };

  // Get current price for selected coin
  const selectedCoinData = markets.find(c => c.id === selectedCoin);

  // Check alert status
  const getAlertStatus = (alert) => {
    const coin = markets.find(c => c.id === alert.symbol);
    if (!coin) return { triggered: false, diff: 0 };
    
    const currentPrice = coin.current_price;
    const triggered = alert.condition === "above" 
      ? currentPrice >= alert.target_price
      : currentPrice <= alert.target_price;
    
    const diff = ((currentPrice - alert.target_price) / alert.target_price) * 100;
    return { triggered, diff, currentPrice };
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-48 bg-white/5 rounded animate-pulse" />
        <div className="space-y-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-24 bg-white/5 rounded-xl animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="alerts-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold font-manrope">Alertes</h1>
          <p className="text-muted-foreground">
            Configurez des alertes sur les prix des cryptos
          </p>
        </div>
        
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button className="bg-primary hover:bg-primary/90 text-black font-bold" data-testid="new-alert-btn">
              <Plus className="w-4 h-4 mr-2" />
              Nouvelle Alerte
            </Button>
          </DialogTrigger>
          <DialogContent className="glass border-white/10">
            <DialogHeader>
              <DialogTitle>Créer une Alerte</DialogTitle>
              <DialogDescription>
                Soyez notifié quand le prix atteint votre objectif
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Cryptomonnaie *</Label>
                <Select value={selectedCoin} onValueChange={setSelectedCoin}>
                  <SelectTrigger className="bg-black/20 border-white/10" data-testid="alert-coin-select">
                    <SelectValue placeholder="Sélectionner une crypto" />
                  </SelectTrigger>
                  <SelectContent className="glass border-white/10 max-h-64">
                    {markets.slice(0, 30).map(coin => (
                      <SelectItem key={coin.id} value={coin.id}>
                        <div className="flex items-center gap-2">
                          <img src={coin.image} alt={coin.name} className="w-5 h-5 rounded-full" />
                          <span>{coin.name}</span>
                          <span className="text-muted-foreground font-mono">
                            ${coin.current_price?.toLocaleString()}
                          </span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {selectedCoinData && (
                  <p className="text-sm text-muted-foreground">
                    Prix actuel: <span className="font-mono text-primary">${selectedCoinData.current_price?.toLocaleString()}</span>
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label>Condition *</Label>
                <div className="grid grid-cols-2 gap-2">
                  <Button
                    type="button"
                    variant={condition === "above" ? "default" : "outline"}
                    onClick={() => setCondition("above")}
                    className={condition === "above" ? "bg-emerald-500 hover:bg-emerald-600" : "border-white/10"}
                    data-testid="condition-above"
                  >
                    <ArrowUp className="w-4 h-4 mr-2" />
                    Au-dessus de
                  </Button>
                  <Button
                    type="button"
                    variant={condition === "below" ? "default" : "outline"}
                    onClick={() => setCondition("below")}
                    className={condition === "below" ? "bg-rose-500 hover:bg-rose-600" : "border-white/10"}
                    data-testid="condition-below"
                  >
                    <ArrowDown className="w-4 h-4 mr-2" />
                    En-dessous de
                  </Button>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Prix cible ($) *</Label>
                <Input
                  type="number"
                  value={targetPrice}
                  onChange={(e) => setTargetPrice(e.target.value)}
                  placeholder="50000"
                  className="bg-black/20 border-white/10 font-mono"
                  step="0.01"
                  min="0"
                  data-testid="target-price"
                />
              </div>

              <div className="space-y-2">
                <Label>Nom de l&apos;alerte (optionnel)</Label>
                <Input
                  value={alertName}
                  onChange={(e) => setAlertName(e.target.value)}
                  placeholder="Ex: BTC breakout"
                  className="bg-black/20 border-white/10"
                  data-testid="alert-name"
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
                disabled={submitting || !selectedCoin || !targetPrice}
                className="bg-primary hover:bg-primary/90 text-black"
                data-testid="create-alert-btn"
              >
                {submitting ? "Création..." : "Créer l'alerte"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Alerts List */}
      {alerts.length > 0 ? (
        <Card className="glass border-white/5">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Bell className="w-5 h-5 text-yellow-500" />
              Mes Alertes
            </CardTitle>
            <CardDescription>{alerts.length} alerte(s) configurée(s)</CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[500px]">
              <div className="space-y-3">
                {alerts.map((alert) => {
                  const coin = markets.find(c => c.id === alert.symbol);
                  const status = getAlertStatus(alert);

                  return (
                    <div
                      key={alert.id}
                      className={`p-4 rounded-lg border transition-colors ${
                        status.triggered
                          ? "bg-primary/10 border-primary/30"
                          : "bg-white/5 border-white/10"
                      }`}
                      data-testid={`alert-${alert.id}`}
                    >
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-3">
                          {coin && <img src={coin.image} alt={coin.name} className="w-10 h-10 rounded-full" />}
                          <div>
                            <p className="font-medium">{alert.name}</p>
                            <p className="text-sm text-muted-foreground">
                              {coin?.name || alert.symbol}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {status.triggered ? (
                            <Badge className="bg-primary/20 text-primary">
                              <CheckCircle className="w-3 h-3 mr-1" />
                              Atteint
                            </Badge>
                          ) : (
                            <Badge variant="secondary" className="bg-white/5">
                              En attente
                            </Badge>
                          )}
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleDelete(alert.id)}
                            className="text-muted-foreground hover:text-destructive"
                            data-testid={`delete-alert-${alert.id}`}
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                          <p className="text-muted-foreground">Condition</p>
                          <p className="font-medium flex items-center gap-1">
                            {alert.condition === "above" ? (
                              <>
                                <TrendingUp className="w-4 h-4 text-emerald-500" />
                                Au-dessus de
                              </>
                            ) : (
                              <>
                                <TrendingDown className="w-4 h-4 text-rose-500" />
                                En-dessous de
                              </>
                            )}
                          </p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">Prix cible</p>
                          <p className="font-mono font-medium">${alert.target_price.toLocaleString()}</p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">Prix actuel</p>
                          <p className="font-mono font-medium">
                            ${status.currentPrice?.toLocaleString() || "-"}
                          </p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">Écart</p>
                          <p className={`font-mono font-medium ${status.diff >= 0 ? "text-emerald-500" : "text-rose-500"}`}>
                            {status.diff >= 0 ? "+" : ""}{status.diff.toFixed(2)}%
                          </p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      ) : (
        <Card className="glass border-white/5">
          <CardContent className="flex flex-col items-center justify-center py-16">
            <Bell className="w-16 h-16 text-muted-foreground/30 mb-4" />
            <h3 className="text-lg font-medium mb-2">Aucune alerte</h3>
            <p className="text-muted-foreground text-center max-w-md mb-4">
              Créez des alertes pour être notifié quand les prix atteignent vos objectifs.
            </p>
            <Button onClick={() => setDialogOpen(true)} className="bg-primary hover:bg-primary/90 text-black">
              <Plus className="w-4 h-4 mr-2" />
              Créer une alerte
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
