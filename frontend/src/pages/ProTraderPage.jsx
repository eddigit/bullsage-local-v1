import { useState, useEffect, useCallback } from "react";
import { useAuth, API } from "../App";
import axios from "axios";
import { toast } from "sonner";
import {
  TrendingUp,
  TrendingDown,
  Target,
  AlertTriangle,
  Zap,
  RefreshCw,
  Loader2,
  CheckCircle2,
  XCircle,
  Clock,
  DollarSign,
  BarChart3,
  Brain,
  Shield,
  ArrowRight,
  Sparkles,
  Eye,
  ChevronRight,
  Activity,
  Rocket,
  PlayCircle,
  ExternalLink
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { ScrollArea } from "../components/ui/scroll-area";
import { Progress } from "../components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "../components/ui/tooltip";
import { HelpCircle, Info } from "lucide-react";

// Composant pour afficher la qualité du setup avec tooltip
const QualityBadge = ({ quality }) => {
  const styles = {
    "A+": "bg-gradient-to-r from-yellow-400 to-orange-500 text-white font-bold animate-pulse",
    "A": "bg-gradient-to-r from-green-500 to-emerald-600 text-white font-bold",
    "B": "bg-blue-500 text-white",
    "C": "bg-gray-400 text-white",
    "D": "bg-red-500 text-white"
  };

  const descriptions = {
    "A+": "Setup exceptionnel ! Toutes les conditions sont réunies. Trade à haute probabilité de succès.",
    "A": "Très bon setup. Conditions favorables pour trader avec confiance.",
    "B": "Setup correct mais pas optimal. Trader avec prudence ou attendre.",
    "C": "Setup faible. Mieux vaut attendre une meilleure opportunité.",
    "D": "Mauvais setup. Ne pas trader, risque élevé."
  };
  
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Badge className={`${styles[quality] || styles["C"]} text-lg px-3 py-1 cursor-help`}>
          {quality}
        </Badge>
      </TooltipTrigger>
      <TooltipContent side="top" className="max-w-xs bg-slate-900 text-white p-3">
        <p className="font-bold mb-1">Qualité du Setup : {quality}</p>
        <p className="text-sm">{descriptions[quality] || "Qualité non définie"}</p>
      </TooltipContent>
    </Tooltip>
  );
};

// Composant pour la direction du trade avec tooltip explicatif
const DirectionBadge = ({ direction }) => {
  if (direction === "LONG") {
    return (
      <Tooltip>
        <TooltipTrigger asChild>
          <Badge className="bg-green-500/20 text-green-400 border-green-500/50 gap-1 cursor-help">
            <TrendingUp className="w-4 h-4" />
            LONG
          </Badge>
        </TooltipTrigger>
        <TooltipContent side="top" className="max-w-xs bg-slate-900 text-white p-3">
          <p className="font-bold text-green-400 mb-1">📈 Position LONG (Achat)</p>
          <p className="text-sm">Vous pariez sur la HAUSSE du prix.</p>
          <p className="text-sm mt-1">• Acheter maintenant</p>
          <p className="text-sm">• Vendre plus tard à un prix plus élevé</p>
          <p className="text-sm text-green-400 mt-2">✅ Profit si le prix MONTE</p>
        </TooltipContent>
      </Tooltip>
    );
  } else if (direction === "SHORT") {
    return (
      <Tooltip>
        <TooltipTrigger asChild>
          <Badge className="bg-red-500/20 text-red-400 border-red-500/50 gap-1 cursor-help">
            <TrendingDown className="w-4 h-4" />
            SHORT
          </Badge>
        </TooltipTrigger>
        <TooltipContent side="top" className="max-w-xs bg-slate-900 text-white p-3">
          <p className="font-bold text-red-400 mb-1">📉 Position SHORT (Vente)</p>
          <p className="text-sm">Vous pariez sur la BAISSE du prix.</p>
          <p className="text-sm mt-1">• Vendre (emprunter) maintenant</p>
          <p className="text-sm">• Racheter plus tard à un prix plus bas</p>
          <p className="text-sm text-red-400 mt-2">✅ Profit si le prix DESCEND</p>
        </TooltipContent>
      </Tooltip>
    );
  }
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Badge variant="outline" className="gap-1 cursor-help">
          <Clock className="w-4 h-4" />
          ATTENDRE
        </Badge>
      </TooltipTrigger>
      <TooltipContent side="top" className="max-w-xs bg-slate-900 text-white p-3">
        <p className="font-bold text-yellow-400 mb-1">⏳ Attendre</p>
        <p className="text-sm">Pas de signal clair pour le moment.</p>
        <p className="text-sm mt-1">Patience ! Mieux vaut ne pas trader que de forcer une position.</p>
      </TooltipContent>
    </Tooltip>
  );
};

