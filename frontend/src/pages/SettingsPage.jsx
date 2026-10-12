import React, { useState } from 'react';
import { Settings as SettingsIcon, Lock, User, ShieldCheck, Server, Info } from 'lucide-react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { GlassCard } from '../components/ui/GlassCard';
import { Input } from '../components/ui/Input';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { useToast } from '../components/ui/Toast';
import { formatDate } from '../utils/formatters';

export const SettingsPage = () => {
  const { user, backendMode } = useAuth();
  const { toast } = useToast();

  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setError('');

    if (newPassword.length < 8) {
      setError('New password must be at least 8 characters long.');
      return;
    }

    if (newPassword !== confirmPassword) {
      setError('New passwords do not match.');
      return;
    }

    setLoading(true);
    try {
      await api.post('/api/auth/change-password', {
        currentPassword,
        newPassword
      });
      toast.success('Password changed successfully!');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err) {
      const msg = err.response?.data?.error?.message || 'Failed to change password';
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-xl font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
          <SettingsIcon className="w-6 h-6 text-indigo-500" />
          Account & System Settings
        </h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Manage your account credentials and inspect the Cloud Controller runtime status
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* User Profile Card */}
        <GlassCard variant="default" className="p-6 space-y-4">
          <h2 className="text-sm font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
            <User className="w-4 h-4 text-indigo-500" />
            Profile Details
          </h2>

          <div className="space-y-3 text-xs">
            <div>
              <span className="text-slate-400 block text-[10px] uppercase font-semibold">Username</span>
              <span className="font-semibold text-slate-800 dark:text-slate-100">{user?.username}</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px] uppercase font-semibold">Email</span>
              <span className="font-semibold text-slate-800 dark:text-slate-100">{user?.email}</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px] uppercase font-semibold">Role</span>
              <Badge variant={user?.role === 'admin' ? 'info' : 'default'} size="sm">
                {user?.role?.toUpperCase()}
              </Badge>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px] uppercase font-semibold">Storage Quota</span>
              <span className="font-semibold text-slate-800 dark:text-slate-100">{user?.storageQuotaMb || 1024} MB</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px] uppercase font-semibold">Member Since</span>
              <span className="font-semibold text-slate-800 dark:text-slate-100">{formatDate(user?.createdAt)}</span>
            </div>
          </div>
        </GlassCard>

        {/* Change Password Form */}
        <GlassCard variant="default" className="p-6">
          <h2 className="text-sm font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2 mb-4">
            <Lock className="w-4 h-4 text-indigo-500" />
            Change Password
          </h2>

          {error && (
            <div className="mb-4 p-2.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-500 text-xs">
              {error}
            </div>
          )}

          <form onSubmit={handleChangePassword} className="space-y-3">
            <Input
              id="current-password"
              label="Current Password"
              type="password"
              placeholder="••••••••"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              required
            />
            <Input
              id="new-password"
              label="New Password (min 8 chars)"
              type="password"
              placeholder="••••••••"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
            />
            <Input
              id="confirm-password"
              label="Confirm New Password"
              type="password"
              placeholder="••••••••"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
            />
            <Button
              type="submit"
              variant="primary"
              size="sm"
              loading={loading}
              className="w-full mt-2"
            >
              Update Password
            </Button>
          </form>
        </GlassCard>
      </div>

      {/* System Diagnostics Card */}
      <GlassCard variant="default" className="p-6">
        <h2 className="text-sm font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2 mb-3">
          <Server className="w-4 h-4 text-emerald-500" />
          Cloud Controller Environment & Diagnostics
        </h2>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
          <div className="p-3 rounded-xl glass-subtle">
            <p className="text-[10px] text-slate-400 font-semibold uppercase">App Version</p>
            <p className="font-bold text-slate-800 dark:text-slate-100 mt-0.5">v1.0.0</p>
          </div>
          <div className="p-3 rounded-xl glass-subtle">
            <p className="text-[10px] text-slate-400 font-semibold uppercase">Storage Backend</p>
            <p className="font-bold text-slate-800 dark:text-slate-100 mt-0.5 uppercase">{backendMode}</p>
          </div>
          <div className="p-3 rounded-xl glass-subtle">
            <p className="text-[10px] text-slate-400 font-semibold uppercase">Auth Type</p>
            <p className="font-bold text-slate-800 dark:text-slate-100 mt-0.5">JWT / HS256</p>
          </div>
          <div className="p-3 rounded-xl glass-subtle">
            <p className="text-[10px] text-slate-400 font-semibold uppercase">Database Mode</p>
            <p className="font-bold text-slate-800 dark:text-slate-100 mt-0.5">SQLite WAL</p>
          </div>
        </div>
      </GlassCard>
    </div>
  );
};
