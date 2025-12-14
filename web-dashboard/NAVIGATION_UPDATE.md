# Navigation Update Instructions

## Option 1: Using the Navigation Component (Recommended)

Add the Navigation component to your dashboard header by importing it:

```tsx
import { Navigation } from "@/components/Navigation"
```

Then add it to your header section:

```tsx
<div className="flex items-center gap-4">
  <Navigation />
  <div className={cn(
    "flex items-center gap-2 px-4 py-2 rounded-lg",
    isConnected ? "bg-green-500/20 text-green-400" : "bg-red-500/20 text-red-400"
  )}>
    {/* Connection status */}
  </div>
</div>
```

## Option 2: Manual Link Addition

In `components/dashboard/dashboard.tsx`, add this code between the Quality Metrics link and the connection status:

```tsx
<Link href="/time-tracking">
  <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-purple-500/20 text-purple-400 hover:bg-purple-500/30 transition-colors">
    <Clock className="h-5 w-5" />
    <span>Time Tracking</span>
  </button>
</Link>
```

Make sure `Clock` is imported from `lucide-react` at the top of the file (it already is).

## Accessing the Dashboard

Navigate to: `http://localhost:3000/time-tracking`
