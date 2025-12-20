import { useState, useEffect, useCallback } from "react";
import { useAuth, API } from "../App";
import axios from "axios";
import { toast } from "sonner";
import {
  Sun,
  Bell,
  BellRing,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  Zap,
  Target,
  Shield,
  Brain,
  RefreshCw,
  Loader2,
  Plus,
  Trash2,
  Volume2,
  VolumeX,
  Clock,
  ArrowUpRight,
  ArrowDownRight,
  Coffee
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Switch } from "../components/ui/switch";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "../components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";

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

const formatPrice = (price) => {
  if (!price) return "$0.00";
  if (price >= 1000) return `$${price.toLocaleString("en-US", { maximumFractionDigits: 0 })}`;
  if (price >= 1) return `$${price.toFixed(2)}`;
  return `$${price.toFixed(6)}`;
};

export default function CockpitPage() {
  const { user } = useAuth();
  const [briefing, setBriefing] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [markets, setMarkets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingBriefing, setLoadingBriefing] = useState(false);
  const [soundEnabled, setSoundEnabled] = useState(true);
  
  // New alert dialog
  const [newAlertOpen, setNewAlertOpen] = useState(false);
  const [newAlert, setNewAlert] = useState({
    symbol: "",
    symbol_name: "",
    alert_type: "price",
    condition: "below",
    value: "",
    sound_enabled: true,
    repeat: false
  });
  const [submitting, setSubmitting] = useState(false);

  // Auto-check alerts
  const checkAlerts = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/alerts/check`);
      if (response.data.triggered?.length > 0) {
        response.data.triggered.forEach(alert => {
          if (soundEnabled && alert.sound_enabled) {
            playAlertSound();
          }
          toast.warning(
            `🔔 ${alert.symbol_name}: ${alert.condition === "above" ? "↑" : "↓"} ${formatPrice(alert.value)}`,
            { duration: 10000 }
          );
        });
        // Refresh alerts list
        fetchAlerts();
      }
    } catch (error) {
      console.error("Error checking alerts:", error);
    }
  }, [soundEnabled]);

  const fetchBriefing = async () => {
    setLoadingBriefing(true);
    try {
      const response = await axios.get(`${API}/briefing/daily`);
      setBriefing(response.data);
    } catch (error) {
      console.error("Error fetching briefing:", error);
    } finally {
      setLoadingBriefing(false);
    }
  };

  const fetchAlerts = async () => {
    try {
      const response = await axios.get(`${API}/alerts/smart`);
      setAlerts(response.data || []);
    } catch (error) {
      console.error("Error fetching alerts:", error);
    }
  };

  const fetchMarkets = async () => {
    try {
      const response = await axios.get(`${API}/market/crypto`);
      setMarkets(response.data || []);
    } catch (error) {
      console.error("Error fetching markets:", error);
    }
  };

  useEffect(() => {
    const init = async () => {
      await Promise.all([fetchBriefing(), fetchAlerts(), fetchMarkets()]);
      setLoading(false);
    };
    init();
    
    // Check alerts every 30 seconds
    const interval = setInterval(checkAlerts, 30000);
    return () => clearInterval(interval);
  }, [checkAlerts]);

  const handleCreateAlert = async () => {
    if (!newAlert.symbol || !newAlert.value) {
      toast.error("Remplissez tous les champs");
      return;
    }
    
    setSubmitting(true);
    try {
      await axios.post(`${API}/alerts/smart`, {
        ...newAlert,
        value: parseFloat(newAlert.value)
      });
      toast.success("Alerte créée");
      setNewAlertOpen(false);
      setNewAlert({
        symbol: "", symbol_name: "", alert_type: "price",
        condition: "below", value: "", sound_enabled: true, repeat: false
      });
      fetchAlerts();
    } catch (error) {
      toast.error("Erreur lors de la création");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteAlert = async (alertId) => {
    try {
      await axios.delete(`${API}/alerts/smart/${alertId}`);
      toast.success("Alerte supprimée");
      fetchAlerts();
    } catch (error) {
      toast.error("Erreur lors de la suppression");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-12 h-12 animate-spin text-primary" />
          <p className="text-muted-foreground">Préparation du cockpit...</p>
        </div>
      </div>
    );
  }

  const getSentimentColor = (sentiment) => {
    if (sentiment === "bullish") return "text-emerald-500";
    if (sentiment === "bearish") return "text-rose-500";
    return "text-yellow-500";
  };

  const getSentimentIcon = (sentiment) => {
    if (sentiment === "bullish") return <TrendingUp className="w-5 h-5" />;
    if (sentiment === "bearish") return <TrendingDown className="w-5 h-5" />;
    return <Target className="w-5 h-5" />;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-amber-500 to-yellow-500 flex items-center justify-center">
            <Sun className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl md:text-3xl font-bold font-manrope">Cockpit Trading</h1>
            <p className="text-sm text-muted-foreground">Briefing matinal & Alertes</p>
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
            variant="outline"
            onClick={fetchBriefing}
            disabled={loadingBriefing}
            className="border-white/10"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${loadingBriefing ? "animate-spin" : ""}`} />
            Actualiser
          </Button>
        </div>
      </div>

      {/* Daily Briefing */}
      <Card className="glass border-amber-500/20 bg-gradient-to-br from-amber-500/5 to-orange-500/5">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Coffee className="w-5 h-5 text-amber-500" />
              Briefing du {new Date().toLocaleDateString("fr-FR", { weekday: "long", day: "numeric", month: "long" })}
            </CardTitle>
            {briefing && (
              <Badge className={`${getSentimentColor(briefing.sentiment)} bg-transparent border`}>
                {getSentimentIcon(briefing.sentiment)}
                <span className="ml-1 capitalize">{briefing.sentiment}</span>
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {loadingBriefing && !briefing ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-amber-500" />
            </div>
          ) : briefing ? (
            <div className="space-y-4">
              {/* Market Overview */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className="p-3 rounded-lg bg-white/5 text-center">
                  <p className="text-xs text-muted-foreground">Fear & Greed</p>
                  <p className={`text-xl font-bold ${
                    briefing.fear_greed < 30 ? "text-rose-500" :
                    briefing.fear_greed > 70 ? "text-emerald-500" : "text-yellow-500"
                  }`}>
                    {briefing.fear_greed}
                  </p>
                  <p className="text-xs text-muted-foreground">{briefing.fear_greed_label}</p>
                </div>
                <div className="p-3 rounded-lg bg-white/5 text-center">
                  <p className="text-xs text-muted-foreground">Bitcoin</p>
                  <p className="text-xl font-bold">{formatPrice(briefing.btc_price)}</p>
                  <p className={`text-xs ${briefing.btc_change_24h >= 0 ? "text-emerald-500" : "text-rose-500"}`}>
                    {briefing.btc_change_24h >= 0 ? "+" : ""}{briefing.btc_change_24h}%
                  </p>
                </div>
                <div className="p-3 rounded-lg bg-white/5 text-center">
                  <p className="text-xs text-muted-foreground">Trades Ouverts</p>
                  <p className="text-xl font-bold text-blue-500">{briefing.open_trades}</p>
                </div>
                <div className="p-3 rounded-lg bg-white/5 text-center">
                  <p className="text-xs text-muted-foreground">Focus</p>
                  <p className="text-xl font-bold text-violet-500 capitalize">{briefing.watchlist_focus}</p>
                </div>
              </div>
              
              {/* AI Summary */}
              <div className="p-4 rounded-lg bg-amber-500/10 border border-amber-500/20">
                <p className="text-sm">{briefing.summary}</p>
              </div>
              
              {/* Opportunities & Risks */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Opportunities */}
                <div className="p-4 rounded-lg bg-emerald-500/5 border border-emerald-500/20">
                  <h3 className="font-medium text-emerald-500 flex items-center gap-2 mb-2">
                    <Zap className="w-4 h-4" /> Opportunités
                  </h3>
                  {briefing.opportunities?.length > 0 ? (
                    <ul className="space-y-1">
                      {briefing.opportunities.map((opp, idx) => (
                        <li key={idx} className="text-sm flex items-start gap-2">
                          <ArrowUpRight className="w-3 h-3 text-emerald-500 mt-1 flex-shrink-0" />
                          {opp}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-sm text-muted-foreground">Aucune opportunité majeure identifiée</p>
                  )}
                </div>
                
                {/* Risks */}
                <div className="p-4 rounded-lg bg-rose-500/5 border border-rose-500/20">
                  <h3 className="font-medium text-rose-500 flex items-center gap-2 mb-2">
                    <Shield className="w-4 h-4" /> Risques
                  </h3>
                  {briefing.risks?.length > 0 ? (
                    <ul className="space-y-1">
                      {briefing.risks.map((risk, idx) => (
                        <li key={idx} className="text-sm flex items-start gap-2">
                          <AlertTriangle className="w-3 h-3 text-rose-500 mt-1 flex-shrink-0" />
                          {risk}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-sm text-muted-foreground">Aucun risque majeur identifié</p>
                  )}
                </div>
              </div>
              
              {/* Main Action */}
              <div className="p-4 rounded-lg bg-violet-500/10 border border-violet-500/20">
                <h3 className="font-medium text-violet-500 flex items-center gap-2 mb-1">
                  <Brain className="w-4 h-4" /> Action Recommandée
                </h3>
                <p className="text-sm">{briefing.main_action}</p>
              </div>
            </div>
          ) : (
            <p className="text-center text-muted-foreground py-8">
              Impossible de charger le briefing
            </p>
          )}
        </CardContent>
      </Card>

      {/* Smart Alerts */}
      <Card className="glass border-white/5">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Bell className="w-5 h-5 text-primary" />
              Mes Alertes
            </CardTitle>
            <Button onClick={() => setNewAlertOpen(true)} size="sm" className="bg-primary text-black">
              <Plus className="w-4 h-4 mr-1" /> Nouvelle Alerte
            </Button>
          </div>
          <CardDescription>
            Recevez une notification quand vos conditions sont atteintes
          </CardDescription>
        </CardHeader>
        <CardContent>
          {alerts.length === 0 ? (
            <div className="text-center py-8">
              <Bell className="w-12 h-12 text-muted-foreground/30 mx-auto mb-4" />
              <p className="text-muted-foreground">Aucune alerte configurée</p>
              <p className="text-sm text-muted-foreground/70">Créez des alertes pour ne jamais manquer une opportunité</p>
            </div>
          ) : (
            <div className="space-y-2">
              {alerts.map((alert) => (
                <div
                  key={alert.id}
                  className={`p-3 rounded-lg flex items-center justify-between ${
                    alert.triggered ? "bg-amber-500/10 border border-amber-500/20" : "bg-white/5 border border-white/5"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                      alert.condition === "above" ? "bg-emerald-500/20" : "bg-rose-500/20"
                    }`}>
                      {alert.condition === "above" ? (
                        <ArrowUpRight className="w-4 h-4 text-emerald-500" />
                      ) : (
                        <ArrowDownRight className="w-4 h-4 text-rose-500" />
                      )}
                    </div>
                    <div>
                      <p className="font-medium">{alert.symbol_name}</p>
                      <p className="text-xs text-muted-foreground">
                        {alert.condition === "above" ? "Au-dessus de" : "En-dessous de"} {formatPrice(alert.value)}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    {alert.triggered && (
                      <Badge className="bg-amber-500/20 text-amber-500">
                        <BellRing className="w-3 h-3 mr-1" /> Déclenchée
                      </Badge>
                    )}
                    {alert.sound_enabled && !alert.triggered && (
                      <Volume2 className="w-4 h-4 text-muted-foreground" />
                    )}
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleDeleteAlert(alert.id)}
                      className="text-muted-foreground hover:text-rose-500"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* New Alert Dialog */}
      <Dialog open={newAlertOpen} onOpenChange={setNewAlertOpen}>
        <DialogContent className="glass border-white/10 max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Bell className="w-5 h-5 text-primary" />
              Nouvelle Alerte
            </DialogTitle>
            <DialogDescription>
              Soyez notifié quand le prix atteint votre cible
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Crypto</Label>
              <Select
                value={newAlert.symbol}
                onValueChange={(value) => {
                  const coin = markets.find(m => m.id === value);
                  setNewAlert({
                    ...newAlert,
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
                        {coin.name} - {formatPrice(coin.current_price)}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Condition</Label>
                <Select value={newAlert.condition} onValueChange={(v) => setNewAlert({...newAlert, condition: v})}>
                  <SelectTrigger className="bg-black/20 border-white/10">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="glass border-white/10">
                    <SelectItem value="above">↑ Au-dessus de</SelectItem>
                    <SelectItem value="below">↓ En-dessous de</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div className="space-y-2">
                <Label>Prix cible ($)</Label>
                <Input
                  type="number"
                  step="any"
                  placeholder="0.00"
                  value={newAlert.value}
                  onChange={(e) => setNewAlert({...newAlert, value: e.target.value})}
                  className="bg-black/20 border-white/10"
                />
              </div>
            </div>
            
            <div className="flex items-center justify-between">
              <Label className="flex items-center gap-2">
                <Volume2 className="w-4 h-4" /> Son activé
              </Label>
              <Switch
                checked={newAlert.sound_enabled}
                onCheckedChange={(v) => setNewAlert({...newAlert, sound_enabled: v})}
              />
            </div>
            
            <div className="flex items-center justify-between">
              <Label className="flex items-center gap-2">
                <RefreshCw className="w-4 h-4" /> Répéter l'alerte
              </Label>
              <Switch
                checked={newAlert.repeat}
                onCheckedChange={(v) => setNewAlert({...newAlert, repeat: v})}
              />
            </div>
            
            <Button
              onClick={handleCreateAlert}
              disabled={submitting}
              className="w-full bg-primary text-black"
            >
              {submitting ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Bell className="w-4 h-4 mr-2" />}
              Créer l'Alerte
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
