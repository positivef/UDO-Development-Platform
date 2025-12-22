import * as React from "react"

type ToasterToast = {
  id: string
  title?: string
  description?: string
  action?: React.ReactNode
  variant?: 'default' | 'destructive'
}

const TOAST_LIMIT = 1
const TOAST_REMOVE_DELAY = 1000000

type ToastActionElement = React.ReactElement<any>

let count = 0

function genId() {
  count = (count + 1) % Number.MAX_SAFE_INTEGER
  return count.toString()
}

type Toast = Omit<ToasterToast, "id">

export function useToast() {
  const [toasts, setToasts] = React.useState<ToasterToast[]>([])

  const toast = React.useCallback(
    function ({ ...props }: Toast) {
      const id = genId()

      const update = (props: ToasterToast) =>
        setToasts((toasts) =>
          toasts.map((t) => (t.id === id ? { ...t, ...props } : t))
        )
      const dismiss = () => setToasts((toasts) => toasts.filter((t) => t.id !== id))

      setToasts((toasts) => {
        const newToasts = [...toasts, { ...props, id }]
        if (newToasts.length > TOAST_LIMIT) {
          return newToasts.slice(-TOAST_LIMIT)
        }
        return newToasts
      })

      return {
        id,
        dismiss,
        update,
      }
    },
    []
  )

  return {
    toast,
    toasts,
    dismiss: (toastId?: string) => {
      setToasts((toasts) =>
        toasts.filter((t) => toastId !== undefined ? t.id !== toastId : true)
      )
    },
  }
}
