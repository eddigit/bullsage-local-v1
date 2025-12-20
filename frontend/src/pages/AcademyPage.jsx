import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Progress } from "../components/ui/progress";
import { ScrollArea } from "../components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import {
  GraduationCap,
  Trophy,
  Star,
  Flame,
  Lock,
  CheckCircle,
  ChevronRight,
  Target,
  Brain,
  Award,
  Zap,
  BookOpen,
  Users,
  Medal
} from "lucide-react";

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Mascot component - BULL the friendly coach
function BullMascot({ message, mood = "happy" }) {
  const expressions = {
    happy: "😊",
    excited: "🤩",
    proud: "💪",
    thinking: "🤔",
    encouraging: "👍"
  };

  return (
    <div className="flex items-start gap-4 p-4 bg-gradient-to-r from-primary/10 to-transparent rounded-xl border border-primary/20">
      <div className="flex-shrink-0">
        <div className="w-16 h-16 rounded-full bg-gradient-to-br from-amber-500 to-amber-600 flex items-center justify-center text-3xl shadow-lg">
          🐂
        </div>
      </div>
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-1">
          <span className="font-bold text-primary">BULL</span>
          <span className="text-lg">{expressions[mood]}</span>
          <Badge variant="outline" className="text-xs border-primary/30 text-primary">
            Ton Coach Trading
          </Badge>
        </div>
        <p className="text-muted-foreground">{message}</p>
      </div>
    </div>
  );
}

// Level Badge component
function LevelBadge({ level, size = "md" }) {
  const sizes = {
    sm: "w-8 h-8 text-sm",
    md: "w-12 h-12 text-lg",
    lg: "w-16 h-16 text-2xl"
  };

  return (
    <div className={`${sizes[size]} rounded-full bg-gradient-to-br from-primary to-primary/60 flex items-center justify-center font-bold shadow-lg`}>
      {level.icon || level.level}
    </div>
  );
}

