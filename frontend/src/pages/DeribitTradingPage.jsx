/**
 * 🐂 BULL SAGE - Page de Trading Deribit
 * 
 * Interface complète pour le trading sur Deribit Testnet/Production:
 * - Résumé du compte (équité, marge, PnL)
 * - Positions ouvertes en temps réel
 * - Passage d'ordres Buy/Sell
 * - Historique des ordres
 * - Instruments disponibles
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
  Activity,
  Wallet,
  Clock,
  Target,
  Zap,
  BarChart3,
  AlertCircle,
  ArrowUpCircle,
  ArrowDownCircle,
  Settings,
  History,
  Coins,
  ShieldCheck,
  Power,
  PowerOff
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../components/ui/tabs";

export default function DeribitTradingPage() {
  const { token } = useAuth();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState(null);
  const [account, setAccount] = useState(null);
  const [positions, setPositions] = useState([]);
  const [openOrders, setOpenOrders] = useState([]);
  const [orderHistory, setOrderHistory] = useState([]);
  const [instruments, setInstruments] = useState([]);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  
  // États pour le modal d'ordre
  const [orderModal, setOrderModal] = useState({ open: false, type: null });
  const [orderForm, setOrderForm] = useState({
    instrument: 'BTC-PERPETUAL',
    amount: '',
    orderType: 'market',
    price: ''
  });
  const [placingOrder, setPlacingOrder] = useState(false);
  
  // États pour fermer une position
  const [closingPosition, setClosingPosition] = useState(null);
  const [cancellingOrder, setCancellingOrder] = useState(null);

  // Vérifier le statut de connexion
  const checkConnection = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/deribit/status`);
      // Backend returns { success, deribit: { connected, authenticated, testnet, ... } }
      const deribit = response.data?.deribit || response.data || {};
      const status = {
        connected: deribit.connected || false,
        authenticated: deribit.authenticated || false,
        is_testnet: deribit.testnet !== undefined ? deribit.testnet : true,
        error: deribit.error || null,
        api_url: deribit.api_url || "",
        account: deribit.account || null
      };
      setConnectionStatus(status);
      return status.connected;
    } catch (error) {
      console.error("Erreur connexion Deribit:", error);
      setConnectionStatus({ connected: false, error: error.response?.data?.detail || error.message });
      return false;
    }
  }, []);

  // Charger le résumé du compte
  const loadAccount = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/deribit/account?currency=BTC`);
      setAccount(response.data.account);
    } catch (error) {
      console.error("Erreur chargement compte:", error);
    }
  }, []);

  // Charger les positions
  const loadPositions = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/deribit/positions?currency=BTC`);
      setPositions(response.data.positions || []);
    } catch (error) {
      console.error("Erreur chargement positions:", error);
    }
  }, []);

  // Charger les ordres
  const loadOrders = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/deribit/orders?currency=BTC`);
      setOpenOrders(response.data.open_orders || []);
      setOrderHistory(response.data.order_history || []);
    } catch (error) {
      console.error("Erreur chargement ordres:", error);
    }
  }, []);

  // Charger les instruments
  const loadInstruments = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/deribit/instruments?currency=BTC&kind=future`);
      setInstruments(response.data.instruments || []);
    } catch (error) {
      console.error("Erreur chargement instruments:", error);
    }
  }, []);

  // Charger toutes les données
  const loadAllData = useCallback(async (silent = false) => {
    if (!silent) setRefreshing(true);
    
    try {
      const isConnected = await checkConnection();
      if (isConnected) {
        await Promise.all([
          loadAccount(),
          loadPositions(),
          loadOrders(),
          loadInstruments()
        ]);
      }
      setLastUpdate(new Date());
    } catch (error) {
      console.error("Erreur chargement données:", error);
      if (!silent) {
        toast.error("Erreur de chargement des données Deribit");
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [checkConnection, loadAccount, loadPositions, loadOrders, loadInstruments]);

  // Passer un ordre
  const placeOrder = async () => {
    if (!orderForm.instrument || !orderForm.amount) {
      toast.error("Veuillez remplir tous les champs");
      return;
    }

    setPlacingOrder(true);
    try {
      const endpoint = orderModal.type === 'buy' ? '/deribit/buy' : '/deribit/sell';
      const payload = {
        instrument_name: orderForm.instrument,
        amount: parseFloat(orderForm.amount),
        type: orderForm.orderType
      };
      
      if (orderForm.orderType === 'limit' && orderForm.price) {
        payload.price = parseFloat(orderForm.price);
      }

      const response = await axios.post(`${API}${endpoint}`, payload);
      
      if (response.data.success) {
        toast.success(`✅ Ordre ${orderModal.type.toUpperCase()} placé avec succès!`);
        setOrderModal({ open: false, type: null });
        setOrderForm({ instrument: 'BTC-PERPETUAL', amount: '', orderType: 'market', price: '' });
        loadAllData(true);
      } else {
        toast.error(response.data.error || "Erreur lors du passage de l'ordre");
      }
    } catch (error) {
      console.error("Erreur ordre:", error);
      toast.error(error.response?.data?.detail || "Erreur lors du passage de l'ordre");
    } finally {
      setPlacingOrder(false);
    }
  };

  // Fermer une position
  const closePosition = async (instrument) => {
    if (!window.confirm(`⚠️ Fermer la position ${instrument} au prix du marché ?`)) {
      return;
    }

    setClosingPosition(instrument);
    try {
      const response = await axios.post(`${API}/deribit/close`, {
        instrument_name: instrument
      });
      
      if (response.data.success) {
        toast.success(`✅ Position ${instrument} fermée`);
        loadAllData(true);
      } else {
        toast.error(response.data.error || "Erreur lors de la fermeture");
      }
    } catch (error) {
      console.error("Erreur fermeture:", error);
      toast.error("Erreur lors de la fermeture de la position");
    } finally {
      setClosingPosition(null);
    }
  };

  // Annuler un ordre
  const cancelOrder = async (orderId) => {
    setCancellingOrder(orderId);
    try {
      const response = await axios.post(`${API}/deribit/cancel`, {
        order_id: orderId
      });
      
      if (response.data.success) {
        toast.success("Ordre annulé");
        loadAllData(true);
      } else {
        toast.error(response.data.error || "Erreur lors de l'annulation");
      }
    } catch (error) {
      console.error("Erreur annulation:", error);
      toast.error("Erreur lors de l'annulation de l'ordre");
    } finally {
      setCancellingOrder(null);
    }
  };

  // Annuler tous les ordres
  const cancelAllOrders = async () => {
    if (!window.confirm("⚠️ Annuler TOUS les ordres ouverts ?")) {
      return;
    }

    try {
      const response = await axios.post(`${API}/deribit/cancel-all`);
      
      if (response.data.success) {
        toast.success(`${response.data.cancelled_count || 0} ordres annulés`);
        loadAllData(true);
      }
    } catch (error) {
      console.error("Erreur annulation:", error);
      toast.error("Erreur lors de l'annulation des ordres");
    }
  };

  // Chargement initial
  useEffect(() => {
    loadAllData();
  }, [loadAllData]);

  // Auto-refresh
  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(() => {
        loadAllData(true);
      }, 10000); // Refresh toutes les 10 secondes
      return () => clearInterval(interval);
    }
  }, [autoRefresh, loadAllData]);

  // Formatage des nombres
  const formatNumber = (num, decimals = 2) => {
    if (num === null || num === undefined) return '-';
    return new Intl.NumberFormat('fr-FR', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    }).format(num);
  };

  const formatCurrency = (num, currency = 'BTC') => {
    if (num === null || num === undefined) return '-';
    return `${formatNumber(num, 8)} ${currency}`;
  };

  const formatUSD = (num) => {
    if (num === null || num === undefined) return '-';
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'USD'
    }).format(num);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[80vh]">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-amber-500 mx-auto mb-4" />
          <p className="text-zinc-400">Connexion à Deribit...</p>
        </div>
      </div>
    );
  }

  return (
    <TooltipProvider>
      <div className="space-y-6 p-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-3xl font-bold text-white flex items-center gap-3">
              <BarChart3 className="h-8 w-8 text-amber-500" />
              Trading Deribit
            </h1>
            <p className="text-zinc-400 mt-1">
              {connectionStatus?.is_testnet ? '🧪 Testnet' : '🔴 Production'} • 
              Dernière mise à jour: {lastUpdate ? lastUpdate.toLocaleTimeString('fr-FR') : '-'}
            </p>
          </div>
          
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={autoRefresh ? "border-green-500 text-green-400" : "border-zinc-600"}
            >
              {autoRefresh ? <Power className="h-4 w-4 mr-2" /> : <PowerOff className="h-4 w-4 mr-2" />}
              Auto-refresh
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={() => loadAllData()}
              disabled={refreshing}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
              Actualiser
            </Button>
          </div>
        </div>

        {/* Statut de connexion */}
        {!connectionStatus?.connected && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Connexion Deribit non établie</AlertTitle>
            <AlertDescription>
              Vérifiez que les clés API Deribit (DERIBIT_CLIENT_ID et DERIBIT_CLIENT_SECRET) sont configurées
              et correspondent à l&apos;environnement {connectionStatus?.is_testnet ? "Testnet" : "Production"}.
              {connectionStatus?.error && (
                <span className="block mt-1 text-xs opacity-80">Détail: {connectionStatus.error}</span>
              )}
            </AlertDescription>
          </Alert>
        )}

        {connectionStatus?.connected && (
          <>
            {/* Résumé du compte */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card className="bg-zinc-900/50 border-zinc-800">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-zinc-400 text-sm">Équité</p>
                      <p className="text-2xl font-bold text-white">
                        {formatCurrency(account?.equity)}
                      </p>
                    </div>
                    <Wallet className="h-8 w-8 text-amber-500" />
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-zinc-900/50 border-zinc-800">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-zinc-400 text-sm">Balance</p>
                      <p className="text-2xl font-bold text-white">
                        {formatCurrency(account?.balance)}
                      </p>
                    </div>
                    <DollarSign className="h-8 w-8 text-blue-500" />
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-zinc-900/50 border-zinc-800">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-zinc-400 text-sm">Marge Utilisée</p>
                      <p className="text-2xl font-bold text-white">
                        {formatCurrency(account?.initial_margin)}
                      </p>
                    </div>
                    <Activity className="h-8 w-8 text-purple-500" />
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-zinc-900/50 border-zinc-800">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-zinc-400 text-sm">PnL Session</p>
                      <p className={`text-2xl font-bold ${
                        (account?.session_rpl || 0) >= 0 ? 'text-green-400' : 'text-red-400'
                      }`}>
                        {formatCurrency(account?.session_rpl)}
                      </p>
                    </div>
                    {(account?.session_rpl || 0) >= 0 ? (
                      <TrendingUp className="h-8 w-8 text-green-500" />
                    ) : (
                      <TrendingDown className="h-8 w-8 text-red-500" />
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Boutons d'action principaux */}
            <div className="flex flex-wrap gap-4">
              <Button
                onClick={() => setOrderModal({ open: true, type: 'buy' })}
                className="bg-green-600 hover:bg-green-700 text-white"
              >
                <ArrowUpCircle className="h-5 w-5 mr-2" />
                Acheter / Long
              </Button>
              
              <Button
                onClick={() => setOrderModal({ open: true, type: 'sell' })}
                className="bg-red-600 hover:bg-red-700 text-white"
              >
                <ArrowDownCircle className="h-5 w-5 mr-2" />
                Vendre / Short
              </Button>

              {openOrders.length > 0 && (
                <Button
                  variant="outline"
                  onClick={cancelAllOrders}
                  className="border-orange-500 text-orange-400 hover:bg-orange-500/10"
                >
                  <XCircle className="h-5 w-5 mr-2" />
                  Annuler tous les ordres ({openOrders.length})
                </Button>
              )}
            </div>

            {/* Tabs pour positions et ordres */}
            <Tabs defaultValue="positions" className="w-full">
              <TabsList className="bg-zinc-900 border border-zinc-800">
                <TabsTrigger value="positions" className="data-[state=active]:bg-amber-500/20">
                  Positions ({positions.length})
                </TabsTrigger>
                <TabsTrigger value="orders" className="data-[state=active]:bg-amber-500/20">
                  Ordres ouverts ({openOrders.length})
                </TabsTrigger>
                <TabsTrigger value="history" className="data-[state=active]:bg-amber-500/20">
                  Historique
                </TabsTrigger>
                <TabsTrigger value="instruments" className="data-[state=active]:bg-amber-500/20">
                  Instruments
                </TabsTrigger>
              </TabsList>

              {/* Positions */}
              <TabsContent value="positions" className="mt-4">
                {positions.length === 0 ? (
                  <Card className="bg-zinc-900/50 border-zinc-800">
                    <CardContent className="p-8 text-center">
                      <Activity className="h-12 w-12 text-zinc-600 mx-auto mb-4" />
                      <p className="text-zinc-400">Aucune position ouverte</p>
                      <p className="text-zinc-500 text-sm mt-2">
                        Utilisez les boutons ci-dessus pour ouvrir une position
                      </p>
                    </CardContent>
                  </Card>
                ) : (
                  <div className="grid gap-4">
                    {positions.map((position, idx) => (
                      <Card key={idx} className="bg-zinc-900/50 border-zinc-800">
                        <CardContent className="p-4">
                          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                            <div className="flex items-center gap-4">
                              <Badge variant={position.direction === 'buy' ? 'success' : 'destructive'}>
                                {position.direction === 'buy' ? 'LONG' : 'SHORT'}
                              </Badge>
                              <div>
                                <p className="font-semibold text-white text-lg">
                                  {position.instrument_name}
                                </p>
                                <p className="text-zinc-400 text-sm">
                                  Taille: {formatNumber(position.size, 4)} • 
                                  Prix entrée: {formatUSD(position.average_price)}
                                </p>
                              </div>
                            </div>

                            <div className="flex items-center gap-6">
                              <div className="text-right">
                                <p className="text-zinc-400 text-sm">PnL Non réalisé</p>
                                <p className={`text-xl font-bold ${
                                  (position.floating_profit_loss || 0) >= 0 ? 'text-green-400' : 'text-red-400'
                                }`}>
                                  {formatCurrency(position.floating_profit_loss)}
                                </p>
                              </div>

                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => closePosition(position.instrument_name)}
                                disabled={closingPosition === position.instrument_name}
                                className="border-red-500 text-red-400 hover:bg-red-500/10"
                              >
                                {closingPosition === position.instrument_name ? (
                                  <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                  <XCircle className="h-4 w-4 mr-1" />
                                )}
                                Fermer
                              </Button>
                            </div>
                          </div>

                          {/* Barre de progression du PnL */}
                          <div className="mt-4">
                            <div className="flex justify-between text-sm mb-1">
                              <span className="text-zinc-400">Niveau de marge</span>
                              <span className="text-zinc-300">
                                {formatNumber((position.maintenance_margin / (account?.equity || 1)) * 100)}%
                              </span>
                            </div>
                            <Progress 
                              value={Math.min((position.maintenance_margin / (account?.equity || 1)) * 100, 100)} 
                              className="h-2"
                            />
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </TabsContent>

              {/* Ordres ouverts */}
              <TabsContent value="orders" className="mt-4">
                {openOrders.length === 0 ? (
                  <Card className="bg-zinc-900/50 border-zinc-800">
                    <CardContent className="p-8 text-center">
                      <Clock className="h-12 w-12 text-zinc-600 mx-auto mb-4" />
                      <p className="text-zinc-400">Aucun ordre en attente</p>
                    </CardContent>
                  </Card>
                ) : (
                  <div className="space-y-3">
                    {openOrders.map((order, idx) => (
                      <Card key={idx} className="bg-zinc-900/50 border-zinc-800">
                        <CardContent className="p-4">
                          <div className="flex justify-between items-center">
                            <div className="flex items-center gap-4">
                              <Badge variant={order.direction === 'buy' ? 'success' : 'destructive'}>
                                {order.direction?.toUpperCase()}
                              </Badge>
                              <div>
                                <p className="font-medium text-white">{order.instrument_name}</p>
                                <p className="text-zinc-400 text-sm">
                                  {order.order_type} • Quantité: {formatNumber(order.amount, 4)} • 
                                  Prix: {order.price ? formatUSD(order.price) : 'Market'}
                                </p>
                              </div>
                            </div>

                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => cancelOrder(order.order_id)}
                              disabled={cancellingOrder === order.order_id}
                              className="text-zinc-400 hover:text-red-400"
                            >
                              {cancellingOrder === order.order_id ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              ) : (
                                <XCircle className="h-4 w-4" />
                              )}
                            </Button>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </TabsContent>

              {/* Historique */}
              <TabsContent value="history" className="mt-4">
                {orderHistory.length === 0 ? (
                  <Card className="bg-zinc-900/50 border-zinc-800">
                    <CardContent className="p-8 text-center">
                      <History className="h-12 w-12 text-zinc-600 mx-auto mb-4" />
                      <p className="text-zinc-400">Aucun historique d'ordres</p>
                    </CardContent>
                  </Card>
                ) : (
                  <div className="space-y-2">
                    {orderHistory.slice(0, 20).map((order, idx) => (
                      <Card key={idx} className="bg-zinc-900/30 border-zinc-800/50">
                        <CardContent className="p-3">
                          <div className="flex justify-between items-center">
                            <div className="flex items-center gap-3">
                              <Badge 
                                variant={order.direction === 'buy' ? 'outline' : 'secondary'}
                                className="text-xs"
                              >
                                {order.direction?.toUpperCase()}
                              </Badge>
                              <span className="text-zinc-300 text-sm">{order.instrument_name}</span>
                            </div>
                            <div className="text-right">
                              <span className="text-zinc-400 text-sm">
                                {formatNumber(order.filled_amount || order.amount, 4)} @ {formatUSD(order.average_price || order.price)}
                              </span>
                              <Badge variant="outline" className="ml-2 text-xs">
                                {order.order_state}
                              </Badge>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </TabsContent>

              {/* Instruments */}
              <TabsContent value="instruments" className="mt-4">
                <Card className="bg-zinc-900/50 border-zinc-800">
                  <CardHeader>
                    <CardTitle className="text-white">Instruments Disponibles</CardTitle>
                    <CardDescription>Futures et Perpetuals BTC</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                      {instruments.map((inst, idx) => (
                        <Card 
                          key={idx} 
                          className="bg-zinc-800/50 border-zinc-700 cursor-pointer hover:border-amber-500/50 transition-colors"
                          onClick={() => {
                            setOrderForm({ ...orderForm, instrument: inst.instrument_name });
                            toast.info(`Instrument sélectionné: ${inst.instrument_name}`);
                          }}
                        >
                          <CardContent className="p-3">
                            <div className="flex justify-between items-center">
                              <div>
                                <p className="font-medium text-white">{inst.instrument_name}</p>
                                <p className="text-zinc-400 text-xs">
                                  Tick: {inst.tick_size} • Min: {inst.min_trade_amount}
                                </p>
                              </div>
                              <Coins className="h-5 w-5 text-amber-500" />
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </>
        )}

        {/* Modal de passage d'ordre */}
        <Dialog open={orderModal.open} onOpenChange={(open) => setOrderModal({ open, type: null })}>
          <DialogContent className="bg-zinc-900 border-zinc-800">
            <DialogHeader>
              <DialogTitle className="text-white flex items-center gap-2">
                {orderModal.type === 'buy' ? (
                  <>
                    <ArrowUpCircle className="h-5 w-5 text-green-500" />
                    Acheter / Ouvrir Long
                  </>
                ) : (
                  <>
                    <ArrowDownCircle className="h-5 w-5 text-red-500" />
                    Vendre / Ouvrir Short
                  </>
                )}
              </DialogTitle>
              <DialogDescription>
                {connectionStatus?.is_testnet && (
                  <Badge variant="outline" className="text-amber-400 border-amber-400">
                    🧪 Testnet - Pas de fonds réels
                  </Badge>
                )}
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Instrument</Label>
                <Select
                  value={orderForm.instrument}
                  onValueChange={(value) => setOrderForm({ ...orderForm, instrument: value })}
                >
                  <SelectTrigger className="bg-zinc-800 border-zinc-700">
                    <SelectValue placeholder="Sélectionner un instrument" />
                  </SelectTrigger>
                  <SelectContent className="bg-zinc-800 border-zinc-700">
                    <SelectItem value="BTC-PERPETUAL">BTC-PERPETUAL</SelectItem>
                    <SelectItem value="ETH-PERPETUAL">ETH-PERPETUAL</SelectItem>
                    {instruments.map((inst) => (
                      <SelectItem key={inst.instrument_name} value={inst.instrument_name}>
                        {inst.instrument_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Type d'ordre</Label>
                <Select
                  value={orderForm.orderType}
                  onValueChange={(value) => setOrderForm({ ...orderForm, orderType: value })}
                >
                  <SelectTrigger className="bg-zinc-800 border-zinc-700">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-zinc-800 border-zinc-700">
                    <SelectItem value="market">Market (Immédiat)</SelectItem>
                    <SelectItem value="limit">Limit (Prix fixé)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Quantité (USD)</Label>
                <Input
                  type="number"
                  placeholder="Ex: 100"
                  value={orderForm.amount}
                  onChange={(e) => setOrderForm({ ...orderForm, amount: e.target.value })}
                  className="bg-zinc-800 border-zinc-700"
                />
                <p className="text-zinc-500 text-xs">
                  Minimum: 10 USD pour BTC-PERPETUAL
                </p>
              </div>

              {orderForm.orderType === 'limit' && (
                <div className="space-y-2">
                  <Label>Prix limite</Label>
                  <Input
                    type="number"
                    placeholder="Ex: 65000"
                    value={orderForm.price}
                    onChange={(e) => setOrderForm({ ...orderForm, price: e.target.value })}
                    className="bg-zinc-800 border-zinc-700"
                  />
                </div>
              )}
            </div>

            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setOrderModal({ open: false, type: null })}
              >
                Annuler
              </Button>
              <Button
                onClick={placeOrder}
                disabled={placingOrder || !orderForm.amount}
                className={orderModal.type === 'buy' 
                  ? 'bg-green-600 hover:bg-green-700' 
                  : 'bg-red-600 hover:bg-red-700'
                }
              >
                {placingOrder ? (
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                ) : null}
                Confirmer l'ordre
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </TooltipProvider>
  );
}
