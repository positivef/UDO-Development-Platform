/**
 * Uncertainty Store - Zustand state management for Uncertainty Analysis
 *
 * Manages uncertainty data, mitigations, and real-time WebSocket updates
 * with optimistic updates for acknowledgments
 */

import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import { useShallow } from 'zustand/react/shallow'
import type {
  UncertaintyStatusResponse,
  UncertaintyState as UncertaintyStateType,
  MitigationStrategy,
} from '@/types/uncertainty'
import type {
  MitigationAckRequest,
  MitigationAckResponse,
  ContextAnalysisRequest,
  HealthResponse,
  BayesianConfidenceRequest,
  BayesianConfidenceResponse,
} from '@/lib/api/uncertainty'
import { uncertaintyAPI } from '@/lib/api/uncertainty'

interface UncertaintyState {
  // State
  uncertaintyData: UncertaintyStatusResponse | null
  healthData: HealthResponse | null
  bayesianConfidence: BayesianConfidenceResponse | null
  isLoading: boolean
  error: Error | null
  appliedMitigations: string[] // IDs of acknowledged mitigations
  acknowledgingMitigation: string | null // ID being acknowledged
  wsConnected: boolean
  wsError: string | null
  lastUpdate: string | null

  // Actions - Data fetching
  fetchUncertaintyStatus: () => Promise<void>
  fetchHealth: () => Promise<void>
  analyzeCustomContext: (context: ContextAnalysisRequest) => Promise<void>
  calculateConfidence: (request: BayesianConfidenceRequest) => Promise<void>

  // Actions - Mitigation management
  acknowledgeMitigation: (
    mitigationId: string,
    request: MitigationAckRequest
  ) => Promise<MitigationAckResponse | null>
  markMitigationApplied: (mitigationId: string) => void

  // Actions - WebSocket
  setWsConnected: (connected: boolean) => void
  setWsError: (error: string | null) => void
  handleWsUpdate: (data: UncertaintyStatusResponse) => void

  // Actions - State management
  setUncertaintyData: (data: UncertaintyStatusResponse) => void
  setHealthData: (data: HealthResponse) => void
  setBayesianConfidence: (data: BayesianConfidenceResponse) => void
  setLoading: (loading: boolean) => void
  setError: (error: Error | null) => void
  clearError: () => void

  // Reset
  reset: () => void
}

const initialState = {
  uncertaintyData: null,
  healthData: null,
  bayesianConfidence: null,
  isLoading: false,
  error: null,
  appliedMitigations: [],
  acknowledgingMitigation: null,
  wsConnected: false,
  wsError: null,
  lastUpdate: null,
}

