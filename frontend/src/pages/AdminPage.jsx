import { useState, useEffect } from "react";
import { API, useAuth } from "../App";
import { Navigate } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import {
  Shield,
  Users,
  TrendingUp,
  MessageCircle,
  Bell,
  Target,
  Trash2,
  RefreshCw,
  UserCog,
  Activity,
  Server,
  FileWarning,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
  Wifi,
  WifiOff,
  Loader2,
  Database,
  Zap,
  Filter,
  ChevronDown
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { ScrollArea } from "../components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Progress } from "../components/ui/progress";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui/table";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "../components/ui/alert-dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "../components/ui/collapsible";

// Status indicator component
const StatusIndicator = ({ status }) => {
  const config = {
    online: { color: "bg-emerald-500", pulse: true, label: "En ligne" },
    offline: { color: "bg-red-500", pulse: false, label: "Hors ligne" },
    error: { color: "bg-red-500", pulse: false, label: "Erreur" },
    timeout: { color: "bg-orange-500", pulse: false, label: "Timeout" },
    rate_limited: { color: "bg-yellow-500", pulse: false, label: "Limité" },
    not_configured: { color: "bg-gray-500", pulse: false, label: "Non configuré" },
  };
  
  const { color, pulse } = config[status] || config.offline;
  
  return (
    <div className="relative flex items-center">
      <div className={`w-3 h-3 rounded-full ${color} ${pulse ? "animate-pulse" : ""}`} />
      {pulse && (
        <div className={`absolute w-3 h-3 rounded-full ${color} animate-ping opacity-75`} />
      )}
    </div>
  );
};

// API Card component
const ApiCard = ({ api }) => {
  const statusConfig = {
    online: { icon: CheckCircle, color: "text-emerald-500", bg: "bg-emerald-500/10" },
    offline: { icon: XCircle, color: "text-red-500", bg: "bg-red-500/10" },
    error: { icon: XCircle, color: "text-red-500", bg: "bg-red-500/10" },
    timeout: { icon: Clock, color: "text-orange-500", bg: "bg-orange-500/10" },
    rate_limited: { icon: AlertTriangle, color: "text-yellow-500", bg: "bg-yellow-500/10" },
    not_configured: { icon: WifiOff, color: "text-gray-500", bg: "bg-gray-500/10" },
  };
  
  const config = statusConfig[api.status] || statusConfig.offline;
  const Icon = config.icon;
  
  return (
    <Card className={`glass border-white/5 ${config.bg}`}>
      <CardContent className="pt-6">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <StatusIndicator status={api.status} />
            <div>
              <h3 className="font-semibold">{api.name}</h3>
              <p className="text-xs text-muted-foreground mt-0.5">{api.message}</p>
            </div>
          </div>
          <Icon className={`w-5 h-5 ${config.color}`} />
        </div>
        {api.response_time_ms && (
          <div className="mt-3 flex items-center gap-2">
            <Zap className="w-3 h-3 text-muted-foreground" />
            <span className="text-xs text-muted-foreground">
              {api.response_time_ms}ms
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

// Log entry component
const LogEntry = ({ log }) => {
  const [expanded, setExpanded] = useState(false);
  
  const severityConfig = {
    error: { icon: XCircle, color: "text-red-500", bg: "bg-red-500/10" },
    warning: { icon: AlertTriangle, color: "text-yellow-500", bg: "bg-yellow-500/10" },
    info: { icon: Activity, color: "text-blue-500", bg: "bg-blue-500/10" },
  };
  
  const config = severityConfig[log.error_type] || severityConfig.error;
  const Icon = config.icon;
  
  const formatDate = (dateStr) => {
    if (!dateStr) return "-";
    const date = new Date(dateStr);
    return date.toLocaleString("fr-FR", {
      day: "2-digit",
      month: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit"
    });
  };
  
  return (
    <Collapsible open={expanded} onOpenChange={setExpanded}>
      <CollapsibleTrigger asChild>
        <div className={`p-3 rounded-lg cursor-pointer hover:bg-white/5 transition-colors ${config.bg}`}>
          <div className="flex items-start gap-3">
            <Icon className={`w-4 h-4 mt-0.5 ${config.color}`} />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <Badge variant="outline" className="text-xs">
                  {log.source}
                </Badge>
                <span className="text-xs text-muted-foreground">
                  {formatDate(log.timestamp)}
                </span>
              </div>
              <p className="text-sm mt-1 truncate">{log.message}</p>
            </div>
            <ChevronDown className={`w-4 h-4 text-muted-foreground transition-transform ${expanded ? "rotate-180" : ""}`} />
          </div>
        </div>
      </CollapsibleTrigger>
      <CollapsibleContent>
        <div className="ml-7 p-3 bg-black/20 rounded-lg mt-1 text-xs font-mono">
          {log.details && Object.keys(log.details).length > 0 ? (
            <pre className="whitespace-pre-wrap overflow-x-auto">
              {JSON.stringify(log.details, null, 2)}
            </pre>
          ) : (
            <p className="text-muted-foreground">Aucun détail supplémentaire</p>
          )}
          {log.user_email && (
            <p className="mt-2 text-muted-foreground">
              Utilisateur: {log.user_email}
            </p>
          )}
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
};

export default function AdminPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState("overview");
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  
  // API Health state
  const [apiHealth, setApiHealth] = useState(null);
  const [loadingHealth, setLoadingHealth] = useState(false);
  
  // Logs state
  const [logs, setLogs] = useState([]);
  const [logStats, setLogStats] = useState(null);
  const [loadingLogs, setLoadingLogs] = useState(false);
  const [logFilter, setLogFilter] = useState("all");
  const [sourceFilter, setSourceFilter] = useState("all");

  const fetchData = async () => {
    try {
      const [statsRes, usersRes] = await Promise.all([
        axios.get(`${API}/admin/stats`),
        axios.get(`${API}/admin/users`)
      ]);
      setStats(statsRes.data || {});
      setUsers(Array.isArray(usersRes.data) ? usersRes.data : []);
    } catch (error) {
      console.error("Error fetching admin data:", error);
      toast.error("Erreur lors du chargement des données admin");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const fetchApiHealth = async () => {
    setLoadingHealth(true);
    try {
      const response = await axios.get(`${API}/admin/api-health`);
      setApiHealth(response.data);
    } catch (error) {
      console.error("Error fetching API health:", error);
      toast.error("Erreur lors du test des API");
    } finally {
      setLoadingHealth(false);
    }
  };

  const fetchLogs = async () => {
    setLoadingLogs(true);
    try {
      const params = new URLSearchParams();
      params.append("limit", "100");
      if (logFilter !== "all") params.append("error_type", logFilter);
      if (sourceFilter !== "all") params.append("source", sourceFilter);
      
      const response = await axios.get(`${API}/admin/logs?${params}`);
      const data = response.data || {};
      setLogs(Array.isArray(data.logs) ? data.logs : []);
      setLogStats(data.stats || null);
    } catch (error) {
      console.error("Error fetching logs:", error);
      // Don't show error toast for logs - might be empty
    } finally {
      setLoadingLogs(false);
    }
  };

  const clearOldLogs = async (days) => {
    try {
      const response = await axios.delete(`${API}/admin/logs?older_than_days=${days}`);
      toast.success(response.data.message);
      fetchLogs();
    } catch (error) {
      toast.error("Erreur lors de la suppression des logs");
    }
  };

  useEffect(() => {
    if (user?.is_admin) {
      fetchData();
    }
  }, [user?.is_admin]);

  useEffect(() => {
    if (activeTab === "apis" && !apiHealth) {
      fetchApiHealth();
    }
    if (activeTab === "logs") {
      fetchLogs();
    }
  }, [activeTab]);

  useEffect(() => {
    if (activeTab === "logs") {
      fetchLogs();
    }
  }, [logFilter, sourceFilter]);

  // Redirect if not admin - AFTER all hooks
  if (!user?.is_admin) {
    return <Navigate to="/" replace />;
  }

  const handleRefresh = () => {
    setRefreshing(true);
    if (activeTab === "overview" || activeTab === "users") {
      fetchData();
    } else if (activeTab === "apis") {
      fetchApiHealth();
      setRefreshing(false);
    } else if (activeTab === "logs") {
      fetchLogs();
      setRefreshing(false);
    }
    toast.success("Données actualisées");
  };

  const handleDeleteUser = async (userId, userName) => {
    try {
      await axios.delete(`${API}/admin/users/${userId}`);
      toast.success(`Utilisateur ${userName} supprimé`);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erreur lors de la suppression");
    }
  };

  const handleToggleAdmin = async (userId, currentStatus, userName) => {
    try {
      await axios.put(`${API}/admin/users/${userId}/admin?is_admin=${!currentStatus}`);
      toast.success(`Statut admin ${!currentStatus ? "accordé à" : "retiré de"} ${userName}`);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erreur lors de la modification");
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-48 bg-white/5 rounded animate-pulse" />
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {[1, 2, 3, 4, 5].map(i => (
            <div key={i} className="h-24 bg-white/5 rounded-xl animate-pulse" />
          ))}
        </div>
        <div className="h-96 bg-white/5 rounded-xl animate-pulse" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="admin-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-violet-500/20 flex items-center justify-center">
            <Shield className="w-6 h-6 text-violet-400" />
          </div>
          <div>
            <h1 className="text-2xl md:text-3xl font-bold font-manrope">Administration</h1>
            <p className="text-muted-foreground">Gérez la plateforme BULL SAGE</p>
          </div>
        </div>
        <Button
          variant="outline"
          onClick={handleRefresh}
          disabled={refreshing || loadingHealth || loadingLogs}
          className="border-white/10 hover:bg-white/5"
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${(refreshing || loadingHealth || loadingLogs) ? "animate-spin" : ""}`} />
          Actualiser
        </Button>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-4 bg-white/5">
          <TabsTrigger value="overview" className="gap-2">
            <Activity className="w-4 h-4" />
            <span className="hidden sm:inline">Vue d&apos;ensemble</span>
          </TabsTrigger>
          <TabsTrigger value="users" className="gap-2">
            <Users className="w-4 h-4" />
            <span className="hidden sm:inline">Utilisateurs</span>
          </TabsTrigger>
          <TabsTrigger value="apis" className="gap-2">
            <Server className="w-4 h-4" />
            <span className="hidden sm:inline">APIs</span>
          </TabsTrigger>
          <TabsTrigger value="logs" className="gap-2">
            <FileWarning className="w-4 h-4" />
            <span className="hidden sm:inline">Logs</span>
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6 mt-6">
          {/* Stats Cards */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <Card className="glass border-white/5">
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
                    <Users className="w-5 h-5 text-blue-500" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold font-mono">{stats?.total_users || 0}</p>
                    <p className="text-xs text-muted-foreground">Utilisateurs</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="glass border-white/5">
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-emerald-500/10 flex items-center justify-center">
                    <TrendingUp className="w-5 h-5 text-emerald-500" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold font-mono">{stats?.total_trades || 0}</p>
                    <p className="text-xs text-muted-foreground">Paper Trades</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="glass border-white/5">
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-violet-500/10 flex items-center justify-center">
                    <MessageCircle className="w-5 h-5 text-violet-500" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold font-mono">{stats?.total_signals || 0}</p>
                    <p className="text-xs text-muted-foreground">Signaux</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="glass border-white/5">
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-yellow-500/10 flex items-center justify-center">
                    <Bell className="w-5 h-5 text-yellow-500" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold font-mono">{stats?.total_alerts || 0}</p>
                    <p className="text-xs text-muted-foreground">Alertes</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="glass border-white/5">
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-rose-500/10 flex items-center justify-center">
                    <Target className="w-5 h-5 text-rose-500" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold font-mono">{stats?.total_strategies || 0}</p>
                    <p className="text-xs text-muted-foreground">Stratégies</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Quick API Status */}
          {apiHealth && (
            <Card className="glass border-white/5">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Server className="w-5 h-5 text-primary" />
                  État des APIs
                </CardTitle>
                <CardDescription>
                  {apiHealth.summary.online}/{apiHealth.summary.total} services en ligne
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Progress 
                  value={apiHealth.summary.health_percentage} 
                  className="h-2"
                />
                <p className="text-sm text-muted-foreground mt-2">
                  Santé globale: {apiHealth.summary.health_percentage}%
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Users Tab */}
        <TabsContent value="users" className="mt-6">
          <Card className="glass border-white/5">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Users className="w-5 h-5 text-blue-500" />
                Gestion des Utilisateurs
              </CardTitle>
              <CardDescription>{users.length} utilisateur(s) inscrit(s)</CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[500px]">
                <Table>
                  <TableHeader>
                    <TableRow className="border-white/5 hover:bg-transparent">
                      <TableHead>Utilisateur</TableHead>
                      <TableHead>Niveau</TableHead>
                      <TableHead>Solde Virtuel</TableHead>
                      <TableHead>Inscrit le</TableHead>
                      <TableHead>Statut</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {users.map((u) => (
                      <TableRow key={u.id} className="border-white/5 hover:bg-white/5">
                        <TableCell>
                          <div>
                            <p className="font-medium">{u.name}</p>
                            <p className="text-xs text-muted-foreground">{u.email}</p>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="secondary" className="bg-white/5 capitalize">
                            {u.trading_level}
                          </Badge>
                        </TableCell>
                        <TableCell className="font-mono">
                          ${u.paper_balance?.toLocaleString() || "10,000"}
                        </TableCell>
                        <TableCell className="text-muted-foreground">
                          {new Date(u.created_at).toLocaleDateString("fr-FR")}
                        </TableCell>
                        <TableCell>
                          {u.is_admin ? (
                            <Badge className="bg-violet-500/20 text-violet-400">
                              <Shield className="w-3 h-3 mr-1" />
                              Admin
                            </Badge>
                          ) : (
                            <Badge variant="secondary" className="bg-white/5">
                              Utilisateur
                            </Badge>
                          )}
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex items-center justify-end gap-2">
                            {u.id !== user?.id && (
                              <>
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  onClick={() => handleToggleAdmin(u.id, u.is_admin, u.name)}
                                  className="hover:bg-violet-500/10 hover:text-violet-400"
                                  title={u.is_admin ? "Retirer admin" : "Promouvoir admin"}
                                >
                                  <UserCog className="w-4 h-4" />
                                </Button>
                                
                                <AlertDialog>
                                  <AlertDialogTrigger asChild>
                                    <Button
                                      variant="ghost"
                                      size="icon"
                                      className="hover:bg-destructive/10 hover:text-destructive"
                                    >
                                      <Trash2 className="w-4 h-4" />
                                    </Button>
                                  </AlertDialogTrigger>
                                  <AlertDialogContent className="glass border-white/10">
                                    <AlertDialogHeader>
                                      <AlertDialogTitle>Supprimer l&apos;utilisateur?</AlertDialogTitle>
                                      <AlertDialogDescription>
                                        Cette action supprimera définitivement {u.name} et toutes ses données (trades, stratégies, alertes).
                                      </AlertDialogDescription>
                                    </AlertDialogHeader>
                                    <AlertDialogFooter>
                                      <AlertDialogCancel className="border-white/10">Annuler</AlertDialogCancel>
                                      <AlertDialogAction
                                        onClick={() => handleDeleteUser(u.id, u.name)}
                                        className="bg-destructive hover:bg-destructive/90"
                                      >
                                        Supprimer
                                      </AlertDialogAction>
                                    </AlertDialogFooter>
                                  </AlertDialogContent>
                                </AlertDialog>
                              </>
                            )}
                            {u.id === user?.id && (
                              <span className="text-xs text-muted-foreground">Vous</span>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        {/* APIs Tab */}
        <TabsContent value="apis" className="mt-6 space-y-6">
          {loadingHealth ? (
            <div className="flex items-center justify-center py-12">
              <div className="flex flex-col items-center gap-4">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
                <p className="text-muted-foreground">Test des API en cours...</p>
              </div>
            </div>
          ) : apiHealth ? (
            <>
              {/* Health Summary */}
              <Card className="glass border-white/5">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="text-lg flex items-center gap-2">
                        <Wifi className="w-5 h-5 text-primary" />
                        Santé des Services
                      </CardTitle>
                      <CardDescription>
                        Dernière vérification: {new Date(apiHealth.timestamp).toLocaleString("fr-FR")}
                      </CardDescription>
                    </div>
                    <div className="text-right">
                      <p className="text-3xl font-bold font-mono">
                        {apiHealth.summary.health_percentage}%
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {apiHealth.summary.online}/{apiHealth.summary.total} en ligne
                      </p>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <Progress 
                    value={apiHealth.summary.health_percentage} 
                    className="h-3"
                  />
                </CardContent>
              </Card>

              {/* API Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {apiHealth.apis.map((api) => (
                  <ApiCard key={api.name} api={api} />
                ))}
              </div>

              {/* API Legend */}
              <Card className="glass border-white/5">
                <CardContent className="pt-6">
                  <div className="flex flex-wrap gap-4">
                    <div className="flex items-center gap-2">
                      <StatusIndicator status="online" />
                      <span className="text-sm">En ligne</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <StatusIndicator status="rate_limited" />
                      <span className="text-sm">Limite atteinte</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <StatusIndicator status="timeout" />
                      <span className="text-sm">Timeout</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <StatusIndicator status="offline" />
                      <span className="text-sm">Hors ligne</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <StatusIndicator status="not_configured" />
                      <span className="text-sm">Non configuré</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </>
          ) : (
            <Card className="glass border-white/5">
              <CardContent className="py-12 text-center">
                <Server className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground">
                  Cliquez sur Actualiser pour tester les API
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Logs Tab */}
        <TabsContent value="logs" className="mt-6 space-y-6">
          {/* Log Stats */}
          {logStats && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Card className="glass border-white/5">
                <CardContent className="pt-6">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-red-500/10 flex items-center justify-center">
                      <FileWarning className="w-5 h-5 text-red-500" />
                    </div>
                    <div>
                      <p className="text-2xl font-bold font-mono">{logStats.total}</p>
                      <p className="text-xs text-muted-foreground">Total logs</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="glass border-white/5">
                <CardContent className="pt-6">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-orange-500/10 flex items-center justify-center">
                      <Clock className="w-5 h-5 text-orange-500" />
                    </div>
                    <div>
                      <p className="text-2xl font-bold font-mono">{logStats.today}</p>
                      <p className="text-xs text-muted-foreground">Aujourd&apos;hui</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="glass border-white/5 col-span-2">
                <CardContent className="pt-6">
                  <p className="text-sm text-muted-foreground mb-2">Types d&apos;erreurs</p>
                  <div className="flex flex-wrap gap-2">
                    {logStats.error_types?.map((e) => (
                      <Badge key={e.type} variant="secondary" className="bg-white/5">
                        {e.type}: {e.count}
                      </Badge>
                    ))}
                    {(!logStats.error_types || logStats.error_types.length === 0) && (
                      <span className="text-xs text-muted-foreground">Aucune erreur</span>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Filters & Actions */}
          <Card className="glass border-white/5">
            <CardContent className="pt-6">
              <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
                <div className="flex flex-wrap gap-3">
                  <Select value={logFilter} onValueChange={setLogFilter}>
                    <SelectTrigger className="w-[140px] bg-black/20 border-white/10">
                      <Filter className="w-4 h-4 mr-2" />
                      <SelectValue placeholder="Type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Tous types</SelectItem>
                      <SelectItem value="error">Erreurs</SelectItem>
                      <SelectItem value="warning">Avertissements</SelectItem>
                      <SelectItem value="info">Info</SelectItem>
                    </SelectContent>
                  </Select>

                  <Select value={sourceFilter} onValueChange={setSourceFilter}>
                    <SelectTrigger className="w-[160px] bg-black/20 border-white/10">
                      <Database className="w-4 h-4 mr-2" />
                      <SelectValue placeholder="Source" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Toutes sources</SelectItem>
                      <SelectItem value="frontend">Frontend</SelectItem>
                      <SelectItem value="backend">Backend</SelectItem>
                      <SelectItem value="api">API externe</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <AlertDialog>
                  <AlertDialogTrigger asChild>
                    <Button variant="outline" size="sm" className="border-white/10">
                      <Trash2 className="w-4 h-4 mr-2" />
                      Nettoyer
                    </Button>
                  </AlertDialogTrigger>
                  <AlertDialogContent className="glass border-white/10">
                    <AlertDialogHeader>
                      <AlertDialogTitle>Nettoyer les logs?</AlertDialogTitle>
                      <AlertDialogDescription>
                        Choisissez la période des logs à supprimer.
                      </AlertDialogDescription>
                    </AlertDialogHeader>
                    <div className="flex flex-col gap-2 my-4">
                      <Button variant="outline" onClick={() => clearOldLogs(7)}>
                        Logs de plus de 7 jours
                      </Button>
                      <Button variant="outline" onClick={() => clearOldLogs(30)}>
                        Logs de plus de 30 jours
                      </Button>
                      <Button variant="destructive" onClick={() => clearOldLogs(0)}>
                        Supprimer tous les logs
                      </Button>
                    </div>
                    <AlertDialogFooter>
                      <AlertDialogCancel className="border-white/10">Annuler</AlertDialogCancel>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
              </div>
            </CardContent>
          </Card>

          {/* Logs List */}
          <Card className="glass border-white/5">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <FileWarning className="w-5 h-5 text-red-500" />
                Journal des erreurs
              </CardTitle>
              <CardDescription>
                {logs.length} log(s) trouvé(s)
              </CardDescription>
            </CardHeader>
            <CardContent>
              {loadingLogs ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="w-6 h-6 animate-spin text-primary" />
                </div>
              ) : logs.length > 0 ? (
                <ScrollArea className="h-[500px]">
                  <div className="space-y-2">
                    {logs.map((log, index) => (
                      <LogEntry key={index} log={log} />
                    ))}
                  </div>
                </ScrollArea>
              ) : (
                <div className="text-center py-12">
                  <CheckCircle className="w-12 h-12 mx-auto text-emerald-500 mb-4" />
                  <p className="text-lg font-medium">Aucune erreur!</p>
                  <p className="text-muted-foreground">Tout fonctionne correctement</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
