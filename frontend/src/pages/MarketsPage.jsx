import { useState, useEffect } from "react";
import { API, useAuth } from "../App";
import axios from "axios";
import { toast } from "sonner";
import {
  Search,
  Star,
  StarOff,
  TrendingUp,
  TrendingDown,
  ArrowUpRight,
  ArrowDownRight,
  RefreshCw,
  Filter
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import { ScrollArea } from "../components/ui/scroll-area";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";

const formatPrice = (price) => {
  if (!price) return "$0.00";
  if (price >= 1000) return `$${price.toLocaleString("en-US", { maximumFractionDigits: 2 })}`;
  if (price >= 1) return `$${price.toFixed(2)}`;
  return `$${price.toFixed(6)}`;
};

const formatPercent = (value) => {
  if (!value && value !== 0) return "0.00%";
  const formatted = Math.abs(value).toFixed(2);
  return value >= 0 ? `+${formatted}%` : `-${formatted}%`;
};

const formatMarketCap = (value) => {
  if (!value) return "$0";
  if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
  if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
  if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
  return `$${value.toLocaleString()}`;
};

export default function MarketsPage() {
  const { user, updateUser } = useAuth();
  const [markets, setMarkets] = useState([]);
  const [filteredMarkets, setFilteredMarkets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState("market_cap_desc");
  const [showWatchlistOnly, setShowWatchlistOnly] = useState(false);

  const fetchMarkets = async () => {
    try {
      const response = await axios.get(`${API}/market/crypto`);
      setMarkets(response.data || []);
    } catch (error) {
      console.error("Error fetching markets:", error);
      toast.error("Erreur lors du chargement des marchés");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchMarkets();
    // Removed auto-refresh to avoid API rate limits
    // Users can manually refresh with the button
  }, []);

  useEffect(() => {
    let filtered = [...markets];

    // Filter by search query
    if (searchQuery) {
      filtered = filtered.filter(
        (coin) =>
          coin.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          coin.symbol.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Filter by watchlist
    if (showWatchlistOnly) {
      filtered = filtered.filter((coin) => user?.watchlist?.includes(coin.id));
    }

    // Sort
    switch (sortBy) {
      case "price_asc":
        filtered.sort((a, b) => a.current_price - b.current_price);
        break;
      case "price_desc":
        filtered.sort((a, b) => b.current_price - a.current_price);
        break;
      case "change_asc":
        filtered.sort((a, b) => a.price_change_percentage_24h - b.price_change_percentage_24h);
        break;
      case "change_desc":
        filtered.sort((a, b) => b.price_change_percentage_24h - a.price_change_percentage_24h);
        break;
      case "market_cap_desc":
      default:
        filtered.sort((a, b) => b.market_cap - a.market_cap);
        break;
    }

    setFilteredMarkets(filtered);
  }, [markets, searchQuery, sortBy, showWatchlistOnly, user?.watchlist]);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchMarkets();
    toast.success("Données actualisées");
  };

  const toggleWatchlist = async (coinId) => {
    const isInWatchlist = user?.watchlist?.includes(coinId);
    
    try {
      if (isInWatchlist) {
        await axios.delete(`${API}/watchlist/${coinId}`);
        updateUser({ watchlist: user.watchlist.filter(id => id !== coinId) });
        toast.success("Retiré de la watchlist");
      } else {
        const response = await axios.post(`${API}/watchlist/${coinId}`);
        updateUser({ watchlist: response.data.watchlist });
        toast.success("Ajouté à la watchlist");
      }
    } catch (error) {
      toast.error("Erreur lors de la mise à jour de la watchlist");
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div className="h-8 w-48 bg-white/5 rounded animate-pulse" />
          <div className="h-10 w-32 bg-white/5 rounded animate-pulse" />
        </div>
        <div className="h-[600px] bg-white/5 rounded-xl animate-pulse" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="markets-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold font-manrope">Marchés</h1>
          <p className="text-muted-foreground">
            Suivez les cryptomonnaies en temps réel
          </p>
        </div>
        <Button
          variant="outline"
          onClick={handleRefresh}
          disabled={refreshing}
          className="border-white/10 hover:bg-white/5"
          data-testid="refresh-markets-btn"
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? "animate-spin" : ""}`} />
          Actualiser
        </Button>
      </div>

      {/* Filters */}
      <Card className="glass border-white/5">
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="Rechercher une crypto..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 bg-black/20 border-white/10"
                data-testid="search-input"
              />
            </div>
            <Select value={sortBy} onValueChange={setSortBy}>
              <SelectTrigger className="w-full md:w-48 bg-black/20 border-white/10">
                <SelectValue placeholder="Trier par" />
              </SelectTrigger>
              <SelectContent className="glass border-white/10">
                <SelectItem value="market_cap_desc">Cap. de marché</SelectItem>
                <SelectItem value="price_desc">Prix (décroissant)</SelectItem>
                <SelectItem value="price_asc">Prix (croissant)</SelectItem>
                <SelectItem value="change_desc">Variation (haut)</SelectItem>
                <SelectItem value="change_asc">Variation (bas)</SelectItem>
              </SelectContent>
            </Select>
            <Button
              variant={showWatchlistOnly ? "default" : "outline"}
              onClick={() => setShowWatchlistOnly(!showWatchlistOnly)}
              className={showWatchlistOnly ? "bg-primary text-black" : "border-white/10"}
              data-testid="watchlist-filter-btn"
            >
              <Star className="w-4 h-4 mr-2" />
              Watchlist
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Markets Table */}
      <Card className="glass border-white/5">
        <CardHeader className="pb-0">
          <CardTitle className="text-lg flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-primary" />
            Cryptomonnaies
          </CardTitle>
          <CardDescription>
            {filteredMarkets.length} résultats
          </CardDescription>
        </CardHeader>
        <CardContent className="pt-4">
          <ScrollArea className="h-[600px]">
            <Table>
              <TableHeader>
                <TableRow className="border-white/5 hover:bg-transparent">
                  <TableHead className="w-12">#</TableHead>
                  <TableHead>Nom</TableHead>
                  <TableHead className="text-right">Prix</TableHead>
                  <TableHead className="text-right">24h %</TableHead>
                  <TableHead className="text-right hidden md:table-cell">7j %</TableHead>
                  <TableHead className="text-right hidden lg:table-cell">Cap. de marché</TableHead>
                  <TableHead className="text-right hidden lg:table-cell">Volume 24h</TableHead>
                  <TableHead className="w-12"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredMarkets.map((coin, index) => {
                  const isInWatchlist = user?.watchlist?.includes(coin.id);
                  const change24h = coin.price_change_percentage_24h || 0;
                  const change7d = coin.price_change_percentage_7d_in_currency || 0;

                  return (
                    <TableRow
                      key={coin.id}
                      className="border-white/5 hover:bg-white/5 cursor-pointer"
                      data-testid={`market-row-${coin.id}`}
                    >
                      <TableCell className="font-mono text-muted-foreground">
                        {coin.market_cap_rank || index + 1}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <img
                            src={coin.image}
                            alt={coin.name}
                            className="w-8 h-8 rounded-full"
                          />
                          <div>
                            <p className="font-medium">{coin.name}</p>
                            <p className="text-xs text-muted-foreground uppercase">
                              {coin.symbol}
                            </p>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell className="text-right font-mono font-medium">
                        {formatPrice(coin.current_price)}
                      </TableCell>
                      <TableCell className="text-right">
                        <div
                          className={`flex items-center justify-end gap-1 font-mono ${
                            change24h >= 0 ? "text-emerald-500" : "text-rose-500"
                          }`}
                        >
                          {change24h >= 0 ? (
                            <ArrowUpRight className="w-4 h-4" />
                          ) : (
                            <ArrowDownRight className="w-4 h-4" />
                          )}
                          {formatPercent(change24h)}
                        </div>
                      </TableCell>
                      <TableCell className="text-right hidden md:table-cell">
                        <span
                          className={`font-mono ${
                            change7d >= 0 ? "text-emerald-500" : "text-rose-500"
                          }`}
                        >
                          {formatPercent(change7d)}
                        </span>
                      </TableCell>
                      <TableCell className="text-right hidden lg:table-cell font-mono text-muted-foreground">
                        {formatMarketCap(coin.market_cap)}
                      </TableCell>
                      <TableCell className="text-right hidden lg:table-cell font-mono text-muted-foreground">
                        {formatMarketCap(coin.total_volume)}
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleWatchlist(coin.id);
                          }}
                          className="hover:bg-white/10"
                          data-testid={`watchlist-btn-${coin.id}`}
                        >
                          {isInWatchlist ? (
                            <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />
                          ) : (
                            <StarOff className="w-4 h-4 text-muted-foreground" />
                          )}
                        </Button>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}