// Composant pour le badge de type de trade (timeframe)
const TradeTypeBadge = ({ tradeType, timeframe, estimatedDuration }) => {
  const styles = {
    "SCALPING": { bg: "bg-purple-500/20", text: "text-purple-400", border: "border-purple-500/50", icon: "⚡" },
    "INTRADAY": { bg: "bg-blue-500/20", text: "text-blue-400", border: "border-blue-500/50", icon: "🕐" },
    "INTRADAY+": { bg: "bg-cyan-500/20", text: "text-cyan-400", border: "border-cyan-500/50", icon: "🕓" },
    "SWING": { bg: "bg-orange-500/20", text: "text-orange-400", border: "border-orange-500/50", icon: "📅" },
    "POSITION": { bg: "bg-amber-500/20", text: "text-amber-400", border: "border-amber-500/50", icon: "📆" }
  };

  const style = styles[tradeType] || styles["INTRADAY"];
  
  const descriptions = {
    "SCALPING": "Trade très court terme (5-30 minutes). Nécessite une surveillance constante.",
    "INTRADAY": "Trade sur quelques heures. À clôturer dans la journée.",
    "INTRADAY+": "Trade étendu sur 4h à 24h. Peut rester ouvert overnight.",
    "SWING": "Trade sur plusieurs jours. Surveiller 1-2 fois par jour suffit.",
    "POSITION": "Trade long terme sur semaines/mois. Peu de surveillance requise."
  };
  
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Badge className={`${style.bg} ${style.text} ${style.border} gap-1 cursor-help`}>
          <Clock className="w-3 h-3" />
          {timeframe || "4H"} • {tradeType || "INTRADAY"}
        </Badge>
      </TooltipTrigger>
      <TooltipContent side="top" className="max-w-sm bg-slate-900 text-white p-3">
        <p className="font-bold mb-1">{style.icon} Type de Trade : {tradeType}</p>
        <p className="text-sm">{descriptions[tradeType] || "Trade standard"}</p>
        <div className="mt-2 p-2 bg-white/10 rounded">
          <p className="text-sm font-semibold">⏱️ Durée estimée : {estimatedDuration || "4 à 24 heures"}</p>
        </div>
      </TooltipContent>
    </Tooltip>
  );
};

