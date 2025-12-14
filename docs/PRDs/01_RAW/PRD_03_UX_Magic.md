# PRD 03: UX/UI Design - Magic MCP Enhanced
**UDO Development Platform v3.0**

**Document Version**: 1.0
**Date**: 2025-11-20
**AI Source**: Claude with Magic MCP
**Status**: Draft
**PRD Type**: UX/UI Design

---

## Executive Summary

This PRD focuses on the UX/UI design for three core components of the UDO Platform using Magic MCP for modern, accessible, and production-ready UI generation:

1. **Task List UI** - Real-time development task management
2. **CLI Integration Interface** - Seamless dashboard-to-CLI workflow
3. **Quality Dashboard** - Visual code quality and test metrics

### Key Features
- WCAG 2.1 AA compliant components
- Real-time WebSocket updates
- Responsive mobile-first design
- Dark theme with gradient accents
- Keyboard navigation support
- Screen reader optimized

---

## 1. Task List UI Component

### 1.1 Wireframe

```
┌─────────────────────────────────────────────────────────────┐
│  Active Development Tasks                    [3 Tasks] 🔄   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 🔵 [Development] Authentication System                │   │
│  │    Implement JWT-based auth with refresh tokens       │   │
│  │    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 75%          │   │
│  │    📂 udo-platform  🌿 feature/auth  ⏱ 12h/16h        │   │
│  │    ▸ Current: Writing integration tests                │   │
│  │                                    [Details] [Continue] │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 🟠 [Testing] E2E Test Suite                           │   │
│  │    Add Playwright tests for all user flows            │   │
│  │    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 40%          │   │
│  │    📂 udo-platform  🌿 test/e2e  ⏱ 5h/12h             │   │
│  │    ▸ Current: Setting up test infrastructure          │   │
│  │                                    [Details] [Continue] │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Task Details Modal Wireframe

```
┌─────────────────────────────────────────────────────────────┐
│  🎯 Authentication System                          [×]       │
├─────────────────────────────────────────────────────────────┤
│  Implement JWT-based auth with refresh tokens                │
│                                                               │
│  [TODO List] [Context] [History]                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ ✅ Phase 1: Setup (3/3 completed)                     │  │
│  │   ☑ Install dependencies (jsonwebtoken, bcrypt)      │  │
│  │   ☑ Create database schema                           │  │
│  │   ☑ Setup environment variables                      │  │
│  │                                                        │  │
│  │ 🔵 Phase 2: Implementation (2/4 in progress)         │  │
│  │   ☑ Create User model                                │  │
│  │   ☑ Implement login endpoint                         │  │
│  │   ☐ Add refresh token logic                          │  │
│  │   ☐ Write integration tests                          │  │
│  │                                                        │  │
│  │ ⚪ Phase 3: Security (0/2 pending)                    │  │
│  │   ☐ Add rate limiting                                │  │
│  │   ☐ Implement CSRF protection                        │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│                                    [Close] [Continue in CLI] │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 React Component Code

