import { Link, useRouterState } from "@tanstack/react-router";
import {
  LayoutDashboard,
  ShieldCheck,
  MessageCircleQuestion,
  Share2,
  Library,
  History,
  UploadCloud,
  Settings,
  Info,
  LogOut,
  Moon,
} from "lucide-react";
import { motion } from "motion/react";

import { Switch } from "@/components/ui/switch";
import { cn } from "@/lib/utils";
import { useTheme } from "@/hooks/use-theme";
import robot from "@/assets/robot.png";

export const navItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/new-verification", label: "New Verification", icon: ShieldCheck },
  { to: "/ask", label: "Ask a Question", icon: MessageCircleQuestion },
  { to: "/knowledge-graph", label: "Knowledge Graph", icon: Share2 },
  { to: "/sources", label: "Sources", icon: Library },
  { to: "/history", label: "History", icon: History },
  { to: "/uploads", label: "Uploads", icon: UploadCloud },
  { to: "/settings", label: "Settings", icon: Settings },
  { to: "/about", label: "About Us", icon: Info },
] as const;

export function BrandMark() {
  return (
    <div className="flex min-w-0 items-center gap-3">
      <div className="grid size-10 shrink-0 place-items-center rounded-xl bg-primary text-primary-foreground">
        <Share2 className="size-5" aria-hidden="true" />
      </div>
      <div className="min-w-0 leading-tight">
        <p className="truncate text-sm font-bold">AI Hallucination</p>
        <p className="truncate text-xs text-muted-foreground">Mitigation System</p>
      </div>
    </div>
  );
}

export function SidebarNav({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const { theme, setTheme } = useTheme();

  return (
    <div className="flex h-full flex-col gap-6 overflow-y-auto p-6">
      <BrandMark />

      <nav aria-label="Main navigation" className="flex flex-col gap-1">
        {navItems.map((item) => {
          const active = item.to === "/" ? pathname === "/" : pathname.startsWith(item.to);
          return (
            <Link
              key={item.to}
              to={item.to}
              onClick={onNavigate}
              aria-current={active ? "page" : undefined}
              className={cn(
                "group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200",
                "focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-sidebar focus-visible:outline-none",
                active
                  ? "bg-sidebar-accent text-sidebar-accent-foreground font-semibold"
                  : "text-muted-foreground hover:translate-x-0.5 hover:bg-sidebar-accent/60 hover:text-foreground",
              )}
            >
              <item.icon className="size-4.5 shrink-0" aria-hidden="true" />
              <span className="truncate">{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto flex flex-col gap-4">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="relative overflow-hidden rounded-2xl bg-accent p-4"
        >
          <p className="text-sm font-bold text-accent-foreground">AI Accuracy, Built on Real Evidence</p>
          <p className="mt-1 text-xs text-muted-foreground">
            Reduce hallucinations. Trust every answer.
          </p>
          <img
            src={robot}
            alt=""
            aria-hidden="true"
            loading="lazy"
            width={768}
            height={640}
            className="pointer-events-none mt-2 ml-auto h-16 w-auto"
          />
        </motion.div>

        <label className="flex cursor-pointer items-center justify-between gap-3 rounded-xl px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground">
          <span className="flex items-center gap-3">
            <Moon className="size-4.5" aria-hidden="true" />
            Dark Mode
          </span>
          <Switch
            checked={theme === "dark"}
            onCheckedChange={(v) => setTheme(v ? "dark" : "light")}
            aria-label="Toggle dark mode"
          />
        </label>

        <button
          type="button"
          className="flex items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-sidebar-accent/60 hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
        >
          <LogOut className="size-4.5" aria-hidden="true" />
          Logout
        </button>
      </div>
    </div>
  );
}
