export function formatDuration(minutes: number): string {
  if (minutes < 60) {
    return `${Math.round(minutes)}m`
  }
  const hours = Math.floor(minutes / 60)
  const mins = Math.round(minutes % 60)
  return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`
}

export function formatNumber(num: number, decimals: number = 0): string {
  return num.toFixed(decimals).replace(/\B(?=(\d{3})+(?!\d))/g, ",")
}

export function formatPercentage(num: number, decimals: number = 1): string {
  return `${num > 0 ? "+" : ""}${num.toFixed(decimals)}%`
}

export function getSeverityVariant(
  severity: "low" | "medium" | "high" | "critical"
): "default" | "secondary" | "destructive" | "outline" {
  switch (severity) {
    case "low":
      return "secondary"
    case "medium":
      return "outline"
    case "high":
      return "default"
    case "critical":
      return "destructive"
    default:
      return "default"
  }
}
