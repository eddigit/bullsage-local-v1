import { Outlet, NavLink, useLocation } from "react-router-dom";
import { useAuth } from "../App";
import { useState } from "react";
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
  Shield
} from "lucide-react";
import { Button } from "../components/ui/button";
import { ScrollArea } from "../components/ui/scroll-area";
import { Avatar, AvatarFallback } from "../components/ui/avatar";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "../components/ui/tooltip";

const navigation = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Marchés", href: "/markets", icon: TrendingUp },
  { name: "Assistant IA", href: "/assistant", icon: MessageCircle, highlight: true },
  { name: "Paper Trading", href: "/paper-trading", icon: Wallet },
  { name: "Stratégies", href: "/strategies", icon: Target },
  { name: "Alertes", href: "/alerts", icon: Bell },
  { name: "Paramètres", href: "/settings", icon: Settings },
];

const adminNavigation = [
  { name: "Administration", href: "/admin", icon: Shield, admin: true },
];

export default function MainLayout() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const getInitials = (name) => {
    return name?.split(" ").map(n => n[0]).join("").toUpperCase() || "U";
  };

  const NavItem = ({ item, mobile = false }) => {
    const isActive = location.pathname === item.href;
    
    return (
      <NavLink
        to={item.href}
        onClick={() => mobile && setSidebarOpen(false)}
        className={`
          flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200
          ${isActive 
            ? "bg-primary/10 text-primary border border-primary/20" 
            : "text-muted-foreground hover:text-foreground hover:bg-white/5"
          }
          ${item.highlight && !isActive ? "text-violet-400 hover:text-violet-300" : ""}
          ${item.admin && !isActive ? "text-violet-400 hover:text-violet-300" : ""}
        `}
        data-testid={`nav-${item.name.toLowerCase().replace(/\s+/g, '-')}`}
      >
        <item.icon className={`w-5 h-5 ${(item.highlight || item.admin) && !isActive ? "text-violet-400" : ""}`} />
        <span className="font-medium">{item.name}</span>
        {item.highlight && (
          <Zap className="w-4 h-4 ml-auto text-violet-400" />
        )}
        {item.admin && (
          <Shield className="w-4 h-4 ml-auto text-violet-400" />
        )}
      </NavLink>
    );
  };

  return (
    <TooltipProvider>
      <div className="min-h-screen bg-background">
        {/* Mobile Header */}
        <header className="md:hidden fixed top-0 left-0 right-0 h-16 glass-heavy z-50 flex items-center justify-between px-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setSidebarOpen(true)}
            data-testid="mobile-menu-btn"
          >
            <Menu className="w-6 h-6" />
          </Button>
          
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
              <TrendingUp className="w-5 h-5 text-black" />
            </div>
            <span className="font-bold text-lg font-manrope">BULL SAGE</span>
          </div>

          <Avatar className="w-8 h-8">
            <AvatarFallback className="bg-secondary text-sm">
              {getInitials(user?.name)}
            </AvatarFallback>
          </Avatar>
        </header>

        {/* Mobile Sidebar Overlay */}
        {sidebarOpen && (
          <div 
            className="md:hidden fixed inset-0 bg-black/60 z-50"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Sidebar */}
        <aside className={`
          fixed top-0 left-0 h-full w-64 glass-heavy z-50 
          transform transition-transform duration-300 ease-out
          md:translate-x-0
          ${sidebarOpen ? "translate-x-0" : "-translate-x-full"}
        `}>
          <div className="flex flex-col h-full">
            {/* Logo */}
            <div className="h-16 flex items-center justify-between px-4 border-b border-white/5">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-primary flex items-center justify-center glow-primary">
                  <TrendingUp className="w-6 h-6 text-black" />
                </div>
                <div>
                  <h1 className="font-bold text-lg font-manrope tracking-tight">BULL SAGE</h1>
                  <p className="text-xs text-muted-foreground">Trading Assistant</p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="icon"
                className="md:hidden"
                onClick={() => setSidebarOpen(false)}
              >
                <X className="w-5 h-5" />
              </Button>
            </div>

            {/* Navigation */}
            <ScrollArea className="flex-1 px-3 py-4">
              <nav className="space-y-1">
                {navigation.map((item) => (
                  <NavItem key={item.name} item={item} mobile />
                ))}
                
                {/* Admin Navigation */}
                {user?.is_admin && (
                  <>
                    <div className="my-4 border-t border-white/5" />
                    {adminNavigation.map((item) => (
                      <NavItem key={item.name} item={item} mobile />
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
                className="w-full justify-start text-muted-foreground hover:text-destructive"
                onClick={logout}
                data-testid="logout-btn"
              >
                <LogOut className="w-4 h-4 mr-2" />
                Déconnexion
              </Button>
            </div>
          </div>
        </aside>

        {/* Main Content */}
        <main className="md:ml-64 min-h-screen pt-16 md:pt-0">
          <div className="p-4 md:p-6">
            <Outlet />
          </div>
        </main>
      </div>
    </TooltipProvider>
  );
}