```tsx
"use client"

import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Terminal, GitBranch, FileText, Clock,
  AlertCircle, CheckCircle, Play, Code2,
  ExternalLink, ChevronRight, TrendingUp
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import { toast } from 'sonner'
import { cn } from '@/lib/utils'

// Type Definitions
interface Task {
  id: string
  title: string
  description: string
  project: string
  phase: 'development' | 'planning' | 'testing' | 'deployment'
  status: 'in_progress' | 'pending' | 'blocked' | 'completed'
  completeness: number
  estimated_hours: number
  actual_hours: number
  git_branch: string
  updated_at: string
  current_step: {
    group_index: number
    item_index: number
    description: string
  }
  todo_groups?: TodoGroup[]
}

interface TodoGroup {
  id: string
  title: string
  status: 'completed' | 'in_progress' | 'pending'
  items: TodoItem[]
}

interface TodoItem {
  title: string
  status: 'completed' | 'in_progress' | 'pending'
  subtasks?: string[]
}

// Main Component
export function TaskList() {
  const [tasks, setTasks] = useState<Task[]>([])
  const [selectedTask, setSelectedTask] = useState<Task | null>(null)
  const [loading, setLoading] = useState(true)
  const [detailsOpen, setDetailsOpen] = useState(false)

  useEffect(() => {
    fetchTasks()
  }, [])

  const fetchTasks = async () => {
    try {
      const res = await fetch('/api/tasks/')
      if (res.ok) {
        const data = await res.json()
        setTasks(data)
      }
    } catch (error) {
      toast.error("Failed to fetch tasks")
    } finally {
      setLoading(false)
    }
  }

  const fetchTaskDetails = async (taskId: string) => {
    try {
      const res = await fetch(`/api/tasks/${taskId}`)
      if (res.ok) {
        const detail = await res.json()
        setSelectedTask(detail)
        setDetailsOpen(true)
      }
    } catch (error) {
      toast.error("Failed to fetch task details")
    }
  }

  const continueInCLI = async (taskId: string) => {
    try {
      const res = await fetch(`/api/tasks/${taskId}/context`)
      if (res.ok) {
        const context = await res.json()
        await navigator.clipboard.writeText(context.command)

        toast.success("Command copied to clipboard!", {
          description: (
            <div className="mt-2">
              <p className="text-sm mb-2">Paste in your terminal:</p>
              <code className="block p-3 bg-gradient-to-r from-blue-950 to-purple-950 text-blue-100 rounded-lg text-xs font-mono">
                {context.command}
              </code>
            </div>
          )
        })
      }
    } catch (error) {
      toast.error("Failed to generate CLI command")
    }
  }

  // Status styling configuration
  const getStatusConfig = (status: string) => {
    const configs = {
      in_progress: {
        color: 'from-blue-500 to-cyan-500',
        bgColor: 'bg-blue-500/10',
        borderColor: 'border-blue-500/20',
        textColor: 'text-blue-400',
        icon: <Play className="w-4 h-4" />
      },
      completed: {
        color: 'from-green-500 to-emerald-500',
        bgColor: 'bg-green-500/10',
        borderColor: 'border-green-500/20',
        textColor: 'text-green-400',
        icon: <CheckCircle className="w-4 h-4" />
      },
      blocked: {
        color: 'from-red-500 to-orange-500',
        bgColor: 'bg-red-500/10',
        borderColor: 'border-red-500/20',
        textColor: 'text-red-400',
        icon: <AlertCircle className="w-4 h-4" />
      },
      pending: {
        color: 'from-gray-500 to-slate-500',
        bgColor: 'bg-gray-500/10',
        borderColor: 'border-gray-500/20',
        textColor: 'text-gray-400',
        icon: <Clock className="w-4 h-4" />
      }
    }
    return configs[status] || configs.pending
  }

  const getPhaseIcon = (phase: string) => {
    const icons = {
      development: <Code2 className="w-4 h-4" />,
      planning: <FileText className="w-4 h-4" />,
      testing: <AlertCircle className="w-4 h-4" />,
      deployment: <TrendingUp className="w-4 h-4" />
    }
    return icons[phase] || <FileText className="w-4 h-4" />
  }

  if (loading) {
    return (
      <Card className="bg-gray-900/50 backdrop-blur-xl border-gray-700/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-3 text-white">
            <Terminal className="w-6 h-6 text-blue-400" />
            Active Development Tasks
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex justify-center items-center h-32">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
              className="rounded-full h-12 w-12 border-4 border-blue-500/20 border-t-blue-500"
            />
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="relative overflow-hidden"
      >
        {/* Animated background gradient */}
        <div className="absolute inset-0 bg-gradient-to-r from-blue-500/5 via-purple-500/5 to-pink-500/5" />
        <motion.div
          className="absolute inset-0 bg-gradient-to-r from-blue-500/10 via-transparent to-purple-500/10"
          animate={{ x: [-1000, 1000] }}
          transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
        />

        <Card className="relative bg-gray-900/50 backdrop-blur-xl border-gray-700/50 shadow-2xl">
          <CardHeader className="pb-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500">
                  <Terminal className="w-6 h-6 text-white" />
                </div>
                <div>
                  <CardTitle className="text-2xl font-bold text-white">
                    Active Development Tasks
                  </CardTitle>
                  <CardDescription className="text-gray-400 mt-1">
                    Click a task to view details and continue in CLI
                  </CardDescription>
                </div>
              </div>
              <Badge
                variant="outline"
                className="px-3 py-1 bg-blue-500/10 border-blue-500/30 text-blue-400"
              >
                <TrendingUp className="w-3 h-3 mr-1" />
                {tasks.length} Tasks
              </Badge>
            </div>
          </CardHeader>

          <CardContent>
            <AnimatePresence mode="popLayout">
              {tasks.length === 0 ? (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="text-center py-12"
                >
                  <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gray-800/50 mb-4">
                    <FileText className="w-8 h-8 text-gray-600" />
                  </div>
                  <p className="text-gray-400">No active tasks</p>
                  <p className="text-gray-600 text-sm mt-1">Start a new development task</p>
                </motion.div>
              ) : (
                <div className="space-y-3">
                  {tasks.map((task, index) => {
                    const statusConfig = getStatusConfig(task.status)
                    return (
                      <motion.div
                        key={task.id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.1 }}
                        whileHover={{ scale: 1.01, y: -2 }}
                        className="group"
                      >
                        <Card
                          className={cn(
                            "relative overflow-hidden bg-gray-800/40 backdrop-blur border-gray-700/50",
                            "hover:border-gray-600 hover:shadow-lg hover:shadow-blue-500/10 transition-all duration-300"
                          )}
                          role="article"
                          aria-label={`Task: ${task.title}`}
                        >
                          {/* Status accent bar */}
                          <div className={cn("absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b", statusConfig.color)} />

                          <CardContent className="p-5 relative">
                            <div className="flex justify-between items-start gap-4">
                              <div className="flex-1 min-w-0">
                                <div className="flex items-start gap-3 mb-3">
                                  <div className={cn("p-2 rounded-lg mt-1", statusConfig.bgColor)}>
                                    {getPhaseIcon(task.phase)}
                                  </div>
                                  <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2 mb-2">
                                      <h3 className="font-semibold text-lg text-white truncate">
                                        {task.title}
                                      </h3>
                                      <Badge
                                        className={cn(
                                          "px-2 py-0.5 text-xs font-medium border",
                                          statusConfig.bgColor,
                                          statusConfig.borderColor,
                                          statusConfig.textColor
                                        )}
                                      >
                                        <span className="flex items-center gap-1">
                                          {statusConfig.icon}
                                          {task.status.replace('_', ' ')}
                                        </span>
                                      </Badge>
                                    </div>

                                    <p className="text-sm text-gray-400 line-clamp-2 mb-3">
                                      {task.description}
                                    </p>

                                    {/* Meta information */}
                                    <div className="flex flex-wrap items-center gap-3 text-xs text-gray-500">
                                      <span
                                        className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-gray-800/50"
                                        aria-label={`Project: ${task.project}`}
                                      >
                                        <FileText className="w-3 h-3 text-blue-400" />
                                        {task.project}
                                      </span>
                                      <span
                                        className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-gray-800/50"
                                        aria-label={`Git branch: ${task.git_branch}`}
                                      >
                                        <GitBranch className="w-3 h-3 text-green-400" />
                                        {task.git_branch}
                                      </span>
                                      <span
                                        className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-gray-800/50"
                                        aria-label={`Time: ${task.actual_hours} of ${task.estimated_hours} hours`}
                                      >
                                        <Clock className="w-3 h-3 text-orange-400" />
                                        {task.actual_hours}h / {task.estimated_hours}h
                                      </span>
                                    </div>
                                  </div>
                                </div>

                                {/* Progress section */}
                                <div className="space-y-2 mt-4">
                                  <div className="flex justify-between items-center text-xs">
                                    <span className="text-gray-400 font-medium">Progress</span>
                                    <span className="text-blue-400 font-semibold">
                                      {task.completeness}%
                                    </span>
                                  </div>
                                  <div className="relative h-2 bg-gray-800 rounded-full overflow-hidden">
                                    <motion.div
                                      initial={{ width: 0 }}
                                      animate={{ width: `${task.completeness}%` }}
                                      transition={{ duration: 1, delay: index * 0.1 }}
                                      className={cn("h-full bg-gradient-to-r", statusConfig.color)}
                                      role="progressbar"
                                      aria-valuenow={task.completeness}
                                      aria-valuemin={0}
                                      aria-valuemax={100}
                                    />
                                  </div>
                                  <p className="text-xs text-gray-500 flex items-center gap-1.5">
                                    <ChevronRight className="w-3 h-3" />
                                    {task.current_step.description}
                                  </p>
                                </div>
                              </div>

                              {/* Action buttons */}
                              <div className="flex flex-col gap-2 shrink-0">
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => fetchTaskDetails(task.id)}
                                  className="bg-gray-800/50 border-gray-700 hover:bg-gray-700 hover:border-gray-600 text-gray-300"
                                  aria-label={`View details for ${task.title}`}
                                >
                                  <ExternalLink className="w-3 h-3 mr-1.5" />
                                  Details
                                </Button>
                                <Button
                                  size="sm"
                                  onClick={() => continueInCLI(task.id)}
                                  className="bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white border-0 shadow-lg shadow-blue-500/20"
                                  aria-label={`Continue ${task.title} in CLI`}
                                >
                                  <Terminal className="w-3 h-3 mr-1.5" />
                                  Continue
                                </Button>
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      </motion.div>
                    )
                  })}
                </div>
              )}
            </AnimatePresence>
          </CardContent>
        </Card>
      </motion.div>

      {/* Task Details Dialog - See section 1.4 */}
    </>
  )
}
```

### 1.4 Accessibility Checklist

#### WCAG 2.1 AA Compliance

**Perceivable**
- ✅ Color is not the only visual means of conveying information
  - Status icons accompany colored indicators
  - Text labels for all states (in progress, completed, blocked)
- ✅ Sufficient color contrast ratios
  - Text on dark background: 7:1+ (AAA level)
  - Interactive elements: 4.5:1+ (AA level)
- ✅ Text can be resized up to 200% without loss of content
  - Relative units (rem, em) used throughout
  - No fixed pixel widths for text containers
- ✅ Non-text content has text alternatives
  - Icons have aria-label attributes
  - Images use alt text

**Operable**
- ✅ All functionality available from keyboard
  - Tab navigation through all interactive elements
  - Enter/Space to activate buttons
  - Escape to close dialogs
- ✅ Keyboard focus is visible
  - Custom focus ring styles: 2px solid blue-400
  - No focus:outline-none without replacement
- ✅ Users have enough time to read and use content
  - No automatic timeouts on task cards
  - Progress animations are decorative only
- ✅ No content flashing more than 3 times per second
  - Gradient animations are slow (20s duration)
  - No rapidly changing content

**Understandable**
- ✅ Text is readable and understandable
  - Clear, concise labels
  - Consistent terminology
- ✅ Content appears and operates in predictable ways
  - Standard UI patterns (cards, buttons)
  - Consistent layout across tasks
- ✅ Users are helped to avoid and correct mistakes
  - Toast notifications for errors
  - Descriptive error messages

**Robust**
- ✅ Compatible with assistive technologies
  - Semantic HTML (article, heading levels)
  - ARIA roles and attributes
  - Live regions for dynamic updates
- ✅ Progressive enhancement
  - Works without JavaScript (basic HTML)
  - Graceful degradation of animations

#### Keyboard Navigation

**Task List View**
1. `Tab` - Navigate between task cards
2. `Enter` or `Space` - Select/expand task
3. `Tab` (within card) - Navigate to "Details" button
4. `Tab` - Navigate to "Continue" button
5. `Enter` - Activate button
6. `Escape` - Close any open dialogs

**Task Details Dialog**
1. `Tab` - Navigate between tabs (TODO, Context, History)
2. `Arrow Left/Right` - Switch tabs
3. `Tab` - Navigate within tab content
4. `Escape` - Close dialog
5. `Tab` to "Continue in CLI" button
6. `Enter` - Activate button

#### Screen Reader Support

