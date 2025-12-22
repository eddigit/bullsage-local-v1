import { useState, useEffect, useRef, useCallback } from "react";
import { createChart, CrosshairMode } from "lightweight-charts";
import axios from "axios";
import { toast } from "sonner";
import {
  TrendingUp,
  TrendingDown,
  RefreshCw,
  Star,
  Loader2,
  ChevronDown,
  Wifi
} from "lucide-react";
import { Card, CardContent } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "../components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "../components/ui/popover";
import { API } from "../App";

// Top crypto pairs
const TOP_PAIRS = [
  { symbol: "BTCUSDT", name: "Bitcoin", icon: "₿" },
  { symbol: "ETHUSDT", name: "Ethereum", icon: "Ξ" },
  { symbol: "SOLUSDT", name: "Solana", icon: "◎" },
  { symbol: "BNBUSDT", name: "BNB", icon: "◆" },
  { symbol: "XRPUSDT", name: "XRP", icon: "✕" },
  { symbol: "ADAUSDT", name: "Cardano", icon: "₳" },
  { symbol: "DOGEUSDT", name: "Dogecoin", icon: "Ð" },
  { symbol: "AVAXUSDT", name: "Avalanche", icon: "▲" },
  { symbol: "DOTUSDT", name: "Polkadot", icon: "●" },
  { symbol: "MATICUSDT", name: "Polygon", icon: "⬡" },
  { symbol: "LINKUSDT", name: "Chainlink", icon: "⬢" },
  { symbol: "LTCUSDT", name: "Litecoin", icon: "Ł" },
  { symbol: "ATOMUSDT", name: "Cosmos", icon: "⚛" },
  { symbol: "NEARUSDT", name: "NEAR", icon: "N" },
  { symbol: "UNIUSDT", name: "Uniswap", icon: "🦄" },
];

// Timeframe options
const TIMEFRAMES = [
  { value: "1m", label: "1m", interval: "1m", refreshMs: 10000 },
  { value: "5m", label: "5m", interval: "5m", refreshMs: 30000 },
  { value: "15m", label: "15m", interval: "15m", refreshMs: 60000 },
  { value: "1h", label: "1H", interval: "1h", refreshMs: 60000 },
  { value: "4h", label: "4H", interval: "4h", refreshMs: 120000 },
  { value: "1d", label: "1D", interval: "1d", refreshMs: 300000 },
];

