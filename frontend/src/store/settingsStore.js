import { create } from 'zustand';
import { persist } from 'zustand/middleware';

const useSettingsStore = create(
  persist(
    (set) => ({
      // LLM settings
      llmProvider: 'gpt',
      llmModel: 'gpt-4o-mini',
      
      // Embedding settings
      embeddingProvider: 'openai_small',
      
      // Scope mode
      scopeMode: 'page',
      
      // Actions
      setLlmProvider: (provider, model) => set({ llmProvider: provider, llmModel: model }),
      setEmbeddingProvider: (provider) => set({ embeddingProvider: provider }),
      setScopeMode: (mode) => set({ scopeMode: mode }),
      
      // Update both provider and model
      updateLlmSettings: (provider, model) => set({ llmProvider: provider, llmModel: model }),
    }),
    {
      name: 'settings-storage',
    }
  )
);

export default useSettingsStore;