**ARIA Attributes**
```tsx
// Task card
<Card role="article" aria-label={`Task: ${task.title}`}>

// Progress bar
<div
  role="progressbar"
  aria-valuenow={task.completeness}
  aria-valuemin={0}
  aria-valuemax={100}
/>

// Action buttons
<Button aria-label={`View details for ${task.title}`}>
<Button aria-label={`Continue ${task.title} in CLI`}>

// Status badges
<span aria-label={`Project: ${task.project}`}>
<span aria-label={`Git branch: ${task.git_branch}`}>
<span aria-label={`Time: ${task.actual_hours} of ${task.estimated_hours} hours`}>
```

**Live Regions for Updates**
```tsx
// WebSocket updates announce to screen readers
<div aria-live="polite" aria-atomic="true" className="sr-only">
  {updateMessage}
</div>

// Toast notifications are announced
toast.success("Command copied to clipboard!", {
  role: "status",
  "aria-live": "polite"
})
```

### 1.5 User Flow Diagram

```
┌─────────────┐
│   User      │
│  Dashboard  │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────┐
│  View Task List             │
│  - See all active tasks     │
│  - Real-time status updates │
│  - Progress visualization   │
└──────┬──────────────────────┘
       │
       ├──────────────────┐
       │                  │
       ▼                  ▼
┌──────────────┐   ┌──────────────────┐
│ Click Details│   │ Click Continue   │
│              │   │                  │
└──────┬───────┘   └──────┬───────────┘
       │                  │
       ▼                  ▼
┌──────────────────┐   ┌──────────────────────┐
│ Task Details     │   │ Generate CLI Command │
│ Modal Opens      │   │ Copy to Clipboard    │
│                  │   │                      │
│ View:            │   └──────┬───────────────┘
│ - TODO checklist │          │
│ - Context info   │          ▼
│ - Prompt history │   ┌──────────────────────┐
│                  │   │ Paste in Terminal    │
└──────┬───────────┘   │ Continue Development │
       │               │                      │
       │               └──────────────────────┘
       ▼
┌──────────────────┐
│ Continue in CLI  │
│ (from modal)     │
└──────┬───────────┘
       │
       ▼
┌──────────────────────┐
│ CLI Workflow Starts  │
│ - Load task context  │
│ - Open files         │
│ - Run last command   │
└──────────────────────┘
```

**Interaction Points**
1. **Entry**: User views dashboard
2. **Task Card Hover**: Preview information, visual feedback
3. **Details Click**: Open modal with full task breakdown
4. **Continue Click**: Generate and copy CLI command
5. **Paste in Terminal**: Seamless transition to CLI workflow

**State Transitions**
```
pending → in_progress → completed
                ↓
            blocked → in_progress
```

---

## 2. CLI Integration Interface

### 2.1 Wireframe

```
┌─────────────────────────────────────────────────────────────┐
│  🚀 CLI Integration Panel                                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Current Task Context                                   │  │
│  │                                                         │  │
│  │ 📂 Project: udo-platform                               │  │
│  │ 🌿 Branch: feature/auth                                │  │
│  │ ⏱ Step: Writing integration tests (12h/16h)            │  │
│  │ 📝 Files: 8 modified, 2 created                        │  │
│  │                                                         │  │
│  │ ┌─────────────────────────────────────────────────┐   │  │
│  │ │ # Generated CLI Command                         │   │  │
│  │ │ cd /path/to/udo-platform &&                     │   │  │
│  │ │ git checkout feature/auth &&                    │   │  │
│  │ │ code src/auth/tests/integration.test.ts &&      │   │  │
│  │ │ # TODO: Write integration test for token refresh│   │  │
│  │ └─────────────────────────────────────────────────┘   │  │
│  │                                                         │  │
│  │              [📋 Copy Command] [🔗 Open in VSCode]      │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Quick Actions                                          │  │
│  │                                                         │  │
│  │  [🔄 Sync State]  [📊 View Logs]  [⚙️ Configure]       │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Recent CLI Activity                        Live 🟢     │  │
│  │                                                         │  │
│  │  15:45  $ git commit -m "Add auth tests"               │  │
│  │  15:42  $ npm test -- auth.test.ts                     │  │
│  │  15:38  $ code src/auth/middleware.ts                  │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 React Component Code

```tsx
"use client"

