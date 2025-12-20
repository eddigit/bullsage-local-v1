import { useState } from "react";
import { useAuth, API } from "../App";
import axios from "axios";
import { toast } from "sonner";
import {
  User,
  Shield,
  Bell,
  Palette,
  Save,
  ChevronRight,
  GraduationCap,
  TrendingUp,
  Zap,
  AlertTriangle
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Badge } from "../components/ui/badge";
import { Separator } from "../components/ui/separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import { Switch } from "../components/ui/switch";

const TRADING_LEVELS = [
  { 
    value: "beginner", 
    label: "Débutant", 
    description: "Je découvre le trading",
    icon: GraduationCap,
    color: "text-blue-500"
  },
  { 
    value: "intermediate", 
    label: "Intermédiaire", 
    description: "J'ai quelques bases",
    icon: TrendingUp,
    color: "text-yellow-500"
  },
  { 
    value: "advanced", 
    label: "Avancé", 
    description: "Je trade régulièrement",
    icon: Zap,
    color: "text-emerald-500"
  },
];

export default function SettingsPage() {
  const { user, updateUser } = useAuth();
  const [tradingLevel, setTradingLevel] = useState(user?.trading_level || "beginner");
  const [saving, setSaving] = useState(false);
  
  // Notification preferences (local state for demo)
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [priceAlerts, setPriceAlerts] = useState(true);
  const [tradingSignals, setTradingSignals] = useState(true);

  const handleSaveTradingLevel = async () => {
    setSaving(true);
    try {
      await axios.put(`${API}/settings/trading-level?level=${tradingLevel}`);
      updateUser({ trading_level: tradingLevel });
      toast.success("Niveau de trading mis à jour");
    } catch (error) {
      toast.error("Erreur lors de la sauvegarde");
    } finally {
      setSaving(false);
    }
  };

  const currentLevel = TRADING_LEVELS.find(l => l.value === tradingLevel);

  return (
    <div className="space-y-6 max-w-3xl" data-testid="settings-page">
      {/* Header */}
      <div>
        <h1 className="text-2xl md:text-3xl font-bold font-manrope">Paramètres</h1>
        <p className="text-muted-foreground">
          Gérez votre profil et vos préférences
        </p>
      </div>

      {/* Profile Section */}
      <Card className="glass border-white/5">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <User className="w-5 h-5 text-primary" />
            Profil
          </CardTitle>
          <CardDescription>Informations de votre compte</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Nom</Label>
              <Input
                value={user?.name || ""}
                disabled
                className="bg-black/20 border-white/10"
              />
            </div>
            <div className="space-y-2">
              <Label>Email</Label>
              <Input
                value={user?.email || ""}
                disabled
                className="bg-black/20 border-white/10"
              />
            </div>
          </div>
          
          <div className="flex items-center gap-2 pt-2">
            <Badge variant="secondary" className="bg-white/5">
              Membre depuis {user?.created_at ? new Date(user.created_at).toLocaleDateString("fr-FR", { year: "numeric", month: "long" }) : "-"}
            </Badge>
            {user?.is_admin && (
              <Badge className="bg-violet-500/20 text-violet-400">
                <Shield className="w-3 h-3 mr-1" />
                Administrateur
              </Badge>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Trading Level */}
      <Card className="glass border-white/5">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <GraduationCap className="w-5 h-5 text-blue-500" />
            Niveau de Trading
          </CardTitle>
          <CardDescription>
            L&apos;assistant IA adaptera ses réponses à votre niveau
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {TRADING_LEVELS.map((level) => (
              <div
                key={level.value}
                className={`p-4 rounded-lg border cursor-pointer transition-all ${
                  tradingLevel === level.value
                    ? "bg-primary/10 border-primary/30"
                    : "bg-white/5 border-white/10 hover:border-white/20"
                }`}
                onClick={() => setTradingLevel(level.value)}
                data-testid={`level-${level.value}`}
              >
                <div className="flex items-center gap-3 mb-2">
                  <level.icon className={`w-5 h-5 ${level.color}`} />
                  <span className="font-medium">{level.label}</span>
                </div>
                <p className="text-sm text-muted-foreground">{level.description}</p>
              </div>
            ))}
          </div>
          
          {tradingLevel !== user?.trading_level && (
            <Button
              onClick={handleSaveTradingLevel}
              disabled={saving}
              className="bg-primary hover:bg-primary/90 text-black"
              data-testid="save-level-btn"
            >
              <Save className="w-4 h-4 mr-2" />
              {saving ? "Sauvegarde..." : "Sauvegarder"}
            </Button>
          )}
        </CardContent>
      </Card>

      {/* Notifications */}
      <Card className="glass border-white/5">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Bell className="w-5 h-5 text-yellow-500" />
            Notifications
          </CardTitle>
          <CardDescription>Gérez vos préférences de notifications</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between py-2">
            <div>
              <p className="font-medium">Notifications par email</p>
              <p className="text-sm text-muted-foreground">Recevoir des emails importants</p>
            </div>
            <Switch
              checked={emailNotifications}
              onCheckedChange={setEmailNotifications}
              data-testid="email-notifications"
            />
          </div>
          <Separator className="bg-white/5" />
          <div className="flex items-center justify-between py-2">
            <div>
              <p className="font-medium">Alertes de prix</p>
              <p className="text-sm text-muted-foreground">Notifications quand vos alertes sont déclenchées</p>
            </div>
            <Switch
              checked={priceAlerts}
              onCheckedChange={setPriceAlerts}
              data-testid="price-alerts"
            />
          </div>
          <Separator className="bg-white/5" />
          <div className="flex items-center justify-between py-2">
            <div>
              <p className="font-medium">Signaux de trading</p>
              <p className="text-sm text-muted-foreground">Recevoir des signaux basés sur vos stratégies</p>
            </div>
            <Switch
              checked={tradingSignals}
              onCheckedChange={setTradingSignals}
              data-testid="trading-signals"
            />
          </div>
        </CardContent>
      </Card>

      {/* About */}
      <Card className="glass border-white/5">
        <CardHeader>
          <CardTitle className="text-lg">À propos</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center justify-between py-2">
            <span className="text-muted-foreground">Version</span>
            <span className="font-mono">1.0.0</span>
          </div>
          <Separator className="bg-white/5" />
          <div className="flex items-center justify-between py-2">
            <span className="text-muted-foreground">Développé par</span>
            <span>BULL SAGE Team</span>
          </div>
          <Separator className="bg-white/5" />
          <div className="flex items-start gap-2 pt-2 text-muted-foreground">
            <AlertTriangle className="w-4 h-4 text-amber-500 mt-0.5 flex-shrink-0" />
            <p className="text-xs">
              BULL SAGE est un outil éducatif. Le trading comporte des risques. 
              Ne tradez jamais plus que ce que vous pouvez vous permettre de perdre.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
