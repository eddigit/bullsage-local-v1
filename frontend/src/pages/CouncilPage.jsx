import { useState, useEffect, useRef, useCallback } from "react";
import { API, useAuth } from "../App";
import { Navigate } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import {
  Brain,
  Users,
  TrendingUp,
  TrendingDown,
  Minus,
  DollarSign,
  Clock,
  CheckCircle,
  AlertCircle,
  Loader2,
  Play,
  BarChart3,
  Shield,
  Globe,
  Hash,
  Newspaper,
  Activity,
  Terminal,
  Coins,
  ChevronRight,
  RefreshCw,
  Zap,
  Eye,
  EyeOff,
  Target,
  Search
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Input } from "../components/ui/input";

// Configuration des agents avec couleurs et icônes (nouvelle structure)
const AGENT_CONFIG = {
  groq_technical: { icon: BarChart3, color: "#3B82F6", bgColor: "bg-blue-500/10" },
  deepseek_quant: { icon: Hash, color: "#8B5CF6", bgColor: "bg-purple-500/10" },
  openrouter_macro: { icon: Globe, color: "#F59E0B", bgColor: "bg-amber-500/10" },
  grok_sentiment: { icon: Activity, color: "#1DA1F2", bgColor: "bg-sky-500/10" },
  perplexity_news: { icon: Newspaper, color: "#10B981", bgColor: "bg-emerald-500/10" },
  claude_fundamental: { icon: Search, color: "#EC4899", bgColor: "bg-pink-500/10" },
  manus_strategy: { icon: Target, color: "#EF4444", bgColor: "bg-red-500/10" },
  orchestrator: { icon: Brain, color: "#F97316", bgColor: "bg-orange-500/10" }
};

// Modes d'analyse
const ANALYSIS_MODES = {
  quick: {
    id: "quick",
    name: "⚡ Rapide",
    description: "2 agents gratuits",
    color: "from-green-500 to-emerald-500",
    borderColor: "border-green-500/50"
  },
  standard: {
    id: "standard", 
    name: "📊 Standard",
    description: "4 agents équilibrés",
    color: "from-blue-500 to-cyan-500",
    borderColor: "border-blue-500/50"
  },
  full: {
    id: "full",
    name: "🏆 Complet",
    description: "7 agents experts",
    color: "from-orange-500 to-red-500",
    borderColor: "border-orange-500/50"
  }
};

const VERDICT_COLORS = {
  STRONG_BUY: { bg: "bg-emerald-500", text: "text-white", icon: TrendingUp },
  BUY: { bg: "bg-green-500", text: "text-white", icon: TrendingUp },
  BULLISH: { bg: "bg-green-500", text: "text-white", icon: TrendingUp },
  HOLD: { bg: "bg-yellow-500", text: "text-black", icon: Minus },
  NEUTRAL: { bg: "bg-gray-500", text: "text-white", icon: Minus },
  SELL: { bg: "bg-red-500", text: "text-white", icon: TrendingDown },
  BEARISH: { bg: "bg-red-500", text: "text-white", icon: TrendingDown },
  STRONG_SELL: { bg: "bg-red-700", text: "text-white", icon: TrendingDown }
};