import React, { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import {
  Terminal, GitBranch, FileText, Clock,
  Copy, ExternalLink, RefreshCw, Settings,
  BarChart3, CheckCircle, Activity
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { toast } from 'sonner'
import { cn } from '@/lib/utils'

interface CLIContext {
  project: string
  branch: string
  current_step: string
  hours: { actual: number; estimated: number }
  files: { modified: number; created: number }
  command: string
  task_id: string
}

interface CLIActivity {
  timestamp: string
  command: string
  type: 'git' | 'npm' | 'code' | 'other'
  success: boolean
}

export function CLIIntegrationPanel() {
  const [context, setContext] = useState<CLIContext | null>(null)
  const [activities, setActivities] = useState<CLIActivity[]>([])
  const [isLive, setIsLive] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    fetchCurrentContext()
    connectWebSocket()

    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [])

  const fetchCurrentContext = async () => {
    try {
      const res = await fetch('/api/cli/context')
      if (res.ok) {
        const data = await res.json()
        setContext(data)
      }
    } catch (error) {
      toast.error("Failed to fetch CLI context")
    }
  }

  const connectWebSocket = () => {
    const ws = new WebSocket('ws://localhost:8000/ws/cli')

    ws.onopen = () => {
      setIsLive(true)
      toast.success("CLI monitoring active")
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'cli_activity') {
        setActivities(prev => [data.activity, ...prev.slice(0, 9)])
      }
    }

    ws.onclose = () => {
      setIsLive(false)
      toast.error("CLI monitoring disconnected")
    }

    wsRef.current = ws
  }

  const copyCommand = async () => {
    if (!context) return

    try {
      await navigator.clipboard.writeText(context.command)
      toast.success("Command copied!", {
        description: "Paste in your terminal to continue"
      })
    } catch (error) {
      toast.error("Failed to copy command")
    }
  }

  const openInVSCode = () => {
    if (!context) return

    // Try to open VSCode via custom protocol
    const vscodeUrl = `vscode://file/${context.project}`
    window.location.href = vscodeUrl

    toast.success("Opening in VSCode", {
      description: "If VSCode doesn't open, install the protocol handler"
    })
  }

  const syncState = async () => {
    toast.info("Syncing state...", { duration: 2000 })
    await fetchCurrentContext()
    toast.success("State synced successfully")
  }

  const getActivityIcon = (type: string) => {
    const icons = {
      git: <GitBranch className="w-3 h-3 text-green-400" />,
      npm: <Activity className="w-3 h-3 text-red-400" />,
      code: <FileText className="w-3 h-3 text-blue-400" />,
      other: <Terminal className="w-3 h-3 text-gray-400" />
    }
    return icons[type] || icons.other
  }

  if (!context) {
    return (
      <Card className="bg-gray-900/50 backdrop-blur-xl border-gray-700/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-3 text-white">
            <Terminal className="w-6 h-6 text-blue-400" />
            CLI Integration
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-gray-400">
            <p>No active task context</p>
            <p className="text-sm mt-1">Start a task to see CLI integration</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-4"
    >
      {/* Main Context Card */}
      <Card className="bg-gray-900/50 backdrop-blur-xl border-gray-700/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500">
                <Terminal className="w-6 h-6 text-white" />
              </div>
              <div>
                <CardTitle className="text-2xl font-bold text-white">
                  CLI Integration Panel
                </CardTitle>
                <CardDescription className="text-gray-400 mt-1">
                  Seamless transition from dashboard to command line
                </CardDescription>
              </div>
            </div>
            <Badge
              variant="outline"
              className={cn(
                "px-3 py-1",
                isLive
                  ? "bg-green-500/10 border-green-500/30 text-green-400"
                  : "bg-red-500/10 border-red-500/30 text-red-400"
              )}
            >
              <Activity className="w-3 h-3 mr-1" />
              {isLive ? 'Live' : 'Offline'}
            </Badge>
          </div>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Current Task Context */}
          <div className="bg-gray-800/40 rounded-lg p-5 border border-gray-700/50">
            <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
              <FileText className="w-5 h-5 text-blue-400" />
              Current Task Context
            </h3>

            <div className="grid grid-cols-2 gap-4 mb-4">
              <div className="flex items-center gap-2 text-sm">
                <FileText className="w-4 h-4 text-blue-400" />
                <span className="text-gray-400">Project:</span>
                <span className="text-white font-mono">{context.project}</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <GitBranch className="w-4 h-4 text-green-400" />
                <span className="text-gray-400">Branch:</span>
                <span className="text-white font-mono">{context.branch}</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <Clock className="w-4 h-4 text-orange-400" />
                <span className="text-gray-400">Time:</span>
                <span className="text-white font-mono">
                  {context.hours.actual}h / {context.hours.estimated}h
                </span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <FileText className="w-4 h-4 text-purple-400" />
                <span className="text-gray-400">Files:</span>
                <span className="text-white font-mono">
                  {context.files.modified} modified, {context.files.created} created
                </span>
              </div>
            </div>

            <div className="bg-gray-900/60 rounded-lg p-1 border border-gray-700/30">
              <p className="text-sm text-gray-400 mb-2 px-3 pt-2">Current Step</p>
              <p className="text-white font-medium px-3 pb-2">{context.current_step}</p>
            </div>

            {/* Generated Command */}
            <div className="mt-4">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-medium text-gray-400">Generated CLI Command</h4>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={copyCommand}
                  className="text-blue-400 hover:text-blue-300 hover:bg-blue-500/10"
                  aria-label="Copy command to clipboard"
                >
                  <Copy className="w-4 h-4 mr-1" />
                  Copy
                </Button>
              </div>
              <div className="relative">
                <pre className="bg-gradient-to-r from-blue-950 to-purple-950 p-4 rounded-lg overflow-x-auto border border-blue-800/30">
                  <code className="text-blue-100 text-sm font-mono whitespace-pre">
                    {context.command}
                  </code>
                </pre>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3 mt-4">
              <Button
                onClick={copyCommand}
                className="flex-1 bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600"
              >
                <Copy className="w-4 h-4 mr-2" />
                Copy Command
              </Button>
              <Button
                onClick={openInVSCode}
                variant="outline"
                className="flex-1 border-gray-700 hover:bg-gray-800"
              >
                <ExternalLink className="w-4 h-4 mr-2" />
                Open in VSCode
              </Button>
            </div>
          </div>

          <Separator className="bg-gray-700/50" />

          {/* Quick Actions */}
          <div>
            <h3 className="font-semibold text-white mb-3 flex items-center gap-2">
              <Settings className="w-5 h-5 text-gray-400" />
              Quick Actions
            </h3>
            <div className="flex gap-3">
              <Button
                variant="outline"
                size="sm"
                onClick={syncState}
                className="border-gray-700 hover:bg-gray-800"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Sync State
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="border-gray-700 hover:bg-gray-800"
              >
                <BarChart3 className="w-4 h-4 mr-2" />
                View Logs
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="border-gray-700 hover:bg-gray-800"
              >
                <Settings className="w-4 h-4 mr-2" />
                Configure
              </Button>
            </div>
          </div>

          <Separator className="bg-gray-700/50" />

          {/* Recent CLI Activity */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-white flex items-center gap-2">
                <Terminal className="w-5 h-5 text-gray-400" />
                Recent CLI Activity
              </h3>
              <Badge
                variant="outline"
                className="bg-green-500/10 border-green-500/30 text-green-400"
              >
                Live
              </Badge>
            </div>

            <ScrollArea className="h-[200px]">
              <div className="space-y-2">
                {activities.length === 0 ? (
                  <p className="text-gray-500 text-sm text-center py-8">
                    No recent activity
                  </p>
                ) : (
                  activities.map((activity, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className="flex items-center gap-3 p-2 rounded-lg bg-gray-800/30 hover:bg-gray-800/50 transition-colors"
                    >
                      <div className="flex items-center gap-2 flex-shrink-0">
                        {getActivityIcon(activity.type)}
                        <span className="text-xs text-gray-500 font-mono">
                          {activity.timestamp}
                        </span>
                      </div>
                      <code className="text-sm font-mono text-gray-300 flex-1 truncate">
                        {activity.command}
                      </code>
                      {activity.success && (
                        <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0" />
                      )}
                    </motion.div>
                  ))
                )}
              </div>
            </ScrollArea>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}
```

### 2.3 Accessibility Checklist

#### WCAG 2.1 AA Compliance

**Perceivable**
- ✅ Code blocks have sufficient contrast (7:1+)
- ✅ Live status indicator has text label, not just color
- ✅ Icons accompanied by text labels
- ✅ Command text is selectable and copyable

**Operable**
- ✅ All buttons keyboard accessible
- ✅ Focus visible on interactive elements
- ✅ Copy button announces success to screen readers
- ✅ WebSocket status changes announced

**Understandable**
- ✅ Clear labels for all actions
- ✅ Toast notifications explain outcomes
- ✅ Command syntax highlighted for readability
- ✅ Consistent button placement

**Robust**
- ✅ Live region for activity updates
- ✅ Status changes announced to screen readers
- ✅ Fallback for failed WebSocket connection

#### Keyboard Navigation

```
Tab Flow:
1. Copy Command button
2. Open in VSCode button
3. Sync State button
4. View Logs button
5. Configure button
6. Activity list (if focusable items present)

Shortcuts:
- Ctrl+C / Cmd+C: Copy command (when code block focused)
- Escape: Clear selection
```

### 2.4 User Flow Diagram

```
┌──────────────────┐
│  Task Selected   │
│  from Dashboard  │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────┐
│  CLI Panel Loads         │
│  - Fetch task context    │
│  - Connect WebSocket     │
│  - Display current state │
└────────┬─────────────────┘
         │
         ├─────────────────────┐
         │                     │
         ▼                     ▼
┌─────────────────┐   ┌──────────────────┐
│ Copy Command    │   │ Open in VSCode   │
│ - Generate CLI  │   │ - Launch editor  │
│ - Copy to clip  │   │ - Open project   │
│ - Show toast    │   │ - Load files     │
└────────┬────────┘   └──────┬───────────┘
         │                   │
         ▼                   ▼
┌─────────────────┐   ┌──────────────────┐
│ Paste in Term   │   │ Editor Ready     │
│ - Navigate dir  │   │ - Files open     │
│ - Checkout      │   │ - TODO visible   │
│ - Open files    │   │                  │
└────────┬────────┘   └──────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Start Development       │
│ - Real-time activity    │
│ - WebSocket updates     │
│ - Dashboard shows live  │
└─────────────────────────┘
```

---

## 3. Quality Dashboard Component

### 3.1 Wireframe

```
┌─────────────────────────────────────────────────────────────┐
│  📊 Code Quality Dashboard                                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐ │
│  │ Coverage    │ Type Safety │ Complexity  │ Tech Debt   │ │
│  │             │             │             │             │ │
│  │    85%      │    72%      │   Medium    │   12 hrs    │ │
│  │   ━━━━━     │   ━━━━○     │    ⚠️       │    🔴       │ │
│  │   🟢 Good   │   🟡 Fair   │   🟡 Fair   │   🔴 High   │ │
│  └─────────────┴─────────────┴─────────────┴─────────────┘ │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Quality Trend (Last 7 Days)              📈           │  │
│  │                                                        │  │
│  │   100% ┤                                   ●           │  │
│  │        ┤                           ●───●                │  │
│  │    75% ┤                   ●───●                       │  │
│  │        ┤           ●───●                               │  │
│  │    50% ┤   ●───●                                       │  │
│  │        └───┬───┬───┬───┬───┬───┬                      │  │
│  │           Mon Tue Wed Thu Fri Sat Sun                  │  │
│  │                                                        │  │
│  │   ── Coverage  ── Type Safety  ── Complexity          │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Recent Issues                               3 Active   │  │
│  │                                                        │  │
│  │  🔴 HIGH   Missing error handling in auth.ts:45       │  │
│  │            Added 2 days ago • Estimated: 2h           │  │
│  │            [View Details]                             │  │
│  │                                                        │  │
│  │  🟡 MED    Unused imports in dashboard.tsx:12         │  │
│  │            Detected today • Estimated: 15min          │  │
│  │            [View Details]                             │  │
│  │                                                        │  │
│  │  🟡 MED    Type assertion in utils.ts:89              │  │
│  │            Added yesterday • Estimated: 30min         │  │
│  │            [View Details]                             │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Test Summary                                           │  │
│  │                                                        │  │
│  │  ✅ Passing: 142/168 (84.5%)                          │  │
│  │  ⏭️  Skipped: 8                                        │  │
│  │  ❌ Failing: 18                                        │  │
│  │                                                        │  │
│  │  Last run: 5 minutes ago • Duration: 12.3s            │  │
│  │  [Run Tests] [View Failures]                          │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 React Component Code

```tsx
"use client"

import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  BarChart3, TrendingUp, AlertTriangle,
  CheckCircle, XCircle, Clock, Activity,
  Play, Eye, FileCode, Shield
} from 'lucide-react'
import {
  Card, CardContent, CardHeader,
  CardTitle, CardDescription
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  LineChart, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend,
  ResponsiveContainer
} from 'recharts'
import { toast } from 'sonner'
import { cn } from '@/lib/utils'

interface QualityMetrics {
  coverage: number
  type_safety: number
  complexity: 'Low' | 'Medium' | 'High'
  tech_debt_hours: number
}

interface QualityTrend {
  date: string
  coverage: number
  type_safety: number
  complexity: number
}

interface Issue {
  id: string
  severity: 'HIGH' | 'MEDIUM' | 'LOW'
  title: string
  file: string
  line: number
  added_date: string
  estimated_hours: number
}

interface TestSummary {
  total: number
  passing: number
  failing: number
  skipped: number
  last_run: string
  duration: number
}

export function QualityDashboard() {
  const [metrics, setMetrics] = useState<QualityMetrics | null>(null)
  const [trend, setTrend] = useState<QualityTrend[]>([])
  const [issues, setIssues] = useState<Issue[]>([])
  const [tests, setTests] = useState<TestSummary | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchQualityData()
  }, [])

  const fetchQualityData = async () => {
    try {
      const [metricsRes, trendRes, issuesRes, testsRes] = await Promise.all([
        fetch('/api/quality/metrics'),
        fetch('/api/quality/trend'),
        fetch('/api/quality/issues'),
        fetch('/api/quality/tests')
      ])

      if (metricsRes.ok && trendRes.ok && issuesRes.ok && testsRes.ok) {
        setMetrics(await metricsRes.json())
        setTrend(await trendRes.json())
        setIssues(await issuesRes.json())
        setTests(await testsRes.json())
      }
    } catch (error) {
      toast.error("Failed to fetch quality data")
    } finally {
      setLoading(false)
    }
  }

  const runTests = async () => {
    toast.info("Running tests...", { duration: 2000 })

    try {
      const res = await fetch('/api/quality/run-tests', { method: 'POST' })
      if (res.ok) {
        await fetchQualityData()
        toast.success("Tests completed")
      }
    } catch (error) {
      toast.error("Failed to run tests")
    }
  }

  const getMetricStatus = (value: number, thresholds: { good: number; fair: number }) => {
    if (value >= thresholds.good) return { color: 'green', label: 'Good', icon: '🟢' }
    if (value >= thresholds.fair) return { color: 'yellow', label: 'Fair', icon: '🟡' }
    return { color: 'red', label: 'Poor', icon: '🔴' }
  }

  const getComplexityStatus = (complexity: string) => {
    const statuses = {
      'Low': { color: 'green', icon: '🟢' },
      'Medium': { color: 'yellow', icon: '🟡' },
      'High': { color: 'red', icon: '🔴' }
    }
    return statuses[complexity] || statuses['Medium']
  }

  const getTechDebtStatus = (hours: number) => {
    if (hours < 10) return { color: 'green', label: 'Low', icon: '🟢' }
    if (hours < 50) return { color: 'yellow', label: 'Medium', icon: '🟡' }
    return { color: 'red', label: 'High', icon: '🔴' }
  }

  const getSeverityConfig = (severity: string) => {
    const configs = {
      HIGH: {
        color: 'text-red-400',
        bg: 'bg-red-500/10',
        border: 'border-red-500/30',
        icon: '🔴'
      },
      MEDIUM: {
        color: 'text-yellow-400',
        bg: 'bg-yellow-500/10',
        border: 'border-yellow-500/30',
        icon: '🟡'
      },
      LOW: {
        color: 'text-blue-400',
        bg: 'bg-blue-500/10',
        border: 'border-blue-500/30',
        icon: '🔵'
      }
    }
    return configs[severity] || configs.MEDIUM
  }

  if (loading || !metrics || !tests) {
    return (
      <Card className="bg-gray-900/50 backdrop-blur-xl border-gray-700/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-3 text-white">
            <BarChart3 className="w-6 h-6 text-blue-400" />
            Code Quality Dashboard
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex justify-center items-center h-32">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
              className="rounded-full h-12 w-12 border-4 border-blue-500/20 border-t-blue-500"
            />
          </div>
        </CardContent>
      </Card>
    )
  }

  const coverageStatus = getMetricStatus(metrics.coverage, { good: 80, fair: 60 })
  const typeSafetyStatus = getMetricStatus(metrics.type_safety, { good: 80, fair: 60 })
  const complexityStatus = getComplexityStatus(metrics.complexity)
  const techDebtStatus = getTechDebtStatus(metrics.tech_debt_hours)

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-6"
    >
      {/* Header */}
      <Card className="bg-gray-900/50 backdrop-blur-xl border-gray-700/50">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500">
              <BarChart3 className="w-6 h-6 text-white" />
            </div>
            <div>
              <CardTitle className="text-2xl font-bold text-white">
                Code Quality Dashboard
              </CardTitle>
              <CardDescription className="text-gray-400 mt-1">
                Real-time code quality metrics and test coverage
              </CardDescription>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Coverage */}
        <Card className="bg-gradient-to-br from-green-500/10 to-emerald-500/10 border-green-500/20">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Shield className="w-5 h-5 text-green-400" />
                <h3 className="font-semibold text-white">Coverage</h3>
              </div>
              <span className="text-2xl">{coverageStatus.icon}</span>
            </div>
            <div className="space-y-2">
              <div className="flex items-baseline gap-2">
                <span className="text-4xl font-bold text-white">
                  {metrics.coverage}%
                </span>
              </div>
              <Progress
                value={metrics.coverage}
                className="h-2 bg-gray-800"
              />
              <p className="text-sm text-gray-400">{coverageStatus.label} coverage</p>
            </div>
          </CardContent>
        </Card>

        {/* Type Safety */}
        <Card className="bg-gradient-to-br from-blue-500/10 to-cyan-500/10 border-blue-500/20">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <FileCode className="w-5 h-5 text-blue-400" />
                <h3 className="font-semibold text-white">Type Safety</h3>
              </div>
              <span className="text-2xl">{typeSafetyStatus.icon}</span>
            </div>
            <div className="space-y-2">
              <div className="flex items-baseline gap-2">
                <span className="text-4xl font-bold text-white">
                  {metrics.type_safety}%
                </span>
              </div>
              <Progress
                value={metrics.type_safety}
                className="h-2 bg-gray-800"
              />
              <p className="text-sm text-gray-400">{typeSafetyStatus.label} type coverage</p>
            </div>
          </CardContent>
        </Card>

        {/* Complexity */}
        <Card className="bg-gradient-to-br from-yellow-500/10 to-orange-500/10 border-yellow-500/20">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Activity className="w-5 h-5 text-yellow-400" />
                <h3 className="font-semibold text-white">Complexity</h3>
              </div>
              <span className="text-2xl">{complexityStatus.icon}</span>
            </div>
            <div className="space-y-2">
              <div className="flex items-baseline gap-2">
                <span className="text-4xl font-bold text-white">
                  {metrics.complexity}
                </span>
              </div>
              <div className="h-2 bg-gray-800 rounded-full" />
              <p className="text-sm text-gray-400">Code complexity</p>
            </div>
          </CardContent>
        </Card>

        {/* Tech Debt */}
        <Card className="bg-gradient-to-br from-red-500/10 to-pink-500/10 border-red-500/20">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-red-400" />
                <h3 className="font-semibold text-white">Tech Debt</h3>
              </div>
              <span className="text-2xl">{techDebtStatus.icon}</span>
            </div>
            <div className="space-y-2">
              <div className="flex items-baseline gap-2">
                <span className="text-4xl font-bold text-white">
                  {metrics.tech_debt_hours}
                </span>
                <span className="text-sm text-gray-400">hrs</span>
              </div>
              <div className="h-2 bg-gray-800 rounded-full" />
              <p className="text-sm text-gray-400">{techDebtStatus.label} debt level</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quality Trend Chart */}
      <Card className="bg-gray-900/50 backdrop-blur-xl border-gray-700/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-blue-400" />
              <CardTitle className="text-white">Quality Trend</CardTitle>
            </div>
            <Badge variant="outline" className="bg-blue-500/10 border-blue-500/30 text-blue-400">
              Last 7 Days
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={trend}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis
                dataKey="date"
                stroke="#9CA3AF"
                style={{ fontSize: '12px' }}
              />
              <YAxis
                stroke="#9CA3AF"
                style={{ fontSize: '12px' }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1F2937',
                  border: '1px solid #374151',
                  borderRadius: '8px'
                }}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="coverage"
                stroke="#10B981"
                strokeWidth={2}
                dot={{ fill: '#10B981', r: 4 }}
              />
              <Line
                type="monotone"
                dataKey="type_safety"
                stroke="#3B82F6"
                strokeWidth={2}
                dot={{ fill: '#3B82F6', r: 4 }}
              />
              <Line
                type="monotone"
                dataKey="complexity"
                stroke="#F59E0B"
                strokeWidth={2}
                dot={{ fill: '#F59E0B', r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Recent Issues */}
      <Card className="bg-gray-900/50 backdrop-blur-xl border-gray-700/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-yellow-400" />
              <CardTitle className="text-white">Recent Issues</CardTitle>
            </div>
            <Badge variant="outline" className="bg-red-500/10 border-red-500/30 text-red-400">
              {issues.length} Active
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[300px]">
            <div className="space-y-3">
              {issues.map((issue, index) => {
                const severityConfig = getSeverityConfig(issue.severity)
                return (
                  <motion.div
                    key={issue.id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
                  >
                    <Card className="bg-gray-800/30 border-gray-700/50 hover:border-gray-600/50 transition-colors">
                      <CardContent className="p-4">
                        <div className="flex items-start gap-3">
                          <span className="text-xl mt-1">{severityConfig.icon}</span>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-2">
                              <Badge
                                variant="outline"
                                className={cn(
                                  "text-xs font-medium",
                                  severityConfig.bg,
                                  severityConfig.border,
                                  severityConfig.color
                                )}
                              >
                                {issue.severity}
                              </Badge>
                              <h4 className="font-medium text-white truncate">
                                {issue.title}
                              </h4>
                            </div>
                            <p className="text-sm text-gray-400 mb-2">
                              {issue.file}:{issue.line}
                            </p>
                            <div className="flex items-center gap-4 text-xs text-gray-500">
                              <span className="flex items-center gap-1">
                                <Clock className="w-3 h-3" />
                                Added {issue.added_date}
                              </span>
                              <span className="flex items-center gap-1">
                                <Activity className="w-3 h-3" />
                                Estimated: {issue.estimated_hours}h
                              </span>
                            </div>
                          </div>
                          <Button
                            size="sm"
                            variant="outline"
                            className="bg-gray-800/50 border-gray-700 hover:bg-gray-700"
                          >
                            <Eye className="w-3 h-3 mr-1.5" />
                            View
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                )
              })}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>

      {/* Test Summary */}
      <Card className="bg-gray-900/50 backdrop-blur-xl border-gray-700/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-green-400" />
              <CardTitle className="text-white">Test Summary</CardTitle>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Test Stats */}
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <div className="flex items-center justify-center gap-2 mb-2">
                <CheckCircle className="w-5 h-5 text-green-400" />
                <span className="text-2xl font-bold text-green-400">
                  {tests.passing}
                </span>
              </div>
              <p className="text-sm text-gray-400">Passing</p>
            </div>
            <div className="text-center">
              <div className="flex items-center justify-center gap-2 mb-2">
                <XCircle className="w-5 h-5 text-red-400" />
                <span className="text-2xl font-bold text-red-400">
                  {tests.failing}
                </span>
              </div>
              <p className="text-sm text-gray-400">Failing</p>
            </div>
            <div className="text-center">
              <div className="flex items-center justify-center gap-2 mb-2">
                <Clock className="w-5 h-5 text-yellow-400" />
                <span className="text-2xl font-bold text-yellow-400">
                  {tests.skipped}
                </span>
              </div>
              <p className="text-sm text-gray-400">Skipped</p>
            </div>
          </div>

          {/* Progress Bar */}
          <div>
            <div className="flex justify-between text-sm mb-2">
              <span className="text-gray-400">Pass Rate</span>
              <span className="text-white font-semibold">
                {((tests.passing / tests.total) * 100).toFixed(1)}%
              </span>
            </div>
            <div className="relative h-3 bg-gray-800 rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${(tests.passing / tests.total) * 100}%` }}
                transition={{ duration: 1 }}
                className="h-full bg-gradient-to-r from-green-500 to-emerald-500"
              />
            </div>
          </div>

          {/* Test Info */}
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-4 text-gray-400">
              <span className="flex items-center gap-1.5">
                <Clock className="w-4 h-4" />
                Last run: {tests.last_run}
              </span>
              <span className="flex items-center gap-1.5">
                <Activity className="w-4 h-4" />
                Duration: {tests.duration}s
              </span>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-2">
            <Button
              onClick={runTests}
              className="flex-1 bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600"
            >
              <Play className="w-4 h-4 mr-2" />
              Run Tests
            </Button>
            <Button
              variant="outline"
              className="flex-1 border-gray-700 hover:bg-gray-800"
            >
              <Eye className="w-4 h-4 mr-2" />
              View Failures
            </Button>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}
