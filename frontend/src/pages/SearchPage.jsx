import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { searchApi } from '@/lib/api';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, ArrowLeft, FileText, MessageSquare, Clock, Filter } from 'lucide-react';

function SearchPage() {
  const [query, setQuery] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const navigate = useNavigate();

  const { data: results = [], isLoading } = useQuery({
    queryKey: ['search', searchQuery],
    queryFn: async () => {
      if (!searchQuery) return [];
      const { data } = await searchApi.search(searchQuery);
      return data;
    },
    enabled: !!searchQuery,
  });

  const handleSearch = (e) => {
    e.preventDefault();
    setSearchQuery(query);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20">
      {/* Background decorative elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-primary/5 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-secondary/10 rounded-full blur-3xl" />
      </div>

      <div className="relative z-10 p-4 sm:p-8">
        <div className="mx-auto max-w-4xl">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="mb-8 flex items-center justify-between"
          >
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => navigate(-1)}
                className="hover:bg-accent/50"
              >
                <ArrowLeft className="h-5 w-5" />
              </Button>
              <div>
                <h1 className="text-3xl font-bold tracking-tight">Search</h1>
                <p className="text-muted-foreground">Find answers across your documents</p>
              </div>
            </div>
            <ThemeToggle />
          </motion.div>

          {/* Search Form */}
          <motion.form
            onSubmit={handleSearch}
            className="mb-8"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1, duration: 0.5 }}
          >
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                <Search className="h-5 w-5 text-muted-foreground" />
              </div>
              <Input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search documents, questions, answers..."
                className="pl-12 pr-4 h-14 text-base border-border/50 focus:border-primary/50 bg-background/80 backdrop-blur-sm"
              />
              <div className="absolute inset-y-0 right-0 pr-4 flex items-center">
                <Button
                  type="submit"
                  disabled={isLoading}
                  className="h-10 px-6"
                >
                  {isLoading ? (
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                      <span className="hidden sm:inline">Searching...</span>
                    </div>
                  ) : (
                    <span className="hidden sm:inline">Search</span>
                  )}
                </Button>
              </div>
            </div>
          </motion.form>

          {/* Loading State */}
          <AnimatePresence>
            {isLoading && (
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                className="text-center py-12"
              >
                <div className="relative mb-6">
                  <div className="w-16 h-16 bg-primary/10 rounded-2xl flex items-center justify-center mx-auto">
                    <Search className="w-8 h-8 text-primary animate-pulse" />
                  </div>
                  <motion.div
                    className="absolute -top-1 -right-1"
                    animate={{ rotate: 360 }}
                    transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                  >
                    <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                  </motion.div>
                </div>
                <p className="text-lg font-medium mb-2">Searching your documents...</p>
                <p className="text-muted-foreground">Finding the most relevant answers</p>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Results */}
          <AnimatePresence mode="wait">
            {results.length > 0 && (
              <motion.div
                key="results"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
                className="space-y-4"
              >
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-lg font-semibold">
                    {results.length} result{results.length > 1 ? 's' : ''} found
                  </h2>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Filter className="w-4 h-4" />
                    <span>Sorted by relevance</span>
                  </div>
                </div>

                {results.map((result, idx) => (
                  <motion.div
                    key={`${result.doc_id}-${idx}`}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: idx * 0.1, duration: 0.3 }}
                    whileHover={{ scale: 1.02 }}
                    className="group"
                  >
                    <Card
                      className="cursor-pointer border-border/50 shadow-sm hover:shadow-md hover:border-primary/20 transition-all duration-200"
                      onClick={() => navigate(`/doc/${result.doc_id}?page=${result.page_no}`)}
                    >
                      <CardHeader className="pb-3">
                        <div className="flex items-start justify-between">
                          <div className="flex items-center gap-3 flex-1 min-w-0">
                            <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center group-hover:bg-primary/20 transition-colors">
                              {result.type === 'qa' ? (
                                <MessageSquare className="w-5 h-5 text-primary" />
                              ) : (
                                <FileText className="w-5 h-5 text-primary" />
                              )}
                            </div>
                            <div className="flex-1 min-w-0">
                              <CardTitle className="text-base group-hover:text-primary transition-colors truncate">
                                {result.type === 'qa' ? result.metadata.question : `Page ${result.page_no + 1}`}
                              </CardTitle>
                              <div className="flex items-center gap-2 mt-1">
                                <span className="text-xs text-muted-foreground capitalize">
                                  {result.type === 'qa' ? 'Q&A' : 'Document Page'}
                                </span>
                                <div className="w-1 h-1 bg-muted-foreground/50 rounded-full" />
                                <span className="text-xs text-muted-foreground">
                                  Page {result.page_no + 1}
                                </span>
                              </div>
                            </div>
                          </div>
                          <div className="opacity-0 group-hover:opacity-100 transition-opacity">
                            <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center">
                              <ArrowLeft className="w-4 h-4 text-primary rotate-180" />
                            </div>
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent className="pt-0">
                        <p className="text-sm text-muted-foreground leading-relaxed line-clamp-3">
                          {result.snippet}
                        </p>
                      </CardContent>
                    </Card>
                  </motion.div>
                ))}
              </motion.div>
            )}

            {!isLoading && searchQuery && results.length === 0 && (
              <motion.div
                key="no-results"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                className="text-center py-16"
              >
                <div className="w-16 h-16 bg-muted/50 rounded-2xl flex items-center justify-center mx-auto mb-6">
                  <Search className="w-8 h-8 text-muted-foreground" />
                </div>
                <h3 className="text-lg font-semibold mb-2">No results found</h3>
                <p className="text-muted-foreground mb-6 max-w-md mx-auto">
                  Try adjusting your search terms or check for typos.
                  You can search for questions, answers, or document content.
                </p>
                <div className="flex flex-wrap justify-center gap-2 text-sm text-muted-foreground">
                  <div className="flex items-center gap-1">
                    <span className="w-2 h-2 bg-primary rounded-full"></span>
                    <span>Questions</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="w-2 h-2 bg-secondary rounded-full"></span>
                    <span>Answers</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="w-2 h-2 bg-accent rounded-full"></span>
                    <span>Document content</span>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}

export default SearchPage;

