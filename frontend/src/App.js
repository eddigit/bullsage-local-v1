import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useState, useEffect, createContext, useContext } from "react";
import { Toaster } from "sonner";
import axios from "axios";
import { logger } from "./lib/logger";

// Pages - SIMPLIFIÉ : Focus sur le trading Deribit
import LandingPage from "./pages/LandingPage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import OnboardingPage from "./pages/OnboardingPage";

// Core Trading Pages
import DashboardPage from "./pages/DashboardPage";
import ProTraderPage from "./pages/ProTraderPage";      // Signaux IA + Indicateurs + News
import DeribitTradingPage from "./pages/DeribitTradingPage"; // Exécution trades Deribit
import JournalPage from "./pages/JournalPage";          // Historique + Stats
import ChartPage from "./pages/ChartPage";              // Graphiques

// Learning & Settings
import AcademyPage from "./pages/AcademyPage";
import ModulePage from "./pages/ModulePage";
import SettingsPage from "./pages/SettingsPage";

// Admin
import AdminPage from "./pages/AdminPage";
import ApiKeysPage from "./pages/ApiKeysPage";
import NewsletterAdminPage from "./pages/NewsletterAdminPage";

// Layout
import MainLayout from "./layouts/MainLayout";

// Detect environment - use Render backend URL in production
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 
  (window.location.hostname === 'localhost' 
    ? 'http://localhost:8000' 
    : 'https://bullsage-api.onrender.com');
export const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
};

// DEV MODE - Contrôlé via variable d'environnement (désactivé en production)
const DEV_MODE = process.env.REACT_APP_DEV_MODE === 'true';

// Axios interceptor for auth
axios.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

axios.interceptors.response.use(
  (response) => response,
  (error) => {
    // Token expiré ou invalide : déconnecter et rediriger vers login
    if (!DEV_MODE && error.response?.status === 401) {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
          <p className="text-muted-foreground">Chargement...</p>
        </div>
      </div>
    );
  }
  
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  
  return children;
};

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [systemHealth, setSystemHealth] = useState(null);

  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem("token");
      const savedUser = localStorage.getItem("user");
      
      if (token && savedUser) {
        try {
          const response = await axios.get(`${API}/auth/me`);
          setUser(response.data);
          localStorage.setItem("user", JSON.stringify(response.data));
        } catch (error) {
          localStorage.removeItem("token");
          localStorage.removeItem("user");
        }
      }
      setLoading(false);
    };

    initAuth();

    // Startup healthcheck — non-blocking
    const runHealthCheck = async () => {
      try {
        const res = await axios.get(`${API}/system/health`);
        setSystemHealth(res.data);
        if (res.data?.status !== "healthy") {
          const degraded = Object.entries(res.data?.services || {})
            .filter(([, s]) => s.status === "error")
            .map(([k]) => k);
          if (degraded.length > 0) {
            logger.warn(`Services dégradés: ${degraded.join(", ")}`, { services: degraded });
          }
        } else {
          logger.info("System health check passed");
        }
      } catch (e) {
        logger.error("Healthcheck failed — backend unreachable", { error: e.message });
        setSystemHealth({ status: "error", services: {} });
      }
    };
    runHealthCheck();
  }, []);

  const login = async (email, password) => {
    const response = await axios.post(`${API}/auth/login`, { email, password });
    const { access_token, user: userData } = response.data;
    localStorage.setItem("token", access_token);
    localStorage.setItem("user", JSON.stringify(userData));
    setUser(userData);
    return userData;
  };

  const register = async (name, email, password, trading_level) => {
    const response = await axios.post(`${API}/auth/register`, {
      name,
      email,
      password,
      trading_level
    });
    const { access_token, user: userData } = response.data;
    localStorage.setItem("token", access_token);
    localStorage.setItem("user", JSON.stringify(userData));
    setUser(userData);
    // Return with flag indicating new user for onboarding
    return { ...userData, isNewUser: true };
  };

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setUser(null);
  };

  const updateUser = (newUserData) => {
    // Merge with existing user data to avoid losing fields
    const merged = user ? { ...user, ...newUserData } : newUserData;
    setUser(merged);
    localStorage.setItem("user", JSON.stringify(merged));
  };

  // Check if user needs onboarding
  const needsOnboarding = user && !user.onboarding_completed;

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading, updateUser, systemHealth }}>
      <div className="dark">
        <Toaster 
          position="top-right" 
          richColors 
          theme="dark"
          toastOptions={{
            style: {
              background: 'rgba(9, 9, 11, 0.9)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              backdropFilter: 'blur(12px)',
            },
          }}
        />
        <BrowserRouter>
          <Routes>
            {/* Landing page for non-authenticated users */}
            <Route path="/" element={
              user ? <Navigate to="/dashboard" replace /> : <LandingPage />
            } />
            <Route path="/login" element={
              user ? <Navigate to="/dashboard" replace /> : <LoginPage />
            } />
            <Route path="/register" element={
              user ? <Navigate to="/dashboard" replace /> : <RegisterPage />
            } />
            <Route path="/onboarding" element={
              user ? <OnboardingPage /> : <Navigate to="/login" replace />
            } />
            
            <Route path="/dashboard" element={
              <ProtectedRoute>
                {needsOnboarding ? <Navigate to="/onboarding" replace /> : <MainLayout />}
              </ProtectedRoute>
            }>
              {/* Core Trading Flow */}
              <Route index element={<DashboardPage />} />
              <Route path="pro-trader" element={<ProTraderPage />} />
              <Route path="deribit-trading" element={<DeribitTradingPage />} />
              <Route path="chart" element={<ChartPage />} />
              <Route path="journal" element={<JournalPage />} />
              
              {/* Learning */}
              <Route path="academy" element={<AcademyPage />} />
              <Route path="academy/module/:moduleId" element={<ModulePage />} />
              
              {/* Settings */}
              <Route path="settings" element={<SettingsPage />} />
              
              {/* Admin */}
              <Route path="admin" element={<AdminPage />} />
              <Route path="admin/api-keys" element={<ApiKeysPage />} />
              <Route path="admin/newsletter" element={<NewsletterAdminPage />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </div>
    </AuthContext.Provider>
  );
}

export default App;
