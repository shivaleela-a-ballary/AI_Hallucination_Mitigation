import { Link, useRouterState } from "@tanstack/react-router";
import {
  Home,
  MessageSquare,
  History as HistoryIcon,
  Search,
  Share2,
  FileText,
  Settings as SettingsIcon,
  HelpCircle,
  CheckCircle2,
  Cpu,
  BrainCircuit,
  LogOut,
  LogIn,
  Sun,
  Moon,
} from "lucide-react";
import { motion } from "motion/react";

import { cn } from "@/lib/utils";
import { useTheme } from "@/hooks/use-theme";
import { useAuth } from "@/lib/auth-context";

export const navItems = [
  { to: "/", label: "Dashboard", icon: Home },
  { to: "/ask", label: "Ask Question", icon: MessageSquare },
  { to: "/history", label: "Verification History", icon: HistoryIcon },
  { to: "/new-verification", label: "Evidence Search", icon: Search },
  { to: "/sources", label: "Knowledge Graph", icon: Share2 },
  { to: "/check-answer", label: "Reports", icon: FileText },
  { to: "/settings", label: "Settings", icon: SettingsIcon },
  { to: "/about", label: "Help & Docs", icon: HelpCircle },
] as const;

export function BrandMark() {
  return (
    <Link to="/" className="flex items-center gap-3 group transition-opacity hover:opacity-90">
      <div className="relative grid size-10 shrink-0 place-items-center rounded-xl bg-gradient-to-br from-indigo-500/20 via-purple-500/20 to-cyan-500/20 border border-indigo-500/40 shadow-lg shadow-indigo-500/20">
        <BrainCircuit className="size-6 text-cyan-400 group-hover:scale-105 transition-transform" />
        <span className="absolute -top-0.5 -right-0.5 size-2 rounded-full bg-cyan-400 animate-pulse" />
      </div>
      <div className="min-w-0 leading-tight">
        <p className="truncate text-base font-bold text-white tracking-tight">AI Hallucination</p>
        <p className="truncate text-xs font-semibold text-cyan-400">Mitigation System</p>
      </div>
    </Link>
  );
}

export function SidebarNav({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const { theme, setTheme } = useTheme();
  const { user, isAuthenticated, logout, openAuthModal } = useAuth();

  return (
    <div className="flex h-full flex-col justify-between overflow-y-auto bg-[#070d1e] border-r border-[#15203b] p-5">
      <div className="space-y-6">
        {/* Brand Header */}
        <BrandMark />

        {/* Navigation Items */}
        <nav aria-label="Main navigation" className="flex flex-col gap-1.5 pt-2">
          {navItems.map((item) => {
            const active = item.to === "/" ? pathname === "/" : pathname.startsWith(item.to);
            return (
              <Link
                key={item.to}
                to={item.to}
                onClick={onNavigate}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "group relative flex items-center gap-3.5 rounded-xl px-3.5 py-2.5 text-sm font-medium transition-all duration-200",
                  active
                    ? "bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-lg shadow-indigo-600/30 border border-indigo-400/40 font-semibold"
                    : "text-slate-400 hover:text-slate-100 hover:bg-[#111c38] hover:translate-x-0.5",
                )}
              >
                <item.icon
                  className={cn(
                    "size-4.5 shrink-0 transition-colors",
                    active ? "text-white" : "text-slate-400 group-hover:text-slate-200",
                  )}
                  aria-hidden="true"
                />
                <span className="truncate">{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Lower Status & Footer Section */}
      <div className="space-y-4 pt-6 border-t border-[#15203b]/80">
        {/* System Status Card */}
        <div className="rounded-xl bg-[#0b1429] border border-[#1b2a4d] p-3 space-y-2.5">
          <div className="space-y-1">
            <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">System Status</p>
            <div className="flex items-center gap-2 text-xs font-medium text-slate-200">
              <span className="relative flex size-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex rounded-full size-2 bg-emerald-500" />
              </span>
              All systems operational
            </div>
          </div>

          <div className="space-y-1.5 pt-2 border-t border-[#15203b]">
            <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Models Loaded</p>
            <div className="grid grid-cols-1 gap-1 text-xs">
              <div className="flex items-center justify-between text-slate-300">
                <span>SciBERT</span>
                <CheckCircle2 className="size-3.5 text-emerald-400" />
              </div>
              <div className="flex items-center justify-between text-slate-300">
                <span>Retriever</span>
                <CheckCircle2 className="size-3.5 text-emerald-400" />
              </div>
              <div className="flex items-center justify-between text-slate-300">
                <span>NLI Model</span>
                <CheckCircle2 className="size-3.5 text-emerald-400" />
              </div>
              <div className="flex items-center justify-between text-slate-300">
                <span>Risk Analyzer</span>
                <CheckCircle2 className="size-3.5 text-emerald-400" />
              </div>
            </div>
          </div>
        </div>

        {/* User / Auth Info */}
        <div className="flex items-center justify-between px-1">
          {isAuthenticated && user ? (
            <div className="flex items-center justify-between w-full">
              <span className="text-xs text-slate-400 truncate max-w-[120px]">
                {user.username || user.full_name}
              </span>
              <button
                type="button"
                onClick={() => void logout()}
                className="text-xs text-rose-400 hover:text-rose-300 flex items-center gap-1"
              >
                <LogOut className="size-3.5" /> Sign Out
              </button>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => openAuthModal("login")}
              className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1.5"
            >
              <LogIn className="size-3.5" /> Sign In / Register
            </button>
          )}
        </div>

        {/* Footer */}
        <div className="text-[11px] text-slate-500 flex flex-col gap-0.5 leading-relaxed px-1">
          <p>© 2024 AI Hallucination</p>
          <p>Mitigation System</p>
          <p className="text-[10px] text-slate-600 mt-0.5">v2.1.0</p>
        </div>
      </div>
    </div>
  );
}
