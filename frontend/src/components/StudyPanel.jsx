import { useState, useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import useSettingsStore from '@/store/settingsStore';
import useStreamingQA from '@/hooks/useStreamingQA';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Markdown } from './ui/markdown';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, ChevronUp, Send, Copy, Loader2, BookOpen, MessageSquare, Sparkles, ChevronLeft, ChevronRight, History, Check } from 'lucide-react';

function StudyPanel({ docId, pageNo, pageData }) {
  const [question, setQuestion] = useState('');
  const [showExplanation, setShowExplanation] = useState(true);
  const [qaPage, setQaPage] = useState(0);
  const qaPerPage = 5;
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [copied, setCopied] = useState(false);
  const { llmProvider, llmModel, embeddingProvider, scopeMode } = useSettingsStore();
  const { streamAnswer, currentAnswer, isStreaming } = useStreamingQA();

  // Check if currentAnswer already exists in pageData.qa to avoid duplicates
  // Compare by question (normalized) since answers might have slight formatting differences
  const currentAnswerExists = currentAnswer && !isStreaming && pageData?.qa?.some(
    (qa) => qa.question.trim().toLowerCase() === currentAnswer.question.trim().toLowerCase()
  );

  // Helper function to filter Q&A by current page number
  const filterQAByPage = (qa) => {
    // Primary check: page_no matches current page
    if (qa.page_no !== undefined && qa.page_no !== null) {
      return qa.page_no === pageNo;
    }
    // Fallback: check citations if page_no is not available
    if (qa.citations && qa.citations.length > 0) {
      return qa.citations.some(citation => citation.page_no === pageNo);
    }
    // Exclude if no page information available (safety measure)
    return false;
  };

  // Filter Q&A for current page
  const filteredQA = pageData?.qa?.filter(filterQAByPage) || [];
  
  // Pagination for Q&A
  const totalQAPages = Math.max(1, Math.ceil(filteredQA.length / qaPerPage));
  const safeQaPage = Math.min(qaPage, totalQAPages - 1);
  const paginatedQA = filteredQA.slice(safeQaPage * qaPerPage, (safeQaPage + 1) * qaPerPage);
  
  // Reset to first page when pageNo changes or when filteredQA length changes
  useEffect(() => {
    setQaPage(0);
  }, [pageNo]);
  
  // Ensure qaPage doesn't exceed bounds when Q&A list changes
  useEffect(() => {
    if (qaPage >= totalQAPages && totalQAPages > 0) {
      setQaPage(Math.max(0, totalQAPages - 1));
    }
  }, [filteredQA.length, qaPage, totalQAPages]);

  const handleAsk = async () => {
    if (!question.trim() || isStreaming) return;

    // ALWAYS use openai_small for embeddings (text-embedding-3-small)
    const forcedEmbeddingProvider = 'openai_small';

    await streamAnswer({
      docId,
      pageNo,
      question,
      scopeMode,
      llmProvider,
      llmModel,
      embeddingProvider: forcedEmbeddingProvider,
    });

    // Refresh page data to show new Q&A
    queryClient.invalidateQueries(['page', docId, pageNo]);
    setQuestion('');
    setQaPage(0); // Reset to first page after asking a new question
  };

  return (
    <motion.div
      className="flex h-full flex-col overflow-hidden bg-background"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      <div className="flex-1 overflow-y-auto p-4 sm:p-6">
        {/* Explanation Section */}
        {pageData && pageData.summary && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <Card className="mb-4 border-border/50 shadow-sm">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg flex items-center gap-2">
                    <BookOpen className="w-5 h-5 text-primary" />
                    Page Summary
                  </CardTitle>
                  <div className="flex items-center gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        navigator.clipboard.writeText(pageData.summary);
                        setCopied(true);
                        setTimeout(() => setCopied(false), 2000);
                      }}
                      className="h-8 w-8 p-0"
                      title="Copy summary"
                    >
                      {copied ? (
                        <Check className="h-3.5 w-3.5 text-green-500" />
                      ) : (
                        <Copy className="h-3.5 w-3.5" />
                      )}
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setShowExplanation(!showExplanation)}
                      className="h-8 w-8 p-0"
                    >
                      <motion.div
                        animate={{ rotate: showExplanation ? 0 : 180 }}
                        transition={{ duration: 0.2 }}
                      >
                        <ChevronDown className="h-4 w-4" />
                      </motion.div>
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <AnimatePresence>
                {showExplanation && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.3, ease: 'easeInOut' }}
                  >
                    <CardContent className="pt-0">
                      <Markdown className="text-sm leading-relaxed">
                        {pageData.summary}
                      </Markdown>
                    </CardContent>
                  </motion.div>
                )}
              </AnimatePresence>
            </Card>
          </motion.div>
        )}

        {/* Key Terms */}
        {pageData && pageData.key_terms && pageData.key_terms.length > 0 && (
          <motion.div
            className="mb-4"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <h3 className="mb-3 text-sm font-medium flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-primary" />
              Key Terms
            </h3>
            <div className="flex flex-wrap gap-2">
              {pageData.key_terms.map((term, idx) => (
                <motion.span
                  key={idx}
                  className="rounded-full bg-primary/10 px-3 py-1.5 text-sm text-primary font-medium border border-primary/20"
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.3 + idx * 0.1, duration: 0.2 }}
                  whileHover={{ scale: 1.05 }}
                >
                  {term}
                </motion.span>
              ))}
            </div>
          </motion.div>
        )}

        {/* Q&A Timeline */}
        <motion.div
          className="space-y-4"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium flex items-center gap-2">
              <MessageSquare className="w-4 h-4 text-primary" />
              Q&A History
              {filteredQA.length > 0 && (
                <span className="text-xs text-muted-foreground ml-1">
                  ({filteredQA.length} on this page)
                </span>
              )}
            </h3>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate(`/doc/${docId}/history`)}
              className="h-8 gap-2 text-xs"
            >
              <History className="w-3.5 h-3.5" />
              View All
            </Button>
          </div>

          {/* Current streaming answer - show while streaming OR if answer exists and hasn't been saved yet */}
          {currentAnswer && !currentAnswerExists && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
            >
              <Card className={`${currentAnswer.isError ? 'border-destructive' : 'border-primary/20'} shadow-sm`}>
                <CardContent className="pt-6">
                  <div className="flex items-start justify-between mb-3">
                    <p className="font-medium text-sm flex-1">{currentAnswer.question}</p>
                    {isStreaming && (
                      <div className="flex items-center gap-2 ml-2">
                        <div className="w-2 h-2 bg-primary rounded-full animate-pulse" />
                        <span className="text-xs text-muted-foreground">Thinking...</span>
                      </div>
                    )}
                  </div>
                  <Markdown className={currentAnswer.isError ? 'text-destructive' : ''}>
                    {currentAnswer.answer || 'Processing...'}
                  </Markdown>
                  {currentAnswer.citations && currentAnswer.citations.length > 0 && (
                    <motion.div
                      className="flex flex-wrap gap-2 mt-4"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: 0.5 }}
                    >
                      {currentAnswer.citations.map((citation, idx) => (
                        <motion.span
                          key={idx}
                          className="text-xs rounded-full bg-accent px-3 py-1.5 cursor-pointer hover:bg-accent/80 transition-colors border border-border/50"
                          title={citation.text}
                          initial={{ opacity: 0, scale: 0.8 }}
                          animate={{ opacity: 1, scale: 1 }}
                          transition={{ delay: 0.6 + idx * 0.1 }}
                          whileHover={{ scale: 1.05 }}
                        >
                          Page {citation.page_no + 1}, Chunk {citation.chunk_index}
                        </motion.span>
                      ))}
                    </motion.div>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* Past Q&A - Paginated and Filtered by current page number */}
          {paginatedQA.map((qa, index) => (
            <motion.div
              key={qa.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 + index * 0.1, duration: 0.3 }}
            >
              <Card className="border-border/50 shadow-sm hover:shadow-md transition-shadow">
                <CardContent className="pt-6">
                  <p className="mb-3 font-medium text-sm">{qa.question}</p>
                  <Markdown className="mb-4 text-sm">
                    {qa.answer}
                  </Markdown>

                  {/* Citations */}
                  {qa.citations && qa.citations.length > 0 && (
                    <div className="flex flex-wrap gap-2 mb-3">
                      {qa.citations.map((citation, idx) => (
                        <span
                          key={idx}
                          className="text-xs rounded-full bg-accent px-3 py-1 cursor-pointer hover:bg-accent/80 transition-colors border border-border/50"
                          title={citation.text}
                        >
                          Page {citation.page_no + 1}, Chunk {citation.chunk_index}
                        </span>
                      ))}
                    </div>
                  )}

                  <div className="flex items-center justify-between">
                    <span className="text-xs text-muted-foreground">
                      {new Date(qa.created_at).toLocaleString()}
                    </span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => navigator.clipboard.writeText(qa.answer)}
                      className="h-8 w-8 p-0"
                    >
                      <Copy className="h-3 w-3" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}

          {filteredQA.length === 0 && !isStreaming && !currentAnswer && (
            <motion.div
              className="text-center py-12"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.5 }}
            >
              <MessageSquare className="w-12 h-12 text-muted-foreground/50 mx-auto mb-4" />
              <p className="text-sm text-muted-foreground">
                No questions yet for this page. Ask something below!
              </p>
            </motion.div>
          )}

          {/* Pagination Controls */}
          {filteredQA.length > qaPerPage && (
            <motion.div
              className="flex items-center justify-between pt-4 border-t"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5 }}
            >
              <Button
                variant="outline"
                size="sm"
                onClick={() => setQaPage(Math.max(0, safeQaPage - 1))}
                disabled={safeQaPage === 0}
                className="h-8"
              >
                <ChevronLeft className="h-4 w-4 mr-1" />
                Previous
              </Button>

              <span className="text-sm text-muted-foreground">
                Page {safeQaPage + 1} of {Math.ceil(filteredQA.length / qaPerPage)}
              </span>

              <Button
                variant="outline"
                size="sm"
                onClick={() => setQaPage(Math.min(Math.ceil(filteredQA.length / qaPerPage) - 1, safeQaPage + 1))}
                disabled={safeQaPage >= Math.ceil(filteredQA.length / qaPerPage) - 1}
                className="h-8"
              >
                Next
                <ChevronRight className="h-4 w-4 ml-1" />
              </Button>
            </motion.div>
          )}
        </motion.div>
      </div>

      {/* Ask Question Input */}
      <motion.div
        className="border-t bg-background/95 backdrop-blur-sm p-4"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6, duration: 0.3 }}
      >
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <Input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleAsk()}
              placeholder="Ask a question about this page..."
              disabled={isStreaming}
              className="pr-12 h-12 text-base border-border/50 focus:border-primary/50"
            />
            {question.trim() && (
              <motion.div
                className="absolute right-3 top-1/2 -translate-y-1/2"
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
              >
                <div className="w-2 h-2 bg-primary rounded-full" />
              </motion.div>
            )}
          </div>
          <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
            <Button
              onClick={handleAsk}
              disabled={isStreaming || !question.trim()}
              className="h-12 px-6"
              size="lg"
            >
              {isStreaming ? (
                <div className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span className="hidden sm:inline">Thinking...</span>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <Send className="h-4 w-4" />
                  <span className="hidden sm:inline">Ask</span>
                </div>
              )}
            </Button>
          </motion.div>
        </div>
        <p className="text-xs text-muted-foreground mt-2 text-center">
          AI-powered answers with citations from your document
        </p>
      </motion.div>
    </motion.div>
  );
}

export default StudyPanel;