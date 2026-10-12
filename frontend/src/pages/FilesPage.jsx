import React, { useState, useEffect } from 'react';
import {
  FolderPlus,
  UploadCloud,
  LayoutGrid,
  List,
  Download,
  Trash2,
  Star,
  MoreVertical,
  ChevronRight,
  Folder,
  Edit2,
  FolderInput,
  Search,
  Check
} from 'lucide-react';
import { api } from '../services/api';
import { GlassCard } from '../components/ui/GlassCard';
import { Button } from '../components/ui/Button';
import { Modal } from '../components/ui/Modal';
import { Input } from '../components/ui/Input';
import { FileIcon } from '../components/files/FileIcon';
import { EmptyState } from '../components/ui/EmptyState';
import { useToast } from '../components/ui/Toast';
import { formatBytes, formatDate } from '../utils/formatters';

export const FilesPage = ({ onUploadClick, searchQuery }) => {
  const { toast } = useToast();

  const [currentFolderId, setCurrentFolderId] = useState(null);
  const [breadcrumbs, setBreadcrumbs] = useState([]);
  const [folders, setFolders] = useState([]);
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState('list'); // 'list' | 'grid'

  // Modal states
  const [createFolderModal, setCreateFolderModal] = useState(false);
  const [newFolderName, setNewFolderName] = useState('');
  const [renameModal, setRenameModal] = useState(false);
  const [targetItem, setTargetItem] = useState(null);
  const [renameValue, setRenameValue] = useState('');
  const [moveModal, setMoveModal] = useState(false);
  const [allUserFolders, setAllUserFolders] = useState([]);
  const [selectedDestinationFolder, setSelectedDestinationFolder] = useState(null);

  // Fetch current folder contents
  const loadFolderContents = async (folderId = currentFolderId) => {
    setLoading(true);
    try {
      if (folderId) {
        const res = await api.get(`/api/folders/${folderId}/contents`);
        if (res.data.success) {
          const { breadcrumbs: bc, folders: flds, files: fls } = res.data.data;
          setBreadcrumbs(bc || []);
          setFolders(flds || []);
          setFiles(fls || []);
        }
      } else {
        // Root folder
        const [foldersRes, filesRes] = await Promise.all([
          api.get('/api/folders'),
          api.get(`/api/files${searchQuery ? `?q=${encodeURIComponent(searchQuery)}` : ''}`)
        ]);

        if (foldersRes.data.success) {
          setFolders(foldersRes.data.data.folders || []);
          setBreadcrumbs([]);
        }
        if (filesRes.data.success) {
          setFiles(filesRes.data.data.files || []);
        }
      }
    } catch (err) {
      toast.error('Failed to load files and folders.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFolderContents(currentFolderId);
  }, [currentFolderId, searchQuery]);

  // Folder Actions
  const handleCreateFolder = async (e) => {
    e.preventDefault();
    if (!newFolderName.trim()) return;
    try {
      await api.post('/api/folders', {
        name: newFolderName.trim(),
        parent_folder_id: currentFolderId
      });
      toast.success(`Folder "${newFolderName}" created!`);
      setNewFolderName('');
      setCreateFolderModal(false);
      loadFolderContents();
    } catch (err) {
      toast.error(err.response?.data?.error?.message || 'Could not create folder');
    }
  };

  // Download action with fallback to signed download tokens
  const handleDownload = async (file) => {
    try {
      // First try direct authenticated blob stream
      const res = await api.get(`/api/files/${file.id}/download`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', file.original_name);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success(`Downloaded ${file.original_name}`);
    } catch (err) {
      // Fallback: request signed token
      try {
        const tokenRes = await api.post(`/api/files/${file.id}/download-token`);
        const token = tokenRes.data.data.downloadToken;
        window.location.href = `/api/files/${file.id}/download?token=${token}`;
      } catch {
        toast.error('Failed to download file from storage.');
      }
    }
  };

  // Toggle star
  const handleToggleStar = async (file) => {
    const isCurrentlyStarred = file.is_starred === 1;
    try {
      if (isCurrentlyStarred) {
        await api.delete(`/api/files/${file.id}/star`);
      } else {
        await api.post(`/api/files/${file.id}/star`);
      }
      setFiles((prev) =>
        prev.map((f) => (f.id === file.id ? { ...f, is_starred: isCurrentlyStarred ? 0 : 1 } : f))
      );
      toast.info(isCurrentlyStarred ? 'Removed from starred' : 'Added to starred');
    } catch {
      toast.error('Failed to update star');
    }
  };

  // Soft delete file or folder
  const handleDeleteItem = async (item, isFolder = false) => {
    try {
      if (isFolder) {
        await api.delete(`/api/folders/${item.id}`);
        toast.success(`Folder "${item.folder_name}" moved to Trash`);
      } else {
        await api.delete(`/api/files/${item.id}`);
        toast.success(`File "${item.original_name}" moved to Trash`);
      }
      loadFolderContents();
    } catch {
      toast.error('Failed to move item to trash');
    }
  };

  // Rename submit
  const handleRenameSubmit = async (e) => {
    e.preventDefault();
    if (!targetItem || !renameValue.trim()) return;
    try {
      if (targetItem.isFolder) {
        await api.patch(`/api/folders/${targetItem.id}`, { name: renameValue.trim() });
        toast.success('Folder renamed');
      } else {
        await api.patch(`/api/files/${targetItem.id}`, { name: renameValue.trim() });
        toast.success('File renamed');
      }
      setRenameModal(false);
      loadFolderContents();
    } catch (err) {
      toast.error(err.response?.data?.error?.message || 'Rename failed');
    }
  };

  // Move submit
  const openMoveModal = async (file) => {
    setTargetItem(file);
    try {
      const res = await api.get('/api/folders');
      setAllUserFolders(res.data.data.folders || []);
      setSelectedDestinationFolder(null);
      setMoveModal(true);
    } catch {
      toast.error('Could not load destination folders');
    }
  };

  const handleMoveSubmit = async () => {
    if (!targetItem) return;
    try {
      await api.patch(`/api/files/${targetItem.id}`, { folder_id: selectedDestinationFolder });
      toast.success(`Moved "${targetItem.original_name}" successfully`);
      setMoveModal(false);
      loadFolderContents();
    } catch {
      toast.error('Failed to move file');
    }
  };

  return (
    <div className="space-y-5">
      {/* Action Bar & Breadcrumbs */}
      <GlassCard variant="default" className="p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Breadcrumb Navigation */}
        <div className="flex items-center gap-1.5 text-xs font-medium overflow-x-auto py-1">
          <button
            onClick={() => setCurrentFolderId(null)}
            className={`px-2 py-1 rounded-lg hover:bg-white/40 dark:hover:bg-slate-800/40 ${
              currentFolderId === null ? 'font-bold text-indigo-600 dark:text-indigo-400' : 'text-slate-600 dark:text-slate-300'
            }`}
          >
            My Files
          </button>
          {breadcrumbs.map((bc) => (
            <React.Fragment key={bc.id}>
              <ChevronRight className="w-3.5 h-3.5 text-slate-400 shrink-0" />
              <button
                onClick={() => setCurrentFolderId(bc.id)}
                className={`px-2 py-1 rounded-lg hover:bg-white/40 dark:hover:bg-slate-800/40 truncate max-w-[120px] ${
                  currentFolderId === bc.id ? 'font-bold text-indigo-600 dark:text-indigo-400' : 'text-slate-600 dark:text-slate-300'
                }`}
              >
                {bc.name}
              </button>
            </React.Fragment>
          ))}
        </div>

        {/* Buttons & View Toggle */}
        <div className="flex items-center gap-2 self-end md:self-auto shrink-0">
          <Button
            variant="secondary"
            size="sm"
            icon={FolderPlus}
            onClick={() => setCreateFolderModal(true)}
          >
            New Folder
          </Button>

          <Button
            variant="primary"
            size="sm"
            icon={UploadCloud}
            onClick={onUploadClick}
          >
            Upload
          </Button>

          <div className="h-6 w-[1px] bg-white/20 dark:border-white/10 mx-1"></div>

          <div className="flex rounded-xl glass-subtle p-0.5">
            <button
              onClick={() => setViewMode('list')}
              className={`p-1.5 rounded-lg ${viewMode === 'list' ? 'bg-white/80 dark:bg-slate-800 text-indigo-600' : 'text-slate-400'}`}
              title="List view"
            >
              <List className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('grid')}
              className={`p-1.5 rounded-lg ${viewMode === 'grid' ? 'bg-white/80 dark:bg-slate-800 text-indigo-600' : 'text-slate-400'}`}
              title="Grid view"
            >
              <LayoutGrid className="w-4 h-4" />
            </button>
          </div>
        </div>
      </GlassCard>

      {/* Main Content Area */}
      {loading ? (
        <div className="space-y-3 animate-pulse">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-12 rounded-xl bg-white/30 dark:bg-slate-900/30"></div>
          ))}
        </div>
      ) : folders.length === 0 && files.length === 0 ? (
        <EmptyState
          icon={Folder}
          title="This folder is empty"
          description="Upload files or create subfolders to organize your laboratory data."
          actionLabel="Upload Files"
          onAction={onUploadClick}
        />
      ) : viewMode === 'list' ? (
        /* LIST VIEW */
        <GlassCard variant="default" className="overflow-hidden">
          <div className="overflow-x-auto">
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
                {/* Folders */}
                {folders.map((folder) => (
                  <tr
                    key={`folder-${folder.id}`}
                    onDoubleClick={() => setCurrentFolderId(folder.id)}
                    className="hover:bg-white/30 dark:hover:bg-slate-800/30 transition-colors group cursor-pointer"
                  >
                    <td className="py-3 px-4 flex items-center gap-3 font-medium text-slate-800 dark:text-slate-100">
                      <Folder className="w-5 h-5 text-amber-500 fill-amber-500/20" />
                      <span className="truncate">{folder.folder_name}</span>
                    </td>
                    <td className="py-3 px-4 text-slate-400 hidden sm:table-cell">—</td>
                    <td className="py-3 px-4 text-slate-400 hidden md:table-cell">{formatDate(folder.created_at)}</td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end gap-1 opacity-80 group-hover:opacity-100">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setTargetItem({ ...folder, isFolder: true });
                            setRenameValue(folder.folder_name);
                            setRenameModal(true);
                          }}
                          className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                          title="Rename folder"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteItem(folder, true);
                          }}
                          className="p-1 rounded-lg text-slate-400 hover:text-rose-500"
                          title="Move to Trash"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}

                {/* Files */}
                {files.map((file) => (
                  <tr
                    key={`file-${file.id}`}
                    className="hover:bg-white/30 dark:hover:bg-slate-800/30 transition-colors group"
                  >
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
                      <div className="flex items-center justify-end gap-1 opacity-80 group-hover:opacity-100">
                        <button
                          onClick={() => handleToggleStar(file)}
                          className={`p-1 rounded-lg ${file.is_starred ? 'text-yellow-500' : 'text-slate-400 hover:text-yellow-500'}`}
                          title="Star file"
                        >
                          <Star className="w-3.5 h-3.5" fill={file.is_starred ? 'currentColor' : 'none'} />
                        </button>
                        <button
                          onClick={() => handleDownload(file)}
                          className="p-1 rounded-lg text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400"
                          title="Download"
                        >
                          <Download className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => openMoveModal(file)}
                          className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                          title="Move to folder"
                        >
                          <FolderInput className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => {
                            setTargetItem({ ...file, isFolder: false });
                            setRenameValue(file.original_name);
                            setRenameModal(true);
                          }}
                          className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                          title="Rename"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => handleDeleteItem(file, false)}
                          className="p-1 rounded-lg text-slate-400 hover:text-rose-500"
                          title="Delete to Trash"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </GlassCard>
      ) : (
        /* GRID VIEW */
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
          {/* Folders */}
          {folders.map((folder) => (
            <GlassCard
              key={`grid-folder-${folder.id}`}
              variant="default"
              hover
              onClick={() => setCurrentFolderId(folder.id)}
              className="p-4 cursor-pointer flex flex-col justify-between h-36"
            >
              <div className="flex items-start justify-between">
                <Folder className="w-8 h-8 text-amber-500 fill-amber-500/20" />
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDeleteItem(folder, true);
                  }}
                  className="text-slate-400 hover:text-rose-500"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
              <div>
                <p className="text-xs font-semibold text-slate-800 dark:text-slate-100 truncate">
                  {folder.folder_name}
                </p>
                <p className="text-[10px] text-slate-400">Folder</p>
              </div>
            </GlassCard>
          ))}

          {/* Files */}
          {files.map((file) => (
            <GlassCard
              key={`grid-file-${file.id}`}
              variant="default"
              hover
              className="p-4 flex flex-col justify-between h-36 group"
            >
              <div className="flex items-start justify-between">
                <FileIcon category={file.category} extension={file.extension} className="w-8 h-8" />
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => handleToggleStar(file)}
                    className={`${file.is_starred ? 'text-yellow-500' : 'text-slate-400'}`}
                  >
                    <Star className="w-3.5 h-3.5" fill={file.is_starred ? 'currentColor' : 'none'} />
                  </button>
                  <button
                    onClick={() => handleDownload(file)}
                    className="text-slate-400 hover:text-indigo-600"
                  >
                    <Download className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
              <div>
                <p className="text-xs font-semibold text-slate-800 dark:text-slate-100 truncate" title={file.original_name}>
                  {file.original_name}
                </p>
                <p className="text-[10px] text-slate-400 mt-0.5">
                  {formatBytes(file.file_size)}
                </p>
              </div>
            </GlassCard>
          ))}
        </div>
      )}

      {/* Modal 1: Create Folder */}
      <Modal
        isOpen={createFolderModal}
        onClose={() => setCreateFolderModal(false)}
        title="Create New Folder"
      >
        <form onSubmit={handleCreateFolder} className="space-y-4">
          <Input
            id="folder-name-input"
            label="Folder Name"
            placeholder="e.g. Lab Assignments"
            value={newFolderName}
            onChange={(e) => setNewFolderName(e.target.value)}
            required
            autoFocus
          />
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setCreateFolderModal(false)}>Cancel</Button>
            <Button variant="primary" type="submit">Create Folder</Button>
          </div>
        </form>
      </Modal>

      {/* Modal 2: Rename Item */}
      <Modal
        isOpen={renameModal}
        onClose={() => setRenameModal(false)}
        title={`Rename ${targetItem?.isFolder ? 'Folder' : 'File'}`}
      >
        <form onSubmit={handleRenameSubmit} className="space-y-4">
          <Input
            id="rename-input"
            label="New Name"
            value={renameValue}
            onChange={(e) => setRenameValue(e.target.value)}
            required
            autoFocus
          />
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setRenameModal(false)}>Cancel</Button>
            <Button variant="primary" type="submit">Save Name</Button>
          </div>
        </form>
      </Modal>

      {/* Modal 3: Move File to Folder */}
      <Modal
        isOpen={moveModal}
        onClose={() => setMoveModal(false)}
        title={`Move "${targetItem?.original_name}"`}
      >
        <div className="space-y-4">
          <p className="text-xs text-slate-500">Select a destination folder:</p>
          <div className="max-h-48 overflow-y-auto space-y-1 pr-1">
            <button
              onClick={() => setSelectedDestinationFolder(null)}
              className={`w-full flex items-center justify-between p-2 rounded-xl text-xs font-medium text-left ${
                selectedDestinationFolder === null ? 'bg-indigo-500/20 text-indigo-600 font-bold' : 'glass-subtle'
              }`}
            >
              <span>Root Folder (My Files)</span>
              {selectedDestinationFolder === null && <Check className="w-4 h-4" />}
            </button>
            {allUserFolders.map((fld) => (
              <button
                key={fld.id}
                onClick={() => setSelectedDestinationFolder(fld.id)}
                className={`w-full flex items-center justify-between p-2 rounded-xl text-xs font-medium text-left ${
                  selectedDestinationFolder === fld.id ? 'bg-indigo-500/20 text-indigo-600 font-bold' : 'glass-subtle'
                }`}
              >
                <span>{fld.folder_name}</span>
                {selectedDestinationFolder === fld.id && <Check className="w-4 h-4" />}
              </button>
            ))}
          </div>
          <div className="flex justify-end gap-2 pt-2 border-t border-white/20 dark:border-white/10">
            <Button variant="ghost" onClick={() => setMoveModal(false)}>Cancel</Button>
            <Button variant="primary" onClick={handleMoveSubmit}>Move File</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
