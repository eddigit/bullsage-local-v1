import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useState, useEffect, createContext, useContext } from "react";
import { Toaster } from "sonner";
import axios from "axios";

// Pages
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import DashboardPage from "./pages/DashboardPage";
import MarketsPage from "./pages/MarketsPage";
import AssistantPage from "./pages/AssistantPage";
import PaperTradingPage from "./pages/PaperTradingPage";
import StrategiesPage from "./pages/StrategiesPage";
import AlertsPage from "./pages/AlertsPage";
import SettingsPage from "./pages/SettingsPage";
import AdminPage from "./pages/AdminPage";
import ApiKeysPage from "./pages/ApiKeysPage";
import MarketIntelligencePage from "./pages/MarketIntelligencePage";
import SignalsPage from "./pages/SignalsPage";
import TradingModePage from "./pages/TradingModePage";
import JournalPage from "./pages/JournalPage";
import CockpitPage from "./pages/CockpitPage";
import AcademyPage from "./pages/AcademyPage";
import ModulePage from "./pages/ModulePage";
import OnboardingPage from "./pages/OnboardingPage";
import SmartInvestPage from "./pages/SmartInvestPage";
import AutoTradingPage from "./pages/AutoTradingPage";
import WalletPage from "./pages/WalletPage";
import DeFiScannerPage from "./pages/DeFiScannerPage";
import ChartPage from "./pages/ChartPage";

// Layout
import MainLayout from "./layouts/MainLayout";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
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
    if (error.response?.status === 401) {
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
    setUser(newUserData);
    localStorage.setItem("user", JSON.stringify(newUserData));
  };

  // Check if user needs onboarding
  const needsOnboarding = user && !user.onboarding_completed;

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading, updateUser }}>
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
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/onboarding" element={
              user ? <OnboardingPage /> : <Navigate to="/login" replace />
            } />
            
            <Route path="/" element={
              <ProtectedRoute>
                <MainLayout />
              </ProtectedRoute>
            }>
              <Route index element={<DashboardPage />} />
              <Route path="markets" element={<MarketsPage />} />
              <Route path="assistant" element={<AssistantPage />} />
              <Route path="paper-trading" element={<PaperTradingPage />} />
              <Route path="strategies" element={<StrategiesPage />} />
              <Route path="alerts" element={<AlertsPage />} />
              <Route path="settings" element={<SettingsPage />} />
              <Route path="intelligence" element={<MarketIntelligencePage />} />
              <Route path="signals" element={<SignalsPage />} />
              <Route path="trading" element={<TradingModePage />} />
              <Route path="journal" element={<JournalPage />} />
              <Route path="cockpit" element={<CockpitPage />} />
              <Route path="academy" element={<AcademyPage />} />
              <Route path="academy/module/:moduleId" element={<ModulePage />} />
              <Route path="admin" element={<AdminPage />} />
              <Route path="admin/api-keys" element={<ApiKeysPage />} />
              <Route path="smart-invest" element={<SmartInvestPage />} />
              <Route path="auto-trading" element={<AutoTradingPage />} />
              <Route path="wallet" element={<WalletPage />} />
              <Route path="defi-scanner" element={<DeFiScannerPage />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </div>
    </AuthContext.Provider>
  );
}

export default App;
