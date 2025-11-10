import { useNavigate } from 'react-router-dom';
import useSettingsStore from '@/store/settingsStore';
import useAuthStore from '@/store/authStore';
import { Button } from './ui/button';
import { ThemeToggle } from './ui/theme-toggle';
import ModelSelector from './ModelSelector';
import { ArrowLeft, Search, LogOut, ChevronLeft, ChevronRight, MessageSquare } from 'lucide-react';

function Header({ document, currentPage, onPageChange }) {
  const navigate = useNavigate();
  const logout = useAuthStore((state) => state.logout);
  const { scopeMode, setScopeMode, llmProvider, embeddingProvider } = useSettingsStore();

  const scopeModes = ['page', 'near', 'deck'];

  return (
    <header className="border-b bg-background p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate('/')}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          
          <h1 className="text-xl font-semibold">{document?.title || 'Loading...'}</h1>
          
          {document && (
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => onPageChange(Math.max(0, currentPage - 1))}
                disabled={currentPage === 0}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              
              <span className="text-sm text-muted-foreground">
                Page {currentPage + 1} of {document.page_count || '?'}
              </span>
              
              <Button
                variant="ghost"
                size="icon"
                onClick={() => onPageChange(currentPage + 1)}
                disabled={!document.page_count || currentPage >= document.page_count - 1}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          )}
        </div>

        <div className="flex items-center gap-2">
          {/* Scope Mode Toggle */}
          <div className="hidden md:flex gap-1 rounded-lg border p-1">
            {scopeModes.map((mode) => (
              <button
                key={mode}
                onClick={() => setScopeMode(mode)}
                className={`rounded px-3 py-1 text-sm transition-colors ${
                  scopeMode === mode
                    ? 'bg-primary text-primary-foreground'
                    : 'hover:bg-accent'
                }`}
              >
                {mode === 'page' && 'This Page'}
                {mode === 'near' && '±2 Pages'}
                {mode === 'deck' && 'Entire Deck'}
              </button>
            ))}
          </div>

          <ThemeToggle />
          <ModelSelector />

          {document && (
            <Button 
              variant="ghost" 
              size="icon" 
              onClick={() => navigate(`/doc/${document.id}/history`)}
              className="hidden sm:flex"
              title="Conversation History"
            >
              <MessageSquare className="h-5 w-5" />
            </Button>
          )}

          <Button variant="ghost" size="icon" onClick={() => navigate('/search')} className="hidden sm:flex">
            <Search className="h-5 w-5" />
          </Button>

          <Button variant="ghost" size="icon" onClick={logout}>
            <LogOut className="h-5 w-5" />
          </Button>
        </div>
      </div>
    </header>
  );
}

export default Header;

