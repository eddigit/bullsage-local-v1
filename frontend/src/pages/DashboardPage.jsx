import { useState, useEffect } from "react";
import { useAuth, API } from "../App";
import { Link } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import {
  TrendingUp,
  TrendingDown,
  Wallet,
  MessageCircle,
  ArrowUpRight,
  ArrowDownRight,
  Zap,
  Eye,
  RefreshCw,
  Sparkles,
  Loader2
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { ScrollArea } from "../components/ui/scroll-area";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart
} from "recharts";

const formatPrice = (price) => {
  if (price >= 1000) return `$${price.toLocaleString("en-US", { maximumFractionDigits: 2 })}`;
  if (price >= 1) return `$${price.toFixed(2)}`;
  return `$${price.toFixed(6)}`;
};

const formatPercent = (value) => {
  const formatted = Math.abs(value).toFixed(2);
  return value >= 0 ? `+${formatted}%` : `-${formatted}%`;
};

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="glass rounded-lg px-3 py-2 text-sm">
        <p className="text-muted-foreground">{label}</p>
        <p className="font-mono font-medium text-primary">
          ${payload[0].value?.toLocaleString()}
        </p>
      </div>
    );
  }
  return null;
};

export default function DashboardPage() {
  const { user } = useAuth();
  const [markets, setMarkets] = useState([]);
  const [trending, setTrending] = useState([]);
  const [portfolio, setPortfolio] = useState(null);
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [chartLoading, setChartLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [marketsRes, trendingRes, portfolioRes] = await Promise.all([
        axios.get(`${API}/market/crypto`),
        axios.get(`${API}/market/trending`),
        axios.get(`${API}/paper-trading/portfolio`)
      ]);
      setMarkets(marketsRes.data || []);
      setTrending(trendingRes.data?.coins || []);
      setPortfolio(portfolioRes.data);
    } catch (error) {
      console.error("Error fetching data:", error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // Fetch real chart data from CoinGecko
  const fetchChartData = async () => {
    setChartLoading(true);
    try {
      const response = await axios.get(`${API}/market/crypto/bitcoin/chart?days=7`);
      if (response.data && response.data.prices) {
        const formattedData = response.data.prices.map((item, index) => {
          const date = new Date(item[0]);
          return {
            day: date.toLocaleDateString('fr-FR', { weekday: 'short', day: 'numeric' }),
            price: item[1],
            timestamp: item[0]
          };
        });
        // Sample every few points to avoid too many data points
        const sampledData = formattedData.filter((_, i) => i % Math.ceil(formattedData.length / 20) === 0);
        setChartData(sampledData);
      }
    } catch (error) {
      console.error("Error fetching chart data:", error);
      setChartData([]);
    } finally {
      setChartLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    fetchChartData();
    const interval = setInterval(fetchData, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchData();
    toast.success("Données actualisées");
  };

  // Filter watchlist coins
  const watchlistCoins = markets.filter(coin => 
    user?.watchlist?.includes(coin.id)
  );

  // Calculate portfolio value
  const calculatePortfolioValue = () => {
    if (!portfolio || !markets.length) return portfolio?.balance || 10000;
    
    let totalValue = portfolio.balance;
    Object.entries(portfolio.portfolio || {}).forEach(([symbol, holding]) => {
      const coin = markets.find(c => c.id === symbol);
      if (coin) {
        totalValue += holding.amount * coin.current_price;
      }
    });
    return totalValue;
  };

  const portfolioValue = calculatePortfolioValue();
  const portfolioChange = ((portfolioValue - 10000) / 10000) * 100;

  // Generate mock chart data
  const chartData = markets.slice(0, 1).map(coin => {
    // Create 7 day mock data
    return Array.from({ length: 7 }, (_, i) => ({
      day: `J-${6-i}`,
      price: coin.current_price * (0.95 + Math.random() * 0.1)
    }));
  })[0] || [];

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-8 w-48 bg-white/5 rounded" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-32 bg-white/5 rounded-xl" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="h-80 bg-white/5 rounded-xl" />
          <div className="h-80 bg-white/5 rounded-xl" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="dashboard">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold font-manrope">
            Bonjour, {user?.name?.split(" ")[0]} 👋
          </h1>
          <p className="text-muted-foreground">
            Voici votre aperçu des marchés aujourd'hui
          </p>
        </div>
        <Button
          variant="outline"
          onClick={handleRefresh}
          disabled={refreshing}
          className="border-white/10 hover:bg-white/5"
          data-testid="refresh-btn"
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? "animate-spin" : ""}`} />
          Actualiser
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Portfolio Value */}
        <Card className="glass border-white/5 card-hover">
          <CardContent className="pt-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Portfolio Virtuel</p>
                <p className="text-2xl font-bold font-mono mt-1" data-testid="portfolio-value">
                  {formatPrice(portfolioValue)}
                </p>
                <div className={`flex items-center gap-1 mt-1 ${portfolioChange >= 0 ? "text-emerald-500" : "text-rose-500"}`}>
                  {portfolioChange >= 0 ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
                  <span className="text-sm font-mono">{formatPercent(portfolioChange)}</span>
                </div>
              </div>
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                <Wallet className="w-5 h-5 text-primary" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Market Status */}
        <Card className="glass border-white/5 card-hover">
          <CardContent className="pt-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Marché Global</p>
                <p className="text-2xl font-bold font-mono mt-1">
                  {markets[0]?.current_price ? formatPrice(markets[0].current_price) : "$-"}
                </p>
                <p className="text-sm text-muted-foreground mt-1">
                  BTC Dominance
                </p>
              </div>
              <div className="w-10 h-10 rounded-lg bg-orange-500/10 flex items-center justify-center">
                <TrendingUp className="w-5 h-5 text-orange-500" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* AI Assistant Quick Access */}
        <Link to="/assistant">
          <Card className="glass border-violet-500/20 card-hover cursor-pointer group h-full">
            <CardContent className="pt-6 h-full">
              <div className="flex items-start justify-between h-full">
                <div>
                  <p className="text-sm text-violet-400">Assistant IA</p>
                  <p className="text-lg font-bold mt-1">BULL SAGE</p>
                  <p className="text-sm text-muted-foreground mt-1 group-hover:text-violet-400 transition-colors">
                    Demander une analyse →
                  </p>
                </div>
                <div className="w-10 h-10 rounded-lg bg-violet-500/10 flex items-center justify-center group-hover:bg-violet-500/20 transition-colors">
                  <Sparkles className="w-5 h-5 text-violet-400" />
                </div>
              </div>
            </CardContent>
          </Card>
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Watchlist */}
        <Card className="glass border-white/5">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Eye className="w-5 h-5 text-primary" />
                  Ma Watchlist
                </CardTitle>
                <CardDescription>Vos actifs surveillés</CardDescription>
              </div>
              <Link to="/markets">
                <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-foreground">
                  Voir tout
                </Button>
              </Link>
            </div>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[280px]">
              {watchlistCoins.length > 0 ? (
                <div className="space-y-2">
                  {watchlistCoins.map((coin) => (
                    <div
                      key={coin.id}
                      className="flex items-center justify-between p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
                      data-testid={`watchlist-${coin.id}`}
                    >
                      <div className="flex items-center gap-3">
                        <img src={coin.image} alt={coin.name} className="w-8 h-8 rounded-full" />
                        <div>
                          <p className="font-medium">{coin.name}</p>
                          <p className="text-xs text-muted-foreground uppercase">{coin.symbol}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-mono font-medium">{formatPrice(coin.current_price)}</p>
                        <p className={`text-sm font-mono ${coin.price_change_percentage_24h >= 0 ? "text-emerald-500" : "text-rose-500"}`}>
                          {formatPercent(coin.price_change_percentage_24h)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center h-full text-center py-8">
                  <Eye className="w-12 h-12 text-muted-foreground/30 mb-3" />
                  <p className="text-muted-foreground">Aucun actif dans votre watchlist</p>
                  <Link to="/markets">
                    <Button variant="link" className="text-primary mt-2">
                      Ajouter des actifs
                    </Button>
                  </Link>
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Trending */}
        <Card className="glass border-white/5">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Zap className="w-5 h-5 text-yellow-500" />
                  Tendances
                </CardTitle>
                <CardDescription>Les cryptos les plus recherchées</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[280px]">
              <div className="space-y-2">
                {trending.slice(0, 7).map((item, index) => (
                  <div
                    key={item.item?.id || index}
                    className="flex items-center justify-between p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
                    data-testid={`trending-${index}`}
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-6 h-6 rounded-full bg-white/10 flex items-center justify-center text-xs font-bold">
                        {index + 1}
                      </div>
                      {item.item?.thumb && (
                        <img src={item.item.thumb} alt={item.item.name} className="w-8 h-8 rounded-full" />
                      )}
                      <div>
                        <p className="font-medium">{item.item?.name || "Unknown"}</p>
                        <p className="text-xs text-muted-foreground uppercase">{item.item?.symbol}</p>
                      </div>
                    </div>
                    <Badge variant="secondary" className="bg-white/5">
                      #{item.item?.market_cap_rank || "-"}
                    </Badge>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>

      {/* Market Overview Chart */}
      <Card className="glass border-white/5">
        <CardHeader>
          <CardTitle className="text-lg">Aperçu du Marché (BTC)</CardTitle>
          <CardDescription>Performance sur 7 jours</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[200px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10B981" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#10B981" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis 
                  dataKey="day" 
                  axisLine={false} 
                  tickLine={false}
                  tick={{ fill: '#71717a', fontSize: 12 }}
                />
                <YAxis 
                  hide 
                  domain={['dataMin', 'dataMax']}
                />
                <Tooltip content={<CustomTooltip />} />
                <Area
                  type="monotone"
                  dataKey="price"
                  stroke="#10B981"
                  strokeWidth={2}
                  fill="url(#colorPrice)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Link to="/paper-trading">
          <Card className="glass border-white/5 card-hover cursor-pointer">
            <CardContent className="pt-6 text-center">
              <Wallet className="w-8 h-8 mx-auto text-primary mb-2" />
              <p className="font-medium">Paper Trading</p>
            </CardContent>
          </Card>
        </Link>
        <Link to="/strategies">
          <Card className="glass border-white/5 card-hover cursor-pointer">
            <CardContent className="pt-6 text-center">
              <TrendingUp className="w-8 h-8 mx-auto text-blue-500 mb-2" />
              <p className="font-medium">Stratégies</p>
            </CardContent>
          </Card>
        </Link>
        <Link to="/alerts">
          <Card className="glass border-white/5 card-hover cursor-pointer">
            <CardContent className="pt-6 text-center">
              <Zap className="w-8 h-8 mx-auto text-yellow-500 mb-2" />
              <p className="font-medium">Alertes</p>
            </CardContent>
          </Card>
        </Link>
        <Link to="/assistant">
          <Card className="glass border-violet-500/20 card-hover cursor-pointer">
            <CardContent className="pt-6 text-center">
              <MessageCircle className="w-8 h-8 mx-auto text-violet-400 mb-2" />
              <p className="font-medium">Assistant IA</p>
            </CardContent>
          </Card>
        </Link>
      </div>
    </div>
  );
}
