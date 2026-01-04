import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  Clock, 
  RefreshCw,
  Activity,
  Cpu,
  Database,
  Zap,
  TrendingUp,
  Globe
} from 'lucide-react';
import { useToast } from '../hooks/use-toast';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const StatusIcon = ({ status }) => {
  switch (status) {
    case 'operational':
      return <CheckCircle2 className="w-5 h-5 text-green-500" />;
    case 'degraded':
      return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
    case 'down':
      return <XCircle className="w-5 h-5 text-red-500" />;
    case 'standby':
      return <Clock className="w-5 h-5 text-gray-400" />;
    default:
      return <AlertTriangle className="w-5 h-5 text-gray-400" />;
  }
};

const StatusBadge = ({ status }) => {
  const variants = {
    operational: 'bg-green-500/10 text-green-500 border-green-500/20',
    degraded: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
    down: 'bg-red-500/10 text-red-500 border-red-500/20',
    standby: 'bg-gray-500/10 text-gray-400 border-gray-500/20'
  };
  
  const labels = {
    operational: 'Opérationnel',
    degraded: 'Dégradé',
    down: 'Hors ligne',
    standby: 'En standby'
  };
  
  return (
    <Badge 
      variant="outline" 
      className={`${variants[status] || variants.standby} font-medium`}
    >
      {labels[status] || 'Inconnu'}
    </Badge>
  );
};

const HealthScore = ({ score, status }) => {
  const getColor = () => {
    if (score >= 80) return 'text-green-500';
    if (score >= 50) return 'text-yellow-500';
    return 'text-red-500';
  };
  
  const getGradient = () => {
    if (score >= 80) return 'from-green-500 to-emerald-600';
    if (score >= 50) return 'from-yellow-500 to-orange-500';
    return 'from-red-500 to-rose-600';
  };
  
  return (
    <div className="flex items-center gap-4">
      <div className={`text-4xl font-bold ${getColor()}`}>
        {score}%
      </div>
      <div className="flex-1">
        <div className="h-3 bg-gray-700 rounded-full overflow-hidden">
          <div 
            className={`h-full bg-gradient-to-r ${getGradient()} transition-all duration-500`}
            style={{ width: `${score}%` }}
          />
        </div>
        <p className="text-sm text-gray-400 mt-1">
          Score de santé système
        </p>
      </div>
    </div>
  );
};

const APICard = ({ api, icon: Icon }) => {
  return (
    <div className="flex items-center justify-between p-3 bg-gray-800/50 rounded-lg border border-gray-700/50 hover:border-gray-600 transition-colors">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-gray-700/50 rounded-lg">
          <Icon className="w-4 h-4 text-gray-400" />
        </div>
        <div>
          <p className="font-medium text-white">{api.name}</p>
          <p className="text-xs text-gray-400 truncate max-w-[200px]">
            {api.message}
          </p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        {api.response_time_ms && (
          <span className="text-xs text-gray-500">
            {api.response_time_ms}ms
          </span>
        )}
        <StatusIcon status={api.status} />
      </div>
    </div>
  );
};

