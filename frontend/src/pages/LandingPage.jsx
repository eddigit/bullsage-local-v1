import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../App";
import { toast } from "sonner";
import { motion } from "framer-motion";
import {
  TrendingUp,
  Brain,
  Shield,
  Zap,
  GraduationCap,
  ChartBar,
  Bot,
  Wallet,
  ArrowRight,
  Check,
  Mail,
  User,
  Lock,
  Loader2,
  Star,
  Coins,
  Rocket,
  Target,
  Users,
  Play,
  ChevronDown
} from "lucide-react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Card, CardContent } from "../components/ui/card";
import { Badge } from "../components/ui/badge";

// Animation variants
const fadeInUp = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6 } }
};

const stagger = {
  visible: { transition: { staggerChildren: 0.1 } }
};

// Hero Section
function HeroSection() {
  const scrollToSignup = () => {
    document.getElementById('signup-section')?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden px-4 py-20">
      {/* Background effects */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-emerald-900/20 via-transparent to-transparent" />
      <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-emerald-500/10 rounded-full blur-[120px] animate-pulse" />
      <div className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] bg-violet-500/10 rounded-full blur-[100px] animate-pulse" style={{ animationDelay: '1s' }} />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-primary/5 rounded-full blur-[150px]" />
      
      {/* Grid pattern */}
      <div className="absolute inset-0 bg-[linear-gradient(rgba(16,185,129,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(16,185,129,0.03)_1px,transparent_1px)] bg-[size:60px_60px]" />

      <motion.div 
        className="relative z-10 max-w-6xl mx-auto text-center"
        initial="hidden"
        animate="visible"
        variants={stagger}
      >
        {/* Badge */}
        <motion.div variants={fadeInUp} className="mb-6">
          <Badge className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20 px-4 py-2 text-sm font-medium">
            <Rocket className="w-4 h-4 mr-2" />
            La révolution du trading intelligent est là
          </Badge>
        </motion.div>

        {/* Logo */}
        <motion.div variants={fadeInUp} className="flex items-center justify-center gap-4 mb-8">
          <img 
            src="/logo.png" 
            alt="BULL SAGE" 
            className="w-20 h-20 md:w-24 md:h-24 rounded-3xl object-contain shadow-2xl shadow-emerald-500/20"
          />
        </motion.div>

        {/* Main Title */}
        <motion.h1 
          variants={fadeInUp}
          className="text-4xl md:text-6xl lg:text-7xl font-bold font-manrope tracking-tight mb-6"
        >
          <span className="bg-gradient-to-r from-white via-white to-white/70 bg-clip-text text-transparent">
            Trade Smart.
          </span>
          <br />
          <span className="bg-gradient-to-r from-emerald-400 via-emerald-300 to-lime-400 bg-clip-text text-transparent">
            Learn Fast.
          </span>
        </motion.h1>

        {/* Subtitle */}
        <motion.p 
          variants={fadeInUp}
          className="text-lg md:text-xl text-slate-400 max-w-2xl mx-auto mb-10 leading-relaxed"
        >
          L'assistant IA qui révolutionne votre trading. Signaux en temps réel, 
          analyse multi-timeframe, et une académie complète pour maîtriser les marchés crypto.
        </motion.p>

        {/* CTA Buttons */}
        <motion.div 
          variants={fadeInUp}
          className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-12"
        >
          <Button 
            size="lg"
            onClick={scrollToSignup}
            className="bg-emerald-500 hover:bg-emerald-400 text-black font-bold rounded-full px-8 py-6 text-lg shadow-[0_0_30px_rgba(16,185,129,0.4)] hover:shadow-[0_0_40px_rgba(16,185,129,0.6)] transition-all hover:scale-105"
            data-testid="hero-cta-primary"
          >
            Commencer gratuitement
            <ArrowRight className="w-5 h-5 ml-2" />
          </Button>
          <Link to="/login">
            <Button 
              size="lg"
              variant="outline"
              className="border-white/20 text-white hover:bg-white/10 rounded-full px-8 py-6 text-lg"
              data-testid="hero-cta-login"
            >
              J'ai déjà un compte
            </Button>
          </Link>
        </motion.div>

        {/* Stats */}
        <motion.div 
          variants={fadeInUp}
          className="grid grid-cols-3 gap-4 md:gap-8 max-w-2xl mx-auto"
        >
          <div className="text-center">
            <div className="text-2xl md:text-4xl font-bold text-white font-manrope">10K+</div>
            <div className="text-xs md:text-sm text-slate-500">Traders actifs</div>
          </div>
          <div className="text-center">
            <div className="text-2xl md:text-4xl font-bold text-emerald-400 font-manrope">87%</div>
            <div className="text-xs md:text-sm text-slate-500">Signaux rentables</div>
          </div>
          <div className="text-center">
            <div className="text-2xl md:text-4xl font-bold text-white font-manrope">24/7</div>
            <div className="text-xs md:text-sm text-slate-500">Analyse IA</div>
          </div>
        </motion.div>

        {/* Scroll indicator */}
        <motion.div 
          variants={fadeInUp}
          className="absolute bottom-8 left-1/2 -translate-x-1/2"
        >
          <ChevronDown className="w-8 h-8 text-white/30 animate-bounce" />
        </motion.div>
      </motion.div>
    </section>
  );
}

