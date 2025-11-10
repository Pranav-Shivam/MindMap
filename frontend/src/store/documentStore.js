import { create } from 'zustand';

const useDocumentStore = create((set) => ({
  currentDocument: null,
  currentPage: 0,
  
  setCurrentDocument: (doc) => set({ currentDocument: doc }),
  setCurrentPage: (pageNo) => set({ currentPage: pageNo }),
  
  reset: () => set({ currentDocument: null, currentPage: 0 }),
}));

export default useDocumentStore;