// Composant pour une opportunité de trade
const TradeOpportunity = ({ opportunity, onSelect, onApplyTrade, applying, onExecuteDydx, executingDydx, executedDydx }) => {
  const isHot = opportunity.quality === "A+" || (opportunity.quality === "A" && opportunity.urgency === "IMMEDIATE");
  
  return (
    <Card 
      className={`cursor-pointer transition-all hover:scale-[1.02] ${
        isHot ? "border-yellow-500/50 bg-yellow-500/5" : "hover:border-primary/50"
      }`}
      onClick={() => onSelect(opportunity.symbol)}
    >
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className="text-2xl font-bold">{opportunity.symbol}</div>
            <QualityBadge quality={opportunity.quality} />
            <DirectionBadge direction={opportunity.direction} />
            <TradeTypeBadge 
              tradeType={opportunity.trade_type} 
              timeframe={opportunity.timeframe}
              estimatedDuration={opportunity.estimated_duration}
            />
          </div>
          {isHot && <Zap className="w-6 h-6 text-yellow-500 animate-pulse" />}
        </div>
        
        {/* Ligne de durée estimée */}
        <div className="mb-3 p-2 bg-muted/30 rounded-lg flex items-center justify-between">
          <Tooltip>
            <TooltipTrigger asChild>
              <div className="flex items-center gap-2 cursor-help">
                <Clock className="w-4 h-4 text-muted-foreground" />
                <span className="text-sm">
                  <span className="text-muted-foreground">Durée estimée : </span>
                  <span className="font-semibold">{opportunity.estimated_duration || "4 à 24 heures"}</span>
                </span>
              </div>
            </TooltipTrigger>
            <TooltipContent side="top" className="max-w-sm bg-slate-900 text-white p-3">
              <p className="font-bold mb-1">⏱️ Durée de la position</p>
              <p className="text-sm">Temps estimé pour que le trade atteigne son objectif.</p>
              <div className="mt-2 space-y-1 text-sm">
                <p>• <span className="text-muted-foreground">Minimum :</span> {opportunity.hold_time_min || "4 heures"}</p>
                <p>• <span className="text-muted-foreground">Maximum :</span> {opportunity.hold_time_max || "24 heures"}</p>
              </div>
              <p className="text-yellow-400 text-sm mt-2">💡 Planifiez votre disponibilité en conséquence !</p>
            </TooltipContent>
          </Tooltip>
          <Badge variant="outline" className="text-xs">
            {opportunity.timeframe || "4H"}
          </Badge>
        </div>
        
        <div className="grid grid-cols-4 gap-4 text-sm">
          <Tooltip>
            <TooltipTrigger asChild>
              <div className="cursor-help">
                <div className="text-muted-foreground flex items-center gap-1">Entrée <Info className="w-3 h-3" /></div>
                <div className="font-mono font-bold text-lg">${opportunity.entry?.toLocaleString()}</div>
              </div>
            </TooltipTrigger>
            <TooltipContent side="top" className="max-w-xs bg-slate-900 text-white p-3">
              <p className="font-bold mb-1">💰 Prix d'Entrée</p>
              <p className="text-sm">Prix auquel vous devez ouvrir votre position.</p>
              <p className="text-sm mt-1">Attendez que le prix atteigne ce niveau avant d'entrer.</p>
            </TooltipContent>
          </Tooltip>
          <Tooltip>
            <TooltipTrigger asChild>
              <div className="cursor-help">
                <div className="text-muted-foreground flex items-center gap-1">Stop Loss <Info className="w-3 h-3" /></div>
                <div className="font-mono text-red-400">${opportunity.stop?.toLocaleString()}</div>
              </div>
            </TooltipTrigger>
            <TooltipContent side="top" className="max-w-xs bg-slate-900 text-white p-3">
              <p className="font-bold text-red-400 mb-1">🛑 Stop Loss (SL)</p>
              <p className="text-sm">Prix de sortie automatique pour limiter vos pertes.</p>
              <p className="text-sm mt-1">Si le prix atteint ce niveau, la position se ferme automatiquement.</p>
              <p className="text-sm text-red-400 mt-2">⚠️ TOUJOURS placer un Stop Loss !</p>
            </TooltipContent>
          </Tooltip>
          <Tooltip>
            <TooltipTrigger asChild>
              <div className="cursor-help">
                <div className="text-muted-foreground flex items-center gap-1">Take Profit <Info className="w-3 h-3" /></div>
                <div className="font-mono text-green-400">${opportunity.tp1?.toLocaleString()}</div>
              </div>
            </TooltipTrigger>
            <TooltipContent side="top" className="max-w-xs bg-slate-900 text-white p-3">
              <p className="font-bold text-green-400 mb-1">🎯 Take Profit (TP)</p>
              <p className="text-sm">Prix cible pour prendre vos bénéfices.</p>
              <p className="text-sm mt-1">Quand le prix atteint ce niveau, vous encaissez vos gains.</p>
            </TooltipContent>
          </Tooltip>
          <Tooltip>
            <TooltipTrigger asChild>
              <div className="cursor-help">
                <div className="text-muted-foreground flex items-center gap-1">R:R <Info className="w-3 h-3" /></div>
                <div className="font-bold text-primary">1:{opportunity.rr_ratio}</div>
              </div>
            </TooltipTrigger>
            <TooltipContent side="top" className="max-w-xs bg-slate-900 text-white p-3">
              <p className="font-bold text-primary mb-1">⚖️ Ratio Risque/Récompense</p>
              <p className="text-sm">1:{opportunity.rr_ratio} signifie que pour 1€ risqué, vous pouvez gagner {opportunity.rr_ratio}€.</p>
              <p className="text-sm mt-1">Un bon ratio est minimum 1:2 (risquer 1 pour gagner 2).</p>
              <p className="text-sm text-green-400 mt-2">✅ Plus le ratio est élevé, mieux c'est !</p>
            </TooltipContent>
          </Tooltip>
        </div>
        
        <div className="mt-3 flex items-center justify-between">
          <Tooltip>
            <TooltipTrigger asChild>
              <div className="flex items-center gap-2 cursor-help">
                <Progress value={opportunity.confidence} className="w-24 h-2" />
                <span className="text-sm text-muted-foreground">{opportunity.confidence}%</span>
              </div>
            </TooltipTrigger>
            <TooltipContent side="top" className="max-w-xs bg-slate-900 text-white p-3">
              <p className="font-bold mb-1">📊 Niveau de Confiance</p>
              <p className="text-sm">Probabilité estimée de réussite du trade.</p>
              <p className="text-sm mt-1">Plus le pourcentage est élevé, plus le signal est fiable.</p>
            </TooltipContent>
          </Tooltip>
          <Tooltip>
            <TooltipTrigger asChild>
              <Badge variant={opportunity.urgency === "IMMEDIATE" ? "destructive" : "outline"} className="cursor-help">
                {opportunity.urgency === "IMMEDIATE" ? "⚡ MAINTENANT" : 
                 opportunity.urgency === "WAIT_PULLBACK" ? "📉 Attendre pullback" : "⏳ Confirmation"}
              </Badge>
            </TooltipTrigger>
            <TooltipContent side="top" className="max-w-xs bg-slate-900 text-white p-3">
              <p className="font-bold mb-1">⏰ Urgence d'entrée</p>
              {opportunity.urgency === "IMMEDIATE" && (
                <p className="text-sm text-red-400">Le signal est actif MAINTENANT ! Entrez rapidement.</p>
              )}
              {opportunity.urgency === "WAIT_PULLBACK" && (
                <p className="text-sm text-yellow-400">Attendez un petit repli du prix avant d'entrer pour un meilleur prix.</p>
              )}
              {opportunity.urgency !== "IMMEDIATE" && opportunity.urgency !== "WAIT_PULLBACK" && (
                <p className="text-sm">Attendez une confirmation supplémentaire avant d'entrer.</p>
              )}
            </TooltipContent>
          </Tooltip>
        </div>
        
        {opportunity.signals && (
          <div className="mt-3 flex flex-wrap gap-1">
            {opportunity.signals.slice(0, 3).map((signal, i) => (
              <Badge key={i} variant="secondary" className="text-xs">
                {signal}
              </Badge>
            ))}
          </div>
        )}

        {/* Bouton CTA - Appliquer ce Trade */}
        <div className="mt-4 pt-3 border-t border-white/10">
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                className={`w-full gap-2 ${
                  opportunity.direction === "LONG" 
                    ? "bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500" 
                    : "bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500"
                }`}
                onClick={(e) => {
                  e.stopPropagation();
                  onApplyTrade(opportunity);
                }}
                disabled={applying}
              >
                {applying ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Application en cours...
                  </>
                ) : (
                  <>
                    <Rocket className="w-4 h-4" />
                    {opportunity.direction === "LONG" ? "🟢 ACHETER" : "🔴 VENDRE"} - Paper Trading
                  </>
                )}
              </Button>
            </TooltipTrigger>
            <TooltipContent side="bottom" className="max-w-sm bg-slate-900 text-white p-3">
              <p className="font-bold mb-2">
                {opportunity.direction === "LONG" 
                  ? "🟢 Ouvrir une position LONG (Achat)" 
                  : "🔴 Ouvrir une position SHORT (Vente)"}
              </p>
              {opportunity.direction === "LONG" ? (
                <>
                  <p className="text-sm text-green-400">Vous ACHETEZ {opportunity.symbol}</p>
                  <p className="text-sm mt-1">• Vous gagnez si le prix MONTE</p>
                  <p className="text-sm">• Vous perdez si le prix DESCEND</p>
                </>
              ) : (
                <>
                  <p className="text-sm text-red-400">Vous VENDEZ {opportunity.symbol}</p>
                  <p className="text-sm mt-1">• Vous gagnez si le prix DESCEND</p>
                  <p className="text-sm">• Vous perdez si le prix MONTE</p>
                </>
              )}
              <p className="text-sm text-blue-400 mt-2">💡 Ce trade sera ouvert en Paper Trading (argent virtuel)</p>
            </TooltipContent>
          </Tooltip>

          {/* Avertissement si pullback requis */}
          {opportunity.urgency === "WAIT_PULLBACK" && (
            <div className="mt-2 p-2 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
              <p className="text-xs text-yellow-400 flex items-center gap-1">
                <AlertTriangle className="w-3 h-3" />
                <span><strong>Pullback recommandé:</strong> Attendez un repli vers {opportunity.entry_price?.toLocaleString()} avant d'entrer</span>
              </p>
            </div>
          )}

          {/* Bouton Exécuter sur dYdX */}
          <div className="mt-2 flex gap-2">
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="outline"
                  className={`flex-1 gap-2 ${
                    opportunity.urgency === "WAIT_PULLBACK" 
                      ? 'border-yellow-500/50 text-yellow-400 hover:bg-yellow-500/20' 
                      : 'border-purple-500/50 text-purple-400 hover:bg-purple-500/20'
                  } ${executedDydx ? 'bg-purple-500/20' : ''}`}
                  onClick={(e) => {
                    e.stopPropagation();
                    if (opportunity.urgency === "WAIT_PULLBACK") {
                      if (window.confirm(`⚠️ Ce trade recommande d'attendre un PULLBACK vers ${opportunity.entry_price?.toLocaleString()}.\n\nVoulez-vous quand même exécuter MAINTENANT au prix du marché ?`)) {
                        onExecuteDydx(opportunity);
                      }
                    } else {
                      onExecuteDydx(opportunity);
                    }
                  }}
                  disabled={executingDydx || executedDydx}
                >
                  {executingDydx ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Exécution dYdX...
                    </>
                  ) : executedDydx ? (
                    <>
                      <CheckCircle2 className="w-4 h-4 text-green-400" />
                      Exécuté sur dYdX !
                    </>
                  ) : opportunity.urgency === "WAIT_PULLBACK" ? (
                    <>
                      <AlertTriangle className="w-4 h-4" />
                      ⏳ Exécuter malgré pullback
                    </>
                  ) : (
                    <>
                      <Zap className="w-4 h-4" />
                      🚀 Exécuter sur dYdX Testnet
                    </>
                  )}
                </Button>
              </TooltipTrigger>
              <TooltipContent side="bottom" className="max-w-sm bg-slate-900 text-white p-3">
                <p className="font-bold text-purple-400 mb-2">⚡ Exécution RÉELLE sur dYdX</p>
                <p className="text-sm">Ce trade sera exécuté directement sur dYdX Testnet.</p>
                <p className="text-sm mt-1">• Entry automatique au prix marché</p>
                <p className="text-sm">• Stop Loss placé automatiquement</p>
                <p className="text-sm">• Take Profit placé automatiquement</p>
                {opportunity.urgency === "WAIT_PULLBACK" && (
                  <p className="text-sm text-yellow-400 mt-2">⚠️ ATTENTION: Un pullback est recommandé avant d'entrer !</p>
                )}
                <p className="text-sm text-yellow-400 mt-2">⚠️ Fonds testnet requis sur votre wallet dYdX</p>
              </TooltipContent>
            </Tooltip>

            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="border border-purple-500/30 hover:bg-purple-500/20"
                  onClick={(e) => {
                    e.stopPropagation();
                    window.open('https://v4.testnet.dydx.exchange/portfolio/positions', '_blank');
                  }}
                >
                  <ExternalLink className="w-4 h-4 text-purple-400" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="bottom">
                <p>Voir mes positions sur dYdX</p>
              </TooltipContent>
            </Tooltip>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

