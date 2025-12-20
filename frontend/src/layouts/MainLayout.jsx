import { Outlet, NavLink, useLocation } from "react-router-dom";
import { useAuth } from "../App";
import { useState, useEffect } from "react";
import {
  LayoutDashboard,
  TrendingUp,
  MessageCircle,
  Wallet,
  Target,
  Bell,
  Settings,
  LogOut,
  Menu,
  X,
  ChevronRight,
  Zap,
  Shield,
  Key,
  Brain,
  Signal,
  Crosshair,
  BookOpen,
  Sun,
  GraduationCap,
  Home,
  User,
  MoreHorizontal
} from "lucide-react";
import { Button } from "../components/ui/button";
import { ScrollArea } from "../components/ui/scroll-area";
import { Avatar, AvatarFallback } from "../components/ui/avatar";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "../components/ui/sheet";

// Main navigation items
const navigation = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Académie", href: "/academy", icon: GraduationCap, highlight: true },
  { name: "Cockpit", href: "/cockpit", icon: Sun },
  { name: "Mode Trading", href: "/trading", icon: Crosshair },
  { name: "Journal", href: "/journal", icon: BookOpen },
  { name: "Mes Signaux", href: "/signals", icon: Signal },
  { name: "Intelligence", href: "/intelligence", icon: Brain },
  { name: "Marchés", href: "/markets", icon: TrendingUp },
  { name: "Assistant IA", href: "/assistant", icon: MessageCircle },
  { name: "Paper Trading", href: "/paper-trading", icon: Wallet },
  { name: "Stratégies", href: "/strategies", icon: Target },
  { name: "Alertes", href: "/alerts", icon: Bell },
  { name: "Paramètres", href: "/settings", icon: Settings },
];

// Admin navigation
const adminNavigation = [
  { name: "Administration", href: "/admin", icon: Shield, admin: true },
  { name: "Clés API", href: "/admin/api-keys", icon: Key, admin: true },
];

// Bottom bar items (mobile) - 5 main items
const bottomNavItems = [
  { name: "Accueil", href: "/", icon: Home },
  { name: "Académie", href: "/academy", icon: GraduationCap },
  { name: "Trading", href: "/trading", icon: Crosshair },
  { name: "Assistant", href: "/assistant", icon: MessageCircle },
  { name: "Plus", href: null, icon: MoreHorizontal, isMore: true },
];