// Module Card component
function ModuleCard({ module, onClick }) {
  const colorClasses = {
    emerald: "from-emerald-500/20 to-emerald-600/5 border-emerald-500/30",
    blue: "from-blue-500/20 to-blue-600/5 border-blue-500/30",
    violet: "from-violet-500/20 to-violet-600/5 border-violet-500/30",
    rose: "from-rose-500/20 to-rose-600/5 border-rose-500/30",
    amber: "from-amber-500/20 to-amber-600/5 border-amber-500/30",
    cyan: "from-cyan-500/20 to-cyan-600/5 border-cyan-500/30"
  };

  const progressPercent = (module.completed_lessons / module.total_lessons) * 100;
  const isComplete = module.quiz_completed;

  return (
    <Card 
      className={`glass border cursor-pointer transition-all hover:scale-[1.02] hover:shadow-xl ${module.is_locked ? 'opacity-50' : ''} bg-gradient-to-br ${colorClasses[module.color] || colorClasses.emerald}`}
      onClick={() => !module.is_locked && onClick(module)}
    >
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="text-4xl">{module.icon}</div>
          <div className="flex items-center gap-2">
            {module.is_locked && <Lock className="w-5 h-5 text-muted-foreground" />}
            {isComplete && <CheckCircle className="w-5 h-5 text-green-500" />}
            {module.quiz_score && (
              <Badge variant="outline" className="border-green-500/30 text-green-400">
                {module.quiz_score}%
              </Badge>
            )}
          </div>
        </div>
        <CardTitle className="text-lg">{module.title}</CardTitle>
        <CardDescription className="text-sm">{module.description}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">
              {module.completed_lessons}/{module.total_lessons} leçons
            </span>
            <span className="text-muted-foreground">{module.estimated_time}</span>
          </div>
          <Progress value={progressPercent} className="h-2" />
          {!module.is_locked && (
            <Button 
              className="w-full mt-2" 
              variant={isComplete ? "outline" : "default"}
              size="sm"
            >
              {isComplete ? "Revoir" : module.completed_lessons > 0 ? "Continuer" : "Commencer"}
              <ChevronRight className="w-4 h-4 ml-1" />
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// Badge Display component
function BadgeDisplay({ badge, unlocked }) {
  return (
    <div className={`flex flex-col items-center p-3 rounded-xl border ${unlocked ? 'bg-primary/10 border-primary/30' : 'bg-white/5 border-white/10 opacity-50'}`}>
      <div className={`text-3xl mb-2 ${!unlocked && 'grayscale'}`}>{badge.icon}</div>
      <span className={`text-xs font-medium text-center ${unlocked ? 'text-foreground' : 'text-muted-foreground'}`}>
        {badge.name}
      </span>
    </div>
  );
}

// Leaderboard Item component
function LeaderboardItem({ item, index }) {
  const getRankStyle = (rank) => {
    if (rank === 1) return "from-amber-500 to-amber-600 text-black";
    if (rank === 2) return "from-gray-400 to-gray-500 text-black";
    if (rank === 3) return "from-amber-700 to-amber-800 text-white";
    return "from-white/10 to-white/5 text-white";
  };

  return (
    <div className={`flex items-center gap-3 p-3 rounded-lg ${item.is_current_user ? 'bg-primary/20 border border-primary/30' : 'bg-white/5'}`}>
      <div className={`w-8 h-8 rounded-full bg-gradient-to-br ${getRankStyle(item.rank)} flex items-center justify-center font-bold text-sm`}>
        {item.rank}
      </div>
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <span className="font-medium">{item.name}</span>
          <span>{item.level_icon}</span>
          {item.is_current_user && <Badge variant="outline" className="text-xs">Toi</Badge>}
        </div>
        <div className="text-xs text-muted-foreground">
          {item.level_title} • {item.badges_count} badges
        </div>
      </div>
      <div className="text-right">
        <div className="font-bold text-primary">{item.total_xp.toLocaleString()}</div>
        <div className="text-xs text-muted-foreground">XP</div>
      </div>
    </div>
  );
}

export default function AcademyPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [academyData, setAcademyData] = useState(null);
  const [badges, setBadges] = useState([]);
  const [leaderboard, setLeaderboard] = useState([]);
  const [activeTab, setActiveTab] = useState("modules");

  useEffect(() => {
    fetchAcademyData();
  }, []);

  const fetchAcademyData = async () => {
    try {
      const token = localStorage.getItem("token");
      const [modulesRes, badgesRes, leaderboardRes] = await Promise.all([
        axios.get(`${API_URL}/api/academy/modules`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API_URL}/api/academy/badges`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API_URL}/api/academy/leaderboard`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);
      
      setAcademyData(modulesRes.data);
      setBadges(badgesRes.data);
      setLeaderboard(leaderboardRes.data);
    } catch (error) {
      console.error("Error fetching academy data:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleModuleClick = (module) => {
    navigate(`/academy/module/${module.id}`);
  };

  const getMascotMessage = () => {
    if (!academyData) return "Chargement...";
    
    const { total_xp, streak_days, user_progress } = academyData;
    
    if (total_xp === 0) {
      return "Bienvenue dans l'Académie BULL SAGE ! 🎉 Je suis BULL, ton coach personnel. Ensemble, on va faire de toi un trader intelligent et discipliné. Prêt à commencer l'aventure ?";
    }
    
    if (streak_days >= 7) {
      return `Incroyable ! ${streak_days} jours d'apprentissage consécutifs ! 🔥 Ta discipline est exemplaire. Continue comme ça, tu deviens un vrai pro !`;
    }
    
    if (user_progress?.level >= 5) {
      return `Wow, niveau ${user_progress.level} ! Tu progresses super vite ! Je suis fier de toi. Prêt pour de nouveaux défis ?`;
    }
    
    return `Salut champion ! Tu as ${total_xp} XP. Continue d'apprendre et tu vas devenir un Maître Trader ! 💪`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Chargement de l&apos;Académie...</p>
        </div>
      </div>
    );
  }

  const progress = academyData?.user_progress || { level: 1, title: "Nouveau Venu", icon: "🌱" };
  const progressToNext = progress.next_level_xp 
    ? ((academyData?.total_xp || 0) / progress.next_level_xp) * 100 
    : 100;

  return (
    <div className="space-y-6 pb-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <GraduationCap className="w-8 h-8 text-primary" />
            Académie Trading
          </h1>
          <p className="text-muted-foreground mt-1">
            Apprends le trading comme un pro, étape par étape
          </p>
        </div>
        
        {/* User Progress Summary */}
        <Card className="glass border-white/10 md:min-w-[300px]">
          <CardContent className="p-4">
            <div className="flex items-center gap-4">
              <LevelBadge level={progress} size="lg" />
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-bold">{progress.title}</span>
                  <Badge variant="outline" className="text-xs">
                    Niv. {progress.level}
                  </Badge>
                </div>
                <div className="text-sm text-muted-foreground mb-2">
                  {academyData?.total_xp?.toLocaleString() || 0} XP
                </div>
                <Progress value={progressToNext} className="h-2" />
                {progress.xp_to_next > 0 && (
                  <div className="text-xs text-muted-foreground mt-1">
                    {progress.xp_to_next} XP pour le niveau suivant
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Mascot Message */}
      <BullMascot 
        message={getMascotMessage()} 
        mood={academyData?.total_xp > 0 ? "proud" : "excited"}
      />

      {/* Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="glass border-white/10">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-amber-500/20 flex items-center justify-center">
              <Zap className="w-5 h-5 text-amber-500" />
            </div>
            <div>
              <div className="text-2xl font-bold">{academyData?.total_xp?.toLocaleString() || 0}</div>
              <div className="text-xs text-muted-foreground">XP Total</div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="glass border-white/10">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-orange-500/20 flex items-center justify-center">
              <Flame className="w-5 h-5 text-orange-500" />
            </div>
            <div>
              <div className="text-2xl font-bold">{academyData?.streak_days || 0}</div>
              <div className="text-xs text-muted-foreground">Jours de suite</div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="glass border-white/10">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-green-500/20 flex items-center justify-center">
              <BookOpen className="w-5 h-5 text-green-500" />
            </div>
            <div>
              <div className="text-2xl font-bold">
                {academyData?.modules?.reduce((sum, m) => sum + m.completed_lessons, 0) || 0}
              </div>
              <div className="text-xs text-muted-foreground">Leçons terminées</div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="glass border-white/10">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-purple-500/20 flex items-center justify-center">
              <Award className="w-5 h-5 text-purple-500" />
            </div>
            <div>
              <div className="text-2xl font-bold">{academyData?.badges?.length || 0}</div>
              <div className="text-xs text-muted-foreground">Badges débloqués</div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="bg-white/5 border border-white/10 mb-4">
          <TabsTrigger value="modules" className="data-[state=active]:bg-primary data-[state=active]:text-black">
            <BookOpen className="w-4 h-4 mr-2" />
            Modules
          </TabsTrigger>
          <TabsTrigger value="badges" className="data-[state=active]:bg-primary data-[state=active]:text-black">
            <Trophy className="w-4 h-4 mr-2" />
            Badges
          </TabsTrigger>
          <TabsTrigger value="leaderboard" className="data-[state=active]:bg-primary data-[state=active]:text-black">
            <Users className="w-4 h-4 mr-2" />
            Classement
          </TabsTrigger>
        </TabsList>

        <TabsContent value="modules" className="mt-0">
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {academyData?.modules?.map((module) => (
              <ModuleCard 
                key={module.id} 
                module={module} 
                onClick={handleModuleClick}
              />
            ))}
          </div>
        </TabsContent>

        <TabsContent value="badges" className="mt-0">
          <Card className="glass border-white/10">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Trophy className="w-5 h-5 text-amber-500" />
                Collection de Badges
              </CardTitle>
              <CardDescription>
                Débloque des badges en progressant dans ton apprentissage
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 md:grid-cols-5 lg:grid-cols-7 gap-3">
                {badges.map((badge) => (
                  <BadgeDisplay 
                    key={badge.id} 
                    badge={badge} 
                    unlocked={badge.unlocked}
                  />
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="leaderboard" className="mt-0">
          <Card className="glass border-white/10">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Medal className="w-5 h-5 text-amber-500" />
                Classement des Apprenants
              </CardTitle>
              <CardDescription>
                Compare ta progression avec les autres traders en formation
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[400px]">
                <div className="space-y-2">
                  {leaderboard?.leaderboard?.map((item, index) => (
                    <LeaderboardItem key={item.user_id} item={item} index={index} />
                  ))}
                </div>
              </ScrollArea>
              {leaderboard?.current_user_rank && (
                <div className="mt-4 p-3 bg-primary/10 rounded-lg border border-primary/30 text-center">
                  <span className="text-muted-foreground">Ton classement : </span>
                  <span className="font-bold text-primary">#{leaderboard.current_user_rank}</span>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
