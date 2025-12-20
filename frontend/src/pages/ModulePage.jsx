import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import ReactMarkdown from "react-markdown";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Progress } from "../components/ui/progress";
import { ScrollArea } from "../components/ui/scroll-area";
import { RadioGroup, RadioGroupItem } from "../components/ui/radio-group";
import { Label } from "../components/ui/label";
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle,
  Circle,
  BookOpen,
  Brain,
  Trophy,
  Zap,
  Star,
  PartyPopper,
  X,
  RotateCcw
} from "lucide-react";

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Celebration Modal
function CelebrationModal({ isOpen, onClose, result }) {
  if (!isOpen) return null;

  const passed = result?.passed;

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
      <Card className={`glass border max-w-md w-full ${passed ? 'border-green-500/30' : 'border-red-500/30'}`}>
        <CardContent className="p-8 text-center">
          <div className="text-6xl mb-4">
            {passed ? "🎉" : "💪"}
          </div>
          <h2 className="text-2xl font-bold mb-2">
            {passed ? "Félicitations !" : "Pas encore..."}
          </h2>
          <p className="text-muted-foreground mb-4">
            {passed 
              ? `Tu as réussi avec ${result.percentage}% !` 
              : `Tu as obtenu ${result.percentage}%. Il faut ${result.passing_score}% pour valider.`
            }
          </p>
          
          <div className="flex justify-center items-center gap-4 mb-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-primary">{result.score}</div>
              <div className="text-xs text-muted-foreground">Bonnes réponses</div>
            </div>
            <div className="text-2xl text-muted-foreground">/</div>
            <div className="text-center">
              <div className="text-3xl font-bold">{result.total}</div>
              <div className="text-xs text-muted-foreground">Questions</div>
            </div>
          </div>

          {passed && result.xp_earned > 0 && (
            <div className="flex items-center justify-center gap-2 mb-4 text-amber-500">
              <Zap className="w-5 h-5" />
              <span className="font-bold">+{result.xp_earned} XP gagnés !</span>
            </div>
          )}

          {result.badges_earned?.length > 0 && (
            <div className="mb-4">
              <p className="text-sm text-muted-foreground mb-2">Nouveaux badges :</p>
              <div className="flex justify-center gap-2">
                {result.badges_earned.map((badge) => (
                  <Badge key={badge} variant="outline" className="border-amber-500/30 text-amber-500">
                    🏆 {badge}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          <div className="flex gap-3">
            {!passed && (
              <Button onClick={onClose} variant="outline" className="flex-1">
                <RotateCcw className="w-4 h-4 mr-2" />
                Réessayer
              </Button>
            )}
            <Button onClick={onClose} className={`flex-1 ${passed ? 'bg-green-600 hover:bg-green-700' : ''}`}>
              {passed ? "Continuer" : "Voir les corrections"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// Lesson Content Component
function LessonContent({ lesson, onComplete, isCompleted }) {
  return (
    <Card className="glass border-white/10">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <Badge variant="outline" className="mb-2 border-primary/30 text-primary">
              <Zap className="w-3 h-3 mr-1" />
              +{lesson.xp_reward} XP
            </Badge>
            <CardTitle className="text-xl">{lesson.title}</CardTitle>
            <CardDescription>{lesson.description}</CardDescription>
          </div>
          {isCompleted && (
            <CheckCircle className="w-8 h-8 text-green-500" />
          )}
        </div>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[500px] pr-4">
          <div className="prose prose-invert prose-sm max-w-none">
            <ReactMarkdown
              components={{
                h1: ({ children }) => <h1 className="text-2xl font-bold text-foreground mb-4 mt-6 first:mt-0">{children}</h1>,
                h2: ({ children }) => <h2 className="text-xl font-semibold text-foreground mb-3 mt-5">{children}</h2>,
                h3: ({ children }) => <h3 className="text-lg font-semibold text-foreground mb-2 mt-4">{children}</h3>,
                p: ({ children }) => <p className="text-muted-foreground mb-3 leading-relaxed">{children}</p>,
                ul: ({ children }) => <ul className="list-disc list-inside space-y-1 mb-4 text-muted-foreground">{children}</ul>,
                ol: ({ children }) => <ol className="list-decimal list-inside space-y-1 mb-4 text-muted-foreground">{children}</ol>,
                li: ({ children }) => <li className="text-muted-foreground">{children}</li>,
                strong: ({ children }) => <strong className="text-foreground font-semibold">{children}</strong>,
                blockquote: ({ children }) => (
                  <blockquote className="border-l-4 border-primary pl-4 py-2 my-4 bg-primary/10 rounded-r-lg italic text-foreground">
                    {children}
                  </blockquote>
                ),
                code: ({ children }) => (
                  <code className="bg-white/10 px-2 py-1 rounded text-sm font-mono text-primary">{children}</code>
                ),
                pre: ({ children }) => (
                  <pre className="bg-black/50 p-4 rounded-lg overflow-x-auto my-4 border border-white/10">
                    {children}
                  </pre>
                ),
                table: ({ children }) => (
                  <div className="overflow-x-auto my-4">
                    <table className="w-full border-collapse border border-white/20 rounded-lg">{children}</table>
                  </div>
                ),
                th: ({ children }) => (
                  <th className="border border-white/20 px-4 py-2 bg-white/10 text-left font-semibold">{children}</th>
                ),
                td: ({ children }) => (
                  <td className="border border-white/20 px-4 py-2">{children}</td>
                ),
                hr: () => <hr className="my-6 border-white/10" />,
              }}
            >
              {lesson.content}
            </ReactMarkdown>
          </div>
        </ScrollArea>
        
        {!isCompleted && (
          <div className="mt-6 pt-4 border-t border-white/10">
            <Button onClick={onComplete} className="w-full" size="lg">
              <CheckCircle className="w-5 h-5 mr-2" />
              Marquer comme terminé (+{lesson.xp_reward} XP)
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// Quiz Component
function QuizComponent({ quiz, onSubmit, result }) {
  const [answers, setAnswers] = useState({});
  const [showResults, setShowResults] = useState(false);

  const handleAnswer = (questionId, answerIndex) => {
    setAnswers(prev => ({ ...prev, [questionId]: answerIndex }));
  };

  const handleSubmit = () => {
    onSubmit(answers);
    setShowResults(true);
  };

  const allAnswered = quiz.questions.every(q => answers[q.id] !== undefined);

  return (
    <Card className="glass border-white/10">
      <CardHeader>
        <div className="flex items-center gap-2">
          <Brain className="w-6 h-6 text-primary" />
          <div>
            <CardTitle>{quiz.title}</CardTitle>
            <CardDescription>{quiz.description}</CardDescription>
          </div>
        </div>
        <div className="flex items-center gap-4 mt-2">
          <Badge variant="outline">
            {quiz.questions.length} questions
          </Badge>
          <Badge variant="outline" className="border-green-500/30 text-green-400">
            Minimum {quiz.passing_score}% pour valider
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[500px] pr-4">
          <div className="space-y-6">
            {quiz.questions.map((question, qIndex) => {
              const isCorrect = result?.correct_answers?.[question.id];
              const showResult = showResults && result;
              
              return (
                <div 
                  key={question.id} 
                  className={`p-4 rounded-lg border ${
                    showResult 
                      ? isCorrect 
                        ? 'border-green-500/30 bg-green-500/10' 
                        : 'border-red-500/30 bg-red-500/10'
                      : 'border-white/10 bg-white/5'
                  }`}
                >
                  <div className="flex items-start gap-3 mb-4">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                      showResult
                        ? isCorrect ? 'bg-green-500 text-black' : 'bg-red-500 text-white'
                        : 'bg-primary text-black'
                    }`}>
                      {qIndex + 1}
                    </div>
                    <p className="font-medium flex-1">{question.question}</p>
                  </div>
                  
                  <RadioGroup 
                    value={answers[question.id]?.toString()} 
                    onValueChange={(value) => !showResults && handleAnswer(question.id, parseInt(value))}
                    className="space-y-2"
                  >
                    {question.options.map((option, oIndex) => {
                      const isSelected = answers[question.id] === oIndex;
                      const isCorrectAnswer = result && quiz.questions.find(q => q.id === question.id)?.correct_answer === oIndex;
                      
                      return (
                        <div 
                          key={oIndex}
                          className={`flex items-center space-x-3 p-3 rounded-lg border cursor-pointer transition-all ${
                            showResult
                              ? isCorrectAnswer
                                ? 'border-green-500 bg-green-500/20'
                                : isSelected && !isCorrect
                                  ? 'border-red-500 bg-red-500/20'
                                  : 'border-white/10'
                              : isSelected
                                ? 'border-primary bg-primary/20'
                                : 'border-white/10 hover:border-white/30'
                          }`}
                        >
                          <RadioGroupItem 
                            value={oIndex.toString()} 
                            id={`${question.id}-${oIndex}`}
                            disabled={showResults}
                          />
                          <Label 
                            htmlFor={`${question.id}-${oIndex}`}
                            className="flex-1 cursor-pointer"
                          >
                            {option}
                          </Label>
                          {showResult && isCorrectAnswer && (
                            <CheckCircle className="w-5 h-5 text-green-500" />
                          )}
                          {showResult && isSelected && !isCorrect && !isCorrectAnswer && (
                            <X className="w-5 h-5 text-red-500" />
                          )}
                        </div>
                      );
                    })}
                  </RadioGroup>
                  
                  {showResult && result?.explanations?.[question.id] && (
                    <div className="mt-3 p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                      <p className="text-sm text-blue-400">
                        💡 {result.explanations[question.id]}
                      </p>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </ScrollArea>
        
        {!showResults && (
          <div className="mt-6 pt-4 border-t border-white/10">
            <Button 
              onClick={handleSubmit} 
              className="w-full" 
              size="lg"
              disabled={!allAnswered}
            >
              <Trophy className="w-5 h-5 mr-2" />
              {allAnswered 
                ? "Valider mes réponses" 
                : `Réponds à toutes les questions (${Object.keys(answers).length}/${quiz.questions.length})`
              }
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default function ModulePage() {
  const { moduleId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [module, setModule] = useState(null);
  const [currentView, setCurrentView] = useState("lessons"); // lessons, lesson, quiz
  const [currentLesson, setCurrentLesson] = useState(null);
  const [completedLessons, setCompletedLessons] = useState([]);
  const [quiz, setQuiz] = useState(null);
  const [quizResult, setQuizResult] = useState(null);
  const [showCelebration, setShowCelebration] = useState(false);

  useEffect(() => {
    fetchModuleData();
  }, [moduleId]);

  const fetchModuleData = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(`${API_URL}/api/academy/modules/${moduleId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setModule(response.data);
      setCompletedLessons(response.data.lessons.filter(l => l.completed).map(l => l.id));
    } catch (error) {
      console.error("Error fetching module:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleLessonSelect = async (lesson) => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(`${API_URL}/api/academy/lessons/${lesson.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCurrentLesson(response.data.lesson);
      setCurrentView("lesson");
    } catch (error) {
      console.error("Error fetching lesson:", error);
    }
  };

  const handleLessonComplete = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.post(
        `${API_URL}/api/academy/lessons/${currentLesson.id}/complete`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      setCompletedLessons(prev => [...prev, currentLesson.id]);
      
      // Show celebration if XP earned
      if (response.data.xp_earned > 0) {
        setQuizResult({
          passed: true,
          xp_earned: response.data.xp_earned,
          badges_earned: response.data.badges_earned,
          percentage: 100,
          score: 1,
          total: 1
        });
        setShowCelebration(true);
      }
      
      // Go to next lesson or back to list
      const currentIndex = module.lessons.findIndex(l => l.id === currentLesson.id);
      if (currentIndex < module.lessons.length - 1) {
        handleLessonSelect(module.lessons[currentIndex + 1]);
      } else {
        setCurrentView("lessons");
      }
    } catch (error) {
      console.error("Error completing lesson:", error);
    }
  };

  const handleStartQuiz = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(`${API_URL}/api/academy/quiz/${moduleId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setQuiz(response.data);
      setQuizResult(null);
      setCurrentView("quiz");
    } catch (error) {
      console.error("Error fetching quiz:", error);
    }
  };

  const handleQuizSubmit = async (answers) => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.post(
        `${API_URL}/api/academy/quiz/${moduleId}/submit`,
        { lesson_id: moduleId, answers },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setQuizResult(response.data);
      setShowCelebration(true);
    } catch (error) {
      console.error("Error submitting quiz:", error);
    }
  };

  const handleCelebrationClose = () => {
    setShowCelebration(false);
    if (quizResult?.passed) {
      navigate("/academy");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Chargement du module...</p>
        </div>
      </div>
    );
  }

  if (!module) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">Module non trouvé</p>
        <Button onClick={() => navigate("/academy")} className="mt-4">
          Retour à l'Académie
        </Button>
      </div>
    );
  }

  const allLessonsCompleted = module.lessons.every(l => completedLessons.includes(l.id));

  return (
    <div className="space-y-6 pb-8">
      <CelebrationModal 
        isOpen={showCelebration} 
        onClose={handleCelebrationClose}
        result={quizResult}
      />

      {/* Header */}
      <div className="flex items-center gap-4">
        <Button 
          variant="ghost" 
          onClick={() => currentView === "lessons" ? navigate("/academy") : setCurrentView("lessons")}
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Retour
        </Button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <span className="text-4xl">{module.icon}</span>
            <div>
              <h1 className="text-2xl font-bold">{module.title}</h1>
              <p className="text-muted-foreground text-sm">{module.description}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Progress */}
      <Card className="glass border-white/10">
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-muted-foreground">
              Progression du module
            </span>
            <span className="text-sm font-medium">
              {completedLessons.length}/{module.lessons.length} leçons
            </span>
          </div>
          <Progress 
            value={(completedLessons.length / module.lessons.length) * 100} 
            className="h-3"
          />
        </CardContent>
      </Card>

      {/* Main Content */}
      {currentView === "lessons" && (
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Lessons List */}
          <div className="lg:col-span-2 space-y-3">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-primary" />
              Leçons
            </h2>
            {module.lessons.map((lesson, index) => {
              const isCompleted = completedLessons.includes(lesson.id);
              return (
                <Card 
                  key={lesson.id}
                  className={`glass border cursor-pointer transition-all hover:bg-white/10 ${
                    isCompleted ? 'border-green-500/30' : 'border-white/10'
                  }`}
                  onClick={() => handleLessonSelect(lesson)}
                >
                  <CardContent className="p-4 flex items-center gap-4">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                      isCompleted 
                        ? 'bg-green-500 text-white' 
                        : 'bg-white/10 text-muted-foreground'
                    }`}>
                      {isCompleted ? <CheckCircle className="w-5 h-5" /> : index + 1}
                    </div>
                    <div className="flex-1">
                      <h3 className="font-medium">{lesson.title}</h3>
                      <p className="text-sm text-muted-foreground">{lesson.description}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="border-amber-500/30 text-amber-500">
                        +{lesson.xp_reward} XP
                      </Badge>
                      <ArrowRight className="w-4 h-4 text-muted-foreground" />
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>

          {/* Quiz Card */}
          <div>
            <h2 className="text-lg font-semibold flex items-center gap-2 mb-3">
              <Brain className="w-5 h-5 text-primary" />
              Quiz Final
            </h2>
            <Card className={`glass border ${allLessonsCompleted ? 'border-primary/30' : 'border-white/10 opacity-60'}`}>
              <CardContent className="p-6 text-center">
                <Trophy className="w-12 h-12 mx-auto mb-4 text-amber-500" />
                <h3 className="font-semibold mb-2">{module.quiz_info?.title}</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  {module.quiz_info?.question_count} questions • Minimum {module.quiz_info?.passing_score}%
                </p>
                
                {!allLessonsCompleted ? (
                  <div className="text-sm text-muted-foreground">
                    <p>🔒 Termine toutes les leçons pour débloquer le quiz</p>
                  </div>
                ) : (
                  <Button onClick={handleStartQuiz} className="w-full">
                    <Brain className="w-4 h-4 mr-2" />
                    Commencer le Quiz
                  </Button>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {currentView === "lesson" && currentLesson && (
        <div className="max-w-4xl mx-auto">
          <LessonContent 
            lesson={currentLesson}
            onComplete={handleLessonComplete}
            isCompleted={completedLessons.includes(currentLesson.id)}
          />
        </div>
      )}

      {currentView === "quiz" && quiz && (
        <div className="max-w-3xl mx-auto">
          <QuizComponent 
            quiz={quiz}
            onSubmit={handleQuizSubmit}
            result={quizResult}
          />
        </div>
      )}
    </div>
  );
}
