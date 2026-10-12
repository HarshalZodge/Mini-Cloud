import React, { useState, useEffect } from 'react';
import { Star, Download, Trash2 } from 'lucide-react';
import { api } from '../services/api';
import { GlassCard } from '../components/ui/GlassCard';
import { FileIcon } from '../components/files/FileIcon';
import { EmptyState } from '../components/ui/EmptyState';
import { useToast } from '../components/ui/Toast';
import { formatBytes, formatDate } from '../utils/formatters';

export const StarredPage = () => {
  const { toast } = useToast();
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchStarred = async () => {
    try {
      const res = await api.get('/api/files?view=starred');
      if (res.data.success) {
        setFiles(res.data.data.files || []);
      }
    } catch {
      toast.error('Failed to load starred files');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStarred();
  }, []);

  const handleUnstar = async (fileId) => {
    try {
      await api.delete(`/api/files/${fileId}/star`);
      setFiles((prev) => prev.filter((f) => f.id !== fileId));
      toast.info('Removed from starred');
    } catch {
      toast.error('Could not unstar file');
    }
  };

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
            <Star className="w-5 h-5 text-yellow-500 fill-yellow-500" />
            Starred Files
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Your bookmarked favorite documents and media
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
          icon={Star}
          title="No starred files"
          description="Star important files in My Files to easily find them here anytime."
        />
      ) : (
        <GlassCard variant="default" className="overflow-hidden">
          <table className="w-full text-left text-xs">
            <thead className="bg-white/20 dark:bg-slate-900/40 text-slate-500 uppercase tracking-wider font-semibold border-b border-white/20 dark:border-white/10">
              <tr>
                <th className="py-3 px-4">Name</th>
                <th className="py-3 px-4 hidden sm:table-cell">Size</th>
                <th className="py-3 px-4 hidden md:table-cell">Uploaded Date</th>
                <th className="py-3 px-4 text-right">Actions</th>
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
                    {formatDate(file.uploaded_at)}
                  </td>
                  <td className="py-3 px-4 text-right">
                    <div className="flex items-center justify-end gap-1">
                      <button
                        onClick={() => handleUnstar(file.id)}
                        className="p-1.5 rounded-lg text-yellow-500 hover:text-slate-400"
                        title="Remove star"
                      >
                        <Star className="w-4 h-4 fill-current" />
                      </button>
                      <button
                        onClick={() => handleDownload(file)}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-indigo-600 hover:bg-white/40"
                        title="Download"
                      >
                        <Download className="w-4 h-4" />
                      </button>
                    </div>
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
