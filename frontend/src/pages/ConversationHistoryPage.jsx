import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { documentsApi, qaApi } from '@/lib/api';
import useAuthStore from '@/store/authStore';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Markdown } from '@/components/ui/markdown';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ArrowLeft, 
  MessageSquare, 
  ChevronLeft, 
  ChevronRight, 
  FileText,
  ExternalLink,
  LogOut,
  Sparkles
} from 'lucide-react';

function ConversationHistoryPage() {
  const { docId } = useParams();
  const navigate = useNavigate();
  const logout = useAuthStore((state) => state.logout);
  const [currentPage, setCurrentPage] = useState(0);
  const itemsPerPage = 10;

  // Fetch document details
  const { data: document } = useQuery({
    queryKey: ['document', docId],
    queryFn: async () => {
      const { data } = await documentsApi.get(docId);
      return data;
    },
  });

  // Fetch Q&A history with pagination
  const { data: qaHistory = [], isLoading } = useQuery({
    queryKey: ['documentQA', docId, currentPage],
    queryFn: async () => {
      const offset = currentPage * itemsPerPage;
      const { data } = await qaApi.getDocumentQA(docId, offset, itemsPerPage);
      return data;
    },
  });

  const totalPages = qaHistory.length < itemsPerPage ? currentPage + 1 : currentPage + 2;
  const hasNextPage = qaHistory.length === itemsPerPage;

  const handlePageChange = (newPage) => {
    setCurrentPage(Math.max(0, newPage));
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleNavigateToPage = (pageNo) => {
    navigate(`/doc/${docId}?page=${pageNo}`);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20">
      {/* Background decorative elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-primary/5 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-secondary/10 rounded-full blur-3xl" />
      </div>

      <div className="relative z-10">
        {/* Header */}
        <motion.header
          className="border-b bg-background/95 backdrop-blur-sm sticky top-0 z-50"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <div className="max-w-5xl mx-auto px-4 sm:px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => navigate(`/doc/${docId}?page=0`)}
                  className="hover:bg-accent"
                >
                  <ArrowLeft className="h-5 w-5" />
                </Button>
                
                <div className="flex items-center gap-3">
                  <motion.div
                    className="w-10 h-10 bg-primary/10 rounded-xl flex items-center justify-center"
                    whileHover={{ scale: 1.05 }}
                  >
                    <MessageSquare className="w-5 h-5 text-primary" />
                  </motion.div>
                  <div>
                    <h1 className="text-xl font-semibold">Conversation History</h1>
                    <p className="text-sm text-muted-foreground">
                      {document?.title || 'Loading...'}
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <ThemeToggle />
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={logout}
                  className="hover:bg-accent"
                >
                  <LogOut className="h-5 w-5" />
                </Button>
              </div>
            </div>
          </div>
        </motion.header>

        {/* Main Content */}
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
          {isLoading ? (
            <motion.div
              className="flex items-center justify-center py-20"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
            >
              <div className="text-center">
                <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                <p className="text-sm text-muted-foreground">Loading conversation history...</p>
              </div>
            </motion.div>
          ) : qaHistory.length === 0 ? (
            <motion.div
              className="text-center py-20"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.2 }}
            >
              <div className="relative inline-block mb-6">
                <div className="w-20 h-20 bg-muted/50 rounded-2xl flex items-center justify-center mx-auto">
                  <MessageSquare className="w-10 h-10 text-muted-foreground" />
                </div>
                <motion.div
                  className="absolute -top-2 -right-2"
                  animate={{ rotate: 360 }}
                  transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                >
                  <Sparkles className="w-5 h-5 text-primary/50" />
                </motion.div>
              </div>
              <h3 className="text-xl font-semibold mb-2">No Conversations Yet</h3>
              <p className="text-muted-foreground mb-6 max-w-md mx-auto">
                Start asking questions about your document to build your conversation history.
              </p>
              <Button
                onClick={() => navigate(`/doc/${docId}?page=0`)}
                className="gap-2"
              >
                <FileText className="w-4 h-4" />
                Go to Document
              </Button>
            </motion.div>
          ) : (
            <>
              {/* Q&A List */}
              <motion.div
                className="space-y-6"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.1 }}
              >
                {qaHistory.map((qa, index) => (
                  <motion.div
                    key={qa.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05, duration: 0.3 }}
                  >
                    <Card className="overflow-hidden border-border/50 shadow-sm hover:shadow-md transition-all duration-200">
                      <CardContent className="p-0">
                        {/* Question */}
                        <div className="bg-accent/30 p-4 sm:p-6 border-b">
                          <div className="flex items-start gap-3">
                            <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center flex-shrink-0 mt-0.5">
                              <MessageSquare className="w-4 h-4 text-primary-foreground" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="font-medium text-base leading-relaxed">
                                {qa.question}
                              </p>
                              <div className="flex items-center gap-2 mt-3 flex-wrap">
                                <button
                                  onClick={() => handleNavigateToPage(qa.page_no)}
                                  className="inline-flex items-center gap-1.5 text-xs text-primary hover:text-primary/80 font-medium transition-colors group"
                                >
                                  <FileText className="w-3.5 h-3.5" />
                                  <span>Page {qa.page_no + 1}</span>
                                  <ExternalLink className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                                </button>
                                <span className="text-xs text-muted-foreground">
                                  •
                                </span>
                                <span className="text-xs text-muted-foreground">
                                  {new Date(qa.created_at).toLocaleString('en-US', {
                                    month: 'short',
                                    day: 'numeric',
                                    year: 'numeric',
                                    hour: '2-digit',
                                    minute: '2-digit',
                                  })}
                                </span>
                                {qa.scope_mode && (
                                  <>
                                    <span className="text-xs text-muted-foreground">
                                      •
                                    </span>
                                    <span className="text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary font-medium">
                                      {qa.scope_mode === 'page' && 'This Page'}
                                      {qa.scope_mode === 'near' && '±2 Pages'}
                                      {qa.scope_mode === 'deck' && 'Entire Deck'}
                                    </span>
                                  </>
                                )}
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Answer */}
                        <div className="p-4 sm:p-6">
                          <div className="flex items-start gap-3">
                            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary/20 to-secondary/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                              <Sparkles className="w-4 h-4 text-primary" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <Markdown className="prose prose-sm dark:prose-invert max-w-none">
                                {qa.answer}
                              </Markdown>

                              {/* Citations */}
                              {qa.citations && qa.citations.length > 0 && (
                                <div className="flex flex-wrap gap-2 mt-4 pt-4 border-t">
                                  <span className="text-xs text-muted-foreground font-medium">
                                    Sources:
                                  </span>
                                  {qa.citations.map((citation, idx) => (
                                    <button
                                      key={idx}
                                      onClick={() => handleNavigateToPage(citation.page_no)}
                                      className="text-xs rounded-full bg-accent px-3 py-1 hover:bg-accent/80 transition-colors border border-border/50 inline-flex items-center gap-1.5 group"
                                      title={citation.text}
                                    >
                                      <span>Page {citation.page_no + 1}, Chunk {citation.chunk_index}</span>
                                      <ExternalLink className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                                    </button>
                                  ))}
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                ))}
              </motion.div>

              {/* Pagination Controls */}
              {(currentPage > 0 || hasNextPage) && (
                <motion.div
                  className="flex items-center justify-between mt-8 pt-6 border-t"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.3 }}
                >
                  <Button
                    variant="outline"
                    onClick={() => handlePageChange(currentPage - 1)}
                    disabled={currentPage === 0}
                    className="gap-2"
                  >
                    <ChevronLeft className="h-4 w-4" />
                    Previous
                  </Button>

                  <div className="flex items-center gap-2">
                    <span className="text-sm text-muted-foreground">
                      Page {currentPage + 1}
                    </span>
                    {hasNextPage && (
                      <span className="text-sm text-muted-foreground">
                        of {totalPages}+
                      </span>
                    )}
                  </div>

                  <Button
                    variant="outline"
                    onClick={() => handlePageChange(currentPage + 1)}
                    disabled={!hasNextPage}
                    className="gap-2"
                  >
                    Next
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </motion.div>
              )}

              {/* Stats */}
              <motion.div
                className="text-center mt-8 text-sm text-muted-foreground"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.4 }}
              >
                Showing {currentPage * itemsPerPage + 1} - {currentPage * itemsPerPage + qaHistory.length} conversations
              </motion.div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default ConversationHistoryPage;

