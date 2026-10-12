import React, { useState } from 'react';
import {
  Menu,
  Search,
  UploadCloud,
  Bell,
  Sun,
  Moon,
  LogOut,
  User as UserIcon,
  ChevronDown
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../ui/Toast';
import { GlassCard } from '../ui/GlassCard';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';

export const TopBar = ({ onOpenSidebar, onUploadClick, onSearchChange, searchQuery }) => {
  const { user, isDarkMode, toggleTheme, logout, backendMode } = useAuth();
  const { eventHistory } = useToast();
  const [showBellDropdown, setShowBellDropdown] = useState(false);
  const [showUserDropdown, setShowUserDropdown] = useState(false);

  return (
    <header className="sticky top-0 z-30 p-4 pb-0">
      <GlassCard variant="default" className="px-4 py-3 flex items-center justify-between gap-4">
        {/* Left: Mobile hamburger & search */}
        <div className="flex items-center gap-3 flex-1 max-w-md">
          <button
            onClick={onOpenSidebar}
            className="p-2 rounded-xl text-slate-500 hover:text-slate-800 dark:hover:text-slate-100 lg:hidden hover:bg-white/40 dark:hover:bg-slate-800/40"
            aria-label="Open sidebar"
          >
            <Menu className="w-5 h-5" />
          </button>

          {/* Search box */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search files and folders..."
              value={searchQuery || ''}
              onChange={(e) => onSearchChange && onSearchChange(e.target.value)}
              className="w-full pl-9 pr-4 py-1.5 text-xs rounded-xl glass-subtle text-slate-800 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
            />
          </div>
        </div>

        {/* Right: Storage mode badge, Upload button, Bell, Theme, Avatar menu */}
        <div className="flex items-center gap-2.5">
          {/* Storage Backend Badge */}
          {backendMode === 'hdfs' ? (
            <Badge variant="success" size="sm" className="hidden sm:inline-flex gap-1.5 font-bold">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
              HDFS ACTIVE
            </Badge>
          ) : (
            <Badge variant="warning" size="sm" className="hidden sm:inline-flex gap-1.5 font-bold">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
              MOCK MODE
            </Badge>
          )}

          {/* Quick Upload action button */}
          {onUploadClick && (
            <Button
              variant="primary"
              size="sm"
              icon={UploadCloud}
              onClick={onUploadClick}
              className="hidden sm:inline-flex"
            >
              Upload
            </Button>
          )}

          {/* Notification Bell */}
          <div className="relative">
            <button
              onClick={() => {
                setShowBellDropdown(!showBellDropdown);
                setShowUserDropdown(false);
              }}
              className="p-2 rounded-xl text-slate-600 dark:text-slate-300 hover:bg-white/40 dark:hover:bg-slate-800/40 relative"
              aria-label="Notifications"
            >
              <Bell className="w-4 h-4" />
              {eventHistory.length > 0 && (
                <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-indigo-500"></span>
              )}
            </button>

            {/* Bell Dropdown */}
            {showBellDropdown && (
              <GlassCard
                variant="strong"
                className="absolute right-0 mt-2 w-80 p-3 z-50 shadow-2xl animate-in fade-in zoom-in-95"
              >
                <div className="flex items-center justify-between pb-2 border-b border-white/20 dark:border-white/10 mb-2">
                  <h4 className="text-xs font-bold text-slate-800 dark:text-slate-100">
                    Recent Activity
                  </h4>
                  <span className="text-[10px] text-slate-400">In-session</span>
                </div>
                <div className="max-h-60 overflow-y-auto space-y-1.5">
                  {eventHistory.length === 0 ? (
                    <p className="text-xs text-slate-400 text-center py-4">No events yet</p>
                  ) : (
                    eventHistory.map((ev) => (
                      <div
                        key={ev.id}
                        className="p-2 rounded-lg glass-subtle text-xs text-slate-700 dark:text-slate-300 flex items-start gap-2"
                      >
                        <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 mt-1.5 shrink-0"></span>
                        <div className="flex-1">
                          <p>{ev.message}</p>
                          <span className="text-[9px] text-slate-400">
                            {ev.time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </GlassCard>
            )}
          </div>

          {/* Dark Mode Toggle */}
          <button
            onClick={toggleTheme}
            className="p-2 rounded-xl text-slate-600 dark:text-slate-300 hover:bg-white/40 dark:hover:bg-slate-800/40"
            aria-label="Toggle theme"
          >
            {isDarkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </button>

          {/* User Menu Dropdown */}
          <div className="relative">
            <button
              onClick={() => {
                setShowUserDropdown(!showUserDropdown);
                setShowBellDropdown(false);
              }}
              className="flex items-center gap-1.5 p-1 pl-1.5 pr-2 rounded-xl glass-subtle hover:bg-white/60 dark:hover:bg-slate-800/60"
            >
              <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-indigo-500 to-violet-500 text-white font-bold text-xs flex items-center justify-center uppercase shadow-sm">
                {user?.username?.substring(0, 2) || 'MC'}
              </div>
              <ChevronDown className="w-3.5 h-3.5 text-slate-500" />
            </button>

            {showUserDropdown && (
              <GlassCard
                variant="strong"
                className="absolute right-0 mt-2 w-48 p-1.5 z-50 shadow-2xl animate-in fade-in zoom-in-95"
              >
                <div className="px-3 py-2 border-b border-white/20 dark:border-white/10 mb-1">
                  <p className="text-xs font-bold text-slate-800 dark:text-slate-100 truncate">
                    {user?.username}
                  </p>
                  <p className="text-[10px] text-slate-500 dark:text-slate-400 truncate">
                    {user?.email}
                  </p>
                </div>
                <button
                  onClick={() => {
                    setShowUserDropdown(false);
                    window.location.href = '/settings';
                  }}
                  className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium text-slate-700 dark:text-slate-300 hover:bg-white/40 dark:hover:bg-slate-800/40"
                >
                  <UserIcon className="w-3.5 h-3.5" />
                  Account Settings
                </button>
                <button
                  onClick={logout}
                  className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium text-rose-600 dark:text-rose-400 hover:bg-rose-500/10"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  Sign Out
                </button>
              </GlassCard>
            )}
          </div>
        </div>
      </GlassCard>
    </header>
  );
};
