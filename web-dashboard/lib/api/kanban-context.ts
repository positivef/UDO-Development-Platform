/**
 * Kanban Context API Client
 *
 * Week 2 Day 4: Context operations (ZIP upload/download, Q4 implementation)
 *
 * API Endpoints:
 * - GET  /api/kanban/context/{id}       - Get metadata
 * - POST /api/kanban/context/{id}       - Upload ZIP
 * - POST /api/kanban/context/{id}/load  - Track load event
 * - GET  /api/kanban/context/{id}/full  - Get full context
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface ContextMetadata {
  task_id: string
  file_count: number
  total_size_bytes: number
  zip_url?: string
  checksum?: string
  load_count: number
  avg_load_time_ms: number
  created_at: string
  updated_at: string
  last_loaded_at?: string
}

export interface ContextFile {
  path: string
  size_bytes: number
  mime_type?: string
}

export interface TaskContext extends ContextMetadata {
  files: ContextFile[]
}

export interface ContextUploadRequest {
  files: ContextFile[]
  checksum?: string
}

export interface ContextUploadResponse {
  task_id: string
  zip_url: string
  checksum: string
  file_count: number
  total_size_bytes: number
  created_at: string
}

export interface ContextLoadRequest {
  load_time_ms: number
}

export interface ContextLoadResponse {
  task_id: string
  load_count: number
  avg_load_time_ms: number
  last_loaded_at: string
}

export class KanbanContextAPIError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public code?: string
  ) {
    super(message)
    this.name = 'KanbanContextAPIError'
  }
}

/**
 * Get context metadata (single-click popup)
 */
export async function fetchContextMetadata(
  taskId: string
): Promise<ContextMetadata | null> {
  const response = await fetch(
    `${API_BASE_URL}/api/kanban/context/${taskId}`,
    {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    }
  )

  if (response.status === 404) {
    return null // No context found
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new KanbanContextAPIError(
      errorData.error?.message || `Failed to fetch context metadata: ${response.statusText}`,
      response.status,
      errorData.error?.code
    )
  }

  return response.json()
}

/**
 * Upload context as ZIP (<50MB limit)
 */
export async function uploadContext(
  taskId: string,
  uploadRequest: ContextUploadRequest
): Promise<ContextUploadResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/kanban/context/${taskId}`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(uploadRequest),
    }
  )

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))

    // Special handling for size limit exceeded
    if (response.status === 413) {
      throw new KanbanContextAPIError(
        'Context size limit exceeded (50MB max)',
        413,
        'CONTEXT_SIZE_LIMIT_EXCEEDED'
      )
    }

    throw new KanbanContextAPIError(
      errorData.error?.message || `Failed to upload context: ${response.statusText}`,
      response.status,
      errorData.error?.code
    )
  }

  return response.json()
}

/**
 * Upload context ZIP file (Week 6 Day 5: FormData file upload)
 * @param taskId - Task ID to upload context for
 * @param file - ZIP file to upload
 * @returns Upload response with metadata
 * @throws KanbanContextAPIError if upload fails or file exceeds 50MB
 */
export async function uploadContextFile(
  taskId: string,
  file: File
): Promise<ContextUploadResponse> {
  // Validate file size (50MB = 52,428,800 bytes)
  const MAX_SIZE = 50 * 1024 * 1024
  if (file.size > MAX_SIZE) {
    throw new KanbanContextAPIError(
      `File size ${(file.size / 1024 / 1024).toFixed(2)}MB exceeds 50MB limit`,
      413,
      'CONTEXT_SIZE_LIMIT_EXCEEDED'
    )
  }

  // Validate file type (ZIP only)
  if (!file.name.endsWith('.zip') && file.type !== 'application/zip') {
    throw new KanbanContextAPIError(
      'Only ZIP files are allowed',
      400,
      'INVALID_FILE_TYPE'
    )
  }

  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(
    `${API_BASE_URL}/api/kanban/context/${taskId}/upload`,
    {
      method: 'POST',
      body: formData,
      // Note: Don't set Content-Type header - browser will set it with boundary
    }
  )

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))

    // Special handling for size limit exceeded
    if (response.status === 413) {
      throw new KanbanContextAPIError(
        'Context size limit exceeded (50MB max)',
        413,
        'CONTEXT_SIZE_LIMIT_EXCEEDED'
      )
    }

    throw new KanbanContextAPIError(
      errorData.error?.message || `Failed to upload context: ${response.statusText}`,
      response.status,
      errorData.error?.code
    )
  }

  return response.json()
}

/**
 * Track context load event (Q4: double-click auto-load)
 */
export async function trackContextLoad(
  taskId: string,
  loadRequest: ContextLoadRequest
): Promise<ContextLoadResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/kanban/context/${taskId}/load`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(loadRequest),
    }
  )

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new KanbanContextAPIError(
      errorData.error?.message || `Failed to track context load: ${response.statusText}`,
      response.status,
      errorData.error?.code
    )
  }

  return response.json()
}

/**
 * Get full context with files list (for download)
 */
export async function fetchFullContext(
  taskId: string
): Promise<TaskContext | null> {
  const response = await fetch(
    `${API_BASE_URL}/api/kanban/context/${taskId}/full`,
    {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    }
  )

  if (response.status === 404) {
    return null // No context found
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new KanbanContextAPIError(
      errorData.error?.message || `Failed to fetch full context: ${response.statusText}`,
      response.status,
      errorData.error?.code
    )
  }

  return response.json()
}

/**
 * Download context ZIP file (browser download)
 */
export async function downloadContextZip(
  taskId: string,
  zipUrl: string,
  filename?: string
): Promise<void> {
  try {
    const response = await fetch(zipUrl)

    if (!response.ok) {
      throw new KanbanContextAPIError(
        `Failed to download context ZIP: ${response.statusText}`,
        response.status
      )
    }

    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename || `context-${taskId}.zip`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (error) {
    if (error instanceof KanbanContextAPIError) {
      throw error
    }
    throw new KanbanContextAPIError(
      `Failed to download context ZIP: ${error instanceof Error ? error.message : 'Unknown error'}`
    )
  }
}
