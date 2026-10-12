import React, { useState, useRef } from 'react';
import { UploadCloud, X, CheckCircle2, AlertCircle } from 'lucide-react';
import { api } from '../../services/api';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { ProgressBar } from '../ui/ProgressBar';
import { useToast } from '../ui/Toast';
import { formatBytes } from '../../utils/formatters';

export const UploadModal = ({ isOpen, onClose, targetFolderId, onUploadComplete }) => {
  const { toast } = useToast();
  const fileInputRef = useRef(null);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploadProgress, setUploadProgress] = useState({});
  const [uploadStatus, setUploadStatus] = useState({}); // 'pending' | 'uploading' | 'success' | 'error'
  const [uploadError, setUploadError] = useState({});
  const [isUploading, setIsUploading] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0) {
      setSelectedFiles((prev) => [...prev, ...files]);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    const files = Array.from(e.dataTransfer.files || []);
    if (files.length > 0) {
      setSelectedFiles((prev) => [...prev, ...files]);
    }
  };

  const removeFile = (index) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const startUpload = async () => {
    if (selectedFiles.length === 0) return;
    setIsUploading(true);

    let successCount = 0;

    for (let i = 0; i < selectedFiles.length; i++) {
      const file = selectedFiles[i];
      const fileKey = `${file.name}-${i}`;

      setUploadStatus((prev) => ({ ...prev, [fileKey]: 'uploading' }));

      const formData = new FormData();
      formData.append('file', file);
      if (targetFolderId) {
        formData.append('folder_id', targetFolderId);
      }

      try {
        await api.post('/api/files/upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: (progressEvent) => {
            if (progressEvent.total) {
              const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
              setUploadProgress((prev) => ({ ...prev, [fileKey]: percent }));
            }
          },
        });

        setUploadStatus((prev) => ({ ...prev, [fileKey]: 'success' }));
        successCount++;
      } catch (err) {
        const errorMsg = err.response?.data?.error?.message || err.message || 'Upload failed';
        setUploadStatus((prev) => ({ ...prev, [fileKey]: 'error' }));
        setUploadError((prev) => ({ ...prev, [fileKey]: errorMsg }));
      }
    }

    setIsUploading(false);
    if (successCount > 0) {
      toast.success(`Successfully uploaded ${successCount} file(s) to cloud storage!`);
      if (onUploadComplete) onUploadComplete();
    }
  };

  const handleClose = () => {
    if (!isUploading) {
      setSelectedFiles([]);
      setUploadProgress({});
      setUploadStatus({});
      setUploadError({});
      onClose();
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Upload Files to MiniCloud" maxWidth="max-w-xl">
      <div className="space-y-4">
        {/* Drop Zone */}
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragOver(true);
          }}
          onDragLeave={() => setIsDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-2xl p-6 text-center cursor-pointer transition-all duration-200 ${
            isDragOver
              ? 'border-indigo-500 bg-indigo-500/10 shadow-lg shadow-indigo-500/20'
              : 'border-slate-300 dark:border-slate-700 hover:border-indigo-400 glass-subtle'
          }`}
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileSelect}
            multiple
            className="hidden"
          />
          <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 dark:bg-indigo-500/20 text-indigo-600 dark:text-indigo-400 flex items-center justify-center mx-auto mb-3">
            <UploadCloud className="w-6 h-6" />
          </div>
          <p className="text-sm font-semibold text-slate-800 dark:text-slate-100">
            Click to upload or drag and drop files here
          </p>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Files are streamed directly into HDFS cluster blocks (Up to 100 MB per file)
          </p>
        </div>

        {/* Selected Files List */}
        {selectedFiles.length > 0 && (
          <div className="max-h-60 overflow-y-auto space-y-2 pr-1">
            {selectedFiles.map((file, idx) => {
              const fileKey = `${file.name}-${idx}`;
              const status = uploadStatus[fileKey] || 'pending';
              const progress = uploadProgress[fileKey] || 0;
              const error = uploadError[fileKey];

              return (
                <div
                  key={fileKey}
                  className="p-3 rounded-xl glass-subtle flex flex-col gap-2"
                >
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2 truncate pr-2">
                      <span className="font-medium text-slate-800 dark:text-slate-100 truncate">
                        {file.name}
                      </span>
                      <span className="text-slate-400 shrink-0">
                        ({formatBytes(file.size)})
                      </span>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      {status === 'success' && (
                        <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                      )}
                      {status === 'error' && (
                        <AlertCircle className="w-4 h-4 text-rose-500" title={error} />
                      )}
                      {!isUploading && status !== 'success' && (
                        <button
                          onClick={() => removeFile(idx)}
                          className="text-slate-400 hover:text-rose-500"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Progress bar during upload */}
                  {status === 'uploading' && (
                    <ProgressBar percentage={progress} size="sm" />
                  )}

                  {status === 'error' && (
                    <p className="text-[10px] text-rose-500 dark:text-rose-400">{error}</p>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-end gap-2 pt-2 border-t border-white/20 dark:border-white/10">
          <Button variant="ghost" onClick={handleClose} disabled={isUploading}>
            {selectedFiles.some((_, i) => uploadStatus[`${selectedFiles[i]?.name}-${i}`] === 'success') ? 'Done' : 'Cancel'}
          </Button>
          <Button
            variant="primary"
            icon={UploadCloud}
            onClick={startUpload}
            loading={isUploading}
            disabled={selectedFiles.length === 0 || isUploading}
          >
            Upload {selectedFiles.length > 0 ? `(${selectedFiles.length})` : ''}
          </Button>
        </div>
      </div>
    </Modal>
  );
};
