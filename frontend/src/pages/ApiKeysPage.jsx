import { useState, useEffect } from "react";
import { API, useAuth } from "../App";
import { Navigate } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import {
  Key,
  Eye,
  EyeOff,
  Copy,
  Check,
  RefreshCw,
  Shield,
  Database,
  TrendingUp,
  Newspaper,
  BarChart3,
  Brain
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Input } from "../components/ui/input";

const ICON_MAP = {
  "coingecko": Database,
  "alpha_vantage": TrendingUp,
  "finnhub": Newspaper,
  "fred": BarChart3,
  "marketaux": Newspaper,
  "emergent_llm": Brain
};

const COLOR_MAP = {
  "coingecko": "text-emerald-500",
  "alpha_vantage": "text-blue-500",
  "finnhub": "text-orange-500",
  "fred": "text-violet-500",
  "marketaux": "text-pink-500",
  "emergent_llm": "text-cyan-500"
};

export default function ApiKeysPage() {
  const { user } = useAuth();
  const [apiKeys, setApiKeys] = useState({});
  const [loading, setLoading] = useState(true);
  const [visibleKeys, setVisibleKeys] = useState({});
  const [copiedKey, setCopiedKey] = useState(null);

  const fetchApiKeys = async () => {
    try {
      const response = await axios.get(`${API}/admin/api-keys`);
      setApiKeys(response.data);
    } catch (error) {
      console.error("Error fetching API keys:", error);
      toast.error("Erreur lors du chargement des clés API");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user?.is_admin) {
      fetchApiKeys();
    }
  }, [user?.is_admin]);

  // Redirect if not admin - AFTER all hooks
  if (!user?.is_admin) {
    return <Navigate to="/" replace />;
  }

  const toggleVisibility = (key) => {
    setVisibleKeys(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const copyToClipboard = async (key, value) => {
    try {
      await navigator.clipboard.writeText(value);
      setCopiedKey(key);
      toast.success("Clé copiée dans le presse-papier");
      setTimeout(() => setCopiedKey(null), 2000);
    } catch (error) {
      toast.error("Erreur lors de la copie");
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-48 bg-white/5 rounded animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2, 3, 4, 5, 6].map(i => (
            <div key={i} className="h-32 bg-white/5 rounded-xl animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="api-keys-page">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="w-12 h-12 rounded-xl bg-amber-500/20 flex items-center justify-center">
          <Key className="w-6 h-6 text-amber-500" />
        </div>
        <div>
          <h1 className="text-2xl md:text-3xl font-bold font-manrope">Clés API</h1>
          <p className="text-muted-foreground">Gérez vos clés d&apos;accès aux services externes</p>
        </div>
      </div>

      {/* Security Notice */}
      <Card className="glass border-amber-500/20">
        <CardContent className="pt-6">
          <div className="flex items-start gap-3">
            <Shield className="w-5 h-5 text-amber-500 mt-0.5" />
            <div>
              <p className="font-medium text-amber-500">Zone Sécurisée</p>
              <p className="text-sm text-muted-foreground">
                Ces clés API sont sensibles. Ne les partagez jamais publiquement. 
                Elles sont stockées de manière sécurisée côté serveur.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* API Keys Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {Object.entries(apiKeys).map(([key, data]) => {
          const IconComponent = ICON_MAP[key] || Key;
          const colorClass = COLOR_MAP[key] || "text-gray-500";
          const isVisible = visibleKeys[key];
          const isCopied = copiedKey === key;

          return (
            <Card key={key} className="glass border-white/5" data-testid={`api-key-${key}`}>
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-lg bg-white/5 flex items-center justify-center`}>
                      <IconComponent className={`w-5 h-5 ${colorClass}`} />
                    </div>
                    <div>
                      <CardTitle className="text-base">{data.name}</CardTitle>
                      <p className="text-xs text-muted-foreground">{data.usage}</p>
                    </div>
                  </div>
                  <Badge 
                    variant={data.configured ? "default" : "secondary"}
                    className={data.configured ? "bg-emerald-500/20 text-emerald-500" : "bg-rose-500/20 text-rose-500"}
                  >
                    {data.configured ? "Configurée" : "Non configurée"}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <div className="flex-1 relative">
                    <Input
                      type={isVisible ? "text" : "password"}
                      value={isVisible ? data.full : data.masked}
                      readOnly
                      className="bg-black/20 border-white/10 font-mono text-sm pr-20"
                    />
                    <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                      {data.full && (
                        <>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-7 w-7 hover:bg-white/10"
                            onClick={() => toggleVisibility(key)}
                            data-testid={`toggle-${key}`}
                          >
                            {isVisible ? (
                              <EyeOff className="w-4 h-4 text-muted-foreground" />
                            ) : (
                              <Eye className="w-4 h-4 text-muted-foreground" />
                            )}
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-7 w-7 hover:bg-white/10"
                            onClick={() => copyToClipboard(key, data.full)}
                            data-testid={`copy-${key}`}
                          >
                            {isCopied ? (
                              <Check className="w-4 h-4 text-emerald-500" />
                            ) : (
                              <Copy className="w-4 h-4 text-muted-foreground" />
                            )}
                          </Button>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* API Status */}
      <Card className="glass border-white/5">
        <CardHeader>
          <CardTitle className="text-lg">État des Services</CardTitle>
          <CardDescription>Vérifiez la connectivité des APIs</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {Object.entries(apiKeys).map(([key, data]) => (
              <div 
                key={key}
                className={`p-3 rounded-lg text-center ${
                  data.configured ? "bg-emerald-500/10" : "bg-rose-500/10"
                }`}
              >
                <div className={`w-3 h-3 rounded-full mx-auto mb-2 ${
                  data.configured ? "bg-emerald-500" : "bg-rose-500"
                }`} />
                <p className="text-xs font-medium">{data.name}</p>
                <p className={`text-xs ${data.configured ? "text-emerald-500" : "text-rose-500"}`}>
                  {data.configured ? "Actif" : "Inactif"}
                </p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Documentation Links */}
      <Card className="glass border-white/5">
        <CardHeader>
          <CardTitle className="text-lg">Documentation</CardTitle>
          <CardDescription>Liens vers les documentations officielles</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            <a 
              href="https://www.coingecko.com/en/api/documentation" 
              target="_blank" 
              rel="noopener noreferrer"
              className="p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
            >
              <p className="font-medium">CoinGecko API</p>
              <p className="text-xs text-muted-foreground">Documentation crypto</p>
            </a>
            <a 
              href="https://www.alphavantage.co/documentation/" 
              target="_blank" 
              rel="noopener noreferrer"
              className="p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
            >
              <p className="font-medium">Alpha Vantage</p>
              <p className="text-xs text-muted-foreground">Forex & Indicateurs</p>
            </a>
            <a 
              href="https://finnhub.io/docs/api" 
              target="_blank" 
              rel="noopener noreferrer"
              className="p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
            >
              <p className="font-medium">Finnhub</p>
              <p className="text-xs text-muted-foreground">News & Sentiment</p>
            </a>
            <a 
              href="https://fred.stlouisfed.org/docs/api/fred/" 
              target="_blank" 
              rel="noopener noreferrer"
              className="p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
            >
              <p className="font-medium">FRED</p>
              <p className="text-xs text-muted-foreground">Données économiques</p>
            </a>
            <a 
              href="https://www.marketaux.com/documentation" 
              target="_blank" 
              rel="noopener noreferrer"
              className="p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
            >
              <p className="font-medium">Marketaux</p>
              <p className="text-xs text-muted-foreground">News sentiment</p>
            </a>
            <a 
              href="https://api.alternative.me/fng/" 
              target="_blank" 
              rel="noopener noreferrer"
              className="p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
            >
              <p className="font-medium">Fear & Greed</p>
              <p className="text-xs text-muted-foreground">Index sentiment crypto</p>
            </a>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
