import { useState, useCallback } from 'react';
import { qaApi } from '@/lib/api';

function useStreamingQA() {
  const [currentAnswer, setCurrentAnswer] = useState(null);
  const [isStreaming, setIsStreaming] = useState(false);

  const streamAnswer = useCallback(async ({ docId, pageNo, question, scopeMode, llmProvider, llmModel, embeddingProvider }) => {
    setIsStreaming(true);
    setCurrentAnswer({
      question,
      answer: '',
      citations: [],
      isError: false,
    });

    try {
      const { url, body, token } = qaApi.ask(docId, pageNo, question, scopeMode, llmProvider, llmModel, embeddingProvider);

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        throw new Error('Failed to stream answer');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        // Split by double newline (SSE message separator)
        const messages = buffer.split('\n\n');
        // Keep the last incomplete message in buffer
        buffer = messages.pop() || '';

        for (const message of messages) {
          // Skip empty messages
          if (!message.trim()) continue;
          
          // SSE format: "data: {...}"
          const lines = message.split('\n');
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const jsonStr = line.slice(6).trim();
                if (!jsonStr) continue;
                
                const data = JSON.parse(jsonStr);

                if (data.type === 'token') {
                  setCurrentAnswer((prev) => ({
                    ...prev,
                    answer: (prev?.answer || '') + data.token,
                  }));
                } else if (data.type === 'done') {
                  setCurrentAnswer((prev) => ({
                    ...prev,
                    citations: data.citations || [],
                  }));
                } else if (data.type === 'error') {
                  console.error('Streaming error:', data.message);
                  setCurrentAnswer((prev) => {
                    const currentAnswer = prev?.answer || '';
                    return {
                      ...prev,
                      question: prev?.question || 'Question',
                      answer: currentAnswer ? currentAnswer + '\n\n**Error:** ' + data.message : '**Error:** ' + data.message,
                      isError: true,
                    };
                  });
                }
              } catch (e) {
                console.error('Error parsing SSE data:', e, 'Line:', line);
              }
            }
          }
        }
      }
    } catch (error) {
      console.error('Error streaming answer:', error);
      setCurrentAnswer((prev) => ({
        ...prev,
        answer: (prev?.answer || '') + '\n\n**Error:** Failed to get answer. Please try again.',
        isError: true,
      }));
    } finally {
      setIsStreaming(false);
      // Don't clear the answer - let it persist so user can see it
      // It will be replaced when a new question is asked
    }
  }, []);

  return {
    streamAnswer,
    currentAnswer,
    isStreaming,
  };
}

export default useStreamingQA;

