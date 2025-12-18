"use client"

/**
 * ContextManager - Task context management component
 *
 * Week 2 Day 4: Context operations (ZIP upload/download, Q4 implementation)
 *
 * Features:
 * - Display context metadata (file count, size, load stats)
 * - Download context ZIP
 * - Upload context files (basic interface)
 * - Track load events for Q4 analytics
 */

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  Download,
  Upload,
  FileArchive,
  Loader2,
  AlertCircle,
  CheckCircle,
  Clock,
} from 'lucide-react'
import {
  fetchContextMetadata,
  downloadContextZip,
  trackContextLoad,
  uploadContextFile,
  type ContextMetadata,
  KanbanContextAPIError,
} from '@/lib/api/kanban-context'
import { Input } from '@/components/ui/input'

interface ContextManagerProps {
  taskId: string
}

export function ContextManager({ taskId }: ContextManagerProps) {
  const [metadata, setMetadata] = useState<ContextMetadata | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isDownloading, setIsDownloading] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  // Load context metadata on mount
  useEffect(() => {
    loadMetadata()
  }, [taskId])

  const loadMetadata = async () => {
    setIsLoading(true)
    setError(null)

    try {
      const data = await fetchContextMetadata(taskId)
      setMetadata(data)
    } catch (err) {
      if (err instanceof KanbanContextAPIError) {
        setError(err.message)
      } else {
        setError('Failed to load context metadata')
      }
    } finally {
      setIsLoading(false)
    }
  }

  const handleDownload = async () => {
    if (!metadata?.zip_url) {
      setError('No context ZIP available for download')
      return
    }

    setIsDownloading(true)
    setError(null)
    setSuccess(null)

    try {
      // Track load event (Q4: double-click auto-load tracking)
      const loadStartTime = performance.now()
      await downloadContextZip(taskId, metadata.zip_url)
      const loadTime = Math.round(performance.now() - loadStartTime)

      // Track load event to backend
      await trackContextLoad(taskId, { load_time_ms: loadTime })

      // Refresh metadata to show updated stats
      await loadMetadata()

      setSuccess(`Context downloaded successfully (${loadTime}ms)`)
    } catch (err) {
      if (err instanceof KanbanContextAPIError) {
        setError(err.message)
      } else {
        setError('Failed to download context')
      }
    } finally {
      setIsDownloading(false)
    }
  }

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    setSelectedFile(file)
    setError(null)
    setSuccess(null)
  }

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a ZIP file to upload')
      return
    }

    setIsUploading(true)
    setError(null)
    setSuccess(null)

    try {
      // uploadContextFile already validates size (50MB) and file type (ZIP)
      const response = await uploadContextFile(taskId, selectedFile)

      // Refresh metadata to show updated stats
      await loadMetadata()

      setSuccess(
        `Context uploaded successfully! ${response.file_count} files (${formatBytes(response.total_size_bytes)})`
      )
      setSelectedFile(null)

      // Reset file input
      const fileInput = document.getElementById('context-file-input') as HTMLInputElement
      if (fileInput) fileInput.value = ''
    } catch (err) {
      if (err instanceof KanbanContextAPIError) {
        setError(err.message)
      } else {
        setError('Failed to upload context')
      }
    } finally {
      setIsUploading(false)
    }
  }

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return `${Math.round(bytes / Math.pow(k, i) * 100) / 100} ${sizes[i]}`
  }

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleString()
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="flex flex-col items-center gap-2">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          <p className="text-sm text-muted-foreground">Loading context...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Error/Success Messages */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {success && (
        <Alert>
          <CheckCircle className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-600">{success}</AlertDescription>
        </Alert>
      )}

      {/* Context Metadata */}
      {metadata ? (
        <div className="space-y-4">
          {/* Stats Cards */}
          <div className="grid grid-cols-2 gap-4">
            <div className="rounded-lg border p-4">
              <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
                <FileArchive className="h-4 w-4" />
                Files
              </div>
              <p className="text-2xl font-bold">{metadata.file_count}</p>
              <p className="text-xs text-muted-foreground mt-1">
                {formatBytes(metadata.total_size_bytes)}
              </p>
            </div>

            <div className="rounded-lg border p-4">
              <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
                <Clock className="h-4 w-4" />
                Load Stats
              </div>
              <p className="text-2xl font-bold">{metadata.load_count}</p>
              <p className="text-xs text-muted-foreground mt-1">
                Avg: {metadata.avg_load_time_ms}ms
              </p>
            </div>
          </div>

          {/* Metadata Details */}
          <div className="rounded-lg border p-4 space-y-2">
            <h4 className="font-semibold text-sm">Context Details</h4>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div>
                <span className="text-muted-foreground">Created:</span>
                <p className="text-xs">{formatDate(metadata.created_at)}</p>
              </div>
              <div>
                <span className="text-muted-foreground">Updated:</span>
                <p className="text-xs">{formatDate(metadata.updated_at)}</p>
              </div>
              {metadata.last_loaded_at && (
                <div className="col-span-2">
                  <span className="text-muted-foreground">Last Loaded:</span>
                  <p className="text-xs">{formatDate(metadata.last_loaded_at)}</p>
                </div>
              )}
              {metadata.checksum && (
                <div className="col-span-2">
                  <span className="text-muted-foreground">Checksum:</span>
                  <p className="text-xs font-mono truncate">{metadata.checksum}</p>
                </div>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="space-y-3">
            {/* Download Button */}
            <Button
              onClick={handleDownload}
              disabled={!metadata.zip_url || isDownloading}
              className="w-full"
            >
              {isDownloading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Downloading...
                </>
              ) : (
                <>
                  <Download className="mr-2 h-4 w-4" />
                  Download ZIP
                </>
              )}
            </Button>

            {/* Upload Section */}
            <div className="space-y-2">
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <Input
                    id="context-file-input"
                    type="file"
                    accept=".zip,application/zip"
                    onChange={handleFileSelect}
                    disabled={isUploading}
                    className="cursor-pointer"
                  />
                </div>
                <Button
                  variant="outline"
                  onClick={handleUpload}
                  disabled={!selectedFile || isUploading}
                >
                  {isUploading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Uploading...
                    </>
                  ) : (
                    <>
                      <Upload className="mr-2 h-4 w-4" />
                      Upload
                    </>
                  )}
                </Button>
              </div>
              {selectedFile && (
                <p className="text-xs text-muted-foreground">
                  Selected: {selectedFile.name} ({formatBytes(selectedFile.size)})
                </p>
              )}
              <p className="text-xs text-muted-foreground">
                Upload ZIP file (max 50MB)
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div className="text-center py-12">
          <FileArchive className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold mb-2">No Context Available</h3>
          <p className="text-sm text-muted-foreground mb-4">
            Upload context files to get started
          </p>

          {/* Upload Section for No Context */}
          <div className="max-w-md mx-auto space-y-2">
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Input
                  id="context-file-input-no-context"
                  type="file"
                  accept=".zip,application/zip"
                  onChange={handleFileSelect}
                  disabled={isUploading}
                  className="cursor-pointer"
                />
              </div>
              <Button
                onClick={handleUpload}
                disabled={!selectedFile || isUploading}
              >
                {isUploading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload className="mr-2 h-4 w-4" />
                    Upload
                  </>
                )}
              </Button>
            </div>
            {selectedFile && (
              <p className="text-xs text-muted-foreground">
                Selected: {selectedFile.name} ({formatBytes(selectedFile.size)})
              </p>
            )}
            <p className="text-xs text-muted-foreground">
              Upload ZIP file (max 50MB)
            </p>
          </div>
        </div>
      )}

      {/* Q4 Info Banner */}
      <div className="rounded-lg bg-muted p-3 text-sm">
        <p className="text-muted-foreground">
          <strong>Q4 Context Loading:</strong> Double-click a task card to auto-load context.
          Single-click to view this panel.
        </p>
      </div>
    </div>
  )
}