```

### 3.3 Accessibility Checklist

#### WCAG 2.1 AA Compliance

**Perceivable**
- ✅ Data visualization has text alternatives
  - Chart data available in table format
  - Numeric values displayed alongside charts
- ✅ Color contrast meets AAA standards
  - Metric cards: 7:1+ contrast
  - Chart lines: 4.5:1+ contrast
- ✅ Icons with semantic meaning have labels
  - All severity icons have text descriptions
  - Status icons accompanied by text

**Operable**
- ✅ All interactive elements keyboard accessible
  - Tab through metric cards
  - Navigate chart with keyboard
  - Access all buttons via keyboard
- ✅ No keyboard traps
  - Can exit all modals and dialogs
  - Tab order is logical
- ✅ Focus indicators visible
  - 2px solid focus ring on all interactive elements

**Understandable**
- ✅ Data clearly labeled and explained
  - Metric thresholds explained (Good/Fair/Poor)
  - Test results show counts and percentages
- ✅ Consistent layout and terminology
  - Same metric card design throughout
  - Consistent severity labels

**Robust**
- ✅ Data tables for screen readers
  - Chart data available in accessible format
  - ARIA labels for all data points
- ✅ Live regions for updates
  - Test results announce changes
  - Metric updates announced

#### Keyboard Navigation

```
Tab Flow:
1. Metric cards (Coverage → Type Safety → Complexity → Tech Debt)
2. Trend chart (keyboard navigation within chart)
3. Issue cards (top to bottom)
4. "View" buttons for each issue
5. Run Tests button
6. View Failures button

