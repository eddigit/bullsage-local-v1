/**
 * 🐂 BULL SAGE - Page de visualisation des positions dYdX
 * 
 * Affiche en temps réel les positions ouvertes sur dYdX avec:
 * - PnL en temps réel
 * - Statut des ordres SL/TP
 * - Boutons de fermeture manuelle
 * - Alertes pour positions non protégées
 */

import { useState, useEffect, useCallback } from "react";
import { useAuth, API } from "../App";
import axios from "axios";
import { toast } from "sonner";
import {
  TrendingUp,
  TrendingDown,
  RefreshCw,
  Loader2,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  DollarSign,
  Shield,
  ShieldOff,
  ExternalLink,
  Activity,
  Wallet,
  Clock,
  Target,
  StopCircle,
  Zap,
  Eye,
  BarChart3,
  AlertCircle,
  Lock,
  ShieldCheck
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Progress } from "../components/ui/progress";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "../components/ui/dialog";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "../components/ui/tooltip";
import {
  Alert,
  AlertDescription,
  AlertTitle,
} from "../components/ui/alert";

export default function DydxPositionsPage() {
  const { token } = useAuth();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [data, setData] = useState(null);
  const [closingPosition, setClosingPosition] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  
  // États pour le modal de protection
  const [protectModal, setProtectModal] = useState({ open: false, position: null });
  const [protectForm, setProtectForm] = useState({ stopLoss: '', takeProfit: '' });
  const [protecting, setProtecting] = useState(false);

  // Charger les positions
  const loadPositions = useCallback(async (silent = false) => {
    if (!silent) setRefreshing(true);
    
    try {
      const response = await axios.get(`${API}/dydx/positions/detailed`);
      setData(response.data);
      setLastUpdate(new Date());
    } catch (error) {
      console.error("Erreur chargement positions:", error);
      if (!silent) {
        toast.error("Erreur de connexion à dYdX");
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  // Fermer une position
  const closePosition = async (market) => {
    if (!window.confirm(`⚠️ Fermer la position ${market} au prix du marché ?`)) {
      return;
    }
    
    setClosingPosition(market);
    
    try {
      const response = await axios.post(`${API}/dydx/positions/close`, {
        market,
        reason: "manual_close_from_ui"
      });
      
      if (response.data.success) {
        toast.success(`✅ Position ${market} fermée @ $${response.data.closePrice?.toLocaleString()}`);
        loadPositions();
      } else {
        throw new Error(response.data.error);
      }
    } catch (error) {
      toast.error(`Erreur: ${error.response?.data?.detail || error.message}`);
    } finally {
      setClosingPosition(null);
    }
  };

  // Ouvrir le modal de protection
  const openProtectModal = (position) => {
    const currentPrice = position.currentPrice;
    const side = position.side;
    
    // Suggérer des valeurs par défaut
    let suggestedSL, suggestedTP;
    if (side === 'LONG') {
      suggestedSL = (currentPrice * 0.95).toFixed(2); // -5%
      suggestedTP = (currentPrice * 1.10).toFixed(2); // +10%
    } else {
      suggestedSL = (currentPrice * 1.05).toFixed(2); // +5%
      suggestedTP = (currentPrice * 0.90).toFixed(2); // -10%
    }
    
    setProtectForm({
      stopLoss: position.stopLoss?.price || suggestedSL,
      takeProfit: position.takeProfit?.price || suggestedTP
    });
    setProtectModal({ open: true, position });
  };

  // Protéger une position
  const protectPosition = async () => {
    if (!protectForm.stopLoss && !protectForm.takeProfit) {
      toast.error("Définissez au moins un Stop Loss ou Take Profit");
      return;
    }
    
    setProtecting(true);
    
    try {
      const response = await axios.post(`${API}/dydx/positions/protect`, {
        market: protectModal.position.market,
        stopLoss: protectForm.stopLoss ? parseFloat(protectForm.stopLoss) : null,
        takeProfit: protectForm.takeProfit ? parseFloat(protectForm.takeProfit) : null,
        expirationHours: 168 // 7 jours
      });
      
      if (response.data.success) {
        toast.success(`🛡️ Position ${protectModal.position.market} protégée !`);
        setProtectModal({ open: false, position: null });
        loadPositions();
      } else {
        const errors = response.data.orders?.filter(o => !o.success);
        if (errors?.length > 0) {
          toast.error(`Erreur: ${errors[0].error}`);
        } else {
          throw new Error("Échec de la protection");
        }
      }
    } catch (error) {
      toast.error(`Erreur: ${error.response?.data?.detail?.error || error.response?.data?.detail || error.message}`);
    } finally {
      setProtecting(false);
    }
  };

  // Charger au démarrage
  useEffect(() => {
    loadPositions();
  }, [loadPositions]);

  // Auto-refresh toutes les 30 secondes
  useEffect(() => {
    if (!autoRefresh) return;
    
    const interval = setInterval(() => {
      loadPositions(true);
    }, 30000);
    
    return () => clearInterval(interval);
  }, [autoRefresh, loadPositions]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <Activity className="w-16 h-16 mx-auto mb-4 text-purple-500 animate-pulse" />
          <h2 className="text-xl font-bold">Positions dYdX</h2>
          <p className="text-muted-foreground">Connexion à dYdX...</p>
          <Loader2 className="w-8 h-8 mx-auto mt-4 animate-spin" />
        </div>
      </div>
    );
  }

  const positions = data?.positions || [];
  const unprotectedCount = data?.unprotectedPositions || 0;
  const totalPnl = data?.totalUnrealizedPnl || 0;

  return (
    <TooltipProvider delayDuration={200}>
      <div className="container mx-auto p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-3">
              <Activity className="w-10 h-10 text-purple-500" />
              Positions dYdX
              <Badge variant="outline" className="text-purple-400 border-purple-500/50">
                Testnet
              </Badge>
            </h1>
            <p className="text-muted-foreground">
              Visualisation en temps réel de vos positions sur dYdX
            </p>
          </div>
          
          <div className="flex items-center gap-3">
            {lastUpdate && (
              <span className="text-xs text-muted-foreground">
                Màj: {lastUpdate.toLocaleTimeString()}
              </span>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={autoRefresh ? "border-green-500/50" : ""}
            >
              <Clock className={`w-4 h-4 mr-2 ${autoRefresh ? "text-green-400" : ""}`} />
              {autoRefresh ? "Auto" : "Manuel"}
            </Button>
            <Button onClick={() => loadPositions()} disabled={refreshing}>
              <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? "animate-spin" : ""}`} />
              Actualiser
            </Button>
            <Button
              variant="outline"
              onClick={() => window.open('https://v4.testnet.dydx.exchange/portfolio/positions', '_blank')}
            >
              <ExternalLink className="w-4 h-4 mr-2" />
              dYdX
            </Button>
          </div>
        </div>

        {/* Alertes positions non protégées */}
        {unprotectedCount > 0 && (
          <Alert variant="destructive" className="border-red-500/50 bg-red-500/10">
            <AlertTriangle className="h-5 w-5" />
            <AlertTitle className="text-red-400">
              ⚠️ {unprotectedCount} position(s) sans protection !
            </AlertTitle>
            <AlertDescription>
              Ces positions n'ont pas de Stop Loss ou Take Profit actif. 
              Elles risquent des pertes non contrôlées.
            </AlertDescription>
          </Alert>
        )}

        {/* Résumé du compte */}
        <div className="grid grid-cols-4 gap-4">
          <Card className="border-purple-500/30 bg-purple-500/5">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <Wallet className="w-8 h-8 text-purple-400" />
                <div>
                  <div className="text-sm text-muted-foreground">Équité</div>
                  <div className="text-2xl font-bold">${data?.equity?.toLocaleString() || 0}</div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-blue-500/30 bg-blue-500/5">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <DollarSign className="w-8 h-8 text-blue-400" />
                <div>
                  <div className="text-sm text-muted-foreground">Collatéral libre</div>
                  <div className="text-2xl font-bold">${data?.freeCollateral?.toLocaleString() || 0}</div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className={`${totalPnl >= 0 ? 'border-green-500/30 bg-green-500/5' : 'border-red-500/30 bg-red-500/5'}`}>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                {totalPnl >= 0 ? (
                  <TrendingUp className="w-8 h-8 text-green-400" />
                ) : (
                  <TrendingDown className="w-8 h-8 text-red-400" />
                )}
                <div>
                  <div className="text-sm text-muted-foreground">PnL Total</div>
                  <div className={`text-2xl font-bold ${totalPnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {totalPnl >= 0 ? '+' : ''}${totalPnl.toLocaleString()}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-slate-500/30">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <BarChart3 className="w-8 h-8 text-slate-400" />
                <div>
                  <div className="text-sm text-muted-foreground">Positions</div>
                  <div className="text-2xl font-bold">
                    {positions.length}
                    {unprotectedCount > 0 && (
                      <span className="text-red-400 text-sm ml-2">
                        ({unprotectedCount} ⚠️)
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Liste des positions */}
        {positions.length === 0 ? (
          <Card className="border-slate-500/30">
            <CardContent className="p-8 text-center">
              <Target className="w-16 h-16 mx-auto mb-4 text-muted-foreground opacity-50" />
              <h3 className="text-xl font-bold mb-2">Aucune position ouverte</h3>
              <p className="text-muted-foreground">
                Exécutez un trade depuis Pro Trader AI pour le voir ici
              </p>
              <Button 
                className="mt-4"
                onClick={() => window.location.href = '/dashboard/pro-trader'}
              >
                <Zap className="w-4 h-4 mr-2" />
                Aller à Pro Trader AI
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {positions.filter(p => p.size > 0.00001).map((position, index) => (
              <Card 
                key={index}
                className={`transition-all ${
                  !position.hasProtection 
                    ? 'border-red-500/50 bg-red-500/5' 
                    : position.status === 'WINNING'
                      ? 'border-green-500/30 bg-green-500/5'
                      : 'border-orange-500/30 bg-orange-500/5'
                }`}
              >
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    {/* Info principale */}
                    <div className="flex items-center gap-4">
                      <div className={`p-3 rounded-lg ${position.side === 'LONG' ? 'bg-green-500/20' : 'bg-red-500/20'}`}>
                        {position.side === 'LONG' ? (
                          <TrendingUp className="w-8 h-8 text-green-400" />
                        ) : (
                          <TrendingDown className="w-8 h-8 text-red-400" />
                        )}
                      </div>
                      
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-2xl font-bold">{position.market}</span>
                          <Badge className={position.side === 'LONG' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}>
                            {position.side}
                          </Badge>
                          {!position.hasProtection && (
                            <Badge variant="destructive" className="gap-1">
                              <ShieldOff className="w-3 h-3" />
                              SANS PROTECTION
                            </Badge>
                          )}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          Taille: {position.size} | Entrée: ${position.entryPrice?.toLocaleString()}
                        </div>
                      </div>
                    </div>

                    {/* PnL */}
                    <div className="text-right">
                      <div className={`text-3xl font-bold ${position.unrealizedPnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {position.unrealizedPnl >= 0 ? '+' : ''}${position.unrealizedPnl?.toLocaleString()}
                      </div>
                      <div className={`text-lg ${position.pnlPercent >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {position.pnlPercent >= 0 ? '+' : ''}{position.pnlPercent?.toFixed(2)}%
                      </div>
                    </div>

                    {/* Prix actuel */}
                    <div className="text-center px-4">
                      <div className="text-sm text-muted-foreground">Prix actuel</div>
                      <div className="text-xl font-mono">${position.currentPrice?.toLocaleString()}</div>
                    </div>

                    {/* Protection */}
                    <div className="text-center px-4 border-l border-white/10">
                      <div className="text-sm text-muted-foreground mb-1">Protection</div>
                      {position.stopLoss ? (
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <div className="flex items-center gap-1 text-red-400 cursor-help">
                              <StopCircle className="w-4 h-4" />
                              <span className="font-mono">${position.stopLoss.price?.toLocaleString()}</span>
                            </div>
                          </TooltipTrigger>
                          <TooltipContent>Stop Loss actif</TooltipContent>
                        </Tooltip>
                      ) : (
                        <span className="text-red-400 text-sm">Pas de SL</span>
                      )}
                      {position.takeProfit ? (
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <div className="flex items-center gap-1 text-green-400 cursor-help">
                              <Target className="w-4 h-4" />
                              <span className="font-mono">${position.takeProfit.price?.toLocaleString()}</span>
                            </div>
                          </TooltipTrigger>
                          <TooltipContent>Take Profit actif</TooltipContent>
                        </Tooltip>
                      ) : (
                        <span className="text-orange-400 text-sm">Pas de TP</span>
                      )}
                    </div>

                    {/* Actions */}
                    <div className="flex gap-2">
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button
                            variant={position.hasProtection ? "outline" : "default"}
                            size="sm"
                            onClick={() => openProtectModal(position)}
                            className={!position.hasProtection ? "bg-yellow-600 hover:bg-yellow-700" : ""}
                          >
                            {position.hasProtection ? (
                              <ShieldCheck className="w-4 h-4 text-green-400" />
                            ) : (
                              <Shield className="w-4 h-4" />
                            )}
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>
                          {position.hasProtection ? "Modifier la protection" : "Ajouter une protection SL/TP"}
                        </TooltipContent>
                      </Tooltip>
                      
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button
                            variant="destructive"
                            size="sm"
                            onClick={() => closePosition(position.market)}
                            disabled={closingPosition === position.market}
                          >
                            {closingPosition === position.market ? (
                              <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                              <XCircle className="w-4 h-4" />
                            )}
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>Fermer la position</TooltipContent>
                      </Tooltip>
                    </div>
                  </div>

                  {/* Barre de progression vers TP */}
                  {position.stopLoss && position.takeProfit && (
                    <div className="mt-4 pt-3 border-t border-white/10">
                      <div className="flex justify-between text-xs text-muted-foreground mb-1">
                        <span>SL: ${position.stopLoss.price?.toLocaleString()}</span>
                        <span>Entrée: ${position.entryPrice?.toLocaleString()}</span>
                        <span>TP: ${position.takeProfit.price?.toLocaleString()}</span>
                      </div>
                      {(() => {
                        const slPrice = position.stopLoss.price;
                        const tpPrice = position.takeProfit.price;
                        const current = position.currentPrice;
                        const entry = position.entryPrice;
                        
                        // Calcul du pourcentage de progression
                        let progress = 0;
                        if (position.side === 'LONG') {
                          const range = tpPrice - slPrice;
                          progress = ((current - slPrice) / range) * 100;
                        } else {
                          const range = slPrice - tpPrice;
                          progress = ((slPrice - current) / range) * 100;
                        }
                        progress = Math.max(0, Math.min(100, progress));
                        
                        return (
                          <div className="relative h-3 bg-gradient-to-r from-red-500/30 via-slate-500/30 to-green-500/30 rounded-full overflow-hidden">
                            <div 
                              className="absolute top-0 left-0 h-full bg-white/30 transition-all"
                              style={{ width: `${progress}%` }}
                            />
                            <div 
                              className="absolute top-0 h-full w-1 bg-white"
                              style={{ left: `${progress}%` }}
                            />
                          </div>
                        );
                      })()}
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Lien vers monitoring */}
        <Card className="border-yellow-500/30 bg-yellow-500/5">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Eye className="w-8 h-8 text-yellow-400" />
                <div>
                  <div className="font-bold">Monitoring automatique</div>
                  <div className="text-sm text-muted-foreground">
                    Le système surveille vos positions et ferme automatiquement si perte &gt; 10% sans protection
                  </div>
                </div>
              </div>
              <Badge variant="outline" className="text-yellow-400 border-yellow-500/50">
                Actif
              </Badge>
            </div>
          </CardContent>
        </Card>

        {/* Modal de protection */}
        <Dialog open={protectModal.open} onOpenChange={(open) => !open && setProtectModal({ open: false, position: null })}>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Shield className="w-5 h-5 text-yellow-400" />
                Protéger la position {protectModal.position?.market}
              </DialogTitle>
              <DialogDescription>
                Définissez un Stop Loss et/ou Take Profit pour sécuriser votre position
              </DialogDescription>
            </DialogHeader>
            
            {protectModal.position && (
              <div className="space-y-4">
                {/* Infos position */}
                <div className="p-3 rounded-lg bg-slate-800/50 space-y-2">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Position</span>
                    <Badge className={protectModal.position.side === 'LONG' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}>
                      {protectModal.position.side}
                    </Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Prix d'entrée</span>
                    <span className="font-mono">${protectModal.position.entryPrice?.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Prix actuel</span>
                    <span className="font-mono">${protectModal.position.currentPrice?.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">PnL actuel</span>
                    <span className={`font-bold ${protectModal.position.unrealizedPnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {protectModal.position.unrealizedPnl >= 0 ? '+' : ''}${protectModal.position.unrealizedPnl?.toFixed(2)}
                    </span>
                  </div>
                </div>

                {/* Stop Loss */}
                <div className="space-y-2">
                  <Label className="flex items-center gap-2 text-red-400">
                    <StopCircle className="w-4 h-4" />
                    Stop Loss (protection contre les pertes)
                  </Label>
                  <Input
                    type="number"
                    step="0.01"
                    placeholder={protectModal.position.side === 'LONG' ? "Prix inférieur au marché" : "Prix supérieur au marché"}
                    value={protectForm.stopLoss}
                    onChange={(e) => setProtectForm({ ...protectForm, stopLoss: e.target.value })}
                    className="font-mono"
                  />
                  {protectForm.stopLoss && (
                    <p className="text-xs text-muted-foreground">
                      {((parseFloat(protectForm.stopLoss) - protectModal.position.entryPrice) / protectModal.position.entryPrice * 100).toFixed(2)}% par rapport à l'entrée
                    </p>
                  )}
                </div>

                {/* Take Profit */}
                <div className="space-y-2">
                  <Label className="flex items-center gap-2 text-green-400">
                    <Target className="w-4 h-4" />
                    Take Profit (verrouillage des gains)
                  </Label>
                  <Input
                    type="number"
                    step="0.01"
                    placeholder={protectModal.position.side === 'LONG' ? "Prix supérieur au marché" : "Prix inférieur au marché"}
                    value={protectForm.takeProfit}
                    onChange={(e) => setProtectForm({ ...protectForm, takeProfit: e.target.value })}
                    className="font-mono"
                  />
                  {protectForm.takeProfit && (
                    <p className="text-xs text-muted-foreground">
                      {((parseFloat(protectForm.takeProfit) - protectModal.position.entryPrice) / protectModal.position.entryPrice * 100).toFixed(2)}% par rapport à l'entrée
                    </p>
                  )}
                </div>

                {/* Boutons rapides */}
                <div className="space-y-2">
                  <Label className="text-muted-foreground">Suggestions rapides</Label>
                  <div className="flex gap-2 flex-wrap">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        const price = protectModal.position.currentPrice;
                        const side = protectModal.position.side;
                        setProtectForm({
                          stopLoss: (side === 'LONG' ? price * 0.97 : price * 1.03).toFixed(2),
                          takeProfit: (side === 'LONG' ? price * 1.05 : price * 0.95).toFixed(2)
                        });
                      }}
                    >
                      Serré (3%/5%)
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        const price = protectModal.position.currentPrice;
                        const side = protectModal.position.side;
                        setProtectForm({
                          stopLoss: (side === 'LONG' ? price * 0.95 : price * 1.05).toFixed(2),
                          takeProfit: (side === 'LONG' ? price * 1.10 : price * 0.90).toFixed(2)
                        });
                      }}
                    >
                      Normal (5%/10%)
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        const price = protectModal.position.currentPrice;
                        const side = protectModal.position.side;
                        setProtectForm({
                          stopLoss: (side === 'LONG' ? price * 0.90 : price * 1.10).toFixed(2),
                          takeProfit: (side === 'LONG' ? price * 1.20 : price * 0.80).toFixed(2)
                        });
                      }}
                    >
                      Large (10%/20%)
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        // Verrouiller au prix actuel (position gagnante)
                        const price = protectModal.position.currentPrice;
                        const entry = protectModal.position.entryPrice;
                        const side = protectModal.position.side;
                        
                        if (side === 'LONG') {
                          setProtectForm({
                            stopLoss: (price * 0.99).toFixed(2), // SL juste sous le prix actuel
                            takeProfit: (price * 1.05).toFixed(2)
                          });
                        } else {
                          setProtectForm({
                            stopLoss: (price * 1.01).toFixed(2), // SL juste au-dessus du prix actuel
                            takeProfit: (price * 0.95).toFixed(2)
                          });
                        }
                      }}
                      className="border-green-500/50 text-green-400"
                    >
                      🔒 Verrouiller gains
                    </Button>
                  </div>
                </div>
              </div>
            )}

            <DialogFooter className="gap-2">
              <Button variant="outline" onClick={() => setProtectModal({ open: false, position: null })}>
                Annuler
              </Button>
              <Button 
                onClick={protectPosition} 
                disabled={protecting || (!protectForm.stopLoss && !protectForm.takeProfit)}
                className="bg-yellow-600 hover:bg-yellow-700"
              >
                {protecting ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Protection...
                  </>
                ) : (
                  <>
                    <ShieldCheck className="w-4 h-4 mr-2" />
                    Protéger la position
                  </>
                )}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </TooltipProvider>
  );
}
