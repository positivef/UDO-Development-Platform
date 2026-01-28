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

import { useState, useEffect, useRef } from 'react'
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
  UploadCloud,
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
  const [isDragging, setIsDragging] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const dragCounterRef = useRef(0)
  const fileInputRef = useRef<HTMLInputElement>(null)

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
        setError('관련 파일 메타데이터 로드 실패')
      }
    } finally {
      setIsLoading(false)
    }
  }

  const handleDownload = async () => {
    if (!metadata?.zip_url) {
      setError('다운로드할 ZIP 파일이 없습니다')
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

      setSuccess(`파일 다운로드 완료 (${loadTime}ms)`)
    } catch (err) {
      if (err instanceof KanbanContextAPIError) {
        setError(err.message)
      } else {
        setError('파일 다운로드 실패')
      }
    } finally {
      setIsDownloading(false)
    }
  }

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    validateAndSetFile(file)
  }

  const validateFile = (file: File): string | null => {
    // Check file type
    if (!file.type.includes('zip') && !file.name.endsWith('.zip')) {
      return 'ZIP 파일만 지원됩니다'
    }

    // Check file size (50MB limit)
    const MAX_SIZE = 50 * 1024 * 1024
    if (file.size > MAX_SIZE) {
      return `파일 크기가 50MB를 초과합니다 (현재: ${formatBytes(file.size)})`
    }

    return null
  }

  const validateAndSetFile = (file: File) => {
    const validationError = validateFile(file)
    if (validationError) {
      setError(validationError)
      return
    }

    setSelectedFile(file)
    setError(null)
    setSuccess(null)
  }

  // Drag and drop handlers
  const handleDragEnter = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    dragCounterRef.current += 1
    setIsDragging(true)
  }

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    dragCounterRef.current -= 1
    if (dragCounterRef.current === 0) {
      setIsDragging(false)
    }
  }

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
  }

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    dragCounterRef.current = 0
    setIsDragging(false)

    const files = e.dataTransfer.files
    if (files && files.length > 0) {
      validateAndSetFile(files[0])
    }
  }

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a ZIP file to upload')
      return
    }

    setIsUploading(true)
    setUploadProgress(0)
    setError(null)
    setSuccess(null)

    try {
      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => {
          // Increase progress but not beyond 90% until upload completes
          if (prev < 90) {
            return prev + Math.random() * 30
          }
          return prev
        })
      }, 200)

      // uploadContextFile already validates size (50MB) and file type (ZIP)
      const response = await uploadContextFile(taskId, selectedFile)

      // Clear progress simulation
      clearInterval(progressInterval)
      setUploadProgress(100)

      // Refresh metadata to show updated stats
      await loadMetadata()

      setSuccess(
        `업로드 완료! 파일 ${response.file_count}개 (${formatBytes(response.total_size_bytes)})`
      )
      setSelectedFile(null)

      // Reset file input and progress after a delay
      setTimeout(() => {
        setUploadProgress(0)
        const fileInput = fileInputRef.current
        if (fileInput) fileInput.value = ''
      }, 1500)
    } catch (err) {
      if (err instanceof KanbanContextAPIError) {
        setError(err.message)
      } else {
        setError('파일 업로드 실패')
      }
      setUploadProgress(0)
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
          <p className="text-sm text-muted-foreground">관련 파일 불러오는 중...</p>
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
                파일
              </div>
              <p className="text-2xl font-bold">{metadata.file_count}</p>
              <p className="text-xs text-muted-foreground mt-1">
                {formatBytes(metadata.total_size_bytes)}
              </p>
            </div>

            <div className="rounded-lg border p-4">
              <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
                <Clock className="h-4 w-4" />
                로드 통계
              </div>
              <p className="text-2xl font-bold">{metadata.load_count}</p>
              <p className="text-xs text-muted-foreground mt-1">
                평균: {metadata.avg_load_time_ms}ms
              </p>
            </div>
          </div>

          {/* Metadata Details */}
          <div className="rounded-lg border p-4 space-y-2">
            <h4 className="font-semibold text-sm">관련 파일 정보</h4>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div>
                <span className="text-muted-foreground">생성일:</span>
                <p className="text-xs">{formatDate(metadata.created_at)}</p>
              </div>
              <div>
                <span className="text-muted-foreground">수정일:</span>
                <p className="text-xs">{formatDate(metadata.updated_at)}</p>
              </div>
              {metadata.last_loaded_at && (
                <div className="col-span-2">
                  <span className="text-muted-foreground">마지막 로드:</span>
                  <p className="text-xs">{formatDate(metadata.last_loaded_at)}</p>
                </div>
              )}
              {metadata.checksum && (
                <div className="col-span-2">
                  <span className="text-muted-foreground">체크섬:</span>
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
                  다운로드 중...
                </>
              ) : (
                <>
                  <Download className="mr-2 h-4 w-4" />
                  ZIP 다운로드
                </>
              )}
            </Button>

            {/* Upload Section with Drag-Drop */}
            <div className="space-y-2">
              <div
                onDragEnter={handleDragEnter}
                onDragLeave={handleDragLeave}
                onDragOver={handleDragOver}
                onDrop={handleDrop}
                className={`relative rounded-lg border-2 border-dashed p-6 text-center transition-all ${
                  isDragging
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-300 hover:border-gray-400'
                } ${isUploading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
              >
                <Input
                  ref={fileInputRef}
                  id="context-file-input"
                  type="file"
                  accept=".zip,application/zip"
                  onChange={handleFileSelect}
                  disabled={isUploading}
                  className="hidden"
                />
                <div className="flex flex-col items-center gap-2">
                  <UploadCloud className={`h-8 w-8 ${isDragging ? 'text-blue-500' : 'text-gray-400'}`} />
                  <div>
                    <p className="text-sm font-medium">
                      {isDragging ? '파일을 여기에 놓으세요' : 'ZIP 파일을 드래그하여 놓으세요'}
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      또는{' '}
                      <button
                        type="button"
                        onClick={() => fileInputRef.current?.click()}
                        disabled={isUploading}
                        className="text-blue-500 hover:underline font-medium disabled:opacity-50"
                      >
                        클릭하여 선택
                      </button>
                    </p>
                  </div>
                </div>
              </div>

              {/* Progress Bar */}
              {isUploading && uploadProgress > 0 && (
                <div className="space-y-1">
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-500 h-2 rounded-full transition-all"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                  <p className="text-xs text-muted-foreground text-center">
                    업로드 중... {uploadProgress}%
                  </p>
                </div>
              )}

              {/* File Info */}
              {selectedFile && (
                <div className="rounded-lg bg-blue-50 p-3">
                  <p className="text-sm">
                    <span className="font-medium">선택됨:</span> {selectedFile.name}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    크기: {formatBytes(selectedFile.size)}
                  </p>
                </div>
              )}

              {/* Upload Button */}
              {selectedFile && (
                <Button
                  onClick={handleUpload}
                  disabled={!selectedFile || isUploading}
                  className="w-full"
                >
                  {isUploading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      업로드 중... {uploadProgress}%
                    </>
                  ) : (
                    <>
                      <Upload className="mr-2 h-4 w-4" />
                      업로드
                    </>
                  )}
                </Button>
              )}

              <p className="text-xs text-muted-foreground text-center">
                ZIP 파일 • 최대 50MB
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div className="text-center py-12">
          <FileArchive className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold mb-2">관련 파일 없음</h3>
          <p className="text-sm text-muted-foreground mb-4">
            ZIP 파일을 업로드하여 시작하세요
          </p>

          {/* Upload Section for No Context */}
          <div className="max-w-md mx-auto space-y-3">
            <div
              onDragEnter={handleDragEnter}
              onDragLeave={handleDragLeave}
              onDragOver={handleDragOver}
              onDrop={handleDrop}
              className={`relative rounded-lg border-2 border-dashed p-6 text-center transition-all ${
                isDragging
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-300 hover:border-gray-400'
              } ${isUploading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
            >
              <Input
                ref={fileInputRef}
                id="context-file-input-no-context"
                type="file"
                accept=".zip,application/zip"
                onChange={handleFileSelect}
                disabled={isUploading}
                className="hidden"
              />
              <div className="flex flex-col items-center gap-2">
                <UploadCloud className={`h-8 w-8 ${isDragging ? 'text-blue-500' : 'text-gray-400'}`} />
                <div>
                  <p className="text-sm font-medium">
                    {isDragging ? '파일을 여기에 놓으세요' : 'ZIP 파일을 드래그하여 놓으세요'}
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    또는{' '}
                    <button
                      type="button"
                      onClick={() => fileInputRef.current?.click()}
                      disabled={isUploading}
                      className="text-blue-500 hover:underline font-medium disabled:opacity-50"
                    >
                      클릭하여 선택
                    </button>
                  </p>
                </div>
              </div>
            </div>

            {/* Progress Bar */}
            {isUploading && uploadProgress > 0 && (
              <div className="space-y-1">
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-500 h-2 rounded-full transition-all"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
                <p className="text-xs text-muted-foreground text-center">
                  업로드 중... {uploadProgress}%
                </p>
              </div>
            )}

            {/* File Info */}
            {selectedFile && (
              <div className="rounded-lg bg-blue-50 p-3">
                <p className="text-sm">
                  <span className="font-medium">선택됨:</span> {selectedFile.name}
                </p>
                <p className="text-xs text-muted-foreground">
                  크기: {formatBytes(selectedFile.size)}
                </p>
              </div>
            )}

            {/* Upload Button */}
            {selectedFile && (
              <Button
                onClick={handleUpload}
                disabled={!selectedFile || isUploading}
                className="w-full"
              >
                {isUploading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    업로드 중... {uploadProgress}%
                  </>
                ) : (
                  <>
                    <Upload className="mr-2 h-4 w-4" />
                    업로드
                  </>
                )}
              </Button>
            )}

            <p className="text-xs text-muted-foreground text-center">
              ZIP 파일 • 최대 50MB
            </p>
          </div>
        </div>
      )}

      {/* Q4 Info Banner */}
      <div className="rounded-lg bg-muted p-3 text-sm">
        <p className="text-muted-foreground">
          <strong>작업 카드 더블클릭:</strong> 자동 로드, 싱글클릭: 이 패널 보기
        </p>
      </div>
    </div>
  )
}