export default function CouncilPage() {
  const { user, token } = useAuth();
  const [selectedAsset, setSelectedAsset] = useState("bitcoin");
  const [selectedMode, setSelectedMode] = useState("standard");
  const [modes, setModes] = useState({});
  const [costEstimate, setCostEstimate] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isEstimating, setIsEstimating] = useState(false);
  const [terminalLogs, setTerminalLogs] = useState([]);
  const [userCosts, setUserCosts] = useState(null);
  const [showTerminal, setShowTerminal] = useState(true);
  const terminalRef = useRef(null);
  const wsRef = useRef(null);

  // Redirect si non authentifié
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // Charger les modes et coûts
  useEffect(() => {
    fetchModes();
    fetchUserCosts();
    connectWebSocket();
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  // Auto-scroll terminal
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [terminalLogs]);

  const connectWebSocket = useCallback(() => {
    if (!user?.id) return;
    
    const wsUrl = `${API.replace('http', 'ws')}/council/ws/${user.id}`;
    wsRef.current = new WebSocket(wsUrl);
    
    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === "agent_log") {
        addTerminalLog(data);
      }
    };
    
    wsRef.current.onclose = () => {
      setTimeout(connectWebSocket, 3000);
    };
  }, [user?.id]);

  const addTerminalLog = (log) => {
    setTerminalLogs(prev => [...prev, {
      ...log,
      id: Date.now() + Math.random()
    }]);
  };

  const fetchModes = async () => {
    try {
      const response = await axios.get(`${API}/council/modes`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setModes(response.data.available_modes || {});
    } catch (error) {
      console.error("Error fetching modes:", error);
    }
  };

  const fetchUserCosts = async () => {
    try {
      const response = await axios.get(`${API}/council/costs/summary`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUserCosts(response.data);
    } catch (error) {
      console.error("Error fetching costs:", error);
    }
  };

  const estimateCost = async (mode = selectedMode) => {
    setIsEstimating(true);
    try {
      const response = await axios.get(`${API}/council/cost-estimate/${mode}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setCostEstimate(response.data);
      addTerminalLog({
        timestamp: new Date().toISOString(),
        agent_id: "system",
        agent_name: "🔮 Système",
        status: "info",
        message: `Mode ${mode}: ${response.data.agents_count} agents • ~$${response.data.estimated_cost_usd.toFixed(4)}`
      });
      
    } catch (error) {
      toast.error("Erreur lors de l'estimation");
    } finally {
      setIsEstimating(false);
    }
  };

  const runAnalysis = async () => {
    setIsAnalyzing(true);
    setAnalysisResult(null);
    setTerminalLogs([]);
    
    addTerminalLog({
      timestamp: new Date().toISOString(),
      agent_id: "council",
      agent_name: "🏛️ Bull Sage Council",
      status: "starting",
      message: `Analyse ${selectedAsset.toUpperCase()} en mode ${ANALYSIS_MODES[selectedMode]?.name}...`
    });

    try {
      const response = await axios.post(`${API}/council/analyze`, {
        symbol: selectedAsset,
        mode: selectedMode,
        confirm_cost: true
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.data.status === "completed") {
        setAnalysisResult(response.data.result);
        
        if (response.data.logs) {
          response.data.logs.forEach(log => addTerminalLog(log));
        }
        
        toast.success("Analyse terminée !");
        fetchUserCosts();
      } else {
        // Confirmation required
        setCostEstimate(response.data.estimate);
        toast.info(response.data.message);
      }
      
    } catch (error) {
      toast.error("Erreur lors de l'analyse");
      addTerminalLog({
        timestamp: new Date().toISOString(),
        agent_id: "system",
        agent_name: "❌ Erreur",
        status: "error",
        message: error.response?.data?.detail || error.message
      });
    } finally {
      setIsAnalyzing(false);
    }
  };

  const selectMode = (modeId) => {
    setSelectedMode(modeId);
    setCostEstimate(null);
    estimateCost(modeId);
  };

  const getVerdictStyle = (verdict) => {
    return VERDICT_COLORS[verdict?.toUpperCase()] || VERDICT_COLORS.NEUTRAL;
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-900 to-black text-white p-4 md:p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 bg-orange-500/20 rounded-xl">
            <Brain className="w-8 h-8 text-orange-500" />
          </div>
          <div>
            <h1 className="text-2xl md:text-3xl font-bold">Bull Sage Council</h1>
            <p className="text-gray-400 text-sm">7 agents IA spécialisés + orchestrateur Groq</p>
          </div>
        </div>
        
        {/* Indicateur de coûts global */}
        {userCosts && (
          <div className="flex flex-wrap gap-4 mt-4">
            <div className="flex items-center gap-2 bg-gray-800/50 rounded-lg px-3 py-2">
              <DollarSign className="w-4 h-4 text-green-500" />
              <span className="text-sm">Total: <span className="font-mono font-bold">${userCosts.total_cost_usd?.toFixed(4) || '0'}</span></span>
            </div>
            <div className="flex items-center gap-2 bg-gray-800/50 rounded-lg px-3 py-2">
              <BarChart3 className="w-4 h-4 text-blue-500" />
              <span className="text-sm">Analyses: <span className="font-bold">{userCosts.total_analyses || 0}</span></span>
            </div>
            <div className="flex items-center gap-2 bg-gray-800/50 rounded-lg px-3 py-2">
              <Activity className="w-4 h-4 text-purple-500" />
              <span className="text-sm">Moy: <span className="font-mono">${userCosts.average_cost_per_analysis?.toFixed(4) || '0'}</span>/analyse</span>
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Colonne gauche: Sélection & Modes */}
        <div className="space-y-6">
          {/* Sélection asset */}
          <Card className="bg-gray-800/50 border-gray-700">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center gap-2">
                <Coins className="w-5 h-5 text-yellow-500" />
                Asset à analyser
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Input
                value={selectedAsset}
                onChange={(e) => {
                  setSelectedAsset(e.target.value.toLowerCase());
                  setCostEstimate(null);
                }}
                placeholder="bitcoin, ethereum, solana..."
                className="bg-gray-900/50 border-gray-600"
              />
              <p className="text-xs text-gray-500 mt-2">
                Symbole ou ID CoinGecko (BTC, ETH, bitcoin, ethereum...)
              </p>
            </CardContent>
          </Card>

          {/* Sélection du mode */}
          <Card className="bg-gray-800/50 border-gray-700">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center gap-2">
                <Zap className="w-5 h-5 text-yellow-500" />
                Mode d'analyse
              </CardTitle>
              <CardDescription>
                Choisissez selon votre besoin
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {Object.values(ANALYSIS_MODES).map((mode) => {
                const modeData = modes[mode.id];
                const isSelected = selectedMode === mode.id;
                
                return (
                  <div
                    key={mode.id}
                    onClick={() => selectMode(mode.id)}
                    className={`
                      p-4 rounded-lg border-2 cursor-pointer transition-all
                      ${isSelected 
                        ? `bg-gradient-to-r ${mode.color} bg-opacity-20 ${mode.borderColor}` 
                        : 'bg-gray-900/50 border-gray-700 hover:border-gray-600'
                      }
                    `}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-bold">{mode.name}</p>
                        <p className="text-xs text-gray-400">{mode.description}</p>
                      </div>
                      <div className="text-right">
                        {modeData ? (
                          <>
                            <p className="font-mono font-bold text-lg">
                              ${modeData.estimated_cost_usd?.toFixed(3) || '0.00'}
                            </p>
                            <p className="text-xs text-gray-500">
                              {modeData.agents_count || 0} agents
                            </p>
                          </>
                        ) : (
                          <Loader2 className="w-4 h-4 animate-spin text-gray-500" />
                        )}
                      </div>
                    </div>
                    
                    {/* Agents du mode */}
                    {isSelected && modeData?.agents && (
                      <div className="mt-3 pt-3 border-t border-gray-700/50">
                        <div className="flex flex-wrap gap-2">
                          {modeData.agents.map((agent) => {
                            const config = AGENT_CONFIG[agent.id] || { icon: Brain, color: "#6B7280" };
                            return (
                              <div
                                key={agent.id}
                                className="flex items-center gap-1 px-2 py-1 bg-gray-800/50 rounded text-xs"
                              >
                                <span>{agent.emoji}</span>
                                <span className="text-gray-400">{agent.name}</span>
                                {!agent.configured && (
                                  <AlertCircle className="w-3 h-3 text-yellow-500" title="API key manquante" />
                                )}
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </CardContent>
          </Card>

          {/* Estimation & Lancement */}
          <Card className="bg-gray-800/50 border-gray-700">
            <CardContent className="pt-6 space-y-4">
              {/* Affichage estimation */}
              {costEstimate && (
                <div className="p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <AlertCircle className="w-4 h-4 text-yellow-500" />
                    <span className="font-medium text-yellow-500">Coût estimé</span>
                  </div>
                  <div className="flex justify-between items-end">
                    <div>
                      <p className="text-gray-400 text-sm">{costEstimate.mode_name}</p>
                      <p className="font-mono font-bold text-2xl">
                        ${costEstimate.estimated_cost_usd?.toFixed(4) || '0.0000'}
                      </p>
                    </div>
                    <div className="text-right text-sm text-gray-500">
                      <p>{costEstimate.agents_count} agents</p>
                      <p>~{costEstimate.estimated_time_seconds}s</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Bouton analyse */}
              <Button
                onClick={runAnalysis}
                className={`w-full bg-gradient-to-r ${ANALYSIS_MODES[selectedMode]?.color || 'from-orange-500 to-red-500'} hover:opacity-90`}
                disabled={isAnalyzing}
              >
                {isAnalyzing ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Analyse en cours...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 mr-2" />
                    Lancer l'analyse {ANALYSIS_MODES[selectedMode]?.name}
                  </>
                )}
              </Button>

              <p className="text-xs text-center text-gray-500">
                ⚠️ Cette action sera facturée au coût indiqué
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Colonne centrale: Terminal */}
        <div className="lg:col-span-2 space-y-6">
          {/* Terminal de logs */}
          <Card className="bg-gray-900 border-gray-700">
            <CardHeader className="pb-2 flex flex-row items-center justify-between">
              <div className="flex items-center gap-2">
                <Terminal className="w-5 h-5 text-green-500" />
                <CardTitle className="text-lg">Terminal Agent</CardTitle>
                <Badge variant="outline" className="text-xs">
                  {terminalLogs.length} logs
                </Badge>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setTerminalLogs([])}
                >
                  <RefreshCw className="w-4 h-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowTerminal(!showTerminal)}
                >
                  {showTerminal ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </Button>
              </div>
            </CardHeader>
            {showTerminal && (
              <CardContent>
                <div
                  ref={terminalRef}
                  className="bg-black rounded-lg p-4 h-64 overflow-y-auto font-mono text-sm space-y-1"
                >
                  {terminalLogs.length === 0 ? (
                    <div className="text-gray-500 flex items-center gap-2">
                      <span className="animate-pulse">▌</span>
                      Sélectionnez un mode et lancez une analyse...
                    </div>
                  ) : (
                    terminalLogs.map((log) => (
                      <div key={log.id} className="flex gap-2">
                        <span className="text-gray-500 text-xs">
                          {new Date(log.timestamp).toLocaleTimeString()}
                        </span>
                        <span 
                          className={`
                            ${log.status === 'completed' ? 'text-green-400' : ''}
                            ${log.status === 'error' ? 'text-red-400' : ''}
                            ${log.status === 'thinking' || log.status === 'analyzing' ? 'text-yellow-400' : ''}
                            ${log.status === 'starting' || log.status === 'info' ? 'text-blue-400' : ''}
                          `}
                        >
                          [{log.agent_name}]
                        </span>
                        <span className="text-gray-300">{log.message}</span>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            )}
          </Card>

          {/* Résultat de l'analyse */}
          {analysisResult && (
            <>
              {/* Recommandation finale */}
              <Card className="bg-gradient-to-r from-gray-800 to-gray-900 border-orange-500/50">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="p-3 bg-orange-500/20 rounded-xl">
                        <Brain className="w-6 h-6 text-orange-500" />
                      </div>
                      <div>
                        <CardTitle>Recommandation Finale</CardTitle>
                        <CardDescription>
                          Synthèse du Council pour {analysisResult.symbol?.toUpperCase()}
                        </CardDescription>
                      </div>
                    </div>
                    
                    {/* Badge verdict */}
                    {analysisResult.recommendation?.action && (
                      <Badge 
                        className={`text-lg px-4 py-2 ${getVerdictStyle(analysisResult.recommendation.action).bg} ${getVerdictStyle(analysisResult.recommendation.action).text}`}
                      >
                        {analysisResult.recommendation.action}
                      </Badge>
                    )}
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Votes du Council (consensus) */}
                  {analysisResult.consensus?.votes && (
                    <div className="grid grid-cols-3 gap-4">
                      <div className="text-center p-3 bg-green-500/10 rounded-lg">
                        <TrendingUp className="w-6 h-6 text-green-500 mx-auto mb-1" />
                        <p className="text-2xl font-bold text-green-500">
                          {analysisResult.consensus.votes.bullish || 0}
                        </p>
                        <p className="text-xs text-gray-400">Bullish</p>
                      </div>
                      <div className="text-center p-3 bg-gray-500/10 rounded-lg">
                        <Minus className="w-6 h-6 text-gray-500 mx-auto mb-1" />
                        <p className="text-2xl font-bold text-gray-500">
                          {analysisResult.consensus.votes.neutral || 0}
                        </p>
                        <p className="text-xs text-gray-400">Neutral</p>
                      </div>
                      <div className="text-center p-3 bg-red-500/10 rounded-lg">
                        <TrendingDown className="w-6 h-6 text-red-500 mx-auto mb-1" />
                        <p className="text-2xl font-bold text-red-500">
                          {analysisResult.consensus.votes.bearish || 0}
                        </p>
                        <p className="text-xs text-gray-400">Bearish</p>
                      </div>
                    </div>
                  )}

                  {/* Scores */}
                  <div className="flex gap-4">
                    <div className="flex-1 p-3 bg-gray-800/50 rounded-lg">
                      <p className="text-sm text-gray-400 mb-1">Confiance</p>
                      <div className="flex items-center gap-2">
                        <div className="flex-1 bg-gray-700 rounded-full h-2">
                          <div 
                            className="bg-orange-500 h-2 rounded-full"
                            style={{ width: `${(analysisResult.recommendation?.confidence || 0) * 100}%` }}
                          />
                        </div>
                        <span className="font-bold">{((analysisResult.recommendation?.confidence || 0) * 100).toFixed(0)}%</span>
                      </div>
                    </div>
                    <div className="flex-1 p-3 bg-gray-800/50 rounded-lg">
                      <p className="text-sm text-gray-400 mb-1">Consensus</p>
                      <div className="flex items-center gap-2">
                        <div className="flex-1 bg-gray-700 rounded-full h-2">
                          <div 
                            className="bg-blue-500 h-2 rounded-full"
                            style={{ width: `${analysisResult.consensus?.percentage || 0}%` }}
                          />
                        </div>
                        <span className="font-bold">{analysisResult.consensus?.percentage || 0}%</span>
                      </div>
                    </div>
                  </div>

                  {/* Résumé */}
                  {analysisResult.recommendation?.summary && (
                    <div className="p-4 bg-gray-800/50 rounded-lg">
                      <p className="text-gray-300">{analysisResult.recommendation.summary}</p>
                    </div>
                  )}

                  {/* Niveaux clés */}
                  {analysisResult.synthesis?.key_levels && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      {analysisResult.synthesis.key_levels.entry && (
                        <div className="p-3 bg-blue-500/10 rounded-lg">
                          <p className="text-xs text-gray-400">Entrée</p>
                          <p className="font-mono font-bold text-blue-400">${analysisResult.synthesis.key_levels.entry}</p>
                        </div>
                      )}
                      {analysisResult.synthesis.key_levels.stop_loss && (
                        <div className="p-3 bg-red-500/10 rounded-lg">
                          <p className="text-xs text-gray-400">Stop Loss</p>
                          <p className="font-mono font-bold text-red-400">${analysisResult.synthesis.key_levels.stop_loss}</p>
                        </div>
                      )}
                      {analysisResult.synthesis.key_levels.take_profit_1 && (
                        <div className="p-3 bg-green-500/10 rounded-lg">
                          <p className="text-xs text-gray-400">TP1</p>
                          <p className="font-mono font-bold text-green-400">${analysisResult.synthesis.key_levels.take_profit_1}</p>
                        </div>
                      )}
                      {analysisResult.synthesis.key_levels.take_profit_2 && (
                        <div className="p-3 bg-emerald-500/10 rounded-lg">
                          <p className="text-xs text-gray-400">TP2</p>
                          <p className="font-mono font-bold text-emerald-400">${analysisResult.synthesis.key_levels.take_profit_2}</p>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Plan d'action */}
                  {analysisResult.recommendation?.action_plan?.length > 0 && (
                    <div className="p-4 bg-gray-800/50 rounded-lg">
                      <p className="text-sm font-medium mb-2 text-gray-300">📋 Plan d'action</p>
                      <ul className="space-y-1">
                        {analysisResult.recommendation.action_plan.map((step, i) => (
                          <li key={i} className="text-sm text-gray-400 flex items-start gap-2">
                            <ChevronRight className="w-4 h-4 mt-0.5 text-orange-500" />
                            {step}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Coûts de l'analyse */}
                  {analysisResult.cost && (
                    <div className="flex items-center justify-between p-3 bg-gray-800/30 rounded-lg border border-gray-700">
                      <div className="flex items-center gap-2">
                        <DollarSign className="w-4 h-4 text-green-500" />
                        <span className="text-sm text-gray-400">Coût de cette analyse</span>
                      </div>
                      <div className="flex items-center gap-4">
                        <span className="font-mono font-bold">
                          ${analysisResult.cost.total_cost_usd?.toFixed(6) || '0'}
                        </span>
                        <span className="text-gray-500 text-sm">
                          {analysisResult.execution_time_seconds}s
                        </span>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Analyses individuelles des agents */}
              <Card className="bg-gray-800/50 border-gray-700">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Users className="w-5 h-5 text-blue-500" />
                    Analyses des Agents ({analysisResult.individual_analyses?.length || 0})
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {analysisResult.individual_analyses?.map((agentResult) => {
                      const config = AGENT_CONFIG[agentResult.agent_id] || { icon: Brain, color: "#6B7280" };
                      const IconComponent = config.icon;
                      const verdict = agentResult.analysis?.signal;
                      const verdictStyle = getVerdictStyle(verdict);
                      
                      return (
                        <div
                          key={agentResult.agent_id}
                          className="p-4 bg-gray-900/50 rounded-lg border border-gray-700"
                        >
                          <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center gap-2">
                              <span className="text-lg">{agentResult.emoji}</span>
                              <span className="font-medium text-sm">{agentResult.agent}</span>
                            </div>
                            {verdict && (
                              <Badge className={`${verdictStyle.bg} ${verdictStyle.text}`}>
                                {verdict}
                              </Badge>
                            )}
                          </div>
                          
                          {/* Confiance */}
                          <div className="mb-2">
                            <div className="flex justify-between text-xs mb-1">
                              <span className="text-gray-400">Confiance</span>
                              <span>{((agentResult.analysis?.confidence || 0) * 100).toFixed(0)}%</span>
                            </div>
                            <div className="bg-gray-700 rounded-full h-1.5">
                              <div 
                                className="h-1.5 rounded-full"
                                style={{ 
                                  width: `${(agentResult.analysis?.confidence || 0) * 100}%`,
                                  backgroundColor: config.color
                                }}
                              />
                            </div>
                          </div>
                          
                          {/* Résumé */}
                          {agentResult.analysis?.summary && (
                            <p className="text-xs text-gray-400 line-clamp-2">
                              {agentResult.analysis.summary}
                            </p>
                          )}
                          
                          {/* Métriques */}
                          <div className="flex items-center gap-2 mt-2 text-xs text-gray-500">
                            <Clock className="w-3 h-3" />
                            <span>{agentResult.execution_time}s</span>
                            <span>•</span>
                            <span className="text-gray-600">{agentResult.provider}</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