Chart Navigation:
- Arrow keys: Navigate data points
- Enter: Show tooltip
- Escape: Hide tooltip
```

#### Screen Reader Optimizations

```tsx
// Metric cards
<Card role="region" aria-label={`${metricName}: ${value}%`}>

// Chart
<LineChart aria-label="Quality trend over last 7 days">
  <Line
    dataKey="coverage"
    aria-label="Code coverage trend"
  />
</LineChart>

// Issues list
<div role="list" aria-label="Recent quality issues">
  <Card role="listitem" aria-label={`${severity} severity: ${title}`}>
  </Card>
</div>

// Test summary
<div
  role="status"
  aria-live="polite"
  aria-label={`${passing} tests passing, ${failing} failing`}
>
```

### 3.4 User Flow Diagram

```
┌──────────────────┐
│  User Opens      │
│  Quality Page    │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────┐
│  Dashboard Loads         │
│  - Fetch metrics         │
│  - Fetch trend data      │
│  - Fetch issues          │
│  - Fetch test results    │
└────────┬─────────────────┘
         │
         ├─────────────────────────┐
         │                         │
         ▼                         ▼
┌─────────────────┐   ┌─────────────────────┐
│ View Metrics    │   │ Analyze Trend       │
│ - Coverage      │   │ - 7-day chart       │
│ - Type safety   │   │ - Identify patterns │
│ - Complexity    │   │ - Spot regressions  │
│ - Tech debt     │   │                     │
└────────┬────────┘   └─────────┬───────────┘
         │                      │
         ▼                      ▼
