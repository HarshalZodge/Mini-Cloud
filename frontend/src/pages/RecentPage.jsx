import React, { useState, useEffect } from 'react';
import { Clock, Download } from 'lucide-react';
import { api } from '../services/api';
import { GlassCard } from '../components/ui/GlassCard';
import { FileIcon } from '../components/files/FileIcon';
import { EmptyState } from '../components/ui/EmptyState';
import { useToast } from '../components/ui/Toast';
import { formatBytes, formatDate } from '../utils/formatters';

export const RecentPage = () => {
  const { toast } = useToast();
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchRecent = async () => {
      try {
        const res = await api.get('/api/files?view=recent&sort=last_accessed&order=desc');
        if (res.data.success) {
          setFiles(res.data.data.files || []);
        }
      } catch (err) {
        toast.error('Failed to load recent files');
      } finally {
        setLoading(false);
      }
    };
    fetchRecent();
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
      toast.success(`Downloaded ${file.original_name}`);
    } catch {
      toast.error('Download failed');
    }
  };

  return (
    <div className="space-y-4">
      <GlassCard variant="default" className="p-4 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
            <Clock className="w-5 h-5 text-indigo-500" />
            Recent Files
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Files accessed or uploaded recently across all folders
          </p>
        </div>
      </GlassCard>

      {loading ? (
        <div className="space-y-2 animate-pulse">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-12 rounded-xl bg-white/40 dark:bg-slate-900/40"></div>
          ))}
        </div>
      ) : files.length === 0 ? (
        <EmptyState
          icon={Clock}
          title="No recent files"
          description="Files you upload or download will appear here for quick access."
        />
      ) : (
        <GlassCard variant="default" className="overflow-hidden">
          <table className="w-full text-left text-xs">
            <thead className="bg-white/20 dark:bg-slate-900/40 text-slate-500 uppercase tracking-wider font-semibold border-b border-white/20 dark:border-white/10">
              <tr>
                <th className="py-3 px-4">Name</th>
                <th className="py-3 px-4 hidden sm:table-cell">Size</th>
                <th className="py-3 px-4 hidden md:table-cell">Last Accessed</th>
                <th className="py-3 px-4 text-right">Download</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/10 dark:divide-white/5">
              {files.map((file) => (
                <tr key={file.id} className="hover:bg-white/30 dark:hover:bg-slate-800/30 transition-colors">
                  <td className="py-3 px-4 flex items-center gap-3 font-medium text-slate-800 dark:text-slate-100 min-w-0">
                    <FileIcon category={file.category} extension={file.extension} />
                    <span className="truncate">{file.original_name}</span>
                  </td>
                  <td className="py-3 px-4 text-slate-500 dark:text-slate-400 hidden sm:table-cell">
                    {formatBytes(file.file_size)}
                  </td>
                  <td className="py-3 px-4 text-slate-400 hidden md:table-cell">
                    {formatDate(file.last_accessed_at)}
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={() => handleDownload(file)}
                      className="p-1.5 rounded-lg text-slate-400 hover:text-indigo-600 hover:bg-white/40"
                    >
                      <Download className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </GlassCard>
      )}
    </div>
  );
};
