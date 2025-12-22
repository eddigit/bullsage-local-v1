import { useState, useEffect } from "react";
import axios from "axios";
import { toast } from "sonner";
import {
  Mail,
  Send,
  Settings,
  Clock,
  Users,
  CheckCircle,
  XCircle,
  RefreshCw,
  Play,
  Eye,
  Loader2,
  Calendar,
  AlertTriangle
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Switch } from "../components/ui/switch";
import { Badge } from "../components/ui/badge";
import { Separator } from "../components/ui/separator";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../components/ui/dialog";
import { API } from "../App";

export default function NewsletterAdminPage() {
  const [config, setConfig] = useState({
    host: "smtp.gmail.com",
    port: 587,
    username: "",
    password: "",
    from_email: "",
    enabled: false,
    send_time: "09:00"
  });
  const [logs, setLogs] = useState([]);
  const [subscribers, setSubscribers] = useState({ total_users: 0, subscribed: 0, unsubscribed: 0 });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [sending, setSending] = useState(false);
  const [testEmail, setTestEmail] = useState("");
  const [showTestDialog, setShowTestDialog] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [configRes, logsRes, subsRes] = await Promise.all([
        axios.get(`${API}/admin/newsletter/config`),
        axios.get(`${API}/admin/newsletter/logs?limit=10`),
        axios.get(`${API}/admin/newsletter/subscribers`)
      ]);
      
      if (configRes.data && configRes.data.host) {
        setConfig(prev => ({ ...prev, ...configRes.data }));
      }
      setLogs(logsRes.data || []);
      setSubscribers(subsRes.data);
    } catch (error) {
      console.error("Load error:", error);
    } finally {
      setLoading(false);
    }
  };

  const saveConfig = async () => {
    setSaving(true);
    try {
      await axios.post(`${API}/admin/newsletter/config`, config);
      toast.success("Configuration sauvegardée !");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erreur de sauvegarde");
    } finally {
      setSaving(false);
    }
  };

  const sendTestNewsletter = async () => {
    setSending(true);
    try {
      const params = testEmail ? `?email=${encodeURIComponent(testEmail)}` : "";
      await axios.post(`${API}/admin/newsletter/test${params}`);
      toast.success("Newsletter de test envoyée !");
      setShowTestDialog(false);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erreur d'envoi");
    } finally {
      setSending(false);
    }
  };

  const sendNow = async () => {
    if (!window.confirm("Envoyer la newsletter à TOUS les abonnés maintenant ?")) return;
    
    setSending(true);
    try {
      const response = await axios.post(`${API}/admin/newsletter/send-now`);
      toast.success(`Newsletter envoyée ! ${response.data.sent} envoyés, ${response.data.failed} échecs`);
      loadData(); // Refresh logs
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erreur d'envoi");
    } finally {
      setSending(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold font-manrope flex items-center gap-3">
            <Mail className="w-8 h-8 text-primary" />
            Newsletter
          </h1>
          <p className="text-muted-foreground mt-1">
            Configuration de la newsletter quotidienne
          </p>
        </div>
        
        <Button variant="outline" onClick={loadData}>
          <RefreshCw className="w-4 h-4 mr-2" />
          Actualiser
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card className="glass border-white/5">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Abonnés</p>
                <p className="text-2xl font-bold text-emerald-500">{subscribers.subscribed}</p>
              </div>
              <Users className="w-8 h-8 text-emerald-500/50" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="glass border-white/5">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Désabonnés</p>
                <p className="text-2xl font-bold text-red-500">{subscribers.unsubscribed}</p>
              </div>
              <XCircle className="w-8 h-8 text-red-500/50" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="glass border-white/5">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Utilisateurs</p>
                <p className="text-2xl font-bold">{subscribers.total_users}</p>
              </div>
              <Users className="w-8 h-8 text-primary/50" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* SMTP Configuration */}
      <Card className="glass border-white/5">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg flex items-center gap-2">
                <Settings className="w-5 h-5 text-primary" />
                Configuration SMTP
              </CardTitle>
              <CardDescription>Paramètres Gmail pour l'envoi des newsletters</CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">Activé</span>
              <Switch
                checked={config.enabled}
                onCheckedChange={(checked) => setConfig({ ...config, enabled: checked })}
              />
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Serveur SMTP</Label>
              <Input
                value={config.host}
                onChange={(e) => setConfig({ ...config, host: e.target.value })}
                placeholder="smtp.gmail.com"
                className="bg-black/20 border-white/10"
              />
            </div>
            <div className="space-y-2">
              <Label>Port</Label>
              <Input
                type="number"
                value={config.port}
                onChange={(e) => setConfig({ ...config, port: parseInt(e.target.value) })}
                placeholder="587"
                className="bg-black/20 border-white/10"
              />
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Email Gmail</Label>
              <Input
                type="email"
                value={config.username}
                onChange={(e) => setConfig({ ...config, username: e.target.value })}
                placeholder="votre-email@gmail.com"
                className="bg-black/20 border-white/10"
              />
            </div>
            <div className="space-y-2">
              <Label>Mot de passe d'application</Label>
              <Input
                type="password"
                value={config.password}
                onChange={(e) => setConfig({ ...config, password: e.target.value })}
                placeholder="••••••••"
                className="bg-black/20 border-white/10"
              />
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Email expéditeur (optionnel)</Label>
              <Input
                type="email"
                value={config.from_email}
                onChange={(e) => setConfig({ ...config, from_email: e.target.value })}
                placeholder="newsletter@bullsage.com"
                className="bg-black/20 border-white/10"
              />
            </div>
            <div className="space-y-2">
              <Label>Heure d'envoi</Label>
              <Input
                type="time"
                value={config.send_time}
                onChange={(e) => setConfig({ ...config, send_time: e.target.value })}
                className="bg-black/20 border-white/10"
              />
            </div>
          </div>
          
          <div className="flex items-start gap-2 p-3 bg-yellow-500/10 rounded-lg">
            <AlertTriangle className="w-5 h-5 text-yellow-500 mt-0.5 flex-shrink-0" />
            <div className="text-sm">
              <p className="text-yellow-200 font-medium">Configuration Gmail</p>
              <p className="text-muted-foreground">
                Pour utiliser Gmail, vous devez créer un <strong>mot de passe d'application</strong> :
                <br />1. Allez dans les paramètres Google → Sécurité
                <br />2. Activez la validation en 2 étapes
                <br />3. Créez un mot de passe d'application pour "Mail"
              </p>
            </div>
          </div>
          
          <div className="flex justify-end gap-2">
            <Button onClick={saveConfig} disabled={saving} className="bg-primary hover:bg-primary/90 text-black">
              {saving ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <CheckCircle className="w-4 h-4 mr-2" />}
              Sauvegarder
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Actions */}
      <Card className="glass border-white/5">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Send className="w-5 h-5 text-primary" />
            Actions
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-3">
            <Dialog open={showTestDialog} onOpenChange={setShowTestDialog}>
              <DialogTrigger asChild>
                <Button variant="outline" className="border-white/10">
                  <Eye className="w-4 h-4 mr-2" />
                  Envoyer un test
                </Button>
              </DialogTrigger>
              <DialogContent className="glass border-white/10">
                <DialogHeader>
                  <DialogTitle>Newsletter de test</DialogTitle>
                  <DialogDescription>
                    Envoyez une newsletter de test pour vérifier le rendu et la configuration.
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="space-y-2">
                    <Label>Email de destination (optionnel)</Label>
                    <Input
                      type="email"
                      value={testEmail}
                      onChange={(e) => setTestEmail(e.target.value)}
                      placeholder="Laissez vide pour utiliser votre email admin"
                      className="bg-black/20 border-white/10"
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="ghost" onClick={() => setShowTestDialog(false)}>Annuler</Button>
                  <Button onClick={sendTestNewsletter} disabled={sending} className="bg-primary text-black">
                    {sending ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Send className="w-4 h-4 mr-2" />}
                    Envoyer le test
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
            
            <Button 
              onClick={sendNow} 
              disabled={sending || !config.enabled}
              className="bg-emerald-600 hover:bg-emerald-700"
            >
              {sending ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Play className="w-4 h-4 mr-2" />}
              Envoyer maintenant à tous
            </Button>
          </div>
          
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Clock className="w-4 h-4" />
            <span>Prochain envoi automatique : <strong>{config.send_time}</strong> (Europe/Paris)</span>
          </div>
        </CardContent>
      </Card>

      {/* Logs */}
      <Card className="glass border-white/5">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Calendar className="w-5 h-5 text-primary" />
            Historique des envois
          </CardTitle>
        </CardHeader>
        <CardContent>
          {logs.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Mail className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>Aucune newsletter envoyée</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Abonnés</TableHead>
                  <TableHead>Envoyés</TableHead>
                  <TableHead>Échecs</TableHead>
                  <TableHead>Statut</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {logs.map((log, index) => (
                  <TableRow key={index}>
                    <TableCell>
                      {new Date(log.sent_at).toLocaleDateString("fr-FR", {
                        day: "2-digit",
                        month: "2-digit",
                        year: "numeric",
                        hour: "2-digit",
                        minute: "2-digit"
                      })}
                    </TableCell>
                    <TableCell>{log.subscribers_count}</TableCell>
                    <TableCell className="text-emerald-500">{log.sent}</TableCell>
                    <TableCell className="text-red-500">{log.failed}</TableCell>
                    <TableCell>
                      {log.failed === 0 ? (
                        <Badge className="bg-emerald-500/20 text-emerald-500">Succès</Badge>
                      ) : log.sent > 0 ? (
                        <Badge className="bg-yellow-500/20 text-yellow-500">Partiel</Badge>
                      ) : (
                        <Badge className="bg-red-500/20 text-red-500">Échec</Badge>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
