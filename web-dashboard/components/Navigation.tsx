"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { Home, BarChart3, Clock, Lightbulb, Palette, KanbanSquare, AlertTriangle, Gauge, Archive, TrendingUp } from "lucide-react"
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
    <nav className="flex items-center gap-2">
      {navItems.map((item) => {
        const Icon = item.icon
        const isActive = pathname === item.href

        return (
          <Link key={item.href} href={item.href}>
            <button
              className={cn(
                "flex items-center gap-2 px-4 py-2 rounded-lg transition-colors",
                isActive
                  ? "bg-primary/20 text-primary"
                  : "bg-muted/50 text-muted-foreground hover:bg-muted"
              )}
            >
              <Icon className="h-5 w-5" />
              <span className="hidden sm:inline">{item.label}</span>
            </button>
          </Link>
        )
      })}
    </nav>
  )
}
