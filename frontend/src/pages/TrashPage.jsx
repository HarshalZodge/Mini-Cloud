import React, { useState, useEffect } from 'react';
import { Trash2, RotateCcw, AlertTriangle, Flame } from 'lucide-react';
import { api } from '../services/api';
import { GlassCard } from '../components/ui/GlassCard';
import { Button } from '../components/ui/Button';
import { Modal } from '../components/ui/Modal';
import { FileIcon } from '../components/files/FileIcon';
import { EmptyState } from '../components/ui/EmptyState';
import { useToast } from '../components/ui/Toast';
import { formatBytes, formatDate } from '../utils/formatters';

export const TrashPage = () => {
  const { toast } = useToast();
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [emptyTrashModal, setEmptyTrashModal] = useState(false);
  const [permanentlyDeleting, setPermanentlyDeleting] = useState(false);

  const fetchTrash = async () => {
    try {
      const res = await api.get('/api/files?view=trash');
      if (res.data.success) {
        setFiles(res.data.data.files || []);
      }
    } catch {
      toast.error('Failed to load trash');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTrash();
  }, []);

  const handleRestore = async (fileId) => {
    try {
      await api.post(`/api/files/${fileId}/restore`);
      setFiles((prev) => prev.filter((f) => f.id !== fileId));
      toast.success('File restored to My Files');
    } catch {
      toast.error('Could not restore file');
    }
  };

  const handlePermanentDelete = async (fileId) => {
    try {
      await api.delete(`/api/files/${fileId}/permanent`);
      setFiles((prev) => prev.filter((f) => f.id !== fileId));
      toast.success('File permanently removed from HDFS storage');
    } catch {
      toast.error('Failed to permanently delete file');
    }
  };

  const handleEmptyTrash = async () => {
    setPermanentlyDeleting(true);
    try {
      await api.delete('/api/trash');
      setFiles([]);
      toast.success('Trash emptied. Storage space reclaimed.');
      setEmptyTrashModal(false);
    } catch {
      toast.error('Failed to empty trash');
    } finally {
      setPermanentlyDeleting(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Top Banner */}
      <GlassCard variant="default" className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
            <Trash2 className="w-5 h-5 text-rose-500" />
            Trash
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Items in trash still consume storage quota until permanently deleted.
          </p>
        </div>

        {files.length > 0 && (
          <Button
            variant="danger"
            size="sm"
            icon={Flame}
            onClick={() => setEmptyTrashModal(true)}
          >
            Empty Trash
          </Button>
        )}
      </GlassCard>

      {loading ? (
        <div className="space-y-2 animate-pulse">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-12 rounded-xl bg-white/40 dark:bg-slate-900/40"></div>
          ))}
        </div>
      ) : files.length === 0 ? (
        <EmptyState
          icon={Trash2}
          title="Trash is empty"
          description="Deleted files will appear here. You can restore them or delete them permanently."
        />
      ) : (
        <GlassCard variant="default" className="overflow-hidden">
          <table className="w-full text-left text-xs">
            <thead className="bg-white/20 dark:bg-slate-900/40 text-slate-500 uppercase tracking-wider font-semibold border-b border-white/20 dark:border-white/10">
              <tr>
                <th className="py-3 px-4">Name</th>
                <th className="py-3 px-4 hidden sm:table-cell">Size</th>
                <th className="py-3 px-4 hidden md:table-cell">Deleted Date</th>
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
                    {formatDate(file.deleted_at)}
                  </td>
                  <td className="py-3 px-4 text-right">
                    <div className="flex items-center justify-end gap-1">
                      <button
                        onClick={() => handleRestore(file.id)}
                        className="p-1.5 rounded-lg text-slate-500 hover:text-emerald-600 hover:bg-emerald-500/10"
                        title="Restore file"
                      >
                        <RotateCcw className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handlePermanentDelete(file.id)}
                        className="p-1.5 rounded-lg text-slate-500 hover:text-rose-600 hover:bg-rose-500/10"
                        title="Delete permanently"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </GlassCard>
      )}

      {/* Confirmation Modal */}
      <Modal
        isOpen={emptyTrashModal}
        onClose={() => setEmptyTrashModal(false)}
        title="Empty Trash Permanently?"
      >
        <div className="space-y-4">
          <div className="flex items-start gap-3 p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-600 dark:text-rose-400 text-xs">
            <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5" />
            <p>
              This will permanently delete all {files.length} items from physical HDFS storage.
              This action cannot be undone.
            </p>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={() => setEmptyTrashModal(false)}>Cancel</Button>
            <Button
              variant="danger"
              icon={Flame}
              onClick={handleEmptyTrash}
              loading={permanentlyDeleting}
            >
              Confirm & Empty
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
