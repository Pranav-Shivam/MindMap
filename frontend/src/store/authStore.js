import { create } from 'zustand';
import { persist } from 'zustand/middleware';

const useAuthStore = create(
  persist(
    (set) => ({
      user: null,
      token: null,
      
      setAuth: (user, token) => {
        localStorage.setItem('auth_token', token);
        set({ user, token });
      },
      
      logout: () => {
        localStorage.removeItem('auth_token');
        set({ user: null, token: null });
      },
      
      updateUser: (user) => set({ user }),
    }),
    {
      name: 'auth-storage',
    }
  )
);

export default useAuthStore;