export default function MainLayout() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [moreMenuOpen, setMoreMenuOpen] = useState(false);
  const [isInstallable, setIsInstallable] = useState(false);
  const [deferredPrompt, setDeferredPrompt] = useState(null);

  // Check if app is installable
  useEffect(() => {
    const handler = (e) => {
      e.preventDefault();
      setDeferredPrompt(e);
      setIsInstallable(true);
    };
    
    window.addEventListener('beforeinstallprompt', handler);
    return () => window.removeEventListener('beforeinstallprompt', handler);
  }, []);

  const handleInstall = async () => {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    if (outcome === 'accepted') {
      setIsInstallable(false);
    }
    setDeferredPrompt(null);
  };

  const getInitials = (name) => {
    return name?.split(" ").map(n => n[0]).join("").toUpperCase() || "U";
  };

  // Desktop sidebar nav item
  const NavItem = ({ item, mobile = false, onClick }) => {
    const isActive = location.pathname === item.href;
    
    return (
      <NavLink
        to={item.href}
        onClick={onClick}
        className={`
          flex items-center gap-3 px-3 py-3 rounded-xl transition-all duration-200 min-h-[44px]
          ${isActive 
            ? "bg-primary/10 text-primary border border-primary/20" 
            : "text-muted-foreground hover:text-foreground hover:bg-white/5 active:bg-white/10"
          }
          ${item.highlight && !isActive ? "text-violet-400 hover:text-violet-300" : ""}
          ${item.admin && !isActive ? "text-violet-400 hover:text-violet-300" : ""}
        `}
        data-testid={`nav-${item.name.toLowerCase().replace(/\s+/g, '-')}`}
      >
        <item.icon className={`w-5 h-5 flex-shrink-0 ${(item.highlight || item.admin) && !isActive ? "text-violet-400" : ""}`} />
        <span className="font-medium truncate">{item.name}</span>
        {item.highlight && (
          <Zap className="w-4 h-4 ml-auto text-violet-400 flex-shrink-0" />
        )}
        {item.admin && (
          <Shield className="w-4 h-4 ml-auto text-violet-400 flex-shrink-0" />
        )}
      </NavLink>
    );
  };

  // Mobile bottom nav item
  const BottomNavItem = ({ item, onClick }) => {
    const isActive = item.href && location.pathname === item.href;
    
    if (item.isMore) {
      return (
        <button
          onClick={onClick}
          className={`
            flex flex-col items-center justify-center gap-1 py-2 px-4 min-w-[64px] min-h-[56px]
            transition-all duration-200 rounded-xl
            ${moreMenuOpen ? "text-primary" : "text-muted-foreground"}
          `}
          data-testid="nav-more"
        >
          <item.icon className="w-6 h-6" />
          <span className="text-[10px] font-medium">{item.name}</span>
        </button>
      );
    }
    
    return (
      <NavLink
        to={item.href}
        className={`
          flex flex-col items-center justify-center gap-1 py-2 px-4 min-w-[64px] min-h-[56px]
          transition-all duration-200 rounded-xl
          ${isActive 
            ? "text-primary" 
            : "text-muted-foreground hover:text-foreground active:scale-95"
          }
        `}
        data-testid={`nav-${item.name.toLowerCase()}`}
      >
        <div className={`relative ${isActive ? 'scale-110' : ''} transition-transform`}>
          <item.icon className="w-6 h-6" />
          {isActive && (
            <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full bg-primary" />
          )}
        </div>
        <span className="text-[10px] font-medium">{item.name}</span>
      </NavLink>
    );
  };

  return (
    <div className="min-h-screen bg-background">
      {/* ===================== MOBILE HEADER ===================== */}
      <header className="md:hidden fixed top-0 left-0 right-0 h-14 glass-heavy z-40 flex items-center justify-between px-4 safe-area-top">
        <div className="flex items-center gap-2">
          <img 
            src="/logo.png" 
            alt="BULL SAGE" 
            className="w-8 h-8 rounded-lg object-contain"
          />
          <span className="font-bold text-lg font-manrope">BULL SAGE</span>
        </div>

        <div className="flex items-center gap-2">
          {isInstallable && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleInstall}
              className="text-primary text-xs"
            >
              Installer
            </Button>
          )}
          <Avatar className="w-8 h-8">
            <AvatarFallback className="bg-secondary text-sm">
              {getInitials(user?.name)}
            </AvatarFallback>
          </Avatar>
        </div>
      </header>

      {/* ===================== DESKTOP SIDEBAR ===================== */}
      <aside className="hidden md:block fixed top-0 left-0 h-full w-64 glass-heavy z-50">
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="h-16 flex items-center justify-between px-4 border-b border-white/5">
            <div className="flex items-center gap-3">
              <img 
                src="/logo.png" 
                alt="BULL SAGE" 
                className="w-10 h-10 rounded-xl object-contain"
              />
              <div>
                <h1 className="font-bold text-lg font-manrope tracking-tight">BULL SAGE</h1>
                <p className="text-xs text-muted-foreground">Trading Assistant</p>
              </div>
            </div>
          </div>

          {/* Navigation */}
          <ScrollArea className="flex-1 px-3 py-4">
            <nav className="space-y-1">
              {navigation.map((item) => (
                <NavItem key={item.name} item={item} />
              ))}
              
              {/* Admin Navigation */}
              {user?.is_admin && (
                <>
                  <div className="my-4 border-t border-white/5" />
                  {adminNavigation.map((item) => (
                    <NavItem key={item.name} item={item} />
                  ))}
                </>
              )}
            </nav>
          </ScrollArea>

          {/* User Section */}
          <div className="p-4 border-t border-white/5">
            <div className="flex items-center gap-3 mb-4">
              <Avatar className="w-10 h-10">
                <AvatarFallback className="bg-secondary">
                  {getInitials(user?.name)}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1 min-w-0">
                <p className="font-medium truncate">{user?.name}</p>
                <p className="text-xs text-muted-foreground capitalize">{user?.trading_level}</p>
              </div>
            </div>
            <Button
              variant="ghost"
              className="w-full justify-start text-muted-foreground hover:text-destructive min-h-[44px]"
              onClick={logout}
              data-testid="logout-btn"
            >
              <LogOut className="w-4 h-4 mr-2" />
              Déconnexion
            </Button>
          </div>
        </div>
      </aside>

      {/* ===================== MAIN CONTENT ===================== */}
      <main className="md:ml-64 min-h-screen pt-14 pb-24 md:pt-0 md:pb-0 flex flex-col">
        <div className="p-4 md:p-6 flex-1">
          <Outlet />
        </div>
        
        {/* Footer - Desktop only */}
        <footer className="hidden md:block py-4 px-6 border-t border-white/5">
          <div className="flex flex-col md:flex-row items-center justify-center gap-2 text-xs text-muted-foreground">
            <span>© {new Date().getFullYear()} BULL SAGE v1.0.0</span>
            <span className="hidden md:inline">•</span>
            <span>
              Propulsé par{" "}
              <a 
                href="mailto:coachdigitalparis@gmail.com" 
                className="text-primary hover:underline font-medium"
              >
                GILLES KORZEC
              </a>
            </span>
          </div>
        </footer>
      </main>

      {/* ===================== MOBILE BOTTOM NAVIGATION ===================== */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-black/90 backdrop-blur-xl border-t border-white/10 z-50 safe-area-bottom">
        <div className="flex justify-around items-center h-16 px-2">
          {bottomNavItems.map((item) => (
            <BottomNavItem 
              key={item.name} 
              item={item}
              onClick={item.isMore ? () => setMoreMenuOpen(true) : undefined}
            />
          ))}
        </div>
      </nav>

      {/* ===================== MORE MENU SHEET ===================== */}
      <Sheet open={moreMenuOpen} onOpenChange={setMoreMenuOpen}>
        <SheetContent side="bottom" className="bg-background/95 backdrop-blur-xl border-t border-white/10 rounded-t-3xl pb-8">
          <SheetHeader className="pb-4">
            <SheetTitle className="text-left">Plus d&apos;options</SheetTitle>
          </SheetHeader>
          
          <div className="grid grid-cols-4 gap-4 mb-6">
            {navigation.filter(item => !bottomNavItems.some(b => b.href === item.href)).slice(0, 8).map((item) => (
              <NavLink
                key={item.name}
                to={item.href}
                onClick={() => setMoreMenuOpen(false)}
                className={`
                  flex flex-col items-center gap-2 p-3 rounded-xl transition-all
                  ${location.pathname === item.href 
                    ? "bg-primary/10 text-primary" 
                    : "text-muted-foreground hover:bg-white/5 active:bg-white/10"
                  }
                `}
              >
                <item.icon className="w-6 h-6" />
                <span className="text-xs text-center font-medium">{item.name}</span>
              </NavLink>
            ))}
          </div>

          {/* User info & logout */}
          <div className="border-t border-white/10 pt-4">
            <div className="flex items-center gap-3 mb-4 px-2">
              <Avatar className="w-12 h-12">
                <AvatarFallback className="bg-secondary text-lg">
                  {getInitials(user?.name)}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1">
                <p className="font-semibold">{user?.name}</p>
                <p className="text-sm text-muted-foreground capitalize">{user?.trading_level}</p>
              </div>
              <NavLink 
                to="/settings"
                onClick={() => setMoreMenuOpen(false)}
                className="p-2 rounded-full hover:bg-white/5"
              >
                <Settings className="w-5 h-5 text-muted-foreground" />
              </NavLink>
            </div>
            
            <Button
              variant="ghost"
              className="w-full justify-center text-destructive hover:text-destructive hover:bg-destructive/10 min-h-[48px] rounded-xl"
              onClick={() => {
                setMoreMenuOpen(false);
                logout();
              }}
              data-testid="logout-btn-mobile"
            >
              <LogOut className="w-4 h-4 mr-2" />
              Déconnexion
            </Button>
          </div>
        </SheetContent>
      </Sheet>
    </div>
  );
}
