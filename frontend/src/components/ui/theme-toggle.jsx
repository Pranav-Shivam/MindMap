import { Moon, Sun } from 'lucide-react';
import { Button } from './button';
import { useTheme } from '@/lib/theme-provider';
import { motion } from 'framer-motion';

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();

  const toggleTheme = () => {
    if (theme === 'light') {
      setTheme('dark');
    } else if (theme === 'dark') {
      setTheme('system');
    } else {
      setTheme('light');
    }
  };

  const getIcon = () => {
    switch (theme) {
      case 'light':
        return <Sun className="h-[1.2rem] w-[1.2rem]" />;
      case 'dark':
        return <Moon className="h-[1.2rem] w-[1.2rem]" />;
      default:
        return (
          <div className="relative h-[1.2rem] w-[1.2rem]">
            <Sun className="absolute inset-0 h-full w-full opacity-50" />
            <Moon className="absolute inset-0 h-full w-full opacity-50" />
          </div>
        );
    }
  };

  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={toggleTheme}
      className="h-9 w-9 px-0"
    >
      <motion.div
        key={theme}
        initial={{ rotate: -90, opacity: 0 }}
        animate={{ rotate: 0, opacity: 1 }}
        exit={{ rotate: 90, opacity: 0 }}
        transition={{ duration: 0.2 }}
      >
        {getIcon()}
      </motion.div>
      <span className="sr-only">Toggle theme</span>
    </Button>
  );
}