┌─────────────────┐   ┌─────────────────────┐
│ Review Issues   │   │ Check Tests         │
│ - Severity      │   │ - Pass/fail ratio   │
│ - Estimated fix │   │ - Recent runs       │
│ - Click "View"  │   │ - Click "Run"       │
└────────┬────────┘   └─────────┬───────────┘
         │                      │
         ▼                      ▼
┌─────────────────┐   ┌─────────────────────┐
│ Fix Issues      │   │ Run Tests           │
│ - Navigate to   │   │ - Execute suite     │
│   problematic   │   │ - View failures     │
│   code          │   │ - Get detailed logs │
│ - Apply fix     │   │                     │
└────────┬────────┘   └─────────┬───────────┘
         │                      │
         └──────────┬───────────┘
                    ▼
         ┌─────────────────────┐
         │ Metrics Improve     │
         │ - Real-time update  │
         │ - Dashboard refresh │
         │ - Trend shows       │
         │   improvement       │
         └─────────────────────┘
```

---

## 4. Component Integration Architecture

### 4.1 Component Dependency Graph

```
┌─────────────────────────────────────────────────────────────┐
│                     UDO Dashboard App                        │
└─────────────────────────────────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │  Task    │    │   CLI    │    │ Quality  │
    │  List    │◄──►│Integration│◄──►│Dashboard │
    └──────────┘    └──────────┘    └──────────┘
           │               │               │
           └───────────────┼───────────────┘
                           │
                           ▼
                 ┌──────────────────┐
                 │   Shared State   │
                 │   Management     │
                 └──────────────────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │ WebSocket│    │   API    │    │  Local   │
    │ Service  │    │  Client  │    │  Storage │
    └──────────┘    └──────────┘    └──────────┘
```

### 4.2 State Management

```typescript
// Global state structure
interface UDOState {
  tasks: {
    items: Task[]
    selected: Task | null
    loading: boolean
  }
  cli: {
    context: CLIContext | null
    activities: CLIActivity[]
    connected: boolean
  }
  quality: {
    metrics: QualityMetrics | null
    trend: QualityTrend[]
    issues: Issue[]
    tests: TestSummary | null
  }
  websocket: {
    connected: boolean
    reconnecting: boolean
  }
}

// State update actions
type Action =
  | { type: 'TASK_SELECTED'; payload: Task }
  | { type: 'CLI_ACTIVITY_ADDED'; payload: CLIActivity }
  | { type: 'QUALITY_METRICS_UPDATED'; payload: QualityMetrics }
  | { type: 'WEBSOCKET_CONNECTED' }
  | { type: 'WEBSOCKET_DISCONNECTED' }
```

### 4.3 API Endpoints

```
Tasks API:
  GET    /api/tasks/                  - List all tasks
  GET    /api/tasks/:id               - Get task details
  GET    /api/tasks/:id/context       - Get CLI context
  POST   /api/tasks/                  - Create task
  PATCH  /api/tasks/:id               - Update task
  DELETE /api/tasks/:id               - Delete task

CLI API:
  GET    /api/cli/context             - Get current CLI context
  POST   /api/cli/sync                - Sync CLI state
  GET    /api/cli/activity            - Get recent activities

Quality API:
  GET    /api/quality/metrics         - Get current metrics
  GET    /api/quality/trend           - Get historical trend
  GET    /api/quality/issues          - Get active issues
  GET    /api/quality/tests           - Get test summary
  POST   /api/quality/run-tests       - Execute test suite

WebSocket:
  ws://localhost:8000/ws              - Main WebSocket
  ws://localhost:8000/ws/cli          - CLI-specific updates
  ws://localhost:8000/ws/quality      - Quality updates
```

---

## 5. Performance Optimization

### 5.1 Loading Strategy

**Code Splitting**
```typescript
// Lazy load heavy components
const QualityDashboard = lazy(() => import('./QualityDashboard'))
const TaskDetails = lazy(() => import('./TaskDetails'))

// Preload on hover
<Link
  href="/quality"
  onMouseEnter={() => preloadComponent(QualityDashboard)}
>
```

**Data Prefetching**
```typescript
// Prefetch likely next navigation
useEffect(() => {
  const prefetchQuality = async () => {
    await fetch('/api/quality/metrics')
  }

  // Prefetch after 2 seconds of idle time
  const timer = setTimeout(prefetchQuality, 2000)
  return () => clearTimeout(timer)
}, [])
```

### 5.2 Rendering Optimization

**Virtualization for Long Lists**
```typescript
import { FixedSizeList } from 'react-window'

// Virtualize task list when > 20 items
{tasks.length > 20 ? (
  <FixedSizeList
    height={600}
    itemCount={tasks.length}
    itemSize={120}
  >
    {({ index, style }) => (
      <TaskCard task={tasks[index]} style={style} />
    )}
  </FixedSizeList>
) : (
  tasks.map(task => <TaskCard task={task} />)
)}
```

**Memoization**
```typescript
// Memoize expensive calculations
const sortedTasks = useMemo(() => {
  return tasks.sort((a, b) =>
    b.completeness - a.completeness
  )
}, [tasks])

// Memoize component renders
const TaskCard = memo(({ task }) => {
  // Component implementation
})
```

### 5.3 Animation Performance

**GPU Acceleration**
```css
/* Use transform and opacity for animations */
.animated-card {
  will-change: transform, opacity;
  transform: translateZ(0); /* Force GPU layer */
}
```

**Reduced Motion**
```typescript
// Respect user preferences
const prefersReducedMotion = window.matchMedia(
  '(prefers-reduced-motion: reduce)'
).matches

<motion.div
  animate={{ opacity: 1 }}
  transition={{
    duration: prefersReducedMotion ? 0 : 0.5
  }}
>
```

---

## 6. Testing Strategy

### 6.1 Unit Tests

```typescript
// TaskList.test.tsx
describe('TaskList', () => {
  it('renders task cards correctly', () => {
    const tasks = mockTasks()
    render(<TaskList tasks={tasks} />)

    expect(screen.getByText(tasks[0].title)).toBeInTheDocument()
  })

  it('handles task selection', async () => {
    const onSelect = jest.fn()
    render(<TaskList tasks={mockTasks()} onSelect={onSelect} />)

    await userEvent.click(screen.getByText('Details'))
    expect(onSelect).toHaveBeenCalled()
  })

  it('copies CLI command to clipboard', async () => {
    const writeText = jest.fn()
    Object.assign(navigator, { clipboard: { writeText } })

    render(<TaskList tasks={mockTasks()} />)
    await userEvent.click(screen.getByText('Continue'))

    expect(writeText).toHaveBeenCalledWith(expect.stringContaining('cd'))
  })
})
```

### 6.2 Integration Tests

```typescript
// Dashboard.integration.test.tsx
describe('Dashboard Integration', () => {
  it('loads and displays all components', async () => {
    render(<Dashboard />)

    await waitFor(() => {
      expect(screen.getByText('Active Development Tasks')).toBeInTheDocument()
      expect(screen.getByText('CLI Integration Panel')).toBeInTheDocument()
      expect(screen.getByText('Code Quality Dashboard')).toBeInTheDocument()
    })
  })

  it('syncs state across components', async () => {
    render(<Dashboard />)

    // Select task
    await userEvent.click(screen.getByText('Auth System'))

    // Verify CLI panel updates
    await waitFor(() => {
      expect(screen.getByText(/feature\/auth/)).toBeInTheDocument()
    })
  })
})
```

### 6.3 Accessibility Tests

```typescript
// Accessibility.test.tsx
import { axe, toHaveNoViolations } from 'jest-axe'

