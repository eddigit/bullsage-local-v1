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
  Activity
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
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

export default function AdminPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = async () => {
    try {
      const [statsRes, usersRes] = await Promise.all([
        axios.get(`${API}/admin/stats`),
        axios.get(`${API}/admin/users`)
      ]);
      setStats(statsRes.data);
      setUsers(usersRes.data);
    } catch (error) {
      console.error("Error fetching admin data:", error);
      toast.error("Erreur lors du chargement des données admin");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    if (user?.is_admin) {
      fetchData();
    }
  }, [user?.is_admin]);

  // Redirect if not admin - AFTER all hooks
  if (!user?.is_admin) {
    return <Navigate to="/" replace />;
  }

  const handleRefresh = () => {
    setRefreshing(true);
    fetchData();
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
          disabled={refreshing}
          className="border-white/10 hover:bg-white/5"
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? "animate-spin" : ""}`} />
          Actualiser
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card className="glass border-white/5">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
                <Users className="w-5 h-5 text-blue-500" />
              </div>
              <div>
                <p className="text-2xl font-bold font-mono">{stats?.users || 0}</p>
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
                <p className="text-2xl font-bold font-mono">{stats?.paper_trades || 0}</p>
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
                <p className="text-2xl font-bold font-mono">{stats?.ai_chats || 0}</p>
                <p className="text-xs text-muted-foreground">Chats IA</p>
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
                <p className="text-2xl font-bold font-mono">{stats?.alerts || 0}</p>
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
                <p className="text-2xl font-bold font-mono">{stats?.strategies || 0}</p>
                <p className="text-xs text-muted-foreground">Stratégies</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Users Table */}
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
    </div>
  );
}
