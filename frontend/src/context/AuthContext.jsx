import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('minicloud_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState(() => localStorage.getItem('minicloud_token'));
  const [loading, setLoading] = useState(true);
  const [backendMode, setBackendMode] = useState('mock'); // 'hdfs' | 'mock'
  const [isDarkMode, setIsDarkMode] = useState(() => {
    return localStorage.getItem('minicloud_theme') === 'dark' ||
      (!('minicloud_theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches);
  });

  // Apply dark mode class to html tag
  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('minicloud_theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('minicloud_theme', 'light');
    }
  }, [isDarkMode]);

  const toggleTheme = () => setIsDarkMode((prev) => !prev);

  // Fetch current user and backend health
  const refreshUser = async () => {
    if (!token) {
      setLoading(false);
      return;
    }
    try {
      const [meRes, healthRes] = await Promise.all([
        api.get('/api/auth/me'),
        api.get('/api/health').catch(() => ({ data: { data: { storageBackend: 'mock' } } }))
      ]);

      if (meRes.data.success) {
        setUser(meRes.data.data);
        localStorage.setItem('minicloud_user', JSON.stringify(meRes.data.data));
      }
      if (healthRes.data?.data?.storageBackend) {
        setBackendMode(healthRes.data.data.storageBackend);
      }
    } catch (err) {
      console.error('Failed to load profile:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshUser();
  }, [token]);

  const login = async (identifier, password) => {
    const res = await api.post('/api/auth/login', { identifier, password });
    if (res.data.success) {
      const { token: newToken, user: newUser } = res.data.data;
      localStorage.setItem('minicloud_token', newToken);
      localStorage.setItem('minicloud_user', JSON.stringify(newUser));
      setToken(newToken);
      setUser(newUser);
      return newUser;
    }
    throw new Error(res.data.error?.message || 'Login failed');
  };

  const register = async (username, email, password) => {
    const res = await api.post('/api/auth/register', { username, email, password });
    if (res.data.success) {
      const { token: newToken, user: newUser } = res.data.data;
      localStorage.setItem('minicloud_token', newToken);
      localStorage.setItem('minicloud_user', JSON.stringify(newUser));
      setToken(newToken);
      setUser(newUser);
      return newUser;
    }
    throw new Error(res.data.error?.message || 'Registration failed');
  };

  const logout = async () => {
    try {
      if (token) {
        await api.post('/api/auth/logout');
      }
    } catch (e) {
      console.warn('Logout notification error:', e);
    } finally {
      localStorage.removeItem('minicloud_token');
      localStorage.removeItem('minicloud_user');
      setToken(null);
      setUser(null);
      window.location.href = '/login';
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        backendMode,
        isDarkMode,
        toggleTheme,
        login,
        register,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