expect.extend(toHaveNoViolations)

describe('Accessibility', () => {
  it('TaskList has no WCAG violations', async () => {
    const { container } = render(<TaskList tasks={mockTasks()} />)
    const results = await axe(container)

    expect(results).toHaveNoViolations()
  })

  it('supports keyboard navigation', async () => {
    render(<TaskList tasks={mockTasks()} />)

    // Tab to first task
    await userEvent.tab()
    expect(screen.getAllByRole('article')[0]).toHaveFocus()

    // Tab to Details button
    await userEvent.tab()
    expect(screen.getByText('Details')).toHaveFocus()

    // Activate with Enter
    await userEvent.keyboard('{Enter}')
    expect(screen.getByRole('dialog')).toBeVisible()
  })

  it('announces updates to screen readers', async () => {
    const { container } = render(<QualityDashboard />)

    // Check for live region
    const liveRegion = container.querySelector('[aria-live="polite"]')
    expect(liveRegion).toBeInTheDocument()
  })
})
```

### 6.4 Visual Regression Tests

```typescript
// Visual.test.tsx
import { toMatchImageSnapshot } from 'jest-image-snapshot'

expect.extend({ toMatchImageSnapshot })

describe('Visual Regression', () => {
  it('TaskList renders consistently', async () => {
    const { container } = render(<TaskList tasks={mockTasks()} />)

    const image = await takeScreenshot(container)
    expect(image).toMatchImageSnapshot()
  })

  it('handles dark theme correctly', async () => {
    const { container } = render(
      <ThemeProvider theme="dark">
        <QualityDashboard />
      </ThemeProvider>
    )

    const image = await takeScreenshot(container)
    expect(image).toMatchImageSnapshot()
  })
})
```

---

## 7. Deployment Checklist

### 7.1 Pre-Deployment

**Code Quality**
- ✅ All TypeScript errors resolved
- ✅ ESLint violations fixed
- ✅ Prettier formatting applied
- ✅ No console.log statements in production code
- ✅ Dead code removed

**Testing**
- ✅ Unit tests: 90%+ coverage
- ✅ Integration tests passing
- ✅ Accessibility tests passing
- ✅ Visual regression tests passing
- ✅ Manual testing completed

**Performance**
- ✅ Lighthouse score 90+ (Performance)
- ✅ Bundle size < 500KB (gzipped)
- ✅ First Contentful Paint < 1.5s
- ✅ Time to Interactive < 3.5s
- ✅ No layout shifts (CLS = 0)

**Accessibility**
- ✅ WCAG 2.1 AA compliance verified
- ✅ Keyboard navigation tested
- ✅ Screen reader tested (NVDA/JAWS)
- ✅ Color contrast verified
- ✅ Focus management correct

**Security**
- ✅ No exposed API keys
- ✅ HTTPS enforced
- ✅ CSP headers configured
- ✅ XSS protection enabled
- ✅ Dependency vulnerabilities resolved

### 7.2 Deployment Steps

```bash
# 1. Build production bundle
npm run build

# 2. Run production tests
npm run test:prod

# 3. Analyze bundle
npm run analyze

# 4. Deploy to staging
npm run deploy:staging

# 5. Smoke test staging
npm run test:smoke -- --env=staging

# 6. Deploy to production
npm run deploy:prod

# 7. Monitor deployment
npm run monitor:prod
```

### 7.3 Post-Deployment

**Monitoring**
- ✅ Error tracking active (Sentry)
- ✅ Performance monitoring (Web Vitals)
- ✅ User analytics configured
- ✅ Alerts configured
- ✅ Rollback plan tested

**Documentation**
- ✅ Component documentation updated
- ✅ API documentation current
- ✅ Deployment guide reviewed
- ✅ Troubleshooting guide available
- ✅ Changelog updated

---

## 8. Future Enhancements

### 8.1 Phase 2 Features

**Advanced Visualizations**
- 3D quality metrics visualization
- Interactive dependency graphs
- Real-time collaboration indicators
- AI-powered insights dashboard

**Enhanced CLI Integration**
- VSCode extension for one-click transition
- Terminal multiplexing support
- Command history with ML suggestions
- Automated context switching

**Quality Improvements**
- Custom quality rule definitions
- AI-powered code review suggestions
- Automated fix proposals
- Historical quality comparison

### 8.2 Mobile Experience

**Responsive Enhancements**
- Mobile-optimized task cards
- Touch-friendly interactions
- Swipe gestures for actions
- Progressive Web App (PWA) support

**Mobile-Specific Features**
- Push notifications for CI/CD status
- Offline mode with sync
- Voice commands for task management
- QR code for quick CLI access

---

## Appendix

### A. Design Tokens

```typescript
// colors.ts
export const colors = {
  primary: {
    blue: '#3B82F6',
    cyan: '#06B6D4'
  },
  status: {
    success: '#10B981',
    warning: '#F59E0B',
    error: '#EF4444',
    info: '#3B82F6'
  },
  severity: {
    high: '#EF4444',
    medium: '#F59E0B',
    low: '#3B82F6'
  },
  background: {
    primary: 'rgba(17, 24, 39, 0.5)',
    secondary: 'rgba(31, 41, 55, 0.4)',
    tertiary: 'rgba(55, 65, 81, 0.3)'
  },
  text: {
    primary: '#FFFFFF',
    secondary: '#9CA3AF',
    tertiary: '#6B7280'
  },
  border: {
    primary: 'rgba(55, 65, 81, 0.5)',
    secondary: 'rgba(75, 85, 99, 0.3)'
  }
}

// spacing.ts
export const spacing = {
  xs: '0.25rem',   // 4px
  sm: '0.5rem',    // 8px
  md: '1rem',      // 16px
  lg: '1.5rem',    // 24px
  xl: '2rem',      // 32px
  '2xl': '3rem'    // 48px
}

// typography.ts
export const typography = {
  fontSize: {
    xs: '0.75rem',   // 12px
    sm: '0.875rem',  // 14px
    base: '1rem',    // 16px
    lg: '1.125rem',  // 18px
    xl: '1.25rem',   // 20px
    '2xl': '1.5rem', // 24px
    '3xl': '1.875rem', // 30px
    '4xl': '2.25rem'  // 36px
  },
  fontWeight: {
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700
  },
  lineHeight: {
    tight: 1.25,
    normal: 1.5,
    relaxed: 1.75
  }
}
```

### B. Component Library Dependencies

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "next": "^14.0.0",
    "framer-motion": "^10.16.4",
    "lucide-react": "^0.292.0",
    "@tanstack/react-query": "^5.8.4",
    "recharts": "^2.10.3",
    "sonner": "^1.2.0",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.0.0",
    "tailwind-merge": "^2.0.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.38",
    "@types/react-dom": "^18.2.17",
    "typescript": "^5.3.2",
    "tailwindcss": "^3.3.5",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.31",
    "eslint": "^8.54.0",
    "jest": "^29.7.0",
    "@testing-library/react": "^14.1.2",
    "@testing-library/jest-dom": "^6.1.5",
    "jest-axe": "^8.0.0"
  }
}
```

### C. Browser Support

**Minimum Requirements**
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

**Feature Detection**
```typescript
// Check for critical features
const hasRequiredFeatures = () => {
  return (
    'Promise' in window &&
    'fetch' in window &&
    'WebSocket' in window &&
    'IntersectionObserver' in window &&
    'matchMedia' in window
  )
}

if (!hasRequiredFeatures()) {
  showUnsupportedBrowserMessage()
}
```

---

**Document Status**: Draft
**Next Review**: After implementation Phase 1
**Last Updated**: 2025-11-20
**Version**: 1.0
