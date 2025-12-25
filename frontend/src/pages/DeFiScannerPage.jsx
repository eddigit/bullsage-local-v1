import { useState, useEffect } from "react";
import axios from "axios";
import { toast } from "sonner";
import {
  Search,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  Filter,
  ExternalLink,
  Star,
  Zap,
  BarChart3,
  DollarSign,
  Activity,
  Loader2,
  ChevronDown,
  ArrowUpRight,
  ArrowDownRight
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "../components/ui/collapsible";
import { API } from "../App";

const CHAIN_OPTIONS = [
  { id: "solana", name: "Solana", logo: "https://cryptologos.cc/logos/solana-sol-logo.png" },
  { id: "ethereum", name: "Ethereum", logo: "https://cryptologos.cc/logos/ethereum-eth-logo.png" },
  { id: "bsc", name: "BSC", logo: "https://cryptologos.cc/logos/bnb-bnb-logo.png" },
  { id: "polygon", name: "Polygon", logo: "https://cryptologos.cc/logos/polygon-matic-logo.png" },
];

const EXPLORER_URLS = {
  solana: "https://solscan.io/token/",
  ethereum: "https://etherscan.io/token/",
  bsc: "https://bscscan.com/token/",
  polygon: "https://polygonscan.com/token/"
};

export default function DeFiScannerPage() {
  const [tokens, setTokens] = useState([]);
  const [loading, setLoading] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [filtersOpen, setFiltersOpen] = useState(false);
  
  // Filter state
  const [selectedChain, setSelectedChain] = useState("solana");
  const [minLiquidity, setMinLiquidity] = useState(10000);
  const [minVolume, setMinVolume] = useState(5000);
  const [limit, setLimit] = useState(20);
  
  // Stats
  const [scanTime, setScanTime] = useState(null);
  const [totalFound, setTotalFound] = useState(0);

  useEffect(() => {
    // Initial scan on mount
    handleScan();
  }, []);

  const handleScan = async () => {
    setScanning(true);
    try {
      const params = new URLSearchParams({
        chain: selectedChain,
        limit: limit.toString(),
        min_liquidity: minLiquidity.toString(),
        min_volume: minVolume.toString()
      });
      
      const response = await axios.get(`${API}/defi-scanner/scan?${params}`);
      const data = response.data || {};
      setTokens(Array.isArray(data.tokens) ? data.tokens : []);
      setScanTime(data.scan_time || null);
      setTotalFound(data.total_found || 0);
      toast.success(`${data.total_found || 0} tokens trouvés!`);
    } catch (error) {
      console.error("Scan error:", error);
      toast.error("Erreur lors du scan");
    } finally {
      setScanning(false);
    }
  };

  const formatNumber = (num, decimals = 2) => {
    if (num >= 1000000) return `$${(num / 1000000).toFixed(decimals)}M`;
    if (num >= 1000) return `$${(num / 1000).toFixed(decimals)}K`;
    return `$${num.toFixed(decimals)}`;
  };

  const formatPrice = (price) => {
    if (price < 0.00001) return `$${price.toExponential(2)}`;
    if (price < 0.01) return `$${price.toFixed(6)}`;
    if (price < 1) return `$${price.toFixed(4)}`;
    return `$${price.toFixed(2)}`;
  };

  const getScoreColor = (score) => {
    if (score >= 80) return "text-emerald-500";
    if (score >= 60) return "text-yellow-500";
    if (score >= 40) return "text-orange-500";
    return "text-red-500";
  };

  const getScoreBg = (score) => {
    if (score >= 80) return "bg-emerald-500/20";
    if (score >= 60) return "bg-yellow-500/20";
    if (score >= 40) return "bg-orange-500/20";
    return "bg-red-500/20";
  };

  const openExplorer = (token) => {
    const baseUrl = EXPLORER_URLS[token.chain] || EXPLORER_URLS.solana;
    window.open(`${baseUrl}${token.address}`, '_blank');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold font-manrope flex items-center gap-3">
            <Search className="w-8 h-8 text-primary" />
            Scanner DeFi
          </h1>
          <p className="text-muted-foreground mt-1">
            Trouvez les tokens tendance sur les DEX
          </p>
        </div>
        
        <Button 
          onClick={handleScan}
          disabled={scanning}
          className="bg-primary hover:bg-primary/90 text-black"
        >
          {scanning ? (
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
          ) : (
            <RefreshCw className="w-4 h-4 mr-2" />
          )}
          Scanner
        </Button>
      </div>

      {/* Filters */}
      <Collapsible open={filtersOpen} onOpenChange={setFiltersOpen}>
        <Card className="glass border-white/5">
          <CollapsibleTrigger asChild>
            <CardHeader className="cursor-pointer hover:bg-white/5 transition-colors rounded-t-lg">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Filter className="w-5 h-5 text-primary" />
                  <CardTitle className="text-lg">Filtres</CardTitle>
                </div>
                <ChevronDown className={`w-5 h-5 transition-transform ${filtersOpen ? 'rotate-180' : ''}`} />
              </div>
            </CardHeader>
          </CollapsibleTrigger>
          
          <CollapsibleContent>
            <CardContent className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-0">
              <div className="space-y-2">
                <Label>Blockchain</Label>
                <Select value={selectedChain} onValueChange={setSelectedChain}>
                  <SelectTrigger className="bg-black/20 border-white/10">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {CHAIN_OPTIONS.map(chain => (
                      <SelectItem key={chain.id} value={chain.id}>
                        <div className="flex items-center gap-2">
                          <img src={chain.logo} alt={chain.name} className="w-4 h-4 rounded-full" />
                          {chain.name}
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div className="space-y-2">
                <Label>Liquidité min ($)</Label>
                <Input
                  type="number"
                  value={minLiquidity}
                  onChange={(e) => setMinLiquidity(Number(e.target.value))}
                  className="bg-black/20 border-white/10"
                />
              </div>
              
              <div className="space-y-2">
                <Label>Volume 24h min ($)</Label>
                <Input
                  type="number"
                  value={minVolume}
                  onChange={(e) => setMinVolume(Number(e.target.value))}
                  className="bg-black/20 border-white/10"
                />
              </div>
              
              <div className="space-y-2">
                <Label>Nombre de résultats</Label>
                <Select value={limit.toString()} onValueChange={(v) => setLimit(Number(v))}>
                  <SelectTrigger className="bg-black/20 border-white/10">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="10">10 tokens</SelectItem>
                    <SelectItem value="20">20 tokens</SelectItem>
                    <SelectItem value="30">30 tokens</SelectItem>
                    <SelectItem value="50">50 tokens</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </CollapsibleContent>
        </Card>
      </Collapsible>

      {/* Stats */}
      {scanTime && (
        <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
          <span className="flex items-center gap-1">
            <Activity className="w-4 h-4" />
            {totalFound} tokens trouvés
          </span>
          <span className="flex items-center gap-1">
            <Zap className="w-4 h-4 text-primary" />
            {selectedChain.charAt(0).toUpperCase() + selectedChain.slice(1)}
          </span>
          <span>
            Dernière mise à jour: {new Date(scanTime).toLocaleTimeString('fr-FR')}
          </span>
        </div>
      )}

      {/* Tokens List */}
      {scanning ? (
        <div className="flex flex-col items-center justify-center py-16">
          <Loader2 className="w-12 h-12 animate-spin text-primary mb-4" />
          <p className="text-muted-foreground">Scan des DEX en cours...</p>
          <p className="text-sm text-muted-foreground">GeckoTerminal, DexScreener...</p>
        </div>
      ) : tokens.length === 0 ? (
        <Card className="glass border-white/5">
          <CardContent className="flex flex-col items-center justify-center py-16">
            <Search className="w-16 h-16 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">Aucun token trouvé</h3>
            <p className="text-muted-foreground text-center mb-4">
              Essayez d'ajuster vos filtres ou changez de blockchain
            </p>
            <Button onClick={handleScan} variant="outline">
              <RefreshCw className="w-4 h-4 mr-2" />
              Relancer le scan
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {tokens.map((token, index) => (
            <Card key={`${token.address}-${index}`} className="glass border-white/5 hover:border-white/10 transition-colors">
              <CardContent className="p-4">
                <div className="flex flex-col lg:flex-row lg:items-center gap-4">
                  {/* Token Info */}
                  <div className="flex items-center gap-3 min-w-[200px]">
                    <div className={`w-12 h-12 rounded-full flex items-center justify-center ${getScoreBg(token.score)}`}>
                      <span className={`font-bold ${getScoreColor(token.score)}`}>
                        {token.score}
                      </span>
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-bold">{token.symbol}</h3>
                        <Badge variant="outline" className="text-xs">
                          {token.chain}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground truncate max-w-[150px]">
                        {token.name}
                      </p>
                    </div>
                  </div>
                  
                  {/* Price */}
                  <div className="flex-1 grid grid-cols-2 sm:grid-cols-4 gap-4">
                    <div>
                      <p className="text-xs text-muted-foreground mb-1">Prix</p>
                      <p className="font-semibold">{formatPrice(token.price_usd)}</p>
                    </div>
                    
                    <div>
                      <p className="text-xs text-muted-foreground mb-1">24h</p>
                      <div className={`flex items-center gap-1 font-semibold ${
                        token.price_change_24h >= 0 ? 'text-emerald-500' : 'text-red-500'
                      }`}>
                        {token.price_change_24h >= 0 ? (
                          <ArrowUpRight className="w-4 h-4" />
                        ) : (
                          <ArrowDownRight className="w-4 h-4" />
                        )}
                        {Math.abs(token.price_change_24h).toFixed(2)}%
                      </div>
                    </div>
                    
                    <div>
                      <p className="text-xs text-muted-foreground mb-1">Volume 24h</p>
                      <p className="font-semibold">{formatNumber(token.volume_24h)}</p>
                    </div>
                    
                    <div>
                      <p className="text-xs text-muted-foreground mb-1">Liquidité</p>
                      <p className="font-semibold">{formatNumber(token.liquidity)}</p>
                    </div>
                  </div>
                  
                  {/* Actions */}
                  <div className="flex items-center gap-2">
                    <Badge className={`${getScoreBg(token.score)} ${getScoreColor(token.score)} border-none`}>
                      {token.score >= 80 ? "🔥 Hot" : token.score >= 60 ? "📈 Trending" : "👀 Watch"}
                    </Badge>
                    
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => openExplorer(token)}
                      className="h-8 w-8"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
                
                {/* Additional Info */}
                {token.dex && (
                  <div className="flex items-center gap-4 mt-3 pt-3 border-t border-white/5 text-sm text-muted-foreground">
                    <span>DEX: {token.dex}</span>
                    <span>Source: {token.source}</span>
                    {token.fdv > 0 && <span>FDV: {formatNumber(token.fdv)}</span>}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Info Card */}
      <Card className="glass border-white/5 bg-gradient-to-r from-primary/10 to-violet-500/10">
        <CardContent className="p-6">
          <div className="flex items-start gap-4">
            <Zap className="w-8 h-8 text-primary flex-shrink-0" />
            <div>
              <h3 className="font-semibold mb-2">Comment utiliser le Scanner DeFi</h3>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• <strong>Score</strong>: Plus le score est élevé, plus le token est intéressant (volume, liquidité, momentum)</li>
                <li>• <strong>🔥 Hot</strong>: Score ≥80 - Forte activité et momentum positif</li>
                <li>• <strong>📈 Trending</strong>: Score 60-79 - En tendance, à surveiller</li>
                <li>• <strong>⚠️</strong>: Toujours faire vos propres recherches (DYOR) avant d'investir</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
