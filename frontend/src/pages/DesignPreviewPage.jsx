import React, { useState } from 'react';
import {
  Sparkles,
  UploadCloud,
  CheckCircle2,
  AlertTriangle,
  FolderPlus,
  Trash2,
  HardDrive,
  Eye
} from 'lucide-react';
import { GlassCard } from '../components/ui/GlassCard';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Modal } from '../components/ui/Modal';
import { Badge } from '../components/ui/Badge';
import { ProgressBar } from '../components/ui/ProgressBar';
import { Skeleton } from '../components/ui/Skeleton';
import { EmptyState } from '../components/ui/EmptyState';
import { useToast } from '../components/ui/Toast';

export const DesignPreviewPage = () => {
  const { toast } = useToast();
  const [modalOpen, setModalOpen] = useState(false);
  const [testInput, setTestInput] = useState('');

  return (
    <div className="space-y-8 max-w-6xl mx-auto pb-12">
      {/* Header */}
      <GlassCard variant="default" className="p-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 text-white flex items-center justify-center">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-800 dark:text-slate-100">
              MiniCloud Design System Preview
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Interactive review showroom for glassmorphism tokens, depth layers, typography, and UI components.
            </p>
          </div>
        </div>
      </GlassCard>

      {/* 1. Glass Depth Tokens */}
      <section className="space-y-3">
        <h3 className="text-sm font-bold uppercase tracking-wider text-slate-600 dark:text-slate-300">
          1. Glass Depth Layers
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <GlassCard variant="subtle" className="p-5">
            <span className="text-xs font-bold text-indigo-600 dark:text-indigo-400">glass-subtle</span>
            <p className="text-xs text-slate-600 dark:text-slate-300 mt-2">
              Low opacity (40%), used for table rows, search fields, chips, and nested containers.
            </p>
          </GlassCard>

          <GlassCard variant="default" className="p-5" hover>
            <span className="text-xs font-bold text-indigo-600 dark:text-indigo-400">glass (default)</span>
            <p className="text-xs text-slate-600 dark:text-slate-300 mt-2">
              Medium opacity (60%), 20px blur, shadow-glass. Used for main dashboard cards, sidebar, and topbar. (Hover me)
            </p>
          </GlassCard>

          <GlassCard variant="strong" className="p-5">
            <span className="text-xs font-bold text-indigo-600 dark:text-indigo-400">glass-strong</span>
            <p className="text-xs text-slate-600 dark:text-slate-300 mt-2">
              High opacity (80%), 24px blur, shadow-glass-hover. Used for modals, dropdowns, and toast notices.
            </p>
          </GlassCard>
        </div>
      </section>

      {/* 2. Buttons */}
      <section className="space-y-3">
        <h3 className="text-sm font-bold uppercase tracking-wider text-slate-600 dark:text-slate-300">
          2. Buttons & Actions
        </h3>
        <GlassCard variant="default" className="p-5 flex flex-wrap gap-3 items-center">
          <Button variant="primary" icon={UploadCloud}>Primary Gradient</Button>
          <Button variant="secondary" icon={FolderPlus}>Secondary Glass</Button>
          <Button variant="ghost">Ghost Button</Button>
          <Button variant="danger" icon={Trash2}>Danger Action</Button>
          <Button variant="primary" loading>Loading State</Button>
          <Button variant="secondary" disabled>Disabled State</Button>
        </GlassCard>
      </section>

      {/* 3. Inputs & Form Controls */}
      <section className="space-y-3">
        <h3 className="text-sm font-bold uppercase tracking-wider text-slate-600 dark:text-slate-300">
          3. Inputs & Form Controls
        </h3>
        <GlassCard variant="default" className="p-5 grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input
            id="demo-text"
            label="Standard Input"
            placeholder="Type something here..."
            value={testInput}
            onChange={(e) => setTestInput(e.target.value)}
          />
          <Input
            id="demo-error"
            label="Error Validation State"
            placeholder="Invalid field..."
            value="bad_input_example"
            error="This filename already exists in the destination folder."
            readOnly
          />
        </GlassCard>
      </section>

      {/* 4. Badges & Progress Indicators */}
      <section className="space-y-3">
        <h3 className="text-sm font-bold uppercase tracking-wider text-slate-600 dark:text-slate-300">
          4. Badges & Storage Progress
        </h3>
        <GlassCard variant="default" className="p-5 space-y-4">
          <div className="flex flex-wrap gap-2">
            <Badge variant="success">HDFS ACTIVE</Badge>
            <Badge variant="warning">MOCK MODE</Badge>
            <Badge variant="danger">STORAGE FULL</Badge>
            <Badge variant="info">REPLICATION 2</Badge>
            <Badge variant="default">DEFAULT BADGE</Badge>
          </div>

          <div className="space-y-3 pt-2">
            <ProgressBar label="Storage Quota (35% Used)" valueText="350 MB / 1024 MB" percentage={35} />
            <ProgressBar label="Storage Quota (82% - Warning)" valueText="820 MB / 1024 MB" percentage={82} />
            <ProgressBar label="Storage Quota (95% - Danger Alert)" valueText="970 MB / 1024 MB" percentage={95} />
          </div>
        </GlassCard>
      </section>

      {/* 5. Toasts & Modal Dialog Interactive Triggers */}
      <section className="space-y-3">
        <h3 className="text-sm font-bold uppercase tracking-wider text-slate-600 dark:text-slate-300">
          5. Toast Notifications & Modal Dialog
        </h3>
        <GlassCard variant="default" className="p-5 flex flex-wrap gap-3 items-center">
          <Button
            variant="secondary"
            onClick={() => toast.success('File "project_report.pdf" uploaded to HDFS successfully!')}
          >
            Trigger Success Toast
          </Button>
          <Button
            variant="secondary"
            onClick={() => toast.error('HDFS NameNode connection timed out on port 9870.')}
          >
            Trigger Error Toast
          </Button>
          <Button
            variant="secondary"
            onClick={() => toast.info('Storage reconciliation complete: 0 orphans found.')}
          >
            Trigger Info Toast
          </Button>
          <Button
            variant="primary"
            icon={Eye}
            onClick={() => setModalOpen(true)}
          >
            Open Glass Modal Dialog
          </Button>
        </GlassCard>
      </section>

      {/* 6. Empty States & Skeletons */}
      <section className="space-y-3">
        <h3 className="text-sm font-bold uppercase tracking-wider text-slate-600 dark:text-slate-300">
          6. Empty State & Shimmer Skeletons
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <EmptyState
            icon={HardDrive}
            title="No files in this folder"
            description="Drag and drop files here or click the upload button to store files on your laboratory HDFS cluster."
            actionLabel="Upload First File"
            onAction={() => toast.info('Upload triggered')}
          />
          <GlassCard variant="default" className="p-5 space-y-3">
            <p className="text-xs font-semibold text-slate-500">Skeleton Shimmer Preview</p>
            <Skeleton className="h-6 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
            <Skeleton className="h-16 w-full" />
            <div className="flex gap-2 pt-2">
              <Skeleton className="h-8 w-20" />
              <Skeleton className="h-8 w-24" />
            </div>
          </GlassCard>
        </div>
      </section>

      {/* Modal Demonstration */}
      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title="Interactive Glass Modal Dialog"
      >
        <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed mb-4">
          This dialog uses the <code className="text-indigo-600 dark:text-indigo-400 font-bold">glass-strong</code> surface
          layer with an authentic 24px backdrop blur and semi-transparent dim overlay.
        </p>
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={() => setModalOpen(false)}>Cancel</Button>
          <Button variant="primary" onClick={() => { setModalOpen(false); toast.success('Modal action confirmed!'); }}>
            Confirm Action
          </Button>
        </div>
      </Modal>
    </div>
  );
};
