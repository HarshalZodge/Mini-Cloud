import React from 'react';
import {
  FileText,
  Image as ImageIcon,
  Video,
  Music,
  Archive,
  Code2,
  File,
  Folder
} from 'lucide-react';

export const FileIcon = ({ category, extension, isFolder = false, className = 'w-5 h-5' }) => {
  if (isFolder) {
    return <Folder className={`${className} text-amber-500 fill-amber-500/20`} />;
  }

  const ext = (extension || '').toLowerCase();

  if (category === 'image' || ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'].includes(ext)) {
    return <ImageIcon className={`${className} text-violet-500`} />;
  }

  if (ext === '.pdf') {
    return <FileText className={`${className} text-rose-500`} />;
  }

  if (category === 'document' || ['.doc', '.docx', '.txt', '.md', '.xls', '.xlsx'].includes(ext)) {
    return <FileText className={`${className} text-blue-500`} />;
  }

  if (['.mp4', '.mkv', '.avi', '.mov'].includes(ext)) {
    return <Video className={`${className} text-fuchsia-500`} />;
  }

  if (['.mp3', '.wav', '.flac', '.ogg'].includes(ext)) {
    return <Music className={`${className} text-pink-500`} />;
  }

  if (category === 'archive' || ['.zip', '.tar', '.gz', '.7z', '.rar'].includes(ext)) {
    return <Archive className={`${className} text-amber-500`} />;
  }

  if (category === 'code' || ['.py', '.java', '.c', '.cpp', '.js', '.html', '.css', '.json', '.sql'].includes(ext)) {
    return <Code2 className={`${className} text-emerald-500`} />;
  }

  return <File className={`${className} text-slate-500`} />;
};
