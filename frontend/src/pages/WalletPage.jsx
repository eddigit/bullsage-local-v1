import { useState, useEffect } from "react";
import axios from "axios";
import { toast } from "sonner";
import {
  Wallet,
  Plus,
  Trash2,
  RefreshCw,
  ExternalLink,
  Copy,
  Star,
  Check,
  AlertTriangle,
  Loader2
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { API } from "../App";

const CHAIN_LOGOS = {
  solana: "https://cryptologos.cc/logos/solana-sol-logo.png",
  ethereum: "https://cryptologos.cc/logos/ethereum-eth-logo.png",
  polygon: "https://cryptologos.cc/logos/polygon-matic-logo.png",
  bsc: "https://cryptologos.cc/logos/bnb-bnb-logo.png"
};

const WALLET_ICONS = {
  phantom: "/phantom-icon.png",
  metamask: "/metamask-icon.png"
};

export default function WalletPage() {
  const [wallets, setWallets] = useState([]);
  const [chains, setChains] = useState([]);
  const [loading, setLoading] = useState(true);
  const [balances, setBalances] = useState({});
  const [loadingBalance, setLoadingBalance] = useState({});
  const [showConnectDialog, setShowConnectDialog] = useState(false);
  const [connecting, setConnecting] = useState(false);
  
  // Form state
  const [selectedChain, setSelectedChain] = useState("solana");
  const [walletAddress, setWalletAddress] = useState("");
  const [copied, setCopied] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [walletsRes, chainsRes] = await Promise.all([
        axios.get(`${API}/wallet/list`),
        axios.get(`${API}/wallet/supported-chains`)
      ]);
      setWallets(walletsRes.data);
      setChains(chainsRes.data);
    } catch (error) {
      console.error("Load error:", error);
    } finally {
      setLoading(false);
    }
  };

  const loadBalance = async (walletId) => {
    setLoadingBalance(prev => ({ ...prev, [walletId]: true }));
    try {
      const response = await axios.get(`${API}/wallet/${walletId}/balance`);
      setBalances(prev => ({ ...prev, [walletId]: response.data }));
    } catch (error) {
      toast.error("Erreur lors du chargement du solde");
    } finally {
      setLoadingBalance(prev => ({ ...prev, [walletId]: false }));
    }
  };

  const connectWallet = async () => {
    if (!walletAddress) {
      toast.error("Veuillez entrer une adresse de wallet");
      return;
    }

    setConnecting(true);
    try {
      const chain = chains.find(c => c.id === selectedChain);
      const response = await axios.post(`${API}/wallet/connect`, {
        wallet_type: chain?.wallet_type || "metamask",
        address: walletAddress,
        chain: selectedChain
      });
      
      toast.success("Wallet connecté avec succès!");
      setShowConnectDialog(false);
      setWalletAddress("");
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erreur de connexion");
    } finally {
      setConnecting(false);
    }
  };

  const disconnectWallet = async (walletId) => {
    try {
      await axios.delete(`${API}/wallet/${walletId}`);
      toast.success("Wallet déconnecté");
      loadData();
    } catch (error) {
      toast.error("Erreur lors de la déconnexion");
    }
  };

  const copyAddress = (address) => {
    navigator.clipboard.writeText(address);
    setCopied(address);
    toast.success("Adresse copiée!");
    setTimeout(() => setCopied(null), 2000);
  };

  const formatAddress = (address) => {
    return `${address.slice(0, 6)}...${address.slice(-4)}`;
  };

  const getChainConfig = (chainId) => {
    return chains.find(c => c.id === chainId) || {};
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold font-manrope flex items-center gap-3">
            <Wallet className="w-8 h-8 text-primary" />
            Wallets DeFi
          </h1>
          <p className="text-muted-foreground mt-1">
            Connectez vos wallets Phantom et MetaMask
          </p>
        </div>
        
        <Dialog open={showConnectDialog} onOpenChange={setShowConnectDialog}>
          <DialogTrigger asChild>
            <Button className="bg-primary hover:bg-primary/90 text-black">
              <Plus className="w-4 h-4 mr-2" />
              Connecter un Wallet
            </Button>
          </DialogTrigger>
          <DialogContent className="glass border-white/10">
            <DialogHeader>
              <DialogTitle>Connecter un Wallet</DialogTitle>
              <DialogDescription>
                Entrez l'adresse de votre wallet pour le connecter
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Blockchain</Label>
                <Select value={selectedChain} onValueChange={setSelectedChain}>
                  <SelectTrigger className="bg-black/20 border-white/10">
                    <SelectValue placeholder="Sélectionnez une chain" />
                  </SelectTrigger>
                  <SelectContent>
                    {chains.map(chain => (
                      <SelectItem key={chain.id} value={chain.id}>
                        <div className="flex items-center gap-2">
                          <img 
                            src={CHAIN_LOGOS[chain.id]} 
                            alt={chain.name}
                            className="w-5 h-5 rounded-full"
                          />
                          {chain.name} ({chain.native_symbol})
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div className="space-y-2">
                <Label>Adresse du Wallet</Label>
                <Input
                  placeholder={selectedChain === "solana" ? "Ex: 7xKX..." : "Ex: 0x..."}
                  value={walletAddress}
                  onChange={(e) => setWalletAddress(e.target.value)}
                  className="bg-black/20 border-white/10 font-mono"
                />
              </div>
              
              <div className="flex items-start gap-2 text-sm text-muted-foreground bg-yellow-500/10 p-3 rounded-lg">
                <AlertTriangle className="w-4 h-4 text-yellow-500 mt-0.5 flex-shrink-0" />
                <p>
                  Utilisez <strong>{selectedChain === "solana" ? "Phantom" : "MetaMask"}</strong> pour cette blockchain.
                  La connexion est en lecture seule (visualisation du solde uniquement).
                </p>
              </div>
            </div>
            
            <DialogFooter>
              <Button variant="ghost" onClick={() => setShowConnectDialog(false)}>
                Annuler
              </Button>
              <Button 
                onClick={connectWallet}
                disabled={connecting || !walletAddress}
                className="bg-primary hover:bg-primary/90 text-black"
              >
                {connecting ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Wallet className="w-4 h-4 mr-2" />
                )}
                Connecter
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Wallets Grid */}
      {wallets.length === 0 ? (
        <Card className="glass border-white/5">
          <CardContent className="flex flex-col items-center justify-center py-16">
            <Wallet className="w-16 h-16 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">Aucun wallet connecté</h3>
            <p className="text-muted-foreground text-center mb-6 max-w-md">
              Connectez vos wallets Phantom (Solana) ou MetaMask (Ethereum, Polygon, BSC) 
              pour visualiser vos soldes et préparer vos trades DeFi.
            </p>
            <Button 
              onClick={() => setShowConnectDialog(true)}
              className="bg-primary hover:bg-primary/90 text-black"
            >
              <Plus className="w-4 h-4 mr-2" />
              Connecter mon premier wallet
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {wallets.map(wallet => {
            const chain = getChainConfig(wallet.chain);
            const balance = balances[wallet.id];
            const isLoadingBalance = loadingBalance[wallet.id];
            
            return (
              <Card key={wallet.id} className="glass border-white/5">
                <CardContent className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className="relative">
                        <img 
                          src={CHAIN_LOGOS[wallet.chain]}
                          alt={wallet.chain}
                          className="w-12 h-12 rounded-full"
                        />
                        {wallet.is_primary && (
                          <Star className="w-4 h-4 text-yellow-500 absolute -top-1 -right-1 fill-yellow-500" />
                        )}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold">{chain.name}</h3>
                          <Badge variant="outline" className="text-xs">
                            {wallet.wallet_type}
                          </Badge>
                        </div>
                        <button
                          onClick={() => copyAddress(wallet.address)}
                          className="flex items-center gap-1 text-sm text-muted-foreground hover:text-primary transition-colors font-mono"
                        >
                          {formatAddress(wallet.address)}
                          {copied === wallet.address ? (
                            <Check className="w-3 h-3 text-green-500" />
                          ) : (
                            <Copy className="w-3 h-3" />
                          )}
                        </button>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => window.open(`${chain.explorer}/address/${wallet.address}`, '_blank')}
                        className="h-8 w-8"
                      >
                        <ExternalLink className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => disconnectWallet(wallet.id)}
                        className="h-8 w-8 text-destructive hover:text-destructive"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                  
                  {/* Balance Section */}
                  <div className="bg-black/20 rounded-lg p-4">
                    {balance ? (
                      <div>
                        <p className="text-sm text-muted-foreground mb-1">Solde</p>
                        <div className="flex items-baseline gap-2">
                          <span className="text-2xl font-bold">
                            {balance.native_balance.toFixed(4)}
                          </span>
                          <span className="text-muted-foreground">
                            {balance.native_symbol}
                          </span>
                        </div>
                        <p className="text-emerald-500 text-sm mt-1">
                          ≈ ${balance.usd_value.toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </p>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => loadBalance(wallet.id)}
                          className="mt-2 text-xs"
                        >
                          <RefreshCw className="w-3 h-3 mr-1" />
                          Actualiser
                        </Button>
                      </div>
                    ) : (
                      <Button
                        variant="outline"
                        onClick={() => loadBalance(wallet.id)}
                        disabled={isLoadingBalance}
                        className="w-full border-white/10"
                      >
                        {isLoadingBalance ? (
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        ) : (
                          <RefreshCw className="w-4 h-4 mr-2" />
                        )}
                        Charger le solde
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Supported Chains Info */}
      <Card className="glass border-white/5">
        <CardHeader>
          <CardTitle className="text-lg">Blockchains supportées</CardTitle>
          <CardDescription>Connectez vos wallets sur ces réseaux</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {chains.map(chain => (
              <div 
                key={chain.id}
                className="flex items-center gap-3 p-3 rounded-lg bg-white/5"
              >
                <img 
                  src={CHAIN_LOGOS[chain.id]}
                  alt={chain.name}
                  className="w-8 h-8 rounded-full"
                />
                <div>
                  <p className="font-medium text-sm">{chain.name}</p>
                  <p className="text-xs text-muted-foreground">{chain.wallet_type}</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