// Features Section
function FeaturesSection() {
  const features = [
    {
      icon: <Brain className="w-8 h-8" />,
      title: "Intelligence Artificielle",
      description: "Notre IA analyse les marchés 24/7 et génère des signaux de trading précis basés sur le machine learning.",
      color: "violet"
    },
    {
      icon: <TrendingUp className="w-8 h-8" />,
      title: "Signaux Premium",
      description: "Recevez des alertes en temps réel avec points d'entrée, stop-loss et take-profit optimisés.",
      color: "emerald"
    },
    {
      icon: <ChartBar className="w-8 h-8" />,
      title: "Analyse Multi-Timeframe",
      description: "Visualisez les tendances sur plusieurs échelles de temps pour des décisions éclairées.",
      color: "lime"
    },
    {
      icon: <Bot className="w-8 h-8" />,
      title: "Assistant Cockpit",
      description: "Un copilote IA personnel qui répond à vos questions et vous guide dans vos trades.",
      color: "violet"
    },
    {
      icon: <Shield className="w-8 h-8" />,
      title: "Paper Trading",
      description: "Entraînez-vous sans risque avec notre simulateur de trading réaliste.",
      color: "emerald"
    },
    {
      icon: <Zap className="w-8 h-8" />,
      title: "Auto-Trading",
      description: "Connectez votre exchange et laissez l'IA exécuter les trades automatiquement.",
      color: "lime"
    }
  ];

  const colorClasses = {
    violet: {
      bg: "bg-violet-500/10",
      border: "border-violet-500/20",
      text: "text-violet-400",
      glow: "group-hover:shadow-violet-500/20"
    },
    emerald: {
      bg: "bg-emerald-500/10", 
      border: "border-emerald-500/20",
      text: "text-emerald-400",
      glow: "group-hover:shadow-emerald-500/20"
    },
    lime: {
      bg: "bg-lime-500/10",
      border: "border-lime-500/20", 
      text: "text-lime-400",
      glow: "group-hover:shadow-lime-500/20"
    }
  };

  return (
    <section className="py-24 px-4 relative" id="features">
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-black/50 to-transparent" />
      
      <div className="relative z-10 max-w-6xl mx-auto">
        <motion.div 
          className="text-center mb-16"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
        >
          <Badge className="bg-white/5 text-white/70 border-white/10 mb-4">
            Fonctionnalités
          </Badge>
          <h2 className="text-3xl md:text-5xl font-bold font-manrope mb-4">
            Tout ce dont vous avez besoin
          </h2>
          <p className="text-slate-400 max-w-2xl mx-auto">
            Une suite complète d'outils pour dominer les marchés crypto
          </p>
        </motion.div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1 }}
            >
              <Card className={`group bg-black/40 backdrop-blur-xl border-white/10 hover:${colorClasses[feature.color].border} transition-all duration-300 hover:shadow-xl ${colorClasses[feature.color].glow} h-full`}>
                <CardContent className="p-6">
                  <div className={`w-14 h-14 rounded-2xl ${colorClasses[feature.color].bg} ${colorClasses[feature.color].text} flex items-center justify-center mb-4`}>
                    {feature.icon}
                  </div>
                  <h3 className="text-xl font-bold font-manrope mb-2">{feature.title}</h3>
                  <p className="text-slate-400 text-sm leading-relaxed">{feature.description}</p>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

