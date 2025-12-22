import { useState, useEffect, useRef, useCallback } from "react";
import { createChart, CrosshairMode } from "lightweight-charts";
import axios from "axios";
import { toast } from "sonner";
import {
  TrendingUp,
  TrendingDown,
  RefreshCw,
  Clock,
  Search,
  Star,
  Activity,
  Loader2,
  ChevronDown,
  Wifi,
  WifiOff
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

// Top 10 crypto pairs
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
];

// Timeframe options
const TIMEFRAMES = [
  { value: "15s", label: "15s", binanceInterval: "1s", aggregation: 15 },
  { value: "1m", label: "1m", binanceInterval: "1m", aggregation: 1 },
  { value: "5m", label: "5m", binanceInterval: "5m", aggregation: 1 },
  { value: "15m", label: "15m", binanceInterval: "15m", aggregation: 1 },
  { value: "1h", label: "1H", binanceInterval: "1h", aggregation: 1 },
  { value: "4h", label: "4H", binanceInterval: "4h", aggregation: 1 },
  { value: "1d", label: "1D", binanceInterval: "1d", aggregation: 1 },
];

export default function ChartPage() {
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);
  const candlestickSeriesRef = useRef(null);
  const volumeSeriesRef = useRef(null);
  const wsRef = useRef(null);
  
  const [selectedPair, setSelectedPair] = useState("BTCUSDT");
  const [selectedTimeframe, setSelectedTimeframe] = useState("1m");
  const [allPairs, setAllPairs] = useState([]);
  const [pairSearchOpen, setPairSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [wsConnected, setWsConnected] = useState(false);
  const [currentPrice, setCurrentPrice] = useState(null);
  const [priceChange, setPriceChange] = useState(0);
  const [volume24h, setVolume24h] = useState(0);
  const [high24h, setHigh24h] = useState(0);
  const [low24h, setLow24h] = useState(0);
  
  // Buffer for 15s aggregation
  const candleBufferRef = useRef([]);
  const lastAggregatedTimeRef = useRef(null);

  // Fetch all pairs from backend proxy
  useEffect(() => {
    const fetchPairs = async () => {
      try {
        const response = await axios.get(`${API}/chart/pairs`);
        const pairs = response.data.pairs.map(p => ({
          symbol: p.symbol,
          name: p.baseAsset,
          icon: p.baseAsset.charAt(0)
        }));
        setAllPairs(pairs);
      } catch (error) {
        console.error("Failed to fetch pairs:", error);
        setAllPairs(TOP_PAIRS);
      }
    };
    fetchPairs();
  }, []);

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
        secondsVisible: true,
      },
      handleScroll: { vertTouchDrag: false },
    });

    // Candlestick series
    const candlestickSeries = chart.addCandlestickSeries({
      upColor: "#22c55e",
      downColor: "#ef4444",
      borderUpColor: "#22c55e",
      borderDownColor: "#ef4444",
      wickUpColor: "#22c55e",
      wickDownColor: "#ef4444",
    });

    // Volume series
    const volumeSeries = chart.addHistogramSeries({
      color: "#3b82f6",
      priceFormat: { type: "volume" },
      priceScaleId: "",
      scaleMargins: { top: 0.85, bottom: 0 },
    });

    chartRef.current = chart;
    candlestickSeriesRef.current = candlestickSeries;
    volumeSeriesRef.current = volumeSeries;

    // Handle resize
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

  // Aggregate candles for custom timeframes
  const aggregateCandles = (candles, seconds) => {
    const aggregated = [];
    let currentCandle = null;
    
    for (const candle of candles) {
      const bucketTime = Math.floor(candle.time / seconds) * seconds;
      
      if (!currentCandle || currentCandle.time !== bucketTime) {
        if (currentCandle) {
          aggregated.push(currentCandle);
        }
        currentCandle = {
          time: bucketTime,
          open: candle.open,
          high: candle.high,
          low: candle.low,
          close: candle.close,
          volume: candle.volume,
        };
      } else {
        currentCandle.high = Math.max(currentCandle.high, candle.high);
        currentCandle.low = Math.min(currentCandle.low, candle.low);
        currentCandle.close = candle.close;
        currentCandle.volume += candle.volume;
      }
    }
    
    if (currentCandle) {
      aggregated.push(currentCandle);
    }
    
    return aggregated;
  };

  // Fetch historical data
  const loadChartData = useCallback(async () => {
    setLoading(true);
    const timeframe = TIMEFRAMES.find(t => t.value === selectedTimeframe);
    
    try {
      // Fetch klines from our backend proxy
      const response = await axios.get(`${API}/chart/klines/${selectedPair}`, {
        params: {
          interval: timeframe.binanceInterval,
          limit: 500,
        },
      });

      let candles = response.data.candles;

      // For 15s timeframe, aggregate
      if (timeframe.aggregation > 1) {
        candles = aggregateCandles(candles, timeframe.aggregation);
      }

      if (candlestickSeriesRef.current && volumeSeriesRef.current) {
        candlestickSeriesRef.current.setData(candles);
        volumeSeriesRef.current.setData(
          candles.map(c => ({
            time: c.time,
            value: c.volume,
            color: c.close >= c.open ? "rgba(34, 197, 94, 0.5)" : "rgba(239, 68, 68, 0.5)",
          }))
        );
        
        if (candles.length > 0) {
          const lastCandle = candles[candles.length - 1];
          setCurrentPrice(lastCandle.close);
        }
      }

      // Fetch 24h ticker
      const tickerResponse = await axios.get(`${API}/chart/ticker/${selectedPair}`);
      const ticker = tickerResponse.data;
      
      setCurrentPrice(ticker.price);
      setPriceChange(ticker.priceChangePercent);
      setVolume24h(ticker.quoteVolume);
      setHigh24h(ticker.high);
      setLow24h(ticker.low);

    } catch (error) {
      console.error("Failed to load chart data:", error);
      toast.error("Erreur de chargement des données");
    } finally {
      setLoading(false);
    }
  }, [selectedPair, selectedTimeframe]);

  // Setup WebSocket for real-time updates
  useEffect(() => {
    if (wsRef.current) {
      wsRef.current.close();
    }

    const timeframe = TIMEFRAMES.find(t => t.value === selectedTimeframe);
    const wsInterval = timeframe.binanceInterval;
    
    // Connect directly to Binance WebSocket (WebSocket doesn't have CORS issues)
    const ws = new WebSocket(
      `wss://stream.binance.com:9443/ws/${selectedPair.toLowerCase()}@kline_${wsInterval}`
    );

    ws.onopen = () => {
      setWsConnected(true);
      console.log("WebSocket connected");
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      const kline = data.k;
      
      const candle = {
        time: Math.floor(kline.t / 1000),
        open: parseFloat(kline.o),
        high: parseFloat(kline.h),
        low: parseFloat(kline.l),
        close: parseFloat(kline.c),
        volume: parseFloat(kline.v),
      };

      setCurrentPrice(candle.close);

      // For 15s aggregation
      if (timeframe.aggregation > 1) {
        const bucketTime = Math.floor(candle.time / timeframe.aggregation) * timeframe.aggregation;
        
        if (lastAggregatedTimeRef.current !== bucketTime) {
          lastAggregatedTimeRef.current = bucketTime;
          candleBufferRef.current = [candle];
        } else {
          candleBufferRef.current.push(candle);
        }
        
        const aggregatedCandle = {
          time: bucketTime,
          open: candleBufferRef.current[0].open,
          high: Math.max(...candleBufferRef.current.map(c => c.high)),
          low: Math.min(...candleBufferRef.current.map(c => c.low)),
          close: candle.close,
          volume: candleBufferRef.current.reduce((sum, c) => sum + c.volume, 0),
        };
        
        if (candlestickSeriesRef.current) {
          candlestickSeriesRef.current.update(aggregatedCandle);
        }
        if (volumeSeriesRef.current) {
          volumeSeriesRef.current.update({
            time: aggregatedCandle.time,
            value: aggregatedCandle.volume,
            color: aggregatedCandle.close >= aggregatedCandle.open 
              ? "rgba(34, 197, 94, 0.5)" 
              : "rgba(239, 68, 68, 0.5)",
          });
        }
      } else {
        if (candlestickSeriesRef.current) {
          candlestickSeriesRef.current.update(candle);
        }
        if (volumeSeriesRef.current) {
          volumeSeriesRef.current.update({
            time: candle.time,
            value: candle.volume,
            color: candle.close >= candle.open 
              ? "rgba(34, 197, 94, 0.5)" 
              : "rgba(239, 68, 68, 0.5)",
          });
        }
      }
    };

    ws.onclose = () => {
      setWsConnected(false);
    };

    ws.onerror = () => {
      setWsConnected(false);
    };

    wsRef.current = ws;

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [selectedPair, selectedTimeframe]);

  // Load data when pair or timeframe changes
  useEffect(() => {
    loadChartData();
  }, [loadChartData]);

  const formatVolume = (vol) => {
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
    return price.toLocaleString("fr-FR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  };

  const filteredPairs = searchQuery
    ? allPairs.filter(p => 
        p.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.name.toLowerCase().includes(searchQuery.toLowerCase())
      ).slice(0, 50)
    : TOP_PAIRS;

  const selectedPairInfo = allPairs.find(p => p.symbol === selectedPair) || 
    TOP_PAIRS.find(p => p.symbol === selectedPair) ||
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
                  <span className="text-muted-foreground">/USDT</span>
                </div>
                <ChevronDown className="w-4 h-4 opacity-50" />
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-[300px] p-0 glass border-white/10" align="start">
              <Command>
                <CommandInput 
                  placeholder="Rechercher une paire..." 
                  value={searchQuery}
                  onValueChange={setSearchQuery}
                />
                <CommandList>
                  <CommandEmpty>Aucune paire trouvée</CommandEmpty>
                  <CommandGroup heading="Top 10">
                    {TOP_PAIRS.map(pair => (
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
                        <span className="text-muted-foreground ml-1">/USDT</span>
                      </CommandItem>
                    ))}
                  </CommandGroup>
                  {searchQuery && filteredPairs.length > 0 && (
                    <CommandGroup heading="Résultats">
                      {filteredPairs
                        .filter(p => !TOP_PAIRS.find(tp => tp.symbol === p.symbol))
                        .map(pair => (
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
                            <span className="mr-2">{pair.icon}</span>
                            <span className="font-medium">{pair.name}</span>
                            <span className="text-muted-foreground ml-1">/USDT</span>
                          </CommandItem>
                        ))}
                    </CommandGroup>
                  )}
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
                {priceChange >= 0 ? "+" : ""}{priceChange.toFixed(2)}%
              </Badge>
            </div>
          </div>
        </div>

        {/* Timeframe Selector */}
        <div className="flex items-center gap-2">
          {wsConnected ? (
            <Badge variant="outline" className="text-emerald-500 border-emerald-500/30">
              <Wifi className="w-3 h-3 mr-1" />
              Live
            </Badge>
          ) : (
            <Badge variant="outline" className="text-yellow-500 border-yellow-500/30">
              <WifiOff className="w-3 h-3 mr-1" />
              Connecté
            </Badge>
          )}
          
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
              {priceChange >= 0 ? "+" : ""}{priceChange.toFixed(2)}%
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
        Données en temps réel via Binance • {selectedTimeframe === "15s" ? "Bougies agrégées toutes les 15 secondes" : `Intervalle: ${selectedTimeframe}`}
      </div>
    </div>
  );
}
