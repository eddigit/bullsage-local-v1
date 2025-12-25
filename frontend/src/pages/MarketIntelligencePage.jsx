import { useState, useEffect } from "react";
import { API } from "../App";
import axios from "axios";
import { toast } from "sonner";
import {
  Brain,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Lightbulb,
  Calendar,
  Newspaper,
  BarChart3,
  RefreshCw,
  Loader2,
  Globe,
  DollarSign,
  Activity,
  ChevronUp,
  ChevronDown,
  Minus,
  Gauge
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { ScrollArea } from "../components/ui/scroll-area";
import { Progress } from "../components/ui/progress";

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

const getSentimentColor = (sentiment) => {
  switch (sentiment) {
    case "extreme_fear": return "text-rose-500";
    case "fear": return "text-orange-500";
    case "neutral": return "text-yellow-500";
    case "greed": return "text-lime-500";
    case "extreme_greed": return "text-emerald-500";
    default: return "text-muted-foreground";
  }
};

const getSentimentIcon = (value) => {
  const v = parseInt(value);
  if (v <= 20) return { icon: "TrendingDown", color: "text-rose-500", label: "Extreme Fear" };
  if (v <= 40) return { icon: "ChevronDown", color: "text-orange-500", label: "Fear" };
  if (v <= 60) return { icon: "Minus", color: "text-yellow-500", label: "Neutral" };
  if (v <= 80) return { icon: "ChevronUp", color: "text-lime-500", label: "Greed" };
  return { icon: "TrendingUp", color: "text-emerald-500", label: "Extreme Greed" };
};

export default function MarketIntelligencePage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = async () => {
    try {
      const response = await axios.get(`${API}/market/intelligence`);
      setData(response.data || {});
    } catch (error) {
      console.error("Error fetching market intelligence:", error);
      toast.error("Erreur lors du chargement des données");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchData();
    toast.success("Données actualisées");
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-12 h-12 animate-spin text-primary" />
          <p className="text-muted-foreground">Chargement de l&apos;intelligence marché...</p>
        </div>
      </div>
    );
  }

  const fgValue = parseInt(data?.fear_greed?.current?.value || 50);
  const analysis = data?.analysis || {};

  return (
    <div className="space-y-6" data-testid="market-intelligence-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center">
            <Brain className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl md:text-3xl font-bold font-manrope">Intelligence Marché</h1>
            <p className="text-sm text-muted-foreground">
              Vue globale des données en temps réel • {new Date(data?.timestamp).toLocaleString("fr-FR")}
            </p>
          </div>
        </div>
        <Button
          variant="outline"
          onClick={handleRefresh}
          disabled={refreshing}
          className="border-white/10 hover:bg-white/5"
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? "animate-spin" : ""}`} />
          Actualiser
        </Button>
      </div>

      {/* Analysis Summary */}
      <Card className={`glass border-2 ${
        analysis.risk_level === "high" ? "border-rose-500/30" :
        analysis.risk_level === "low" ? "border-emerald-500/30" : "border-yellow-500/30"
      }`}>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Sentiment */}
            <div className="text-center">
              <p className="text-sm text-muted-foreground mb-2">Sentiment Global</p>
              <p className={`text-2xl font-bold uppercase ${getSentimentColor(analysis.overall_sentiment)}`}>
                {analysis.overall_sentiment?.replace("_", " ") || "NEUTRAL"}
              </p>
            </div>
            
            {/* Risk Level */}
            <div className="text-center">
              <p className="text-sm text-muted-foreground mb-2">Niveau de Risque</p>
              <Badge className={`text-lg px-4 py-1 ${
                analysis.risk_level === "high" ? "bg-rose-500/20 text-rose-500" :
                analysis.risk_level === "low" ? "bg-emerald-500/20 text-emerald-500" : 
                "bg-yellow-500/20 text-yellow-500"
              }`}>
                {analysis.risk_level?.toUpperCase() || "MEDIUM"}
              </Badge>
            </div>
            
            {/* Fear & Greed */}
            <div className="text-center">
              <p className="text-sm text-muted-foreground mb-2">Fear & Greed Index</p>
              <div className="flex items-center justify-center gap-3">
                <div className={`p-2 rounded-full bg-white/5 ${getSentimentIcon(fgValue).color}`}>
                  {fgValue <= 20 ? <TrendingDown className="w-6 h-6" /> :
                   fgValue <= 40 ? <ChevronDown className="w-6 h-6" /> :
                   fgValue <= 60 ? <Minus className="w-6 h-6" /> :
                   fgValue <= 80 ? <ChevronUp className="w-6 h-6" /> :
                   <TrendingUp className="w-6 h-6" />}
                </div>
                <span className="text-3xl font-bold font-mono">{fgValue}</span>
              </div>
              <Progress 
                value={fgValue} 
                className="mt-2 h-2"
                style={{
                  background: 'linear-gradient(to right, #F43F5E, #EAB308, #10B981)'
                }}
              />
            </div>
          </div>
          
          {/* Key Factors */}
          {analysis.key_factors?.length > 0 && (
            <div className="mt-6 pt-6 border-t border-white/10">
              <p className="text-sm font-medium mb-3 flex items-center gap-2">
                <Activity className="w-4 h-4 text-blue-500" />
                Facteurs Clés
              </p>
              <div className="space-y-2">
                {analysis.key_factors.map((factor, i) => (
                  <p key={i} className="text-sm text-muted-foreground">• {factor}</p>
                ))}
              </div>
            </div>
          )}
          
          {/* Warnings & Opportunities */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
            {analysis.warnings?.length > 0 && (
              <div className="p-4 rounded-lg bg-rose-500/10 border border-rose-500/20">
                <p className="text-sm font-medium mb-2 flex items-center gap-2 text-rose-500">
                  <AlertTriangle className="w-4 h-4" />
                  Alertes
                </p>
                {analysis.warnings.map((w, i) => (
                  <p key={i} className="text-sm text-rose-400">• {w}</p>
                ))}
              </div>
            )}
            
            {analysis.opportunities?.length > 0 && (
              <div className="p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                <p className="text-sm font-medium mb-2 flex items-center gap-2 text-emerald-500">
                  <Lightbulb className="w-4 h-4" />
                  Opportunités
                </p>
                {analysis.opportunities.map((o, i) => (
                  <p key={i} className="text-sm text-emerald-400">• {o}</p>
                ))}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Crypto Prices */}
        <Card className="glass border-white/5">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-primary" />
              Prix Crypto
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {data?.crypto_prices?.map((coin) => (
                <div key={coin.id} className="flex items-center justify-between p-3 rounded-lg bg-white/5">
                  <div className="flex items-center gap-3">
                    <img src={coin.image} alt={coin.name} className="w-8 h-8 rounded-full" />
                    <div>
                      <p className="font-medium">{coin.name}</p>
                      <p className="text-xs text-muted-foreground uppercase">{coin.symbol}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-mono font-bold">{formatPrice(coin.current_price)}</p>
                    <div className="flex items-center gap-2 text-xs">
                      <span className={coin.price_change_percentage_24h >= 0 ? "text-emerald-500" : "text-rose-500"}>
                        {formatPercent(coin.price_change_percentage_24h)} 24h
                      </span>
                      <span className={coin.price_change_percentage_7d_in_currency >= 0 ? "text-emerald-500" : "text-rose-500"}>
                        {formatPercent(coin.price_change_percentage_7d_in_currency)} 7j
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Macro Data */}
        <Card className="glass border-white/5">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-violet-500" />
              Données Macro
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 gap-4">
              {/* VIX */}
              {data?.macro?.vix && (
                <div className="p-4 rounded-lg bg-white/5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Activity className="w-5 h-5 text-orange-500" />
                      <span>VIX (Volatilité)</span>
                    </div>
                    <span className={`font-mono font-bold ${
                      parseFloat(data.macro.vix.value) > 25 ? "text-rose-500" :
                      parseFloat(data.macro.vix.value) < 15 ? "text-emerald-500" : "text-yellow-500"
                    }`}>
                      {data.macro.vix.value}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    {parseFloat(data.macro.vix.value) > 25 ? "Haute volatilité - Prudence" :
                     parseFloat(data.macro.vix.value) < 15 ? "Faible volatilité - Marché calme" : "Volatilité normale"}
                  </p>
                </div>
              )}
              
              {/* Fed Rate */}
              {data?.macro?.fed_rate && (
                <div className="p-4 rounded-lg bg-white/5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <DollarSign className="w-5 h-5 text-blue-500" />
                      <span>Taux Fed</span>
                    </div>
                    <span className="font-mono font-bold">{data.macro.fed_rate.value}%</span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    Dernière mise à jour: {data.macro.fed_rate.date}
                  </p>
                </div>
              )}
              
              {/* Dollar Index */}
              {data?.macro?.dxy && (
                <div className="p-4 rounded-lg bg-white/5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Globe className="w-5 h-5 text-green-500" />
                      <span>Dollar Index (DXY)</span>
                    </div>
                    <span className="font-mono font-bold">{data.macro.dxy.value}</span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    Dollar fort = généralement négatif pour crypto
                  </p>
                </div>
              )}
              
              {/* Fear & Greed History */}
              {data?.fear_greed?.history?.length > 0 && (
                <div className="p-4 rounded-lg bg-white/5">
                  <p className="font-medium mb-3 flex items-center gap-2">
                    <Gauge className="w-5 h-5 text-violet-500" />
                    Fear & Greed - 7 derniers jours
                  </p>
                  <div className="flex items-center justify-between gap-1">
                    {data.fear_greed.history.slice().reverse().map((fg, i) => (
                      <div key={i} className="flex-1 text-center">
                        <div 
                          className={`h-12 rounded flex items-center justify-center font-mono text-sm font-bold ${
                            parseInt(fg.value) <= 25 ? "bg-rose-500/30 text-rose-400" :
                            parseInt(fg.value) <= 45 ? "bg-orange-500/30 text-orange-400" :
                            parseInt(fg.value) <= 55 ? "bg-yellow-500/30 text-yellow-400" :
                            parseInt(fg.value) <= 75 ? "bg-lime-500/30 text-lime-400" :
                            "bg-emerald-500/30 text-emerald-400"
                          }`}
                        >
                          {fg.value}
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">J-{6-i}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Economic Calendar */}
        <Card className="glass border-white/5">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Calendar className="w-5 h-5 text-yellow-500" />
              Calendrier Économique
            </CardTitle>
            <CardDescription>Événements importants à venir</CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[300px]">
              {data?.economic_calendar?.length > 0 ? (
                <div className="space-y-3">
                  {data.economic_calendar.map((event, i) => (
                    <div key={i} className="p-3 rounded-lg bg-white/5 border-l-2 border-yellow-500">
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <p className="font-medium text-sm">{event.event}</p>
                          <p className="text-xs text-muted-foreground">{event.date}</p>
                        </div>
                        <Badge className={
                          event.impact === "high" ? "bg-rose-500/20 text-rose-500" :
                          event.impact === "medium" ? "bg-yellow-500/20 text-yellow-500" :
                          "bg-blue-500/20 text-blue-500"
                        }>
                          {event.impact?.toUpperCase()}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-center text-muted-foreground py-8">
                  Aucun événement majeur à venir
                </p>
              )}
            </ScrollArea>
          </CardContent>
        </Card>

        {/* News */}
        <Card className="glass border-white/5">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Newspaper className="w-5 h-5 text-blue-500" />
              Dernières News
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[300px]">
              {data?.news?.length > 0 ? (
                <div className="space-y-3">
                  {data.news.map((article, i) => (
                    <a 
                      key={i} 
                      href={article.url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="block p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
                    >
                      <p className="font-medium text-sm line-clamp-2">{article.headline}</p>
                      <div className="flex items-center justify-between mt-2">
                        <span className="text-xs text-muted-foreground">{article.source}</span>
                        <span className="text-xs text-muted-foreground">
                          {new Date(article.datetime * 1000).toLocaleDateString("fr-FR")}
                        </span>
                      </div>
                    </a>
                  ))}
                </div>
              ) : (
                <p className="text-center text-muted-foreground py-8">
                  Aucune news disponible
                </p>
              )}
            </ScrollArea>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
