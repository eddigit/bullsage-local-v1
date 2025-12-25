import { useState, useEffect, useRef } from "react";
import { API, useAuth } from "../App";
import axios from "axios";
import { toast } from "sonner";
import ReactMarkdown from "react-markdown";
import {
  Send,
  Sparkles,
  User,
  Loader2,
  TrendingUp,
  Lightbulb,
  Target,
  AlertTriangle,
  RefreshCw
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Textarea } from "../components/ui/textarea";
import { ScrollArea } from "../components/ui/scroll-area";
import { Badge } from "../components/ui/badge";
import { chatMarkdownComponents } from "../components/MarkdownComponents";

const QUICK_PROMPTS = [
  { icon: TrendingUp, text: "Analyse BTC/USD pour aujourd'hui", color: "text-emerald-500" },
  { icon: Lightbulb, text: "Quels signaux surveiller ce jour?", color: "text-yellow-500" },
  { icon: Target, text: "Meilleurs points d'entrée crypto", color: "text-blue-500" },
  { icon: AlertTriangle, text: "Risques majeurs du marché", color: "text-rose-500" },
];

export default function AssistantPage() {
  const { user } = useAuth();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [marketContext, setMarketContext] = useState(null);
  const scrollRef = useRef(null);
  const inputRef = useRef(null);

  // Fetch chat history
  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const response = await axios.get(`${API}/assistant/history?limit=20`);
        const historyData = Array.isArray(response.data) ? response.data : [];
        const formattedMessages = historyData.flatMap(item => [
          { role: "user", content: item.message, timestamp: item.timestamp },
          { role: "assistant", content: item.response, timestamp: item.timestamp }
        ]);
        setMessages(formattedMessages);
      } catch (error) {
        console.error("Error fetching history:", error);
      } finally {
        setLoadingHistory(false);
      }
    };

    fetchHistory();
  }, []);

  // Fetch market context for AI
  useEffect(() => {
    const fetchMarketContext = async () => {
      try {
        const response = await axios.get(`${API}/market/crypto`);
        const marketData = Array.isArray(response.data) ? response.data : [];
        setMarketContext(marketData.slice(0, 10));
      } catch (error) {
        console.error("Error fetching market context:", error);
      }
    };

    fetchMarketContext();
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const sendMessage = async (text = input) => {
    if (!text.trim() || loading) return;

    const userMessage = {
      role: "user",
      content: text,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const response = await axios.post(`${API}/assistant/chat`, {
        message: text,
        context: {
          watchlist_data: marketContext
        }
      });

      const assistantMessage = {
        role: "assistant",
        content: response.data.response,
        timestamp: response.data.timestamp
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error("Error sending message:", error);
      toast.error("Erreur de communication avec l'assistant");
      
      // Remove the user message if error
      setMessages(prev => prev.slice(0, -1));
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleQuickPrompt = (text) => {
    setInput(text);
    sendMessage(text);
  };

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col" data-testid="assistant-page">
      {/* Header */}
      <div className="mb-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center glow-accent">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold font-manrope">BULL SAGE</h1>
            <p className="text-sm text-muted-foreground">
              Votre assistant trading IA • Niveau: {user?.trading_level || "beginner"}
            </p>
          </div>
        </div>
      </div>

      {/* Chat Container */}
      <Card className="glass border-white/5 flex-1 flex flex-col overflow-hidden">
        <CardContent className="flex-1 flex flex-col p-0 overflow-hidden">
          {/* Messages */}
          <ScrollArea className="flex-1 p-4" ref={scrollRef}>
            {loadingHistory ? (
              <div className="flex items-center justify-center h-full">
                <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
              </div>
            ) : messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center px-4">
                <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-violet-500/20 to-fuchsia-500/20 flex items-center justify-center mb-6">
                  <Sparkles className="w-10 h-10 text-violet-400" />
                </div>
                <h2 className="text-xl font-bold font-manrope mb-2">
                  Bienvenue sur BULL SAGE
                </h2>
                <p className="text-muted-foreground max-w-md mb-8">
                  Je suis votre assistant trading intelligent. Je peux analyser les marchés,
                  vous donner des signaux de trading et vous aider à améliorer vos stratégies.
                </p>
                
                {/* Quick prompts */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 w-full max-w-lg">
                  {QUICK_PROMPTS.map((prompt, index) => (
                    <Button
                      key={index}
                      variant="outline"
                      className="justify-start h-auto py-3 px-4 border-white/10 hover:bg-white/5 hover:border-white/20"
                      onClick={() => handleQuickPrompt(prompt.text)}
                      data-testid={`quick-prompt-${index}`}
                    >
                      <prompt.icon className={`w-4 h-4 mr-2 ${prompt.color}`} />
                      <span className="text-sm text-left">{prompt.text}</span>
                    </Button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="space-y-4 pb-4">
                {messages.map((message, index) => (
                  <div
                    key={index}
                    className={`flex ${message.role === "user" ? "justify-end" : "justify-start"} animate-fade-in`}
                    data-testid={`message-${index}`}
                  >
                    <div
                      className={`max-w-[85%] md:max-w-[75%] ${
                        message.role === "user"
                          ? "chat-bubble-user"
                          : "chat-bubble-assistant"
                      } p-4`}
                    >
                      <div className="flex items-center gap-2 mb-2">
                        {message.role === "user" ? (
                          <>
                            <span className="text-sm font-medium text-primary">Vous</span>
                            <User className="w-4 h-4 text-primary" />
                          </>
                        ) : (
                          <>
                            <Sparkles className="w-4 h-4 text-violet-400" />
                            <span className="text-sm font-medium sage-gradient">BULL SAGE</span>
                          </>
                        )}
                      </div>
                      <div className="prose prose-sm prose-invert max-w-none">
                        {message.role === "assistant" ? (
                          <ReactMarkdown components={chatMarkdownComponents}>
                            {message.content}
                          </ReactMarkdown>
                        ) : (
                          <p className="whitespace-pre-wrap">{message.content}</p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
                
                {loading && (
                  <div className="flex justify-start animate-fade-in">
                    <div className="chat-bubble-assistant p-4">
                      <div className="flex items-center gap-2">
                        <Sparkles className="w-4 h-4 text-violet-400" />
                        <span className="text-sm font-medium sage-gradient">BULL SAGE</span>
                      </div>
                      <div className="flex items-center gap-2 mt-2">
                        <div className="flex space-x-1">
                          <div className="w-2 h-2 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                          <div className="w-2 h-2 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                          <div className="w-2 h-2 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                        </div>
                        <span className="text-sm text-muted-foreground">Analyse en cours...</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </ScrollArea>

          {/* Input Area */}
          <div className="p-4 border-t border-white/5 bg-black/20">
            <div className="flex gap-3">
              <Textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Posez votre question sur les marchés..."
                className="min-h-[52px] max-h-32 bg-black/20 border-white/10 focus:border-violet-500/50 resize-none"
                disabled={loading}
                data-testid="chat-input"
              />
              <Button
                onClick={() => sendMessage()}
                disabled={!input.trim() || loading}
                className="h-[52px] w-[52px] bg-gradient-to-br from-violet-500 to-fuchsia-500 hover:from-violet-600 hover:to-fuchsia-600"
                data-testid="send-btn"
              >
                {loading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Send className="w-5 h-5" />
                )}
              </Button>
            </div>
            <p className="text-xs text-muted-foreground mt-2 text-center">
              BULL SAGE peut faire des erreurs. Vérifiez toujours les informations importantes.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
