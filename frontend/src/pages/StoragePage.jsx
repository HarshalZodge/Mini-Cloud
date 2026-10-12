import React, { useState, useEffect } from 'react';
import { HardDrive, Server, ShieldCheck, Database, Layers } from 'lucide-react';
import { api } from '../services/api';
import { GlassCard } from '../components/ui/GlassCard';
import { ProgressBar } from '../components/ui/ProgressBar';
import { Badge } from '../components/ui/Badge';
import { formatBytes } from '../utils/formatters';

export const StoragePage = () => {
  const [storageData, setStorageData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStorage = async () => {
      try {
        const res = await api.get('/api/storage/usage');
        if (res.data.success) {
          setStorageData(res.data.data);
        }
      } catch (err) {
        console.error('Failed to load storage details:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchStorage();
  }, []);

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-44 rounded-2xl bg-white/40 dark:bg-slate-900/40"></div>
        <div className="h-60 rounded-2xl bg-white/40 dark:bg-slate-900/40"></div>
      </div>
    );
  }

  const { userQuota, breakdown, clusterStorage } = storageData || {};

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Title */}
      <div>
        <h1 className="text-xl font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
          <HardDrive className="w-6 h-6 text-indigo-500" />
          Storage & Capacity
        </h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Detailed metrics for your personal storage quota versus total HDFS cluster capacity
        </p>
      </div>

      {/* 1. User Quota Card */}
      <GlassCard variant="default" className="p-6">
        <div className="flex items-center justify-between pb-4 border-b border-white/20 dark:border-white/10 mb-4">
          <div>
            <h2 className="text-base font-bold text-slate-800 dark:text-slate-100">
              Your Quota (Configured)
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Allocated ceiling managed by the Cloud Controller
            </p>
          </div>
          <Badge variant={userQuota?.usagePercentage > 90 ? 'danger' : 'info'} size="md">
            {userQuota?.usagePercentage || 0}% Used
          </Badge>
        </div>

        <ProgressBar
          label="Used Space"
          valueText={`${userQuota?.usedMb || 0} MB of ${userQuota?.quotaMb || 1024} MB (${userQuota?.usagePercentage || 0}%)`}
          percentage={userQuota?.usagePercentage || 0}
          size="md"
        />

        <div className="grid grid-cols-3 gap-4 mt-6 pt-6 border-t border-white/20 dark:border-white/10 text-center">
          <div>
            <p className="text-base font-bold text-slate-800 dark:text-slate-100">{formatBytes(userQuota?.usedBytes)}</p>
            <p className="text-[11px] text-slate-400">Space Used</p>
          </div>
          <div>
            <p className="text-base font-bold text-slate-800 dark:text-slate-100">{formatBytes(userQuota?.remainingBytes)}</p>
            <p className="text-[11px] text-slate-400">Space Remaining</p>
          </div>
          <div>
            <p className="text-base font-bold text-slate-800 dark:text-slate-100">{userQuota?.quotaMb || 1024} MB</p>
            <p className="text-[11px] text-slate-400">Total Quota</p>
          </div>
        </div>
      </GlassCard>

      {/* 2. Usage by Category */}
      <GlassCard variant="default" className="p-6">
        <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100 mb-4">
          Usage by File Type
        </h3>
        <div className="space-y-3">
          {breakdown?.map((item) => {
            const percent = userQuota?.usedBytes > 0
              ? Math.round((item.bytes / userQuota.usedBytes) * 100)
              : 0;
            return (
              <div key={item.category} className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="font-medium text-slate-700 dark:text-slate-300">{item.category}</span>
                  <span className="text-slate-400">{formatBytes(item.bytes)} ({percent}%)</span>
                </div>
                <div className="w-full bg-slate-200/50 dark:bg-slate-700/50 rounded-full h-1.5 overflow-hidden">
                  <div
                    className="bg-indigo-500 h-full rounded-full"
                    style={{ width: `${percent}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </GlassCard>

      {/* 3. Total HDFS Cluster Capacity */}
      <GlassCard variant="default" className="p-6">
        <div className="flex items-center justify-between pb-4 border-b border-white/20 dark:border-white/10 mb-4">
          <div>
            <h2 className="text-base font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
              <Server className="w-5 h-5 text-emerald-500" />
              Total HDFS Cluster Capacity
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Raw physical storage pool reported by Hadoop NameNode JMX
            </p>
          </div>
          <Badge variant={clusterStorage?.available ? 'success' : 'warning'}>
            {clusterStorage?.available ? 'JMX CONNECTED' : 'NOT AVAILABLE'}
          </Badge>
        </div>

        {clusterStorage?.available ? (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
            <div className="p-3 rounded-xl glass-subtle">
              <p className="text-base font-bold text-slate-800 dark:text-slate-100">
                {formatBytes(clusterStorage.capacityTotalBytes)}
              </p>
              <p className="text-[10px] text-slate-400">Total HDFS Pool</p>
            </div>
            <div className="p-3 rounded-xl glass-subtle">
              <p className="text-base font-bold text-slate-800 dark:text-slate-100">
                {formatBytes(clusterStorage.capacityUsedBytes)}
              </p>
              <p className="text-[10px] text-slate-400">HDFS Space Used</p>
            </div>
            <div className="p-3 rounded-xl glass-subtle">
              <p className="text-base font-bold text-slate-800 dark:text-slate-100">
                {formatBytes(clusterStorage.capacityRemainingBytes)}
              </p>
              <p className="text-[10px] text-slate-400">HDFS Free Pool</p>
            </div>
            <div className="p-3 rounded-xl glass-subtle">
              <p className="text-base font-bold text-slate-800 dark:text-slate-100">
                {clusterStorage.numLiveDataNodes || 1} Live
              </p>
              <p className="text-[10px] text-slate-400">Active DataNodes</p>
            </div>
          </div>
        ) : (
          <p className="text-xs text-slate-400 text-center py-4">
            Cluster metrics unavailable in current storage mode or NameNode JMX is offline.
          </p>
        )}
      </GlassCard>
    </div>
  );
};