// Composant pour l'analyse rapide
const QuickAnalysis = ({ data, loading }) => {
  if (loading) {
    return (
      <Card className="h-full">
        <CardContent className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </CardContent>
      </Card>
    );
  }
  
  if (!data) return null;
  
  const actionColors = {
    "🟢": "from-green-500/20 to-green-600/10 border-green-500/50",
    "🔴": "from-red-500/20 to-red-600/10 border-red-500/50",
    "🟠": "from-orange-500/20 to-orange-600/10 border-orange-500/50",
    "🟡": "from-yellow-500/20 to-yellow-600/10 border-yellow-500/50"
  };
  
  const actionEmoji = data.action?.substring(0, 2) || "🟡";
  const colorClass = actionColors[actionEmoji] || actionColors["🟡"];
  
  return (
    <Card className={`bg-gradient-to-br ${colorClass} h-full`}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Brain className="w-6 h-6" />
          Analyse Rapide - {data.symbol}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="text-3xl font-bold text-center py-4">
          {data.action}
        </div>
        
        <p className="text-center text-lg">{data.advice}</p>
        
        <div className="grid grid-cols-2 gap-4 mt-4">
          <div className="text-center p-3 bg-background/50 rounded-lg">
            <div className="text-sm text-muted-foreground">Qualité</div>
            <QualityBadge quality={data.quality} />
          </div>
          <div className="text-center p-3 bg-background/50 rounded-lg">
            <div className="text-sm text-muted-foreground">Direction</div>
            <DirectionBadge direction={data.direction} />
          </div>
        </div>
        
        <div className="grid grid-cols-3 gap-2 text-center mt-4">
          <div className="p-2 bg-background/50 rounded">
            <div className="text-xs text-muted-foreground">Entrée</div>
            <div className="font-mono font-bold">${data.entry?.toLocaleString()}</div>
          </div>
          <div className="p-2 bg-background/50 rounded">
            <div className="text-xs text-muted-foreground">Stop Loss</div>
            <div className="font-mono text-red-400">${data.stop_loss?.toLocaleString()}</div>
          </div>
          <div className="p-2 bg-background/50 rounded">
            <div className="text-xs text-muted-foreground">Take Profit</div>
            <div className="font-mono text-green-400">${data.take_profit?.toLocaleString()}</div>
          </div>
        </div>
        
        <div className="text-center mt-4">
          <Badge variant="outline" className="text-lg px-4 py-2">
            Ratio R:R → 1:{data.risk_reward}
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
};

// Composant pour les règles de trading
const TradingRules = ({ rules }) => {
  if (!rules) return null;
  
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Shield className="w-5 h-5 text-primary" />
          {rules.title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-64">
          <div className="space-y-2">
            {rules.rules?.map((rule, i) => (
              <div key={i} className="flex gap-3 p-2 rounded hover:bg-muted/50">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-primary font-bold">
                  {rule.number}
                </div>
                <div>
                  <div className="font-medium">{rule.rule}</div>
                  <div className="text-sm text-muted-foreground">{rule.explanation}</div>
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
        <div className="mt-4 p-3 bg-primary/10 rounded-lg text-center">
          <Sparkles className="w-5 h-5 inline mr-2 text-primary" />
          {rules.reminder}
        </div>
      </CardContent>
    </Card>
  );
};

// Page principale Pro Trader
export default function ProTraderPage() {
  const { token } = useAuth();
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [opportunities, setOpportunities] = useState([]);
  const [selectedSymbol, setSelectedSymbol] = useState("BTC");
  const [quickAnalysis, setQuickAnalysis] = useState(null);
  const [quickLoading, setQuickLoading] = useState(false);
  const [rules, setRules] = useState(null);
  const [marketOverview, setMarketOverview] = useState([]);
  const [scanMessage, setScanMessage] = useState("");
  const [applyingSymbol, setApplyingSymbol] = useState(null);
  const [executingDydx, setExecutingDydx] = useState({});
  const [executedDydx, setExecutedDydx] = useState({});
  
  // Configuration du montant à engager sur dYdX
  const [dydxTradeConfig, setDydxTradeConfig] = useState({
    mode: 'percentage', // 'percentage' ou 'fixed'
    percentage: 5, // % du portefeuille
    fixedAmount: 100, // Montant fixe en USDC
  });

  // Exécuter sur dYdX Testnet
  const executeDydx = async (opportunity) => {
    const symbol = opportunity.symbol;
    setExecutingDydx(prev => ({ ...prev, [symbol]: true }));
    
    try {
      const signal = {
        market: `${symbol}-USD`,
        direction: opportunity.direction,
        // Nouveau: configuration du montant
        sizeMode: dydxTradeConfig.mode,
        percentageOfPortfolio: dydxTradeConfig.percentage,
        fixedAmountUSDC: dydxTradeConfig.fixedAmount,
        // Fallback si le serveur ne supporte pas encore le nouveau format
        size: symbol === 'BTC' ? 0.001 : symbol === 'ETH' ? 0.01 : 0.1,
        stop_loss_pct: opportunity.stop && opportunity.entry 
          ? Math.abs((opportunity.entry - opportunity.stop) / opportunity.entry * 100)
          : 2,
        take_profit_pct: opportunity.tp1 && opportunity.entry
          ? Math.abs((opportunity.tp1 - opportunity.entry) / opportunity.entry * 100)
          : 4,
        // Documentation du trade (pullback inclus)
        metadata: {
          urgency: opportunity.urgency || "IMMEDIATE",
          recommended_entry: opportunity.entry_price || opportunity.entry,
          wait_pullback: opportunity.urgency === "WAIT_PULLBACK",
          pullback_target: opportunity.urgency === "WAIT_PULLBACK" ? (opportunity.entry_price || opportunity.entry) : null,
          confidence: opportunity.confidence,
          quality: opportunity.quality,
          rr_ratio: opportunity.rr_ratio,
          signals: opportunity.signals,
          trade_type: opportunity.trade_type,
          timeframe: opportunity.timeframe,
          estimated_duration: opportunity.estimated_duration,
          executed_at: new Date().toISOString(),
          trade_config: {
            mode: dydxTradeConfig.mode,
            percentage: dydxTradeConfig.percentage,
            fixed_amount: dydxTradeConfig.fixedAmount
          }
        }
      };

      const response = await axios.post(`${API}/dydx/signal/quick`, signal);
      
      if (response.data.success || response.data.signal) {
        setExecutedDydx(prev => ({ ...prev, [symbol]: true }));
        
        // Message adapté selon l'urgence
        const pullbackWarning = opportunity.urgency === "WAIT_PULLBACK" 
          ? `\n⚠️ Note: Pullback était recommandé vers ${opportunity.entry_price || opportunity.entry}`
          : '';
        
        toast.success(
          `🚀 Trade ${opportunity.direction} ${symbol} exécuté sur dYdX!\n` +
          `Mode: ${response.data.mode || 'live'}${pullbackWarning}`,
          { duration: 5000 }
        );
      } else {
        throw new Error(response.data.error || 'Erreur inconnue');
      }
    } catch (error) {
      console.error("Erreur dYdX:", error);
      toast.error(`Erreur dYdX: ${error.response?.data?.detail || error.message}`);
    } finally {
      setExecutingDydx(prev => ({ ...prev, [symbol]: false }));
    }
  };

  // Appliquer un trade dans Paper Trading
  const applyTrade = async (opportunity) => {
    setApplyingSymbol(opportunity.symbol);
    try {
      // Calculer le montant basé sur le prix d'entrée (environ 100$ de trade)
      const amount = 100 / opportunity.entry;
      
      await axios.post(`${API}/paper-trading/trade`, {
        symbol: opportunity.symbol,
        type: opportunity.direction === "LONG" ? "buy" : "sell",
        amount: amount,
        price: opportunity.entry
      });

      toast.success(
        `🚀 Trade ${opportunity.direction} sur ${opportunity.symbol} appliqué!\n` +
        `Entrée: ${opportunity.entry} | SL: ${opportunity.stop} | TP: ${opportunity.tp1}`,
        { duration: 5000 }
      );
    } catch (error) {
      console.error("Erreur application trade:", error);
      toast.error("Erreur lors de l'application du trade");
    } finally {
      setApplyingSymbol(null);
    }
  };
  
  // Charger les données initiales
  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      // Charger le dashboard
      const dashRes = await axios.get(`${API}/pro/dashboard`);
      const dashData = dashRes.data || {};
      setOpportunities(Array.isArray(dashData.best_opportunities) ? dashData.best_opportunities : []);
      setMarketOverview(Array.isArray(dashData.market_overview) ? dashData.market_overview : []);
      setScanMessage(dashRes.data.summary || "");
      
      // Charger les règles
      const rulesRes = await axios.get(`${API}/pro/rules`);
      setRules(rulesRes.data);
      
      // Analyse rapide du premier symbole
      await loadQuickAnalysis("BTC");
      
    } catch (error) {
      console.error("Erreur chargement:", error);
      toast.error("Erreur de chargement des données");
    } finally {
      setLoading(false);
    }
  }, []);
  
  useEffect(() => {
    loadData();
  }, [loadData]);
  
  // Scanner le marché
  const scanMarket = async () => {
    setScanning(true);
    try {
      const symbols = "BTC,ETH,SOL,XRP,ADA,AVAX,DOT,LINK";
      const res = await axios.get(`${API}/pro/scan?symbols=${symbols}`);
      const scanData = res.data || {};
      setOpportunities(Array.isArray(scanData.best_setups) ? scanData.best_setups : []);
      setScanMessage(scanData.message || "");
      toast.success(`${scanData.opportunities_found || 0} opportunités trouvées!`);
    } catch (error) {
      toast.error("Erreur lors du scan");
    } finally {
      setScanning(false);
    }
  };
  
  // Analyse rapide
  const loadQuickAnalysis = async (symbol) => {
    setQuickLoading(true);
    setSelectedSymbol(symbol);
    try {
      const res = await axios.get(`${API}/pro/quick/${symbol}`);
      setQuickAnalysis(res.data);
    } catch (error) {
      toast.error(`Erreur analyse ${symbol}`);
    } finally {
      setQuickLoading(false);
    }
  };
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <Brain className="w-16 h-16 mx-auto mb-4 text-primary animate-pulse" />
          <h2 className="text-xl font-bold">Pro Trader AI</h2>
          <p className="text-muted-foreground">Analyse du marché en cours...</p>
          <Loader2 className="w-8 h-8 mx-auto mt-4 animate-spin" />
        </div>
      </div>
    );
  }
  
  return (
    <TooltipProvider delayDuration={200}>
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <Brain className="w-10 h-10 text-primary" />
            Pro Trader AI
            <Tooltip>
              <TooltipTrigger asChild>
                <HelpCircle className="w-5 h-5 text-muted-foreground cursor-help" />
              </TooltipTrigger>
              <TooltipContent side="right" className="max-w-sm bg-slate-900 text-white p-3">
                <p className="font-bold mb-2">💡 Aide Pro Trader AI</p>
                <p className="text-sm">Passez votre souris sur les éléments pour voir les explications :</p>
                <ul className="text-sm mt-2 space-y-1">
                  <li>• <span className="text-green-400">LONG</span> = Pari à la hausse (Achat)</li>
                  <li>• <span className="text-red-400">SHORT</span> = Pari à la baisse (Vente)</li>
                  <li>• <span className="text-yellow-400">A+/A</span> = Qualité du signal</li>
                  <li>• <span className="text-blue-400">R:R</span> = Ratio Risque/Récompense</li>
                </ul>
              </TooltipContent>
            </Tooltip>
          </h1>
          <p className="text-muted-foreground">
            Votre assistant de trading professionnel - Setups A+ et A uniquement
          </p>
        </div>
        <div className="flex gap-3">
          <Select value={selectedSymbol} onValueChange={loadQuickAnalysis}>
            <SelectTrigger className="w-32">
              <SelectValue placeholder="Symbole" />
            </SelectTrigger>
            <SelectContent>
              {["BTC", "ETH", "SOL", "XRP", "ADA", "AVAX", "DOT", "LINK"].map(s => (
                <SelectItem key={s} value={s}>{s}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button onClick={scanMarket} disabled={scanning}>
            {scanning ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <RefreshCw className="w-4 h-4 mr-2" />
            )}
            Scanner le Marché
          </Button>
        </div>
      </div>
      
      {/* Market Overview */}
      <div className="grid grid-cols-3 gap-4">
        {marketOverview.map((asset, i) => (
          <Card key={i} className="cursor-pointer hover:border-primary/50" onClick={() => loadQuickAnalysis(asset.symbol)}>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="font-bold text-xl">{asset.symbol}</div>
                <Badge variant={asset.trend_1d?.includes("UP") ? "default" : "destructive"}>
                  {asset.trend_1d?.includes("UP") ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                </Badge>
              </div>
              <div className="mt-2 font-mono text-2xl">${asset.price?.toLocaleString()}</div>
              <div className="flex justify-between text-sm text-muted-foreground mt-2">
                <span>RSI 4H: {asset.rsi_4h}</span>
                <span>{asset.phase}</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
      
      {/* Main Content */}
      <div className="grid grid-cols-3 gap-6">
        {/* Quick Analysis */}
        <div className="col-span-1">
          <QuickAnalysis data={quickAnalysis} loading={quickLoading} />
        </div>
        
        {/* Opportunities */}
        <div className="col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="w-5 h-5 text-primary" />
                Meilleures Opportunités
                {opportunities.length > 0 && (
                  <Badge variant="secondary">{opportunities.length}</Badge>
                )}
              </CardTitle>
              <CardDescription>
                Setups de qualité A+ et A uniquement - Les seuls à trader!
              </CardDescription>
            </CardHeader>
            <CardContent>
              {opportunities.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <AlertTriangle className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>Aucune opportunité A+ ou A pour le moment.</p>
                  <p className="text-sm mt-2">La patience est la clé du trading gagnant!</p>
                </div>
              ) : (
                <ScrollArea className="h-[400px]">
                  <div className="space-y-4">
                    {opportunities.map((opp, i) => (
                      <TradeOpportunity 
                          key={i}
                          opportunity={opp}
                          onSelect={loadQuickAnalysis}
                          onApplyTrade={applyTrade}
                          applying={applyingSymbol === opp.symbol}
                          onExecuteDydx={executeDydx}
                          executingDydx={executingDydx[opp.symbol]}
                          executedDydx={executedDydx[opp.symbol]}
                        />
                    ))}
                  </div>
                </ScrollArea>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
      
      {/* Configuration dYdX */}
      <Card className="border-purple-500/30 bg-purple-500/5">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Zap className="w-5 h-5 text-purple-400" />
            Configuration Exécution dYdX
            <Badge variant="outline" className="text-purple-400 border-purple-500/50">Testnet</Badge>
          </CardTitle>
          <CardDescription>
            Définissez le montant à engager pour chaque trade exécuté sur dYdX
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Mode de calcul */}
            <div className="space-y-2">
              <label className="text-sm font-medium flex items-center gap-2">
                <DollarSign className="w-4 h-4 text-muted-foreground" />
                Mode de calcul
              </label>
              <Select 
                value={dydxTradeConfig.mode} 
                onValueChange={(v) => setDydxTradeConfig(prev => ({ ...prev, mode: v }))}
              >
                <SelectTrigger className="border-purple-500/30">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="percentage">📊 % du portefeuille</SelectItem>
                  <SelectItem value="fixed">💵 Montant fixe (USDC)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Pourcentage du portefeuille */}
            {dydxTradeConfig.mode === 'percentage' && (
              <div className="space-y-2">
                <label className="text-sm font-medium flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-muted-foreground" />
                  % du portefeuille
                </label>
                <Select 
                  value={String(dydxTradeConfig.percentage)} 
                  onValueChange={(v) => setDydxTradeConfig(prev => ({ ...prev, percentage: Number(v) }))}
                >
                  <SelectTrigger className="border-purple-500/30">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="1">1% - Ultra conservateur</SelectItem>
                    <SelectItem value="2">2% - Conservateur</SelectItem>
                    <SelectItem value="5">5% - Modéré</SelectItem>
                    <SelectItem value="10">10% - Agressif</SelectItem>
                    <SelectItem value="25">25% - Très agressif</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  💡 Risque recommandé: 2-5% par trade
                </p>
              </div>
            )}

            {/* Montant fixe */}
            {dydxTradeConfig.mode === 'fixed' && (
              <div className="space-y-2">
                <label className="text-sm font-medium flex items-center gap-2">
                  <DollarSign className="w-4 h-4 text-muted-foreground" />
                  Montant fixe (USDC)
                </label>
                <Select 
                  value={String(dydxTradeConfig.fixedAmount)} 
                  onValueChange={(v) => setDydxTradeConfig(prev => ({ ...prev, fixedAmount: Number(v) }))}
                >
                  <SelectTrigger className="border-purple-500/30">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="50">$50 USDC</SelectItem>
                    <SelectItem value="100">$100 USDC</SelectItem>
                    <SelectItem value="250">$250 USDC</SelectItem>
                    <SelectItem value="500">$500 USDC</SelectItem>
                    <SelectItem value="1000">$1,000 USDC</SelectItem>
                    <SelectItem value="2500">$2,500 USDC</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            )}

            {/* Récapitulatif */}
            <div className="p-3 bg-purple-500/10 rounded-lg border border-purple-500/30">
              <div className="text-sm font-medium text-purple-400 mb-1">Configuration actuelle</div>
              <div className="text-lg font-bold">
                {dydxTradeConfig.mode === 'percentage' 
                  ? `${dydxTradeConfig.percentage}% du portefeuille`
                  : `$${dydxTradeConfig.fixedAmount} USDC`
                }
              </div>
              <div className="text-xs text-muted-foreground mt-1">
                par trade exécuté sur dYdX
              </div>
            </div>
          </div>

          {/* Avertissement pullback */}
          <div className="mt-4 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-yellow-400 flex-shrink-0 mt-0.5" />
            <div className="text-sm">
              <span className="font-medium text-yellow-400">Documentation des trades:</span>
              <span className="text-muted-foreground"> Chaque trade enregistre l'urgence (IMMEDIATE/WAIT_PULLBACK), le prix d'entrée recommandé, la qualité du setup, et les métadonnées complètes.</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Scan Message */}
      {scanMessage && (
        <Card className="bg-muted/50">
          <CardContent className="p-4">
            <pre className="whitespace-pre-wrap text-sm font-mono">{scanMessage}</pre>
          </CardContent>
        </Card>
      )}
      
      {/* Trading Rules */}
      <TradingRules rules={rules} />
    </div>
    </TooltipProvider>
  );
}