const SystemHealthMonitor = ({ isAdmin = false }) => {
  const [healthData, setHealthData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const { toast } = useToast();

  const fetchHealth = async (forceRefresh = false) => {
    try {
      const endpoint = isAdmin 
        ? `${API_URL}/api/admin/system-health?force_refresh=${forceRefresh}`
        : `${API_URL}/api/admin/system-health/public`;
      
      const token = localStorage.getItem('token');
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      
      const response = await fetch(endpoint, { headers });
      
      if (response.ok) {
        const data = await response.json();
        setHealthData(data);
      } else {
        throw new Error('Erreur de récupération');
      }
    } catch (error) {
      console.error('Health check error:', error);
      toast({
        title: "Erreur",
        description: "Impossible de vérifier l'état du système",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    // Rafraîchir toutes les 2 minutes
    const interval = setInterval(() => fetchHealth(), 120000);
    return () => clearInterval(interval);
  }, [isAdmin]);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchHealth(true);
  };

  if (loading) {
    return (
      <Card className="bg-gray-900 border-gray-800">
        <CardContent className="p-6">
          <div className="flex items-center justify-center gap-2">
            <RefreshCw className="w-5 h-5 animate-spin text-blue-500" />
            <span className="text-gray-400">Vérification du système...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  const summary = healthData?.summary || {};
  const aiModels = isAdmin 
    ? Object.values(healthData?.ai_models || {})
    : healthData?.ai_models || [];
  const marketData = isAdmin
    ? Object.values(healthData?.market_data || {})
    : healthData?.market_data || [];
  const database = isAdmin
    ? Object.values(healthData?.database || {})
    : [];

  return (
    <Card className="bg-gray-900 border-gray-800">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-lg flex items-center gap-2">
          <Activity className="w-5 h-5 text-blue-500" />
          État du Système
        </CardTitle>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleRefresh}
          disabled={refreshing}
          className="text-gray-400 hover:text-white"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
        </Button>
      </CardHeader>
      
      <CardContent className="space-y-6">
        {/* Score global */}
        <HealthScore 
          score={summary.health_score || 0} 
          status={summary.overall_status}
        />
        
        {/* Résumé */}
        <div className="grid grid-cols-4 gap-2">
          <div className="text-center p-2 bg-green-500/10 rounded-lg">
            <div className="text-lg font-bold text-green-500">{summary.operational || 0}</div>
            <div className="text-xs text-gray-400">OK</div>
          </div>
          <div className="text-center p-2 bg-yellow-500/10 rounded-lg">
            <div className="text-lg font-bold text-yellow-500">{summary.degraded || 0}</div>
            <div className="text-xs text-gray-400">Dégradé</div>
          </div>
          <div className="text-center p-2 bg-red-500/10 rounded-lg">
            <div className="text-lg font-bold text-red-500">{summary.down || 0}</div>
            <div className="text-xs text-gray-400">Hors ligne</div>
          </div>
          <div className="text-center p-2 bg-gray-500/10 rounded-lg">
            <div className="text-lg font-bold text-gray-400">{summary.standby || 0}</div>
            <div className="text-xs text-gray-400">Standby</div>
          </div>
        </div>

        {/* Modèles IA */}
        <div>
          <h3 className="text-sm font-medium text-gray-400 mb-3 flex items-center gap-2">
            <Cpu className="w-4 h-4" />
            Modèles IA ({aiModels.length})
          </h3>
          <div className="space-y-2">
            {aiModels.map((api, idx) => (
              <APICard key={idx} api={api} icon={Zap} />
            ))}
          </div>
        </div>

        {/* Sources de données */}
        <div>
          <h3 className="text-sm font-medium text-gray-400 mb-3 flex items-center gap-2">
            <TrendingUp className="w-4 h-4" />
            Sources de Données ({marketData.length})
          </h3>
          <div className="space-y-2">
            {marketData.map((api, idx) => (
              <APICard key={idx} api={api} icon={Globe} />
            ))}
          </div>
        </div>

        {/* Base de données (admin only) */}
        {isAdmin && database.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-gray-400 mb-3 flex items-center gap-2">
              <Database className="w-4 h-4" />
              Base de Données
            </h3>
            <div className="space-y-2">
              {database.map((api, idx) => (
                <APICard key={idx} api={api} icon={Database} />
              ))}
            </div>
          </div>
        )}

        {/* Dernière vérification */}
        <p className="text-xs text-gray-500 text-center">
          Dernière vérification: {healthData?.checked_at 
            ? new Date(healthData.checked_at).toLocaleString('fr-FR')
            : 'N/A'
          }
        </p>
      </CardContent>
    </Card>
  );
};

export default SystemHealthMonitor;