// Academy Section
function AcademySection() {
  const modules = [
    { icon: "📊", title: "Les bases du trading", level: "Débutant", lessons: 12 },
    { icon: "📈", title: "Analyse technique", level: "Intermédiaire", lessons: 18 },
    { icon: "🧠", title: "Psychologie du trader", level: "Avancé", lessons: 8 },
    { icon: "⚡", title: "Stratégies avancées", level: "Expert", lessons: 15 }
  ];

  return (
    <section className="py-24 px-4 relative overflow-hidden" id="academy">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-violet-900/10 via-transparent to-emerald-900/10" />
      
      <div className="relative z-10 max-w-6xl mx-auto">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Content */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
          >
            <Badge className="bg-violet-500/10 text-violet-400 border-violet-500/20 mb-4">
              <GraduationCap className="w-4 h-4 mr-2" />
              Academy
            </Badge>
            <h2 className="text-3xl md:text-5xl font-bold font-manrope mb-6">
              Apprenez à trader
              <br />
              <span className="text-violet-400">comme un pro</span>
            </h2>
            <p className="text-slate-400 mb-8 leading-relaxed">
              Que vous soyez débutant ou trader expérimenté, notre académie vous accompagne 
              avec des cours interactifs, des quiz et des exercices pratiques. Progressez à 
              votre rythme et débloquez des récompenses !
            </p>

            <div className="space-y-4 mb-8">
              {[
                "Cours vidéo interactifs",
                "Quiz et certifications",
                "Communauté de traders",
                "Suivi de progression gamifié"
              ].map((item, i) => (
                <div key={i} className="flex items-center gap-3">
                  <div className="w-6 h-6 rounded-full bg-violet-500/20 flex items-center justify-center">
                    <Check className="w-4 h-4 text-violet-400" />
                  </div>
                  <span className="text-slate-300">{item}</span>
                </div>
              ))}
            </div>

            <Link to="/register">
              <Button className="bg-violet-500 hover:bg-violet-400 text-white font-bold rounded-full px-6 shadow-[0_0_20px_rgba(139,92,246,0.3)]">
                Accéder à l'Academy
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </Link>
          </motion.div>

          {/* Modules preview */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            className="grid grid-cols-2 gap-4"
          >
            {modules.map((module, index) => (
              <Card 
                key={index}
                className="bg-black/40 backdrop-blur-xl border-white/10 hover:border-violet-500/30 transition-all"
              >
                <CardContent className="p-5">
                  <div className="text-3xl mb-3">{module.icon}</div>
                  <h4 className="font-semibold mb-1">{module.title}</h4>
                  <div className="flex items-center gap-2 text-xs text-slate-500">
                    <Badge variant="outline" className="text-xs">{module.level}</Badge>
                    <span>{module.lessons} leçons</span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </motion.div>
        </div>
      </div>
    </section>
  );
}

// Token Section
function TokenSection() {
  return (
    <section className="py-24 px-4 relative" id="token">
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-emerald-900/5 to-transparent" />
      
      <div className="relative z-10 max-w-6xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center"
        >
          <Card className="bg-gradient-to-br from-emerald-900/20 via-black/60 to-violet-900/20 backdrop-blur-xl border-emerald-500/20 overflow-hidden">
            <CardContent className="p-8 md:p-12">
              <Badge className="bg-lime-400/10 text-lime-400 border-lime-400/20 mb-6">
                <Coins className="w-4 h-4 mr-2" />
                $SAGE Token
              </Badge>
              
              <h2 className="text-3xl md:text-5xl font-bold font-manrope mb-6">
                Le token qui récompense
                <br />
                <span className="bg-gradient-to-r from-emerald-400 to-lime-400 bg-clip-text text-transparent">
                  les traders performants
                </span>
              </h2>
              
              <p className="text-slate-400 max-w-2xl mx-auto mb-8 leading-relaxed">
                Gagnez des tokens $SAGE en tradant, en apprenant et en partageant vos analyses. 
                Utilisez-les pour débloquer des fonctionnalités premium ou échangez-les sur les DEX.
              </p>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-8 mb-8">
                <div className="text-center p-4">
                  <div className="text-2xl md:text-3xl font-bold text-emerald-400 font-manrope">100M</div>
                  <div className="text-xs md:text-sm text-slate-500">Supply totale</div>
                </div>
                <div className="text-center p-4">
                  <div className="text-2xl md:text-3xl font-bold text-white font-manrope">40%</div>
                  <div className="text-xs md:text-sm text-slate-500">Rewards Community</div>
                </div>
                <div className="text-center p-4">
                  <div className="text-2xl md:text-3xl font-bold text-white font-manrope">25%</div>
                  <div className="text-xs md:text-sm text-slate-500">Développement</div>
                </div>
                <div className="text-center p-4">
                  <div className="text-2xl md:text-3xl font-bold text-lime-400 font-manrope">Q2 2026</div>
                  <div className="text-xs md:text-sm text-slate-500">Token Launch</div>
                </div>
              </div>

              <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                <Button className="bg-emerald-500 hover:bg-emerald-400 text-black font-bold rounded-full px-6">
                  Rejoindre la whitelist
                  <Star className="w-4 h-4 ml-2" />
                </Button>
                <Button variant="outline" className="border-white/20 text-white hover:bg-white/10 rounded-full px-6">
                  Lire le Whitepaper
                </Button>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </section>
  );
}

// Testimonials Section
function TestimonialsSection() {
  const testimonials = [
    {
      name: "Alexandre M.",
      role: "Trader indépendant",
      avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=alex",
      content: "Bull Sage a complètement transformé ma façon de trader. Les signaux sont précis et l'Academy m'a permis de passer au niveau supérieur.",
      rating: 5
    },
    {
      name: "Sophie L.",
      role: "Investisseuse crypto",
      avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=sophie",
      content: "L'assistant IA est incroyable ! Il répond à toutes mes questions et m'aide à comprendre les marchés. Je recommande à 100%.",
      rating: 5
    },
    {
      name: "Thomas K.",
      role: "Day trader",
      avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=thomas",
      content: "Le paper trading m'a permis de tester mes stratégies sans risque. Maintenant je trade en réel avec confiance.",
      rating: 5
    }
  ];

  return (
    <section className="py-24 px-4">
      <div className="max-w-6xl mx-auto">
        <motion.div 
          className="text-center mb-16"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
        >
          <Badge className="bg-white/5 text-white/70 border-white/10 mb-4">
            <Users className="w-4 h-4 mr-2" />
            Témoignages
          </Badge>
          <h2 className="text-3xl md:text-5xl font-bold font-manrope mb-4">
            Ils nous font confiance
          </h2>
        </motion.div>

        <div className="grid md:grid-cols-3 gap-6">
          {testimonials.map((testimonial, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1 }}
            >
              <Card className="bg-black/40 backdrop-blur-xl border-white/10 h-full">
                <CardContent className="p-6">
                  <div className="flex items-center gap-1 mb-4">
                    {Array.from({ length: testimonial.rating }).map((_, i) => (
                      <Star key={i} className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                    ))}
                  </div>
                  <p className="text-slate-300 mb-6 leading-relaxed">"{testimonial.content}"</p>
                  <div className="flex items-center gap-3">
                    <img 
                      src={testimonial.avatar} 
                      alt={testimonial.name}
                      className="w-10 h-10 rounded-full bg-white/10"
                    />
                    <div>
                      <div className="font-semibold">{testimonial.name}</div>
                      <div className="text-xs text-slate-500">{testimonial.role}</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

// Signup Section
function SignupSection() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name || !email || !password) {
      toast.error("Veuillez remplir tous les champs");
      return;
    }

    if (password.length < 6) {
      toast.error("Le mot de passe doit contenir au moins 6 caractères");
      return;
    }

    setLoading(true);
    try {
      await register(name, email, password, "beginner");
      toast.success("Compte créé avec succès !");
      navigate("/onboarding");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erreur lors de l'inscription");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="py-24 px-4 relative" id="signup-section">
      <div className="absolute inset-0 bg-gradient-to-t from-emerald-900/10 via-transparent to-transparent" />
      
      <div className="relative z-10 max-w-6xl mx-auto">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Content */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="text-3xl md:text-5xl font-bold font-manrope mb-6">
              Prêt à révolutionner
              <br />
              <span className="text-emerald-400">votre trading ?</span>
            </h2>
            <p className="text-slate-400 mb-8 leading-relaxed">
              Rejoignez des milliers de traders qui font confiance à Bull Sage pour 
              leurs décisions d'investissement. Inscription gratuite, sans engagement.
            </p>

            <div className="space-y-4">
              {[
                "Accès gratuit à l'Academy",
                "Signaux de trading quotidiens",
                "Paper trading illimité",
                "Assistant IA personnel"
              ].map((item, i) => (
                <div key={i} className="flex items-center gap-3">
                  <div className="w-6 h-6 rounded-full bg-emerald-500/20 flex items-center justify-center">
                    <Check className="w-4 h-4 text-emerald-400" />
                  </div>
                  <span className="text-slate-300">{item}</span>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Signup Form */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
          >
            <Card className="bg-black/60 backdrop-blur-xl border-white/10">
              <CardContent className="p-8">
                <h3 className="text-2xl font-bold font-manrope mb-6 text-center">
                  Créer un compte gratuit
                </h3>
                
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="signup-name">Nom complet</Label>
                    <div className="relative">
                      <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                      <Input
                        id="signup-name"
                        type="text"
                        placeholder="John Doe"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        className="pl-10 bg-black/20 border-white/10 focus:border-emerald-500/50 h-12"
                        data-testid="landing-signup-name"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="signup-email">Email</Label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                      <Input
                        id="signup-email"
                        type="email"
                        placeholder="trader@example.com"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        className="pl-10 bg-black/20 border-white/10 focus:border-emerald-500/50 h-12"
                        data-testid="landing-signup-email"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="signup-password">Mot de passe</Label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                      <Input
                        id="signup-password"
                        type="password"
                        placeholder="••••••••"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        className="pl-10 bg-black/20 border-white/10 focus:border-emerald-500/50 h-12"
                        data-testid="landing-signup-password"
                      />
                    </div>
                  </div>

                  <Button 
                    type="submit" 
                    className="w-full bg-emerald-500 hover:bg-emerald-400 text-black font-bold h-12 rounded-full shadow-[0_0_20px_rgba(16,185,129,0.3)]"
                    disabled={loading}
                    data-testid="landing-signup-submit"
                  >
                    {loading ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      <>
                        Créer mon compte
                        <ArrowRight className="w-5 h-5 ml-2" />
                      </>
                    )}
                  </Button>
                </form>

                <p className="text-center text-xs text-slate-500 mt-6">
                  En créant un compte, vous acceptez nos{" "}
                  <a href="#" className="text-emerald-400 hover:underline">conditions d'utilisation</a>
                </p>

                <div className="mt-6 pt-6 border-t border-white/10 text-center">
                  <span className="text-slate-500 text-sm">Déjà un compte ?</span>
                  {" "}
                  <Link to="/login" className="text-emerald-400 hover:underline font-medium text-sm">
                    Se connecter
                  </Link>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </div>
    </section>
  );
}

// Footer
function Footer() {
  return (
    <footer className="py-12 px-4 border-t border-white/5">
      <div className="max-w-6xl mx-auto">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <img 
              src="/logo.png" 
              alt="BULL SAGE" 
              className="w-10 h-10 rounded-xl object-contain"
            />
            <div>
              <div className="font-bold font-manrope">BULL SAGE</div>
              <div className="text-xs text-slate-500">Trade Smart. Learn Fast.</div>
            </div>
          </div>

          <div className="flex items-center gap-8 text-sm text-slate-500">
            <a href="#features" className="hover:text-white transition-colors">Fonctionnalités</a>
            <a href="#academy" className="hover:text-white transition-colors">Academy</a>
            <a href="#token" className="hover:text-white transition-colors">Token</a>
            <Link to="/login" className="hover:text-white transition-colors">Connexion</Link>
          </div>

          <div className="text-xs text-slate-600">
            © 2026 Bull Sage. Tous droits réservés.
          </div>
        </div>
      </div>
    </footer>
  );
}

// Main Landing Page Component
export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#050505] text-slate-50">
      <HeroSection />
      <FeaturesSection />
      <AcademySection />
      <TokenSection />
      <TestimonialsSection />
      <SignupSection />
      <Footer />
    </div>
  );
}
