'use client';

import React from 'react';

interface DependencyGraphProps {
  taskId?: string;
  depth?: number;
  onNodeClick?: (nodeId: string) => void;
  height?: number;
  width?: number;
}

// Placeholder DependencyGraph component
// Will be properly implemented in Phase 4
export function DependencyGraph({
  taskId,
  depth = 3,
  onNodeClick,
  height,
  width,
}: DependencyGraphProps) {
  return (
    <div className="p-4 border rounded-lg" style={{ height, width }}>
      <p className="text-sm text-muted-foreground">
        Dependency Graph (Placeholder - Will be restored in Phase 4)
      </p>
      <p className="text-xs text-muted-foreground mt-2">
        Task ID: {taskId || 'None'} | Depth: {depth}
      </p>
    </div>
  );
}

export default DependencyGraph;
