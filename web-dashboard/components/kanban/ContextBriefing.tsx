'use client';

/**
 * ContextBriefing - Context auto-load briefing modal (Q4 Decision)
 *
 * Features:
 * - Double-click auto-loads context metadata
 * - Shows context summary (file count, size, load stats)
 * - Link to full context view
 *
 * NOTE: This is a placeholder version created during recovery.
 * Full implementation will be restored in Phase 4.
 */

import React from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { FileText, Download } from 'lucide-react';

interface ContextBriefingProps {
  taskId: string;
  taskTitle: string;
  isOpen: boolean;
  onClose: () => void;
}

export function ContextBriefing({
  taskId,
  taskTitle,
  isOpen,
  onClose,
}: ContextBriefingProps) {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Context Briefing
          </DialogTitle>
          <DialogDescription>
            Quick context summary for: {taskTitle}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="text-sm text-muted-foreground">
            <p className="mb-2">
              Double-click auto-load feature (Q4 Decision)
            </p>
            <p className="p-3 bg-muted rounded-md">
              Context briefing functionality will be restored in Phase 4.
              This placeholder ensures build stability.
            </p>
          </div>

          <div className="flex gap-2">
            <Button
              variant="outline"
              className="flex-1"
              onClick={onClose}
            >
              Close
            </Button>
            <Button
              variant="default"
              className="flex-1"
              disabled
            >
              <Download className="h-4 w-4 mr-2" />
              Download Context (Soon)
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
