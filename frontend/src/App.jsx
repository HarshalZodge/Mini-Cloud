import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ToastProvider } from './components/ui/Toast';
import { AppLayout } from './components/layout/AppLayout';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { DesignPreviewPage } from './pages/DesignPreviewPage';
import { DashboardPage } from './pages/DashboardPage';
import { FilesPage } from './pages/FilesPage';
import { RecentPage } from './pages/RecentPage';
import { StarredPage } from './pages/StarredPage';
import { TrashPage } from './pages/TrashPage';
import { StoragePage } from './pages/StoragePage';
import { SettingsPage } from './pages/SettingsPage';
import { ClusterPage } from './pages/ClusterPage';
import { UploadModal } from './components/files/UploadModal';

// Protected Route Guard
const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

// Admin Route Guard
const AdminRoute = ({ children }) => {
  const { user } = useAuth();
  if (user?.role !== 'admin') {
    return <Navigate to="/dashboard" replace />;
  }
  return children;
};

export const App = () => {
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const handleUploadComplete = () => {
    setRefreshTrigger((prev) => prev + 1);
  };

  return (
    <BrowserRouter>
      <AuthProvider>
        <ToastProvider>
          <Routes>
            {/* Public Routes */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />

            {/* Design System Preview Showroom */}
            <Route
              path="/design-preview"
              element={
                <AppLayout
                  onUploadClick={() => setUploadModalOpen(true)}
                  searchQuery={searchQuery}
                  onSearchChange={setSearchQuery}
                >
                  <DesignPreviewPage />
                </AppLayout>
              }
            />

            {/* Protected Routes */}
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <AppLayout
                    onUploadClick={() => setUploadModalOpen(true)}
                    searchQuery={searchQuery}
                    onSearchChange={setSearchQuery}
                  />
                </ProtectedRoute>
              }
            >
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route
                path="dashboard"
                element={<DashboardPage key={refreshTrigger} onUploadClick={() => setUploadModalOpen(true)} />}
              />
              <Route
                path="files"
                element={
                  <FilesPage
                    key={refreshTrigger}
                    onUploadClick={() => setUploadModalOpen(true)}
                    searchQuery={searchQuery}
                  />
                }
              />
              <Route path="recent" element={<RecentPage key={refreshTrigger} />} />
              <Route path="starred" element={<StarredPage key={refreshTrigger} />} />
              <Route path="trash" element={<TrashPage key={refreshTrigger} />} />
              <Route path="storage" element={<StoragePage key={refreshTrigger} />} />
              <Route path="settings" element={<SettingsPage />} />
              <Route
                path="cluster"
                element={
                  <AdminRoute>
                    <ClusterPage />
                  </AdminRoute>
                }
              />
            </Route>

            {/* Catch-all redirect */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>

          {/* Global Upload Modal */}
          <UploadModal
            isOpen={uploadModalOpen}
            onClose={() => setUploadModalOpen(false)}
            onUploadComplete={handleUploadComplete}
          />
        </ToastProvider>
      </AuthProvider>
    </BrowserRouter>
  );
};

export default App;
