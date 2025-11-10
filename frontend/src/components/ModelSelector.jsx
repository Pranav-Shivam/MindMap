import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { providersApi } from '@/lib/api';
import useSettingsStore from '@/store/settingsStore';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Settings, Check, X } from 'lucide-react';

function ModelSelector() {
  const [isOpen, setIsOpen] = useState(false);
  const { llmProvider, llmModel, embeddingProvider, setLlmProvider, setEmbeddingProvider } = useSettingsStore();
  
  // Fetch available providers
  const { data: providersData, isLoading } = useQuery({
    queryKey: ['providers'],
    queryFn: async () => {
      const { data } = await providersApi.getProviders();
      return data;
    },
  });

  const llmProviders = providersData?.llm_providers || {};
  const embeddingProviders = providersData?.embedding_providers || {};

  const handleLlmProviderChange = (provider) => {
    const providerData = llmProviders[provider];
    if (providerData && providerData.available) {
      setLlmProvider(provider, providerData.default);
    }
  };

  const handleLlmModelChange = (model) => {
    setLlmProvider(llmProvider, model);
  };

  const handleEmbeddingProviderChange = (provider) => {
    const providerData = embeddingProviders[provider];
    if (providerData && providerData.available) {
      setEmbeddingProvider(provider);
    }
  };

  const getProviderDisplayName = (provider) => {
    switch (provider) {
      case 'gpt': return 'OpenAI GPT';
      case 'claude': return 'Anthropic Claude (Sonnet)';
      case 'ollama': return 'Ollama (Local)';
      case 'gemini': return 'Google Gemini';
      default: return provider;
    }
  };

  const getEmbeddingDisplayName = (provider) => {
    switch (provider) {
      case 'openai_small': return 'OpenAI Small';
      case 'openai_large': return 'OpenAI Large';
      case 'ollama': return 'Ollama';
      case 'google': return 'Google';
      default: return provider;
    }
  };

  if (!isOpen) {
    return (
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setIsOpen(true)}
        className="flex items-center gap-2"
      >
        <Settings className="h-4 w-4" />
        <span className="text-sm">
          {getProviderDisplayName(llmProvider)} | {getEmbeddingDisplayName(embeddingProvider)}
        </span>
      </Button>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <Card className="w-full max-w-md">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-lg font-semibold">Model Settings</CardTitle>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsOpen(false)}
          >
            <X className="h-4 w-4" />
          </Button>
        </CardHeader>
        <CardContent className="space-y-6">
          {isLoading ? (
            <div className="text-center py-4">Loading providers...</div>
          ) : (
            <>
              {/* LLM Provider Selection */}
              <div className="space-y-3">
                <label className="text-sm font-medium">LLM Provider</label>
                <Select value={llmProvider} onValueChange={handleLlmProviderChange}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select LLM provider" />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(llmProviders).map(([key, provider]) => (
                      <SelectItem key={key} value={key} disabled={!provider.available}>
                        <div className="flex items-center gap-2">
                          {provider.available && <Check className="h-3 w-3 text-green-500" />}
                          {!provider.available && <X className="h-3 w-3 text-red-500" />}
                          {getProviderDisplayName(key)}
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* LLM Model Selection */}
              {llmProvider && llmProviders[llmProvider] && (
                <div className="space-y-3">
                  <label className="text-sm font-medium">Model</label>
                  <Select value={llmModel} onValueChange={handleLlmModelChange}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select model" />
                    </SelectTrigger>
                    <SelectContent>
                      {llmProviders[llmProvider].models.map((model) => (
                        <SelectItem key={model} value={model}>
                          {model}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}

              {/* Embedding Provider Selection */}
              <div className="space-y-3">
                <label className="text-sm font-medium">Embedding Provider</label>
                <Select value={embeddingProvider} onValueChange={handleEmbeddingProviderChange}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select embedding provider" />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(embeddingProviders).map(([key, provider]) => (
                      <SelectItem key={key} value={key} disabled={!provider.available}>
                        <div className="flex items-center gap-2">
                          {provider.available && <Check className="h-3 w-3 text-green-500" />}
                          {!provider.available && <X className="h-3 w-3 text-red-500" />}
                          {getEmbeddingDisplayName(key)}
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Provider Info */}
              {llmProvider && llmProviders[llmProvider] && (
                <div className="rounded-lg bg-muted p-3 text-sm">
                  <p className="font-medium mb-1">Current Selection:</p>
                  <p>LLM: {getProviderDisplayName(llmProvider)} ({llmModel})</p>
                  <p>Embeddings: {getEmbeddingDisplayName(embeddingProvider)}</p>
                </div>
              )}

              <div className="flex justify-end">
                <Button onClick={() => setIsOpen(false)}>
                  Done
                </Button>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default ModelSelector;
