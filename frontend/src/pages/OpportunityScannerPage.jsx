import { useState, useEffect } from "react";
import axios from "axios";
import { toast } from "sonner";
import {
  Search,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  Loader2,
  Zap,
  DollarSign,
  BarChart3,
  Bitcoin,
  Building2,
  LineChart,
  ArrowUpRight,
  ArrowDownRight,
  Target,
  Brain,
  Sparkles,
  Filter,
  CheckCircle
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Switch } from "../components/ui/switch";
import { Label } from "../components/ui/label";
import { API } from "../App";

const TYPE_ICONS = {
  crypto: Bitcoin,
  stock: Building2,
  index: LineChart
};

const TYPE_COLORS = {
  crypto: "from-amber-500/20 to-orange-500/20 border-amber-500/30",
  stock: "from-blue-500/20 to-cyan-500/20 border-blue-500/30",
  index: "from-purple-500/20 to-pink-500/20 border-purple-500/30"
};

const ACTION_STYLES = {
  BUY: { bg: "bg-emerald-500/20", text: "text-emerald-400", border: "border-emerald-500/30" },
  SELL: { bg: "bg-red-500/20", text: "text-red-400", border: "border-red-500/30" },
  WATCH: { bg: "bg-yellow-500/20", text: "text-yellow-400", border: "border-yellow-500/30" }
};

