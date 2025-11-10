import { Routes, Route, Navigate } from 'react-router-dom';
import useAuthStore from './store/authStore';
import LoginPage from './pages/LoginPage';
import UploadPage from './pages/UploadPage';
import DocumentPage from './pages/DocumentPage';
import SearchPage from './pages/SearchPage';
import ConversationHistoryPage from './pages/ConversationHistoryPage';

function App() {
  const { token } = useAuthStore();

  // Protected route wrapper
  const ProtectedRoute = ({ children }) => {
    if (!token) {
      return <Navigate to="/login" replace />;
    }
    return children;
  };

  return (
    <div className="min-h-screen bg-background">
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <UploadPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/doc/:docId"
          element={
            <ProtectedRoute>
              <DocumentPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/doc/:docId/history"
          element={
            <ProtectedRoute>
              <ConversationHistoryPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/search"
          element={
            <ProtectedRoute>
              <SearchPage />
            </ProtectedRoute>
          }
        />
      </Routes>
    </div>
  );
}

export default App;

