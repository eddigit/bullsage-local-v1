import { useState, useEffect } from "react";
import axios from "axios";
import { toast } from "sonner";
import {
  Newspaper,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  ExternalLink,
  Clock,
  BarChart3,
  Calendar,
  Globe,
  Loader2,
  Search,
  Filter,
  ArrowUpRight,
  ArrowDownRight
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Input } from "../components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import { API } from "../App";

const INDEX_COLORS = {
  "QQQ": "from-blue-500/20 to-blue-600/20",
  "SPY": "from-green-500/20 to-green-600/20",
  "DIA": "from-yellow-500/20 to-yellow-600/20",
  "IWM": "from-purple-500/20 to-purple-600/20",
  "VIX": "from-red-500/20 to-red-600/20"
};

export default function MarketNewsPage() {
  const [news, setNews] = useState([]);
  const [indices, setIndices] = useState([]);
  const [economicEvents, setEconomicEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newsLoading, setNewsLoading] = useState(false);
  const [category, setCategory] = useState("general");
  const [searchQuery, setSearchQuery] = useState("");
  const [activeTab, setActiveTab] = useState("news");

  useEffect(() => {
    loadAllData();
  }, []);

  const loadAllData = async () => {
    setLoading(true);
    await Promise.all([
      loadNews(),
      loadIndices(),
      loadEconomicCalendar()
    ]);
    setLoading(false);
  };

  const loadNews = async (cat = category) => {
    setNewsLoading(true);
    try {
      const response = await axios.get(`${API}/market/news?category=${cat}&limit=20`);
      setNews(response.data.news || []);
    } catch (error) {
      console.error("News error:", error);
    } finally {
      setNewsLoading(false);
    }
  };

  const loadIndices = async () => {
    try {
      const response = await axios.get(`${API}/market/indices`);
      setIndices(response.data.indices || []);
    } catch (error) {
      console.error("Indices error:", error);
    }
  };

  const loadEconomicCalendar = async () => {
    try {
      const response = await axios.get(`${API}/market/economic-calendar`);
      setEconomicEvents(response.data.events || []);
    } catch (error) {
      console.error("Calendar error:", error);
    }
  };

  const handleCategoryChange = (newCategory) => {
    setCategory(newCategory);
    loadNews(newCategory);
  };

  const formatPrice = (price) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(price);
  };

  const formatVolume = (vol) => {
    if (vol >= 1e9) return `${(vol / 1e9).toFixed(2)}B`;
    if (vol >= 1e6) return `${(vol / 1e6).toFixed(2)}M`;
    if (vol >= 1e3) return `${(vol / 1e3).toFixed(2)}K`;
    return vol.toString();
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "";
    const date = new Date(dateStr);
    return date.toLocaleDateString("fr-FR", {
      day: "2-digit",
      month: "short",
      hour: "2-digit",
      minute: "2-digit"
    });
  };

  const filteredNews = searchQuery
    ? news.filter(n => 
        n.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        n.summary.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : news;

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold font-manrope flex items-center gap-3">
            <Newspaper className="w-8 h-8 text-primary" />
            Actualités & Indices
          </h1>
          <p className="text-muted-foreground mt-1">
            News financières et indices boursiers en temps réel
          </p>
        </div>
        
        <Button variant="outline" onClick={loadAllData}>
          <RefreshCw className="w-4 h-4 mr-2" />
          Actualiser
        </Button>
      </div>

      {/* Market Indices */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {indices.map(idx => (
          <Card 
            key={idx.symbol} 
            className={`glass border-white/5 bg-gradient-to-br ${INDEX_COLORS[idx.symbol] || "from-gray-500/20 to-gray-600/20"}`}
          >
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-lg">{idx.icon}</span>
                <Badge 
                  variant="outline" 
                  className={idx.change_percent >= 0 ? "text-emerald-500 border-emerald-500/30" : "text-red-500 border-red-500/30"}
                >
                  {idx.change_percent >= 0 ? <ArrowUpRight className="w-3 h-3 mr-1" /> : <ArrowDownRight className="w-3 h-3 mr-1" />}
                  {idx.change_percent >= 0 ? "+" : ""}{idx.change_percent.toFixed(2)}%
                </Badge>
              </div>
              <p className="text-xs text-muted-foreground">{idx.name}</p>
              <p className="text-xl font-bold">{formatPrice(idx.price)}</p>
              <p className={`text-sm ${idx.change >= 0 ? "text-emerald-500" : "text-red-500"}`}>
                {idx.change >= 0 ? "+" : ""}{idx.change.toFixed(2)}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-black/20">
          <TabsTrigger value="news" className="data-[state=active]:bg-primary data-[state=active]:text-black">
            <Newspaper className="w-4 h-4 mr-2" />
            News
          </TabsTrigger>
          <TabsTrigger value="calendar" className="data-[state=active]:bg-primary data-[state=active]:text-black">
            <Calendar className="w-4 h-4 mr-2" />
            Calendrier Éco
          </TabsTrigger>
        </TabsList>

        {/* News Tab */}
        <TabsContent value="news" className="space-y-4">
          {/* Filters */}
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="Rechercher dans les news..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 bg-black/20 border-white/10"
              />
            </div>
            <Select value={category} onValueChange={handleCategoryChange}>
              <SelectTrigger className="w-[180px] bg-black/20 border-white/10">
                <SelectValue placeholder="Catégorie" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="general">Général</SelectItem>
                <SelectItem value="forex">Forex</SelectItem>
                <SelectItem value="crypto">Crypto</SelectItem>
                <SelectItem value="merger">M&A</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* News Grid */}
          {newsLoading ? (
            <div className="flex justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
          ) : filteredNews.length === 0 ? (
            <Card className="glass border-white/5">
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Newspaper className="w-12 h-12 text-muted-foreground mb-4" />
                <p className="text-muted-foreground">Aucune news disponible</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredNews.map((item, index) => (
                <Card 
                  key={item.id || index} 
                  className="glass border-white/5 hover:border-white/10 transition-colors cursor-pointer"
                  onClick={() => item.url && window.open(item.url, '_blank')}
                >
                  <CardContent className="p-4">
                    <div className="flex gap-4">
                      {item.image && (
                        <img 
                          src={item.image} 
                          alt=""
                          className="w-24 h-24 object-cover rounded-lg flex-shrink-0"
                          onError={(e) => e.target.style.display = 'none'}
                        />
                      )}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-2 mb-2">
                          <h3 className="font-semibold line-clamp-2 text-sm">{item.title}</h3>
                          <ExternalLink className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                        </div>
                        <p className="text-xs text-muted-foreground line-clamp-2 mb-2">
                          {item.summary}
                        </p>
                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                          <Globe className="w-3 h-3" />
                          <span>{item.source}</span>
                          {item.published_at && (
                            <>
                              <span>•</span>
                              <Clock className="w-3 h-3" />
                              <span>{formatDate(item.published_at)}</span>
                            </>
                          )}
                        </div>
                        {item.related && (
                          <div className="flex gap-1 mt-2 flex-wrap">
                            {item.related.split(",").slice(0, 3).map((symbol, i) => (
                              symbol.trim() && (
                                <Badge key={i} variant="outline" className="text-xs">
                                  {symbol.trim()}
                                </Badge>
                              )
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Economic Calendar Tab */}
        <TabsContent value="calendar" className="space-y-4">
          <Card className="glass border-white/5">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Calendar className="w-5 h-5 text-primary" />
                Événements Économiques
              </CardTitle>
              <CardDescription>Calendrier des annonces importantes</CardDescription>
            </CardHeader>
            <CardContent>
              {economicEvents.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Calendar className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>Aucun événement à venir</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {economicEvents.map((event, index) => (
                    <div 
                      key={index}
                      className="flex items-center justify-between p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-xs font-bold">
                          {event.country?.slice(0, 2) || "🌍"}
                        </div>
                        <div>
                          <p className="font-medium text-sm">{event.event}</p>
                          <p className="text-xs text-muted-foreground">{event.time}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <Badge 
                          variant="outline"
                          className={
                            event.impact === "high" ? "text-red-500 border-red-500/30" :
                            event.impact === "medium" ? "text-yellow-500 border-yellow-500/30" :
                            "text-green-500 border-green-500/30"
                          }
                        >
                          {event.impact || "low"}
                        </Badge>
                        <div className="text-xs text-muted-foreground mt-1">
                          {event.estimate && <span>Est: {event.estimate}</span>}
                          {event.previous && <span> | Prev: {event.previous}</span>}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