export default function OpportunityScannerPage() {
  const [opportunities, setOpportunities] = useState([]);
  const [aiRecommendation, setAiRecommendation] = useState(null);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [lastScan, setLastScan] = useState(null);
  
  // Filters
  const [includeCrypto, setIncludeCrypto] = useState(true);
  const [includeStocks, setIncludeStocks] = useState(true);
  const [includeIndices, setIncludeIndices] = useState(true);

  useEffect(() => {
    // Auto-scan on page load
    runScan();
  }, []);

  const runScan = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API}/scanner/unified`, {
        include_crypto: includeCrypto,
        include_stocks: includeStocks,
        include_indices: includeIndices,
        max_results: 15
      });
      
      setOpportunities(response.data.opportunities || []);
      setAiRecommendation(response.data.ai_recommendation);
      setSummary(response.data.summary);
      setLastScan(new Date());
      
      toast.success(`🔍 Scan terminé - ${response.data.opportunities?.length || 0} opportunités trouvées`);
    } catch (error) {
      console.error("Scan error:", error);
      toast.error("Erreur lors du scan");
    } finally {
      setLoading(false);
    }
  };

  const formatPrice = (price, type) => {
    if (type === "crypto" && price < 1) {
      return `$${price.toFixed(6)}`;
    }
    return `$${price.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold font-manrope flex items-center gap-3">
            <div className="p-2 bg-gradient-to-br from-violet-600 to-fuchsia-600 rounded-xl">
              <Search className="w-6 h-6 text-white" />
            </div>
            Scanner IA Unifié
          </h1>
          <p className="text-muted-foreground mt-1">
            Analyse en temps réel des cryptos, actions et indices pour trouver les meilleures opportunités
          </p>
        </div>
        
        <Button 
          onClick={runScan} 
          disabled={loading}
          className="bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-500 hover:to-fuchsia-500"
        >
          {loading ? (
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
          ) : (
            <RefreshCw className="w-4 h-4 mr-2" />
          )}
          {loading ? "Scan en cours..." : "Lancer le scan"}
        </Button>
      </div>

      {/* Filters */}
      <Card className="glass border-white/10">
        <CardContent className="pt-4">
          <div className="flex flex-wrap items-center gap-6">
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-muted-foreground" />
              <span className="text-sm font-medium">Filtres:</span>
            </div>
            
            <div className="flex items-center space-x-2">
              <Switch id="crypto" checked={includeCrypto} onCheckedChange={setIncludeCrypto} />
              <Label htmlFor="crypto" className="flex items-center gap-1">
                <Bitcoin className="w-4 h-4 text-amber-500" />
                Cryptos
              </Label>
            </div>
            
            <div className="flex items-center space-x-2">
              <Switch id="stocks" checked={includeStocks} onCheckedChange={setIncludeStocks} />
              <Label htmlFor="stocks" className="flex items-center gap-1">
                <Building2 className="w-4 h-4 text-blue-500" />
                Actions
              </Label>
            </div>
            
            <div className="flex items-center space-x-2">
              <Switch id="indices" checked={includeIndices} onCheckedChange={setIncludeIndices} />
              <Label htmlFor="indices" className="flex items-center gap-1">
                <LineChart className="w-4 h-4 text-purple-500" />
                Indices
              </Label>
            </div>
            
            {lastScan && (
              <span className="text-xs text-muted-foreground ml-auto">
                Dernier scan: {lastScan.toLocaleTimeString("fr-FR")}
              </span>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Summary Stats */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <Card className="glass border-white/10">
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold">{summary.total_scanned}</p>
              <p className="text-xs text-muted-foreground">Actifs scannés</p>
            </CardContent>
          </Card>
          <Card className="glass border-white/10 border-amber-500/30">
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-amber-400">{summary.crypto_count}</p>
              <p className="text-xs text-muted-foreground">Cryptos</p>
            </CardContent>
          </Card>
          <Card className="glass border-white/10 border-blue-500/30">
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-blue-400">{summary.stock_count}</p>
              <p className="text-xs text-muted-foreground">Actions</p>
            </CardContent>
          </Card>
          <Card className="glass border-white/10 border-purple-500/30">
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-purple-400">{summary.index_count}</p>
              <p className="text-xs text-muted-foreground">Indices</p>
            </CardContent>
          </Card>
          <Card className="glass border-white/10 border-emerald-500/30">
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-emerald-400">{summary.buy_signals}</p>
              <p className="text-xs text-muted-foreground">Signaux BUY</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* AI Recommendation */}
      {aiRecommendation && (
        <Card className="glass border-2 border-violet-500/30 bg-gradient-to-br from-violet-500/10 to-fuchsia-500/10">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center gap-2">
              <Brain className="w-5 h-5 text-violet-400" />
              Analyse IA
              <Sparkles className="w-4 h-4 text-fuchsia-400" />
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="prose prose-invert prose-sm max-w-none whitespace-pre-wrap">
              {aiRecommendation}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Best Opportunity Highlight */}
      {summary?.best_opportunity && (
        <Card className="glass border-2 border-emerald-500/30 bg-gradient-to-br from-emerald-500/10 to-teal-500/10 overflow-hidden">
          <div className="absolute top-0 right-0 bg-emerald-500 text-black text-xs font-bold px-3 py-1 rounded-bl-lg">
            🏆 MEILLEURE OPPORTUNITÉ
          </div>
          <CardContent className="pt-8 pb-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-14 h-14 rounded-full bg-emerald-500/20 flex items-center justify-center text-2xl">
                  {summary.best_opportunity.icon}
                </div>
                <div>
                  <h3 className="text-xl font-bold">{summary.best_opportunity.name}</h3>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge variant="outline" className="text-xs">
                      {summary.best_opportunity.type.toUpperCase()}
                    </Badge>
                    <span className="text-sm text-muted-foreground">{summary.best_opportunity.symbol}</span>
                  </div>
                </div>
              </div>
              
              <div className="text-right">
                <p className="text-2xl font-bold font-mono">
                  {formatPrice(summary.best_opportunity.price, summary.best_opportunity.type)}
                </p>
                <p className={`text-sm flex items-center justify-end gap-1 ${summary.best_opportunity.change_24h >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                  {summary.best_opportunity.change_24h >= 0 ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
                  {summary.best_opportunity.change_24h >= 0 ? "+" : ""}{summary.best_opportunity.change_24h}%
                </p>
              </div>
            </div>
            
            <div className="flex flex-wrap gap-2 mt-4">
              {summary.best_opportunity.signals?.map((signal, idx) => (
                <Badge key={idx} variant="outline" className="text-emerald-400 border-emerald-500/30">
                  <CheckCircle className="w-3 h-3 mr-1" />
                  {signal}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Opportunities Grid */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="text-center">
            <Loader2 className="w-12 h-12 animate-spin text-violet-500 mx-auto mb-4" />
            <p className="text-muted-foreground">Analyse des marchés en cours...</p>
            <p className="text-xs text-muted-foreground mt-1">Cryptos • Actions • Indices</p>
          </div>
        </div>
      ) : opportunities.length === 0 ? (
        <Card className="glass border-white/10">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Search className="w-12 h-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">Aucune opportunité trouvée</p>
            <p className="text-xs text-muted-foreground">Activez les filtres et relancez le scan</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {opportunities.map((opp, index) => {
            const TypeIcon = TYPE_ICONS[opp.type] || BarChart3;
            const actionStyle = ACTION_STYLES[opp.action] || ACTION_STYLES.WATCH;
            
            return (
              <Card 
                key={`${opp.symbol}-${index}`}
                className={`glass border bg-gradient-to-br ${TYPE_COLORS[opp.type]} hover:scale-[1.02] transition-transform cursor-pointer`}
              >
                <CardContent className="p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center">
                        {opp.icon ? (
                          <span className="text-lg">{opp.icon}</span>
                        ) : (
                          <TypeIcon className="w-5 h-5" />
                        )}
                      </div>
                      <div>
                        <h3 className="font-semibold">{opp.name}</h3>
                        <p className="text-xs text-muted-foreground">{opp.symbol} • {opp.type}</p>
                      </div>
                    </div>
                    
                    <Badge className={`${actionStyle.bg} ${actionStyle.text} ${actionStyle.border}`}>
                      {opp.action}
                    </Badge>
                  </div>
                  
                  <div className="flex items-end justify-between mb-3">
                    <div>
                      <p className="text-xl font-bold font-mono">
                        {formatPrice(opp.price, opp.type)}
                      </p>
                      <p className={`text-sm flex items-center gap-1 ${opp.change_24h >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                        {opp.change_24h >= 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                        {opp.change_24h >= 0 ? "+" : ""}{opp.change_24h}%
                      </p>
                    </div>
                    
                    <div className="text-right">
                      <p className="text-xs text-muted-foreground">Score</p>
                      <p className={`text-lg font-bold ${opp.score > 0 ? "text-emerald-400" : opp.score < 0 ? "text-red-400" : "text-yellow-400"}`}>
                        {opp.score > 0 ? "+" : ""}{opp.score}
                      </p>
                    </div>
                  </div>
                  
                  {/* Signals */}
                  <div className="flex flex-wrap gap-1">
                    {opp.signals?.slice(0, 2).map((signal, idx) => (
                      <span key={idx} className="text-xs bg-white/5 px-2 py-0.5 rounded">
                        {signal}
                      </span>
                    ))}
                  </div>
                  
                  <div className="mt-2 pt-2 border-t border-white/5">
                    <p className="text-xs text-muted-foreground">
                      Source: {opp.source}
                    </p>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
