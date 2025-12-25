import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Switch } from '../components/ui/switch';
import { Slider } from '../components/ui/slider';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Bot, Play, Pause, TrendingUp, TrendingDown, AlertCircle, Zap, Shield, Target, History, Settings, RefreshCw, DollarSign } from 'lucide-react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

export default function AutoTradingPage() {
  const [config, setConfig] = useState({
    enabled: false,
    max_trade_amount: 100,
    min_score: 5.0,
    risk_level: 'conservative',
    max_daily_trades: 5,
    stop_loss_percent: 5.0,
    take_profit_percent: 10.0,
    assets_to_trade: ['bitcoin', 'ethereum', 'solana', 'cardano', 'ripple']
  });
  const [stats, setStats] = useState({ today_trades: 0, is_active: false });
  const [history, setHistory] = useState({ trades: [], stats: {} });
  const [scanning, setScanning] = useState(false);
  const [scanResult, setScanResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [autoScanInterval, setAutoScanInterval] = useState(null);

  const fetchConfig = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/auto-trading/config`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setConfig(response.data?.config || { enabled: false, assets_to_trade: [], max_position_size: 100, risk_per_trade: 2 });
      setStats(response.data?.stats || { total_trades: 0, win_rate: 0, total_pnl: 0 });
    } catch (error) {
      console.error('Error fetching config:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchHistory = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/auto-trading/history?limit=50`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setHistory(Array.isArray(response.data) ? response.data : []);
    } catch (error) {
      console.error('Error fetching history:', error);
    }
  }, []);

  useEffect(() => {
    fetchConfig();
    fetchHistory();
  }, [fetchConfig, fetchHistory]);

  const saveConfig = async (newConfig) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/auto-trading/config`, newConfig, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setConfig(newConfig);
    } catch (error) {
      console.error('Error saving config:', error);
    }
  };

  const toggleAutoTrading = async () => {
    const newEnabled = !config.enabled;
    const newConfig = { ...config, enabled: newEnabled };
    await saveConfig(newConfig);
    
    if (newEnabled) {
      // Start auto-scan every 15 minutes (reduced to save API calls)
      const interval = setInterval(() => {
        runScan();
        checkExits();
      }, 15 * 60 * 1000);
      setAutoScanInterval(interval);
      
      // Run initial scan
      runScan();
    } else {
      if (autoScanInterval) {
        clearInterval(autoScanInterval);
        setAutoScanInterval(null);
      }
    }
  };

  const runScan = async () => {
    setScanning(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/auto-trading/scan`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setScanResult(response.data);
      fetchHistory();
      fetchConfig();
    } catch (error) {
      console.error('Error scanning:', error);
      setScanResult({ error: error.message });
    } finally {
      setScanning(false);
    }
  };

  const checkExits = async () => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/auto-trading/check-exits`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchHistory();
    } catch (error) {
      console.error('Error checking exits:', error);
    }
  };

  const availableAssets = [
    { id: 'bitcoin', name: 'Bitcoin', symbol: 'BTC' },
    { id: 'ethereum', name: 'Ethereum', symbol: 'ETH' },
    { id: 'solana', name: 'Solana', symbol: 'SOL' },
    { id: 'cardano', name: 'Cardano', symbol: 'ADA' },
    { id: 'ripple', name: 'XRP', symbol: 'XRP' },
    { id: 'dogecoin', name: 'Dogecoin', symbol: 'DOGE' },
    { id: 'polkadot', name: 'Polkadot', symbol: 'DOT' },
    { id: 'avalanche-2', name: 'Avalanche', symbol: 'AVAX' },
    { id: 'chainlink', name: 'Chainlink', symbol: 'LINK' },
    { id: 'litecoin', name: 'Litecoin', symbol: 'LTC' }
  ];

  const toggleAsset = (assetId) => {
    const newAssets = config.assets_to_trade.includes(assetId)
      ? config.assets_to_trade.filter(a => a !== assetId)
      : [...config.assets_to_trade, assetId];
    saveConfig({ ...config, assets_to_trade: newAssets });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-4 md:p-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold flex items-center gap-2">
            <Bot className="h-8 w-8 text-purple-500" />
            Auto-Trading IA
          </h1>
          <p className="text-gray-400 mt-1">
            BULL trade automatiquement avec des signaux haute confiance uniquement
          </p>
        </div>
        
        <div className="flex items-center gap-4">
          <div className={`px-4 py-2 rounded-lg flex items-center gap-2 ${config.enabled ? 'bg-green-500/20 text-green-400' : 'bg-gray-700 text-gray-400'}`}>
            {config.enabled ? <Play className="h-4 w-4" /> : <Pause className="h-4 w-4" />}
            {config.enabled ? 'Actif' : 'Inactif'}
          </div>
          <Switch
            checked={config.enabled}
            onCheckedChange={toggleAutoTrading}
            className="data-[state=checked]:bg-purple-600"
          />
        </div>
      </div>

      {/* Warning Banner */}
      <Card className="bg-yellow-500/10 border-yellow-500/30">
        <CardContent className="p-4 flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-yellow-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-yellow-500">Mode Paper Trading</p>
            <p className="text-sm text-gray-400">
              L'auto-trading fonctionne en mode simulation. Aucun argent réel n'est investi.
              BULL n'exécute que des trades avec un score ≥ {config.min_score} (haute confiance).
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-gray-800/50 border-gray-700">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Trades Aujourd'hui</p>
                <p className="text-2xl font-bold">{stats.today_trades}/{config.max_daily_trades}</p>
              </div>
              <Zap className="h-8 w-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gray-800/50 border-gray-700">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Win Rate</p>
                <p className="text-2xl font-bold text-green-400">{history.stats.win_rate || 0}%</p>
              </div>
              <Target className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gray-800/50 border-gray-700">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">P&L Total</p>
                <p className={`text-2xl font-bold ${(history.stats.total_profit || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  ${(history.stats.total_profit || 0).toFixed(2)}
                </p>
              </div>
              <DollarSign className="h-8 w-8 text-yellow-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gray-800/50 border-gray-700">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Total Trades</p>
                <p className="text-2xl font-bold">{history.stats.total_trades || 0}</p>
              </div>
              <History className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Manual Scan Button */}
      <Card className="bg-gradient-to-r from-purple-900/50 to-blue-900/50 border-purple-500/30">
        <CardContent className="p-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div>
              <h3 className="text-lg font-bold">Scanner le Marché Maintenant</h3>
              <p className="text-sm text-gray-400">
                Analyse tous les actifs et exécute les trades haute confiance
              </p>
            </div>
            <Button
              onClick={runScan}
              disabled={scanning || !config.enabled}
              className="bg-purple-600 hover:bg-purple-700 px-8"
            >
              {scanning ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  Analyse en cours...
                </>
              ) : (
                <>
                  <Zap className="h-4 w-4 mr-2" />
                  Scanner & Trader
                </>
              )}
            </Button>
          </div>
          
          {/* Scan Result */}
          {scanResult && (
            <div className="mt-4 p-4 bg-gray-800/50 rounded-lg">
              {scanResult.error ? (
                <p className="text-red-400">{scanResult.error}</p>
              ) : (
                <div className="space-y-3">
                  <p className="text-green-400">{scanResult.message}</p>
                  
                  {scanResult.trades && scanResult.trades.length > 0 && (
                    <div className="space-y-2">
                      <p className="font-medium">Trades Exécutés:</p>
                      {scanResult.trades.map((trade, idx) => (
                        <div key={idx} className="flex items-center justify-between bg-gray-700/50 p-3 rounded">
                          <div className="flex items-center gap-2">
                            <Badge className={trade.action === 'BUY' ? 'bg-green-600' : 'bg-red-600'}>
                              {trade.action}
                            </Badge>
                            <span className="font-medium">{trade.coin}</span>
                          </div>
                          <div className="text-right">
                            <p className="font-medium">${trade.amount.toFixed(2)}</p>
                            <p className="text-xs text-gray-400">Score: {trade.score}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                  
                  {scanResult.opportunities && scanResult.opportunities.length > 0 && (
                    <div className="space-y-2">
                      <p className="font-medium text-gray-400">Opportunités détectées:</p>
                      {scanResult.opportunities.map((opp, idx) => (
                        <div key={idx} className="flex items-center justify-between text-sm">
                          <span>{opp.name}</span>
                          <span className={opp.score >= 5 ? 'text-green-400' : 'text-yellow-400'}>
                            Score: {opp.score}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Configuration Tabs */}
      <Tabs defaultValue="config" className="space-y-4">
        <TabsList className="bg-gray-800">
          <TabsTrigger value="config" className="data-[state=active]:bg-purple-600">
            <Settings className="h-4 w-4 mr-2" />
            Configuration
          </TabsTrigger>
          <TabsTrigger value="history" className="data-[state=active]:bg-purple-600">
            <History className="h-4 w-4 mr-2" />
            Historique
          </TabsTrigger>
        </TabsList>

        {/* Configuration Tab */}
        <TabsContent value="config" className="space-y-4">
          <div className="grid md:grid-cols-2 gap-4">
            {/* Risk Settings */}
            <Card className="bg-gray-800/50 border-gray-700">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="h-5 w-5 text-blue-500" />
                  Gestion du Risque
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Min Score */}
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <label className="text-sm text-gray-400">Score Minimum (Confiance)</label>
                    <span className="text-sm font-medium">{config.min_score}</span>
                  </div>
                  <Slider
                    value={[config.min_score]}
                    onValueChange={(v) => saveConfig({ ...config, min_score: v[0] })}
                    min={3}
                    max={8}
                    step={0.5}
                    className="w-full"
                  />
                  <p className="text-xs text-gray-500">
                    Plus élevé = moins de trades mais plus sûrs
                  </p>
                </div>

                {/* Max Trade Amount */}
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <label className="text-sm text-gray-400">Montant Max par Trade</label>
                    <span className="text-sm font-medium">${config.max_trade_amount}</span>
                  </div>
                  <Slider
                    value={[config.max_trade_amount]}
                    onValueChange={(v) => saveConfig({ ...config, max_trade_amount: v[0] })}
                    min={20}
                    max={500}
                    step={10}
                    className="w-full"
                  />
                </div>

                {/* Max Daily Trades */}
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <label className="text-sm text-gray-400">Max Trades/Jour</label>
                    <span className="text-sm font-medium">{config.max_daily_trades}</span>
                  </div>
                  <Slider
                    value={[config.max_daily_trades]}
                    onValueChange={(v) => saveConfig({ ...config, max_daily_trades: v[0] })}
                    min={1}
                    max={20}
                    step={1}
                    className="w-full"
                  />
                </div>

                {/* Stop Loss */}
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <label className="text-sm text-gray-400">Stop Loss</label>
                    <span className="text-sm font-medium text-red-400">-{config.stop_loss_percent}%</span>
                  </div>
                  <Slider
                    value={[config.stop_loss_percent]}
                    onValueChange={(v) => saveConfig({ ...config, stop_loss_percent: v[0] })}
                    min={2}
                    max={15}
                    step={0.5}
                    className="w-full"
                  />
                </div>

                {/* Take Profit */}
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <label className="text-sm text-gray-400">Take Profit</label>
                    <span className="text-sm font-medium text-green-400">+{config.take_profit_percent}%</span>
                  </div>
                  <Slider
                    value={[config.take_profit_percent]}
                    onValueChange={(v) => saveConfig({ ...config, take_profit_percent: v[0] })}
                    min={3}
                    max={30}
                    step={1}
                    className="w-full"
                  />
                </div>
              </CardContent>
            </Card>

            {/* Assets Selection */}
            <Card className="bg-gray-800/50 border-gray-700">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="h-5 w-5 text-purple-500" />
                  Actifs à Trader
                </CardTitle>
                <CardDescription>
                  Sélectionnez les cryptos que BULL peut trader automatiquement
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-2">
                  {availableAssets.map((asset) => (
                    <button
                      key={asset.id}
                      onClick={() => toggleAsset(asset.id)}
                      className={`p-3 rounded-lg border transition-all ${
                        config.assets_to_trade.includes(asset.id)
                          ? 'bg-purple-600/20 border-purple-500 text-purple-400'
                          : 'bg-gray-700/50 border-gray-600 text-gray-400 hover:border-gray-500'
                      }`}
                    >
                      <span className="font-medium">{asset.symbol}</span>
                      <span className="text-xs block opacity-70">{asset.name}</span>
                    </button>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* History Tab */}
        <TabsContent value="history">
          <Card className="bg-gray-800/50 border-gray-700">
            <CardHeader>
              <CardTitle>Historique des Auto-Trades</CardTitle>
            </CardHeader>
            <CardContent>
              {history.trades.length === 0 ? (
                <div className="text-center py-8 text-gray-400">
                  <Bot className="h-12 w-12 mx-auto mb-3 opacity-50" />
                  <p>Aucun auto-trade exécuté pour le moment</p>
                  <p className="text-sm">Activez l'auto-trading et scannez le marché</p>
                </div>
              ) : (
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {history.trades.map((trade, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between p-3 bg-gray-700/50 rounded-lg"
                    >
                      <div className="flex items-center gap-3">
                        <Badge className={trade.type === 'buy' ? 'bg-green-600' : 'bg-red-600'}>
                          {trade.type === 'buy' ? 'ACHAT' : 'VENTE'}
                        </Badge>
                        <div>
                          <p className="font-medium">{trade.coin_id}</p>
                          <p className="text-xs text-gray-400">
                            {new Date(trade.created_at).toLocaleString('fr-FR')}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-medium">${trade.amount_usd?.toFixed(2)}</p>
                        {trade.profit_loss !== undefined && (
                          <p className={`text-sm ${trade.profit_loss >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                            {trade.profit_loss >= 0 ? '+' : ''}{trade.profit_loss.toFixed(2)}$
                          </p>
                        )}
                        <p className="text-xs text-gray-500">Score: {trade.score}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* How it Works */}
      <Card className="bg-gray-800/50 border-gray-700">
        <CardHeader>
          <CardTitle>Comment fonctionne l'Auto-Trading ?</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-4 gap-4">
            <div className="text-center p-4">
              <div className="w-12 h-12 bg-purple-600/20 rounded-full flex items-center justify-center mx-auto mb-3">
                <span className="text-xl font-bold text-purple-400">1</span>
              </div>
              <h4 className="font-medium mb-1">Analyse Continue</h4>
              <p className="text-sm text-gray-400">BULL scanne en permanence les marchés avec l'analyse technique</p>
            </div>
            <div className="text-center p-4">
              <div className="w-12 h-12 bg-purple-600/20 rounded-full flex items-center justify-center mx-auto mb-3">
                <span className="text-xl font-bold text-purple-400">2</span>
              </div>
              <h4 className="font-medium mb-1">Score de Confiance</h4>
              <p className="text-sm text-gray-400">Seuls les signaux avec un score ≥ {config.min_score} sont considérés</p>
            </div>
            <div className="text-center p-4">
              <div className="w-12 h-12 bg-purple-600/20 rounded-full flex items-center justify-center mx-auto mb-3">
                <span className="text-xl font-bold text-purple-400">3</span>
              </div>
              <h4 className="font-medium mb-1">Exécution Auto</h4>
              <p className="text-sm text-gray-400">Les trades haute confiance sont exécutés automatiquement</p>
            </div>
            <div className="text-center p-4">
              <div className="w-12 h-12 bg-purple-600/20 rounded-full flex items-center justify-center mx-auto mb-3">
                <span className="text-xl font-bold text-purple-400">4</span>
              </div>
              <h4 className="font-medium mb-1">Stop Loss Auto</h4>
              <p className="text-sm text-gray-400">Chaque trade a un SL (-{config.stop_loss_percent}%) et TP (+{config.take_profit_percent}%) automatique</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
