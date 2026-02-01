import { useState, useRef, useCallback } from "react";
import { useAuth, API } from "../App";
import axios from "axios";
import { toast } from "sonner";
import { BUILD_INFO } from "../buildInfo";
import {
  User,
  Shield,
  Bell,
  Camera,
  Save,
  Trash2,
  GraduationCap,
  TrendingUp,
  Zap,
  AlertTriangle,
  Loader2,
  Settings2,
  ExternalLink,
  Activity,
  RefreshCw,
  CheckCircle2,
  XCircle,
  AlertCircle
} from "lucide-react";
import { Link } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Badge } from "../components/ui/badge";
import { Separator } from "../components/ui/separator";
import { Avatar, AvatarImage, AvatarFallback } from "../components/ui/avatar";
import { Switch } from "../components/ui/switch";

// Detect environment - use Render backend URL in production
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 
  (window.location.hostname === 'localhost' 
    ? 'http://localhost:8000' 
    : 'https://bullsage-api.onrender.com');

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

function SettingsBackupSection() {
  const [backups, setBackups] = useState([]);
  const [loadingBackups, setLoadingBackups] = useState(false);
  const [creating, setCreating] = useState(false);

  const loadBackups = useCallback(async () => {
    setLoadingBackups(true);
    try {
      const res = await axios.get(`${API}/settings/backups`);
      setBackups(res.data?.backups || []);
    } catch (error) {
      console.error("Error loading backups:", error);
    } finally {
      setLoadingBackups(false);
    }
  }, []);

  const createBackup = async () => {
    setCreating(true);
    try {
      await axios.post(`${API}/settings/backup`, { description: "Sauvegarde manuelle" });
      toast.success("Sauvegarde créée");
      loadBackups();
    } catch (error) {
      toast.error("Erreur lors de la sauvegarde");
    } finally {
      setCreating(false);
    }
  };

  const restoreBackup = async (createdAt) => {
    if (!window.confirm("Restaurer ces paramètres ? Vos paramètres actuels seront sauvegardés automatiquement.")) return;
    try {
      await axios.post(`${API}/settings/restore?created_at=${encodeURIComponent(createdAt)}`);
      toast.success("Paramètres restaurés ! Rechargez la page.");
    } catch (error) {
      toast.error("Erreur lors de la restauration");
    }
  };

  return (
    <Card className="glass border-white/5">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg flex items-center gap-2">
              <Save className="w-5 h-5 text-primary" />
              Sauvegarde des paramètres
            </CardTitle>
            <CardDescription>Sauvegardez et restaurez vos réglages</CardDescription>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={loadBackups} disabled={loadingBackups}>
              {loadingBackups ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
            </Button>
            <Button size="sm" onClick={createBackup} disabled={creating}>
              {creating ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : <Save className="w-4 h-4 mr-1" />}
              Sauvegarder
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {backups.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-3">
            Cliquez &quot;Sauvegarder&quot; pour créer votre premier backup, ou l&apos;icône de rafraichissement pour charger les backups existants.
          </p>
        ) : (
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {backups.map((b, i) => (
              <div key={i} className="flex items-center justify-between py-2 px-3 rounded bg-white/5 text-sm">
                <div>
                  <span className="font-medium">{b.description || "Sauvegarde"}</span>
                  <span className="text-xs text-muted-foreground ml-2">
                    {new Date(b.created_at).toLocaleString("fr-FR")}
                  </span>
                </div>
                <Button variant="ghost" size="sm" onClick={() => restoreBackup(b.created_at)}>
                  Restaurer
                </Button>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

const SERVICE_LABELS = {
  mongodb: "Base de données (MongoDB)",
  cryptocompare: "Données marché (CryptoCompare)",
  kraken: "Données graphiques (Kraken)",
  finnhub: "Actualités (Finnhub)",
  deribit: "Exchange (Deribit)",
  llm_xai: "Intelligence IA (xAI/Grok)"
};

function SystemHealthSection() {
  const [health, setHealth] = useState(null);
  const [checking, setChecking] = useState(false);

  const checkHealth = useCallback(async () => {
    setChecking(true);
    try {
      const res = await axios.get(`${API}/system/health`);
      setHealth(res.data);
    } catch (error) {
      toast.error("Impossible de contacter le serveur");
      setHealth({ status: "error", services: { backend: { status: "error", message: error.message } } });
    } finally {
      setChecking(false);
    }
  }, []);

  const statusIcon = (status) => {
    if (status === "ok") return <CheckCircle2 className="w-4 h-4 text-emerald-500" />;
    if (status === "warning") return <AlertCircle className="w-4 h-4 text-yellow-500" />;
    return <XCircle className="w-4 h-4 text-red-500" />;
  };

  return (
    <Card className="glass border-white/5">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg flex items-center gap-2">
              <Activity className="w-5 h-5 text-primary" />
              Santé du système
            </CardTitle>
            <CardDescription>Diagnostic de tous les services</CardDescription>
          </div>
          <Button variant="outline" size="sm" onClick={checkHealth} disabled={checking}>
            {checking ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4 mr-1" />}
            {checking ? "Test..." : "Tester"}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {!health ? (
          <p className="text-sm text-muted-foreground text-center py-4">
            Cliquez &quot;Tester&quot; pour vérifier l&apos;état des services
          </p>
        ) : (
          <div className="space-y-2">
            {health.status && (
              <div className="flex items-center gap-2 mb-3 pb-3 border-b border-white/5">
                {statusIcon(health.status === "healthy" ? "ok" : "error")}
                <span className="font-medium">
                  {health.status === "healthy" ? "Tous les services fonctionnent" : "Certains services sont dégradés"}
                </span>
              </div>
            )}
            {Object.entries(health.services || {}).map(([key, svc]) => (
              <div key={key} className="flex items-center justify-between py-2 px-3 rounded bg-white/5">
                <div className="flex items-center gap-2">
                  {statusIcon(svc.status)}
                  <span className="text-sm">{SERVICE_LABELS[key] || key}</span>
                </div>
                <span className="text-xs text-muted-foreground max-w-[200px] truncate">{svc.message}</span>
              </div>
            ))}
            {health.timestamp && (
              <p className="text-xs text-muted-foreground text-right mt-2">
                Dernière vérification: {new Date(health.timestamp).toLocaleString("fr-FR")}
              </p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default function SettingsPage() {
  const { user, updateUser } = useAuth();
  const [tradingLevel, setTradingLevel] = useState(user?.trading_level || "beginner");
  const [saving, setSaving] = useState(false);
  const [uploadingAvatar, setUploadingAvatar] = useState(false);
  const fileInputRef = useRef(null);
  
  // Notification preferences (local state for demo)
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [priceAlerts, setPriceAlerts] = useState(true);
  const [tradingSignals, setTradingSignals] = useState(true);

  const getInitials = (name) => {
    return name?.split(" ").map(n => n[0]).join("").toUpperCase() || "U";
  };

  const handleAvatarClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file type
    const validTypes = ["image/jpeg", "image/png", "image/gif", "image/webp"];
    if (!validTypes.includes(file.type)) {
      toast.error("Format non supporté. Utilisez JPG, PNG, GIF ou WebP");
      return;
    }

    // Validate file size (5MB max)
    if (file.size > 5 * 1024 * 1024) {
      toast.error("Fichier trop volumineux (max 5MB)");
      return;
    }

    setUploadingAvatar(true);
    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await axios.post(`${API}/profile/avatar`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      // Update user context with new avatar
      const avatarUrl = `${BACKEND_URL}${response.data.avatar}`;
      updateUser({ ...user, avatar: response.data.avatar });
      toast.success("Photo de profil mise à jour !");
    } catch (error) {
      console.error("Upload error:", error);
      toast.error(error.response?.data?.detail || "Erreur lors de l&apos;upload");
    } finally {
      setUploadingAvatar(false);
      // Reset input
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const handleDeleteAvatar = async () => {
    try {
      await axios.delete(`${API}/profile/avatar`);
      updateUser({ ...user, avatar: null });
      toast.success("Photo de profil supprimée");
    } catch (error) {
      toast.error("Erreur lors de la suppression");
    }
  };

  const handleSaveTradingLevel = async () => {
    setSaving(true);
    try {
      await axios.put(`${API}/settings/trading-level?level=${tradingLevel}`);
      updateUser({ ...user, trading_level: tradingLevel });
      toast.success("Niveau de trading mis à jour");
    } catch (error) {
      toast.error("Erreur lors de la sauvegarde");
    } finally {
      setSaving(false);
    }
  };

  // Get avatar URL
  const getAvatarUrl = () => {
    if (user?.avatar) {
      return `${BACKEND_URL}${user.avatar}`;
    }
    return null;
  };

  return (
    <div className="space-y-6 max-w-3xl" data-testid="settings-page">
      {/* Header */}
      <div>
        <h1 className="text-2xl md:text-3xl font-bold font-manrope">Paramètres</h1>
        <p className="text-muted-foreground">
          Gérez votre profil et vos préférences
        </p>
      </div>

      {/* Profile Section with Avatar */}
      <Card className="glass border-white/5">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <User className="w-5 h-5 text-primary" />
            Profil
          </CardTitle>
          <CardDescription>Informations de votre compte</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Avatar Section */}
          <div className="flex flex-col sm:flex-row items-center gap-6">
            <div className="relative group">
              <Avatar className="w-24 h-24 border-2 border-white/10">
                <AvatarImage src={getAvatarUrl()} alt={user?.name} />
                <AvatarFallback className="bg-secondary text-2xl">
                  {getInitials(user?.name)}
                </AvatarFallback>
              </Avatar>
              
              {/* Upload overlay */}
              <button
                onClick={handleAvatarClick}
                disabled={uploadingAvatar}
                className="absolute inset-0 bg-black/60 rounded-full opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center cursor-pointer"
              >
                {uploadingAvatar ? (
                  <Loader2 className="w-6 h-6 text-white animate-spin" />
                ) : (
                  <Camera className="w-6 h-6 text-white" />
                )}
              </button>
              
              <input
                ref={fileInputRef}
                type="file"
                accept="image/jpeg,image/png,image/gif,image/webp"
                onChange={handleFileChange}
                className="hidden"
              />
            </div>

            <div className="flex-1 text-center sm:text-left">
              <h3 className="font-semibold text-lg">{user?.name}</h3>
              <p className="text-muted-foreground text-sm">{user?.email}</p>
              <div className="flex flex-wrap gap-2 mt-3 justify-center sm:justify-start">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleAvatarClick}
                  disabled={uploadingAvatar}
                  className="border-white/10 hover:bg-white/5"
                >
                  {uploadingAvatar ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <Camera className="w-4 h-4 mr-2" />
                  )}
                  Changer la photo
                </Button>
                {user?.avatar && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleDeleteAvatar}
                    className="text-destructive hover:text-destructive hover:bg-destructive/10"
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    Supprimer
                  </Button>
                )}
              </div>
            </div>
          </div>

          <Separator className="bg-white/5" />

          {/* User Info */}
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

      {/* Admin Section - Only visible for admins */}
      {user?.is_admin && (
        <Card className="glass border-amber-500/30 bg-amber-500/5">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Settings2 className="w-5 h-5 text-amber-500" />
              Administration
            </CardTitle>
            <CardDescription>Accès réservé aux administrateurs</CardDescription>
          </CardHeader>
          <CardContent>
            <Link to="/dashboard/admin">
              <Button className="w-full bg-amber-600 hover:bg-amber-700 text-white">
                <Shield className="w-4 h-4 mr-2" />
                Accéder au tableau de bord admin
                <ExternalLink className="w-4 h-4 ml-2" />
              </Button>
            </Link>
            <p className="text-xs text-muted-foreground mt-3">
              Gérez les utilisateurs, surveillez les APIs et consultez les logs d'erreurs.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Backup & Restore */}
      <SettingsBackupSection />

      {/* System Health */}
      <SystemHealthSection />

      {/* About */}
      <Card className="glass border-white/5">
        <CardHeader>
          <CardTitle className="text-lg">À propos</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center justify-between py-2">
            <span className="text-muted-foreground">Version</span>
            <span className="font-mono">{BUILD_INFO.version}</span>
          </div>
          <Separator className="bg-white/5" />
          <div className="flex items-center justify-between py-2">
            <span className="text-muted-foreground">Commit</span>
            <span className="font-mono text-xs bg-white/5 px-2 py-1 rounded">{BUILD_INFO.commitHash}</span>
          </div>
          <Separator className="bg-white/5" />
          <div className="flex items-center justify-between py-2">
            <span className="text-muted-foreground">Dernière mise à jour</span>
            <span className="text-sm">{BUILD_INFO.commitDate} à {BUILD_INFO.commitTime}</span>
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
