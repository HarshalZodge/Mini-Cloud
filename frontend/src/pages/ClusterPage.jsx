import React, { useState, useEffect } from 'react';
import { Server, Activity, ShieldAlert, Cpu, HardDrive, RefreshCw } from 'lucide-react';
import { api } from '../services/api';
import { GlassCard } from '../components/ui/GlassCard';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { useToast } from '../components/ui/Toast';
import { formatBytes } from '../utils/formatters';

export const ClusterPage = () => {
  const { toast } = useToast();
  const [clusterData, setClusterData] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchClusterMetrics = async () => {
    setLoading(true);
    try {
      const res = await api.get('/api/admin/cluster');
      if (res.data.success) {
        setClusterData(res.data.data);
      }
    } catch (err) {
      toast.error('Failed to query cluster metrics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchClusterMetrics();
  }, []);

  const info = clusterData?.clusterInfo || {};

  return (
    <div className="space-y-6 max-w-5xl">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
            <Server className="w-6 h-6 text-indigo-500" />
            Hadoop HDFS Cluster Status
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Real-time telemetry retrieved by Cloud Controller via NameNode JMX
          </p>
        </div>

        <Button
          variant="secondary"
          size="sm"
          icon={RefreshCw}
          onClick={fetchClusterMetrics}
          loading={loading}
        >
          Refresh Metrics
        </Button>
      </div>

      {/* Cluster Health Banner */}
      <GlassCard variant="default" className="p-6">
        <div className="flex items-center justify-between pb-4 border-b border-white/20 dark:border-white/10 mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-800 dark:text-slate-100">
                FSNamesystem Health
              </h2>
              <p className="text-xs text-slate-400">
                Active Storage Backend: <span className="uppercase font-bold text-indigo-600 dark:text-indigo-400">{clusterData?.backend || 'mock'}</span>
              </p>
            </div>
          </div>

          <Badge variant={info.available ? 'success' : 'warning'} size="md">
            {info.available ? 'Cluster Online' : 'Metrics Unavailable'}
          </Badge>
        </div>

        {/* Metric Cards Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl glass-subtle text-center">
            <p className="text-2xl font-bold text-slate-800 dark:text-slate-100">
              {info.numLiveDataNodes !== undefined ? info.numLiveDataNodes : '—'}
            </p>
            <p className="text-xs text-emerald-600 dark:text-emerald-400 font-semibold mt-1">
              Live DataNodes
            </p>
          </div>

          <div className="p-4 rounded-xl glass-subtle text-center">
            <p className="text-2xl font-bold text-slate-800 dark:text-slate-100">
              {info.numDeadDataNodes !== undefined ? info.numDeadDataNodes : '—'}
            </p>
            <p className="text-xs text-rose-500 font-semibold mt-1">
              Dead DataNodes
            </p>
          </div>

          <div className="p-4 rounded-xl glass-subtle text-center">
            <p className="text-2xl font-bold text-slate-800 dark:text-slate-100">
              {info.blocksTotal !== undefined ? info.blocksTotal : '—'}
            </p>
            <p className="text-xs text-indigo-600 dark:text-indigo-400 font-semibold mt-1">
              Total HDFS Blocks
            </p>
          </div>

          <div className="p-4 rounded-xl glass-subtle text-center">
            <p className="text-2xl font-bold text-slate-800 dark:text-slate-100">
              {info.configuredReplication !== undefined ? info.configuredReplication : 1}
            </p>
            <p className="text-xs text-slate-500 font-semibold mt-1">
              Replication Factor
            </p>
          </div>
        </div>

        {/* Raw Capacity Pool */}
        <div className="mt-6 pt-6 border-t border-white/20 dark:border-white/10 grid grid-cols-1 sm:grid-cols-3 gap-4 text-center">
          <div className="p-3 rounded-xl glass-subtle">
            <span className="text-[10px] uppercase font-bold text-slate-400 block">Total Pool Capacity</span>
            <span className="text-base font-bold text-slate-800 dark:text-slate-100">
              {info.capacityTotalBytes ? formatBytes(info.capacityTotalBytes) : '—'}
            </span>
          </div>

          <div className="p-3 rounded-xl glass-subtle">
            <span className="text-[10px] uppercase font-bold text-slate-400 block">Raw Capacity Used</span>
            <span className="text-base font-bold text-slate-800 dark:text-slate-100">
              {info.capacityUsedBytes ? formatBytes(info.capacityUsedBytes) : '—'}
            </span>
          </div>

          <div className="p-3 rounded-xl glass-subtle">
            <span className="text-[10px] uppercase font-bold text-slate-400 block">Raw Capacity Free</span>
            <span className="text-base font-bold text-slate-800 dark:text-slate-100">
              {info.capacityRemainingBytes ? formatBytes(info.capacityRemainingBytes) : '—'}
            </span>
          </div>
        </div>
      </GlassCard>

      {/* Controller Role Card for Viva */}
      <GlassCard variant="default" className="p-6">
        <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2 mb-2">
          <ShieldAlert className="w-4 h-4 text-indigo-500" />
          Cloud Controller Orchestration Overview
        </h3>
        <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
          The MiniCloud Cloud Controller decouples file presentation from low-level distributed storage. It maintains
          virtual folder hierarchies in SQLite while streaming physical bytes into flat UUIDs in HDFS. It continuously
          monitors cluster DataNodes, enforces per-user quotas, prevents path traversal, and provides zero-cost folder
          renames and reorganizations.
        </p>
      </GlassCard>
    </div>
  );
};