export const useUncertaintyStore = create<UncertaintyState>()(
  persist(
    (set, get) => ({
      // Initial state
      ...initialState,

      // Data fetching actions
      fetchUncertaintyStatus: async () => {
        set({ isLoading: true, error: null })
        try {
          const data = await uncertaintyAPI.getStatus()
          set({
            uncertaintyData: data,
            lastUpdate: new Date().toISOString(),
            isLoading: false,
          })
        } catch (error) {
          set({
            error: error instanceof Error ? error : new Error('Failed to fetch uncertainty status'),
            isLoading: false,
          })
        }
      },

      fetchHealth: async () => {
        try {
          const data = await uncertaintyAPI.getHealth()
          set({ healthData: data })
        } catch (error) {
          console.error('Failed to fetch health data:', error)
          // Health check errors are non-critical, don't set main error
        }
      },

      analyzeCustomContext: async (context: ContextAnalysisRequest) => {
        set({ isLoading: true, error: null })
        try {
          const data = await uncertaintyAPI.analyzeContext(context)
          set({
            uncertaintyData: data,
            lastUpdate: new Date().toISOString(),
            isLoading: false,
          })
        } catch (error) {
          set({
            error: error instanceof Error ? error : new Error('Failed to analyze context'),
            isLoading: false,
          })
        }
      },

      calculateConfidence: async (request: BayesianConfidenceRequest) => {
        set({ isLoading: true, error: null })
        try {
          const data = await uncertaintyAPI.calculateConfidence(request)
          set({
            bayesianConfidence: data,
            isLoading: false,
          })
        } catch (error) {
          set({
            error: error instanceof Error ? error : new Error('Failed to calculate confidence'),
            isLoading: false,
          })
        }
      },

      // Mitigation management with optimistic updates
      acknowledgeMitigation: async (mitigationId: string, request: MitigationAckRequest) => {
        set({ acknowledgingMitigation: mitigationId, error: null })

        // Optimistic update: immediately mark as applied
        const currentData = get().uncertaintyData
        if (currentData) {
          const optimisticData: UncertaintyStatusResponse = {
            ...currentData,
            mitigations: currentData.mitigations.map((m) =>
              m.id === mitigationId
                ? {
                    ...m,
                    // Mark as acknowledged (this is not in the original type, but represents local state)
                  }
                : m
            ),
          }
          set({ uncertaintyData: optimisticData })
        }

        try {
          const response = await uncertaintyAPI.acknowledgeMitigation(mitigationId, request)

          // Add to applied mitigations list
          set((state) => ({
            appliedMitigations: [...state.appliedMitigations, mitigationId],
            acknowledgingMitigation: null,
          }))

          // Refresh uncertainty status to get updated state
          await get().fetchUncertaintyStatus()

          return response
        } catch (error) {
          // Rollback optimistic update on error
          if (currentData) {
            set({ uncertaintyData: currentData })
          }

          set({
            error: error instanceof Error ? error : new Error('Failed to acknowledge mitigation'),
            acknowledgingMitigation: null,
          })

          return null
        }
      },

      markMitigationApplied: (mitigationId: string) => {
        set((state) => ({
          appliedMitigations: state.appliedMitigations.includes(mitigationId)
            ? state.appliedMitigations
            : [...state.appliedMitigations, mitigationId],
        }))
      },

      // WebSocket actions
      setWsConnected: (connected: boolean) => {
        set({ wsConnected: connected, wsError: connected ? null : 'Disconnected' })
      },

      setWsError: (error: string | null) => {
        set({ wsError: error })
      },

      handleWsUpdate: (data: UncertaintyStatusResponse) => {
        set({
          uncertaintyData: data,
          lastUpdate: new Date().toISOString(),
        })
      },

      // State management
      setUncertaintyData: (data: UncertaintyStatusResponse) => {
        set({
          uncertaintyData: data,
          lastUpdate: new Date().toISOString(),
        })
      },

      setHealthData: (data: HealthResponse) => {
        set({ healthData: data })
      },

      setBayesianConfidence: (data: BayesianConfidenceResponse) => {
        set({ bayesianConfidence: data })
      },

      setLoading: (loading: boolean) => set({ isLoading: loading }),

      setError: (error: Error | null) => set({ error, isLoading: false }),

      clearError: () => set({ error: null }),

      reset: () => set(initialState),
    }),
    {
      name: 'uncertainty-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        // Persist applied mitigations for cross-session tracking
        appliedMitigations: state.appliedMitigations,
        // Don't persist uncertaintyData (should always fetch fresh)
      }),
    }
  )
)

// Selectors for optimized component re-renders
export const useUncertaintyData = () => useUncertaintyStore((state) => state.uncertaintyData)
export const useHealthData = () => useUncertaintyStore((state) => state.healthData)
export const useBayesianConfidence = () => useUncertaintyStore((state) => state.bayesianConfidence)
export const useUncertaintyLoading = () => useUncertaintyStore((state) => state.isLoading)
export const useUncertaintyError = () => useUncertaintyStore((state) => state.error)
export const useAppliedMitigations = () => useUncertaintyStore((state) => state.appliedMitigations)
export const useAcknowledgingMitigation = () => useUncertaintyStore((state) => state.acknowledgingMitigation)
// Use useShallow to prevent infinite loop during SSR
export const useWsStatus = () => useUncertaintyStore(
  useShallow((state) => ({
    connected: state.wsConnected,
    error: state.wsError,
  }))
)
export const useLastUpdate = () => useUncertaintyStore((state) => state.lastUpdate)

// Helper selectors with computed values
export const useMitigationsByPriority = () => {
  const data = useUncertaintyData()
  if (!data?.mitigations) return []

  return [...data.mitigations].sort((a, b) => b.priority - a.priority)
}

export const useUnappliedMitigations = () => {
  const data = useUncertaintyData()
  const appliedMitigations = useAppliedMitigations()

  if (!data?.mitigations) return []

  return data.mitigations.filter((m) => !appliedMitigations.includes(m.id))
}

export const useUncertaintyHealth = () => {
  const healthData = useHealthData()
  const uncertaintyData = useUncertaintyData()

  return {
    isHealthy: healthData?.status === 'healthy',
    circuitBreakerStatus: healthData?.circuit_breaker_status,
    cacheSize: healthData?.cache_size,
    lastUpdate: healthData?.last_update,
    uncertaintyState: uncertaintyData?.state,
  }
}
