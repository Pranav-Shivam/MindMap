import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { documentsApi, providersApi } from '@/lib/api';
import useAuthStore from '@/store/authStore';
import useSettingsStore from '@/store/settingsStore';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, FileText, Loader2, X, CheckCircle, AlertCircle, BookOpen, Sparkles, Trash2 } from 'lucide-react';

function UploadPage() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [selectedLlmProvider, setSelectedLlmProvider] = useState('gpt');
  const [selectedLlmModel, setSelectedLlmModel] = useState('gpt-4o-mini');
  // Embedding provider is LOCKED to openai_small (text-embedding-3-small)
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef(null);
  const navigate = useNavigate();
  const logout = useAuthStore((state) => state.logout);

  // Fetch available providers
  const { data: providers } = useQuery({
    queryKey: ['providers'],
    queryFn: async () => {
      const { data } = await providersApi.getProviders();
      return data;
    },
  });

  // Fetch documents
  const { data: documents = [], refetch } = useQuery({
    queryKey: ['documents'],
    queryFn: async () => {
      const { data } = await documentsApi.list();
      return data;
    },
  });

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: (file) => documentsApi.upload(file, selectedLlmProvider, selectedLlmModel),
    onSuccess: (response) => {
      const docId = response.data.doc_id;
      refetch();
      navigate(`/doc/${docId}?page=0`);
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (docId) => documentsApi.delete(docId),
    onSuccess: () => {
      refetch();
    },
  });

  const [deleteConfirmDoc, setDeleteConfirmDoc] = useState(null);

  const handleDeleteClick = (e, doc) => {
    e.stopPropagation(); // Prevent navigation
    setDeleteConfirmDoc(doc);
  };

  const handleDeleteConfirm = () => {
    if (deleteConfirmDoc) {
      deleteMutation.mutate(deleteConfirmDoc.id);
      setDeleteConfirmDoc(null);
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (file && file.type === 'application/pdf') {
      setSelectedFile(file);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);

    const file = e.dataTransfer.files?.[0];
    if (file && file.type === 'application/pdf') {
      setSelectedFile(file);
    }
  };

  const removeFile = () => {
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleUpload = () => {
    if (selectedFile) {
      uploadMutation.mutate(selectedFile);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20">
      {/* Background decorative elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-primary/5 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-secondary/10 rounded-full blur-3xl" />
      </div>

      <div className="relative z-10 p-4 sm:p-8">
        <div className="mx-auto max-w-6xl">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="mb-8 flex items-center justify-between"
          >
            <div className="flex items-center gap-4">
              <motion.div
                className="relative"
                whileHover={{ scale: 1.05 }}
                transition={{ type: "spring", stiffness: 400, damping: 10 }}
              >
                <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center">
                  <BookOpen className="w-6 h-6 text-primary" />
                </div>
                <motion.div
                  className="absolute -top-1 -right-1"
                  animate={{ rotate: 360 }}
                  transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                >
                  <Sparkles className="w-3 h-3 text-primary" />
                </motion.div>
              </motion.div>
              <div>
                <h1 className="text-3xl font-bold tracking-tight">MindMap</h1>
                <p className="text-muted-foreground">Upload your study materials</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <ThemeToggle />
              <Button onClick={logout} variant="outline" size="sm">
                Logout
              </Button>
            </div>
          </motion.div>

          {/* Upload Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1, duration: 0.5 }}
          >
            <Card className="backdrop-blur-sm bg-card/80 border-border/50 shadow-xl mb-8">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Upload className="w-5 h-5" />
                  Upload PDF Document
                </CardTitle>
                <p className="text-sm text-muted-foreground">
                  Upload a PDF to start your AI-powered study session
                </p>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {/* File Upload Area */}
                  <div className="space-y-4">
                    <Label className="text-sm font-medium">Document</Label>
                    <motion.div
                      onDragOver={handleDragOver}
                      onDragLeave={handleDragLeave}
                      onDrop={handleDrop}
                      className="relative"
                      whileHover={{ scale: 1.01 }}
                      transition={{ type: "spring", stiffness: 400, damping: 10 }}
                    >
                      <label className="block cursor-pointer">
                        <div className={`
                          relative flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 transition-all duration-200
                          ${isDragOver
                            ? 'border-primary bg-primary/5 scale-[1.02]'
                            : selectedFile
                              ? 'border-primary/50 bg-primary/5'
                              : 'border-border hover:border-primary/50 hover:bg-accent/50'
                          }
                        `}>
                          <AnimatePresence mode="wait">
                            {selectedFile ? (
                              <motion.div
                                key="file-selected"
                                initial={{ opacity: 0, scale: 0.8 }}
                                animate={{ opacity: 1, scale: 1 }}
                                exit={{ opacity: 0, scale: 0.8 }}
                                className="text-center"
                              >
                                <div className="relative inline-block">
                                  <FileText className="mx-auto h-12 w-12 text-primary" />
                                  <Button
                                    type="button"
                                    variant="ghost"
                                    size="sm"
                                    className="absolute -top-2 -right-2 h-6 w-6 p-0 rounded-full bg-destructive hover:bg-destructive/80"
                                    onClick={(e) => {
                                      e.preventDefault();
                                      removeFile();
                                    }}
                                  >
                                    <X className="h-3 w-3" />
                                  </Button>
                                </div>
                                <p className="mt-4 text-sm font-medium">{selectedFile.name}</p>
                                <p className="text-xs text-muted-foreground">
                                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                                </p>
                              </motion.div>
                            ) : (
                              <motion.div
                                key="no-file"
                                initial={{ opacity: 0, scale: 0.8 }}
                                animate={{ opacity: 1, scale: 1 }}
                                exit={{ opacity: 0, scale: 0.8 }}
                                className="text-center"
                              >
                                <Upload className="mx-auto h-12 w-12 text-muted-foreground" />
                                <p className="mt-4 text-base font-medium">
                                  {isDragOver ? 'Drop your PDF here' : 'Click to upload or drag and drop'}
                                </p>
                                <p className="text-sm text-muted-foreground mt-1">
                                  PDF files only, up to 50MB
                                </p>
                              </motion.div>
                            )}
                          </AnimatePresence>
                        </div>
                        <input
                          ref={fileInputRef}
                          type="file"
                          accept=".pdf"
                          onChange={handleFileSelect}
                          className="hidden"
                        />
                      </label>
                    </motion.div>
                  </div>

                  {/* Provider Selection */}
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2, duration: 0.3 }}
                    className="grid grid-cols-1 md:grid-cols-2 gap-4"
                  >
                    <div className="space-y-2">
                      <Label className="text-sm font-medium">LLM Provider</Label>
                      <Select 
                        value={selectedLlmProvider} 
                        onValueChange={(value) => {
                          setSelectedLlmProvider(value);
                          // Update model to first available model for the selected provider
                          const providerModels = providers?.llm_providers?.[value]?.models;
                          if (providerModels && providerModels.length > 0) {
                            setSelectedLlmModel(providerModels[0]);
                          }
                        }}
                      >
                        <SelectTrigger className="h-11">
                          <SelectValue placeholder="Select LLM provider" />
                        </SelectTrigger>
                        <SelectContent>
                          {providers?.llm_providers && Object.entries(providers.llm_providers).map(([key, provider]) => (
                            provider.available && (
                              <SelectItem key={key} value={key}>
                                <div className="flex items-center gap-2">
                                  <span className="font-medium">{key.toUpperCase()}</span>
                                  {key === 'gpt' && <span className="text-xs text-muted-foreground">(OpenAI)</span>}
                                  {key === 'claude' && <span className="text-xs text-muted-foreground">(Anthropic)</span>}
                                  {key === 'gemini' && <span className="text-xs text-muted-foreground">(Google)</span>}
                                </div>
                              </SelectItem>
                            )
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <Label className="text-sm font-medium">LLM Model</Label>
                      <Select value={selectedLlmModel} onValueChange={setSelectedLlmModel}>
                        <SelectTrigger className="h-11">
                          <SelectValue placeholder="Select LLM model" />
                        </SelectTrigger>
                        <SelectContent>
                          {providers?.llm_providers?.[selectedLlmProvider]?.models?.map((model) => (
                            <SelectItem key={model} value={model}>
                              <div className="flex flex-col">
                                <span>{model}</span>
                                {(model.includes('vision') || model.includes('4o') || model.includes('turbo') || 
                                  selectedLlmProvider === 'claude' || selectedLlmProvider === 'gemini') ? (
                                  <span className="text-xs text-muted-foreground">Vision capable</span>
                                ) : null}
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      {providers?.llm_providers?.[selectedLlmProvider] && (
                        <p className="text-xs text-muted-foreground mt-1">
                          {selectedLlmProvider === 'gpt' && 'GPT-4o models support vision'}
                          {selectedLlmProvider === 'claude' && 'Claude models support vision'}
                          {selectedLlmProvider === 'gemini' && 'Gemini models support vision'}
                        </p>
                      )}
                    </div>
                  </motion.div>

                  {/* Embedding Info - Locked */}
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.25, duration: 0.3 }}
                    className="rounded-lg bg-muted/50 p-4 border"
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      <span className="text-sm font-medium">Embedding Model</span>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      Using <span className="font-medium text-foreground">text-embedding-3-small</span> (OpenAI • 1536 dimensions)
                    </p>
                  </motion.div>

                  <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.3, duration: 0.3 }}
                  >
                    <Button
                      onClick={handleUpload}
                      disabled={!selectedFile || uploadMutation.isPending}
                      className="w-full h-12 text-base font-medium"
                      size="lg"
                    >
                      {uploadMutation.isPending ? (
                        <motion.div
                          className="flex items-center gap-2"
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                        >
                          <Loader2 className="h-5 w-5 animate-spin" />
                          Processing your document...
                        </motion.div>
                      ) : (
                        <motion.span
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          transition={{ delay: 0.1 }}
                        >
                          Start AI Study Session
                        </motion.span>
                      )}
                    </Button>
                  </motion.div>
            </div>
          </CardContent>
        </Card>
        </motion.div>

          {/* Documents List */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.5 }}
          >
            <Card className="backdrop-blur-sm bg-card/80 border-border/50 shadow-xl">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="w-5 h-5" />
                  Your Study Documents
                </CardTitle>
                <p className="text-sm text-muted-foreground">
                  {documents.length > 0
                    ? `${documents.length} document${documents.length > 1 ? 's' : ''} ready for study`
                    : 'Upload your first document to get started'
                  }
                </p>
              </CardHeader>
              <CardContent>
                <div className={documents.length === 0 ? "text-center py-12 animate-in fade-in-0 slide-in-from-bottom-4 duration-500" : "space-y-3 animate-in fade-in-0 slide-in-from-bottom-4 duration-500"}>
                  {documents.length === 0 ? (
                    <>
                      <div className="relative mb-6">
                        <div className="w-16 h-16 bg-muted/50 rounded-2xl flex items-center justify-center mx-auto">
                          <BookOpen className="w-8 h-8 text-muted-foreground" />
                        </div>
                        <div className="absolute -top-1 -right-1 animate-spin">
                          <Sparkles className="w-4 h-4 text-primary/50" />
                        </div>
                      </div>
                      <h3 className="text-lg font-semibold mb-2">Ready to start studying?</h3>
                      <p className="text-muted-foreground mb-6 max-w-md mx-auto">
                        Upload a PDF document above to begin your AI-powered study session.
                        Our advanced AI will help you understand complex topics through interactive Q&A.
                      </p>
                      <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
                        <CheckCircle className="w-4 h-4 text-green-500" />
                        <span>Automatic content analysis</span>
                      </div>
                      <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground mt-1">
                        <CheckCircle className="w-4 h-4 text-green-500" />
                        <span>Intelligent Q&A generation</span>
                      </div>
                      <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground mt-1">
                        <CheckCircle className="w-4 h-4 text-green-500" />
                        <span>Context-aware responses</span>
                      </div>
                    </>
                  ) : (
                    documents.map((doc, index) => (
                      <div
                        key={doc.id}
                        onClick={() => navigate(`/doc/${doc.id}?page=0`)}
                        className="group flex items-center justify-between rounded-xl border p-4 cursor-pointer transition-all duration-200 hover:bg-accent hover:shadow-md hover:border-primary/20 hover:scale-[1.02] animate-in fade-in-0 slide-in-from-left-4"
                        style={{ animationDelay: `${0.1 + index * 0.1}s` }}
                      >
                        <div className="flex items-center gap-4 flex-1">
                          <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center group-hover:bg-primary/20 transition-colors">
                            <FileText className="h-5 w-5 text-primary" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <h3 className="font-medium truncate group-hover:text-primary transition-colors">
                              {doc.title}
                            </h3>
                            <div className="flex items-center gap-2 mt-1">
                              <p className="text-sm text-muted-foreground">
                                {doc.page_count ? `${doc.page_count} pages` : 'Processing...'}
                              </p>
                              {doc.ingestion_completed && (
                                <div className="flex items-center gap-1">
                                  <div className="w-1.5 h-1.5 bg-green-500 rounded-full" />
                                  <span className="text-xs text-green-600 font-medium">Ready</span>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => handleDeleteClick(e, doc)}
                            className="h-8 w-8 p-0 text-destructive hover:text-destructive hover:bg-destructive/10"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                          <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center">
                            <svg className="w-4 h-4 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                            </svg>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </div>

      {/* Delete Confirmation Dialog */}
      <AnimatePresence>
        {deleteConfirmDoc && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
            onClick={() => setDeleteConfirmDoc(null)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-card border border-border rounded-xl p-6 max-w-md w-full shadow-xl"
            >
              <div className="flex items-center gap-4 mb-4">
                <div className="w-12 h-12 bg-destructive/10 rounded-full flex items-center justify-center">
                  <AlertCircle className="h-6 w-6 text-destructive" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold">Delete Document?</h3>
                  <p className="text-sm text-muted-foreground">This action cannot be undone</p>
                </div>
              </div>
              <p className="text-sm mb-6">
                Are you sure you want to delete <span className="font-medium">"{deleteConfirmDoc.title}"</span>? 
                This will permanently delete the document, all pages, Q&A records, and vector embeddings.
              </p>
              <div className="flex gap-3 justify-end">
                <Button
                  variant="outline"
                  onClick={() => setDeleteConfirmDoc(null)}
                  disabled={deleteMutation.isPending}
                >
                  Cancel
                </Button>
                <Button
                  variant="destructive"
                  onClick={handleDeleteConfirm}
                  disabled={deleteMutation.isPending}
                >
                  {deleteMutation.isPending ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Deleting...
                    </>
                  ) : (
                    <>
                      <Trash2 className="h-4 w-4 mr-2" />
                      Delete
                    </>
                  )}
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default UploadPage;

