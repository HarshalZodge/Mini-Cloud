import React, { useEffect, useState } from 'react';
import {
  FolderOpen,
  FileText,
  Star,
  Trash2,
  HardDrive,
  ArrowUpRight,
  Download,
  UploadCloud
} from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { GlassCard } from '../components/ui/GlassCard';
import { ProgressBar } from '../components/ui/ProgressBar';
import { Button } from '../components/ui/Button';
import { FileIcon } from '../components/files/FileIcon';
import { formatBytes, formatDate } from '../utils/formatters';

const CHART_COLORS = ['#8b5cf6', '#3b82f6', '#ec4899', '#f59e0b', '#10b981', '#64748b'];

export const DashboardPage = ({ onUploadClick }) => {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [recentFiles, setRecentFiles] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchDashboardData = async () => {
    try {
      const [statsRes, recentRes] = await Promise.all([
        api.get('/api/dashboard/stats'),
        api.get('/api/dashboard/recent-files')
      ]);

      if (statsRes.data.success) {
        setStats(statsRes.data.data);
      }
      if (recentRes.data.success) {
        setRecentFiles(recentRes.data.data.recentFiles || []);
      }
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const handleDownload = async (file) => {
    try {
      const res = await api.get(`/api/files/${file.id}/download`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', file.original_name);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('Download error:', err);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-40 rounded-2xl bg-white/40 dark:bg-slate-900/40"></div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-28 rounded-2xl bg-white/40 dark:bg-slate-900/40"></div>
          ))}
        </div>
      </div>
    );
  }

  const chartData = stats?.typeBreakdown?.filter((item) => item.count > 0) || [];

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <GlassCard variant="default" className="p-6 relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">
              Welcome back, {user?.username}!
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 max-w-xl">
              Your personal cloud storage is active on the laboratory LAN. Files uploaded are backed by Apache Hadoop HDFS.
            </p>
          </div>
          <Button
            variant="primary"
            icon={UploadCloud}
            onClick={onUploadClick}
            className="self-start md:self-center"
          >
            Upload Files
          </Button>
        </div>

        {/* Quota Progress Bar in Banner */}
        <div className="mt-6 pt-5 border-t border-white/20 dark:border-white/10">
          <ProgressBar
            label="Personal Storage Quota"
            valueText={`${stats?.storage?.usedMb || 0} MB / ${stats?.storage?.quotaMb || 1024} MB (${stats?.storage?.percentage || 0}%)`}
            percentage={stats?.storage?.percentage || 0}
          />
        </div>
      </GlassCard>

      {/* 4 Quick Stat Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <GlassCard variant="default" className="p-4" hover>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-500/10 text-blue-600 dark:text-blue-400 flex items-center justify-center">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xl font-bold text-slate-800 dark:text-slate-100">{stats?.totalFiles || 0}</p>
              <p className="text-[11px] font-medium text-slate-500 dark:text-slate-400">Total Files</p>
            </div>
          </div>
        </GlassCard>

        <GlassCard variant="default" className="p-4" hover>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-500/10 text-amber-600 dark:text-amber-400 flex items-center justify-center">
              <FolderOpen className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xl font-bold text-slate-800 dark:text-slate-100">{stats?.totalFolders || 0}</p>
              <p className="text-[11px] font-medium text-slate-500 dark:text-slate-400">Folders</p>
            </div>
          </div>
        </GlassCard>

        <GlassCard variant="default" className="p-4" hover>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-yellow-500/10 text-yellow-600 dark:text-yellow-400 flex items-center justify-center">
              <Star className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xl font-bold text-slate-800 dark:text-slate-100">{stats?.starredCount || 0}</p>
              <p className="text-[11px] font-medium text-slate-500 dark:text-slate-400">Starred</p>
            </div>
          </div>
        </GlassCard>

        <GlassCard variant="default" className="p-4" hover>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-rose-500/10 text-rose-600 dark:text-rose-400 flex items-center justify-center">
              <Trash2 className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xl font-bold text-slate-800 dark:text-slate-100">{stats?.trashCount || 0}</p>
              <p className="text-[11px] font-medium text-slate-500 dark:text-slate-400">Trash</p>
            </div>
          </div>
        </GlassCard>
      </div>

      {/* Two Column Layout: Chart & Recent Files */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: File Type Distribution Donut */}
        <GlassCard variant="default" className="p-5 flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100">
              Storage Distribution
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Breakdown by file category
            </p>
          </div>

          <div className="h-52 w-full my-4 flex items-center justify-center">
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={chartData}
                    dataKey="bytes"
                    nameKey="name"
                    innerRadius={55}
                    outerRadius={80}
                    paddingAngle={4}
                  >
                    {chartData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value) => formatBytes(value)}
                    contentStyle={{
                      backgroundColor: 'rgba(15, 23, 42, 0.9)',
                      borderRadius: '12px',
                      border: 'none',
                      color: '#fff',
                      fontSize: '12px'
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-center text-xs text-slate-400">
                <HardDrive className="w-8 h-8 mx-auto mb-2 opacity-50" />
                No files uploaded yet
              </div>
            )}
          </div>

          <div className="grid grid-cols-2 gap-2 pt-2 border-t border-white/20 dark:border-white/10">
            {stats?.typeBreakdown?.map((item, idx) => (
              <div key={item.category} className="flex items-center gap-1.5 text-[11px]">
                <span
                  className="w-2.5 h-2.5 rounded-full shrink-0"
                  style={{ backgroundColor: CHART_COLORS[idx % CHART_COLORS.length] }}
                />
                <span className="text-slate-600 dark:text-slate-300 truncate">{item.name}</span>
                <span className="text-slate-400 ml-auto">{item.count}</span>
              </div>
            ))}
          </div>
        </GlassCard>

        {/* Right Column: Recent Files Table */}
        <GlassCard variant="default" className="lg:col-span-2 p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-white/20 dark:border-white/10">
              <div>
                <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100">
                  Recent Files
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                  Last accessed or uploaded files
                </p>
              </div>
              <a
                href="/files"
                className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:underline flex items-center gap-1"
              >
                View all <ArrowUpRight className="w-3.5 h-3.5" />
              </a>
            </div>

            {/* List */}
            <div className="divide-y divide-white/10 dark:divide-white/5 mt-2">
              {recentFiles.length === 0 ? (
                <div className="text-center py-10 text-xs text-slate-400">
                  No recent files available
                </div>
              ) : (
                recentFiles.map((file) => (
                  <div
                    key={file.id}
                    className="py-2.5 flex items-center justify-between gap-3 hover:bg-white/30 dark:hover:bg-slate-800/30 rounded-xl px-2 transition-colors"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <FileIcon category={file.category} extension={file.extension} />
                      <div className="truncate">
                        <p className="text-xs font-medium text-slate-800 dark:text-slate-100 truncate">
                          {file.original_name}
                        </p>
                        <p className="text-[10px] text-slate-400">
                          {formatBytes(file.file_size)} • {formatDate(file.uploaded_at)}
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={() => handleDownload(file)}
                      className="p-1.5 rounded-lg text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400 hover:bg-white/50"
                      title="Download file"
                    >
                      <Download className="w-4 h-4" />
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        </GlassCard>
      </div>
    </div>
  );
};
