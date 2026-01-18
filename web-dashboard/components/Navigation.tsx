"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { Home, BarChart3, Clock, Lightbulb, Palette, KanbanSquare, AlertTriangle, Gauge, Archive, TrendingUp, Brain } from "lucide-react"
import { cn } from "@/lib/utils"

const navItems = [
  {
    href: "/",
    label: "Dashboard",
    icon: Home,
  },
  {
    href: "/kanban",
    label: "Kanban Board",
    icon: KanbanSquare,
  },
  {
    href: "/archive",
    label: "Archive",
    icon: Archive,
  },
  {
    href: "/roi-dashboard",
    label: "ROI Dashboard",
    icon: TrendingUp,
  },
  {
    href: "/rl-dashboard",
    label: "RL Knowledge",
    icon: Brain,
  },
  {
    href: "/uncertainty",
    label: "Uncertainty",
    icon: AlertTriangle,
  },
  {
    href: "/confidence",
    label: "Confidence",
    icon: Gauge,
  },
  {
    href: "/quality",
    label: "Quality Metrics",
    icon: BarChart3,
  },
  {
    href: "/time-tracking",
    label: "Time Tracking",
    icon: Clock,
  },
  {
    href: "/gi-formula",
    label: "GI Formula",
    icon: Lightbulb,
  },
  {
    href: "/ck-theory",
    label: "C-K Theory",
    icon: Palette,
  },
]

export function Navigation() {
  const pathname = usePathname()

  return (
    <nav className="flex items-center gap-1 sm:gap-2 overflow-x-auto max-w-full scrollbar-hide">
      {navItems.map((item) => {
        const Icon = item.icon
        const isActive = pathname === item.href

        return (
          <Link key={item.href} href={item.href}>
            <button
              className={cn(
                "flex items-center gap-1 sm:gap-2 px-2 sm:px-4 py-2 rounded-lg transition-colors shrink-0",
                isActive
                  ? "bg-primary/20 text-primary"
                  : "bg-muted/50 text-muted-foreground hover:bg-muted"
              )}
            >
              <Icon className="h-4 w-4 sm:h-5 sm:w-5" />
              <span className="hidden md:inline text-sm">{item.label}</span>
            </button>
          </Link>
        )
      })}
    </nav>
  )
}