export default function ChartPage() {
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);
  const candlestickSeriesRef = useRef(null);
  const volumeSeriesRef = useRef(null);
  const refreshIntervalRef = useRef(null);
  
  const [selectedPair, setSelectedPair] = useState("BTCUSDT");
  const [selectedTimeframe, setSelectedTimeframe] = useState("1m");
  const [pairSearchOpen, setPairSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [currentPrice, setCurrentPrice] = useState(null);
  const [priceChange, setPriceChange] = useState(0);
  const [volume24h, setVolume24h] = useState(0);
  const [high24h, setHigh24h] = useState(0);
  const [low24h, setLow24h] = useState(0);
  const [lastUpdate, setLastUpdate] = useState(null);

  // Initialize chart
  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: "solid", color: "transparent" },
        textColor: "#9ca3af",
      },
      grid: {
        vertLines: { color: "rgba(255, 255, 255, 0.05)" },
        horzLines: { color: "rgba(255, 255, 255, 0.05)" },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: {
          color: "#FFD700",
          width: 1,
          style: 2,
          labelBackgroundColor: "#FFD700",
        },
        horzLine: {
          color: "#FFD700",
          width: 1,
          style: 2,
          labelBackgroundColor: "#FFD700",
        },
      },
      rightPriceScale: {
        borderColor: "rgba(255, 255, 255, 0.1)",
        scaleMargins: { top: 0.1, bottom: 0.2 },
      },
      timeScale: {
        borderColor: "rgba(255, 255, 255, 0.1)",
        timeVisible: true,
        secondsVisible: false,
      },
      handleScroll: { vertTouchDrag: false },
    });

    const candlestickSeries = chart.addCandlestickSeries({
      upColor: "#22c55e",
      downColor: "#ef4444",
      borderUpColor: "#22c55e",
      borderDownColor: "#ef4444",
      wickUpColor: "#22c55e",
      wickDownColor: "#ef4444",
    });

    const volumeSeries = chart.addHistogramSeries({
      color: "#3b82f6",
      priceFormat: { type: "volume" },
      priceScaleId: "",
      scaleMargins: { top: 0.85, bottom: 0 },
    });

    chartRef.current = chart;
    candlestickSeriesRef.current = candlestickSeries;
    volumeSeriesRef.current = volumeSeries;

    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({
          width: chartContainerRef.current.clientWidth,
          height: chartContainerRef.current.clientHeight,
        });
      }
    };

    window.addEventListener("resize", handleResize);
    handleResize();

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
    };
  }, []);

  // Fetch chart data
  const loadChartData = useCallback(async (showLoading = true) => {
    if (showLoading) setLoading(true);
    const timeframe = TIMEFRAMES.find(t => t.value === selectedTimeframe);
    
    try {
      // Fetch klines
      const [klinesRes, tickerRes] = await Promise.all([
        axios.get(`${API}/chart/klines/${selectedPair}`, {
          params: { interval: timeframe.interval, limit: 200 },
        }),
        axios.get(`${API}/chart/ticker/${selectedPair}`)
      ]);

      const candles = klinesRes.data.candles;
      const ticker = tickerRes.data;

      if (candlestickSeriesRef.current && volumeSeriesRef.current && candles.length > 0) {
        candlestickSeriesRef.current.setData(candles);
        volumeSeriesRef.current.setData(
          candles.map(c => ({
            time: c.time,
            value: c.volume,
            color: c.close >= c.open ? "rgba(34, 197, 94, 0.5)" : "rgba(239, 68, 68, 0.5)",
          }))
        );
      }

      setCurrentPrice(ticker.price);
      setPriceChange(ticker.priceChangePercent);
      setVolume24h(ticker.quoteVolume);
      setHigh24h(ticker.high);
      setLow24h(ticker.low);
      setLastUpdate(new Date());

    } catch (error) {
      console.error("Failed to load chart data:", error);
      if (showLoading) {
        toast.error("Erreur de chargement des données");
      }
    } finally {
      if (showLoading) setLoading(false);
    }
  }, [selectedPair, selectedTimeframe]);

  // Load data on mount and when pair/timeframe changes
  useEffect(() => {
    loadChartData(true);
  }, [loadChartData]);

  // Auto-refresh
  useEffect(() => {
    const timeframe = TIMEFRAMES.find(t => t.value === selectedTimeframe);
    
    if (refreshIntervalRef.current) {
      clearInterval(refreshIntervalRef.current);
    }

    refreshIntervalRef.current = setInterval(() => {
      loadChartData(false);
    }, timeframe.refreshMs);

    return () => {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
      }
    };
  }, [selectedTimeframe, loadChartData]);

  const formatVolume = (vol) => {
    if (!vol) return "$0";
    if (vol >= 1e9) return `$${(vol / 1e9).toFixed(2)}B`;
    if (vol >= 1e6) return `$${(vol / 1e6).toFixed(2)}M`;
    if (vol >= 1e3) return `$${(vol / 1e3).toFixed(2)}K`;
    return `$${vol.toFixed(2)}`;
  };

  const formatPrice = (price) => {
    if (!price) return "-";
    if (price < 0.001) return price.toFixed(8);
    if (price < 1) return price.toFixed(6);
    if (price < 100) return price.toFixed(4);
    try {
      return price.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    } catch {
      return price.toFixed(2);
    }
  };

  const filteredPairs = searchQuery
    ? TOP_PAIRS.filter(p => 
        p.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.name.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : TOP_PAIRS;

  const selectedPairInfo = TOP_PAIRS.find(p => p.symbol === selectedPair) ||
    { symbol: selectedPair, name: selectedPair.replace("USDT", ""), icon: "●" };

  return (
    <div className="h-[calc(100vh-120px)] md:h-[calc(100vh-80px)] flex flex-col gap-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          {/* Pair Selector */}
          <Popover open={pairSearchOpen} onOpenChange={setPairSearchOpen}>
            <PopoverTrigger asChild>
              <Button
                variant="outline"
                className="w-[200px] justify-between bg-black/20 border-white/10 hover:bg-white/5"
              >
                <div className="flex items-center gap-2">
                  <span className="text-lg">{selectedPairInfo.icon}</span>
                  <span className="font-bold">{selectedPairInfo.name}</span>
                  <span className="text-muted-foreground">/USD</span>
                </div>
                <ChevronDown className="w-4 h-4 opacity-50" />
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-[300px] p-0 glass border-white/10" align="start">
              <Command>
                <CommandInput 
                  placeholder="Rechercher..." 
                  value={searchQuery}
                  onValueChange={setSearchQuery}
                />
                <CommandList>
                  <CommandEmpty>Aucune paire trouvée</CommandEmpty>
                  <CommandGroup heading="Cryptomonnaies">
                    {filteredPairs.map(pair => (
                      <CommandItem
                        key={pair.symbol}
                        value={pair.symbol}
                        onSelect={() => {
                          setSelectedPair(pair.symbol);
                          setPairSearchOpen(false);
                          setSearchQuery("");
                        }}
                        className="cursor-pointer"
                      >
                        <Star className={`w-4 h-4 mr-2 ${selectedPair === pair.symbol ? "text-yellow-500 fill-yellow-500" : "text-muted-foreground"}`} />
                        <span className="mr-2">{pair.icon}</span>
                        <span className="font-medium">{pair.name}</span>
                        <span className="text-muted-foreground ml-1">/USD</span>
                      </CommandItem>
                    ))}
                  </CommandGroup>
                </CommandList>
              </Command>
            </PopoverContent>
          </Popover>

          {/* Price Display */}
          <div className="hidden sm:flex flex-col">
            <div className="flex items-center gap-2">
              <span className="text-2xl font-bold">${formatPrice(currentPrice)}</span>
              <Badge className={`${priceChange >= 0 ? "bg-emerald-500/20 text-emerald-500" : "bg-red-500/20 text-red-500"}`}>
                {priceChange >= 0 ? <TrendingUp className="w-3 h-3 mr-1" /> : <TrendingDown className="w-3 h-3 mr-1" />}
                {priceChange >= 0 ? "+" : ""}{priceChange?.toFixed(2) || "0.00"}%
              </Badge>
            </div>
          </div>
        </div>

        {/* Timeframe & Refresh */}
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-emerald-500 border-emerald-500/30">
            <Wifi className="w-3 h-3 mr-1" />
            Live
          </Badge>
          
          <Button
            variant="ghost"
            size="icon"
            onClick={() => loadChartData(true)}
            disabled={loading}
            className="h-8 w-8"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </Button>
          
          <div className="flex bg-black/20 rounded-lg p-1">
            {TIMEFRAMES.map(tf => (
              <Button
                key={tf.value}
                variant="ghost"
                size="sm"
                onClick={() => setSelectedTimeframe(tf.value)}
                className={`px-3 py-1 text-xs font-medium transition-all ${
                  selectedTimeframe === tf.value
                    ? "bg-primary text-black"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {tf.label}
              </Button>
            ))}
          </div>
        </div>
      </div>

      {/* Stats Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        <Card className="glass border-white/5">
          <CardContent className="p-3">
            <p className="text-xs text-muted-foreground">24h High</p>
            <p className="font-semibold text-emerald-500">${formatPrice(high24h)}</p>
          </CardContent>
        </Card>
        <Card className="glass border-white/5">
          <CardContent className="p-3">
            <p className="text-xs text-muted-foreground">24h Low</p>
            <p className="font-semibold text-red-500">${formatPrice(low24h)}</p>
          </CardContent>
        </Card>
        <Card className="glass border-white/5">
          <CardContent className="p-3">
            <p className="text-xs text-muted-foreground">24h Volume</p>
            <p className="font-semibold">{formatVolume(volume24h)}</p>
          </CardContent>
        </Card>
        <Card className="glass border-white/5">
          <CardContent className="p-3">
            <p className="text-xs text-muted-foreground">Variation</p>
            <p className={`font-semibold ${priceChange >= 0 ? "text-emerald-500" : "text-red-500"}`}>
              {priceChange >= 0 ? "+" : ""}{priceChange?.toFixed(2) || "0.00"}%
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Chart Container */}
      <Card className="glass border-white/5 flex-1 relative overflow-hidden">
        {loading && (
          <div className="absolute inset-0 bg-background/80 flex items-center justify-center z-10">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
          </div>
        )}
        <div 
          ref={chartContainerRef} 
          className="w-full h-full min-h-[400px]"
        />
      </Card>

      {/* Info */}
      <div className="text-xs text-muted-foreground text-center">
        Données via CryptoCompare • Intervalle: {selectedTimeframe} • 
        {lastUpdate && ` Dernière MAJ: ${lastUpdate.toLocaleTimeString("fr-FR")}`}
      </div>
    </div>
  );
}
