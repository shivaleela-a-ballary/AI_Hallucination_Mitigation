import { useEffect, useState, type ReactNode } from "react";
import { Bell, ChevronDown, Menu, Search } from "lucide-react";
import { motion } from "motion/react";
import { useNavigate, useRouterState } from "@tanstack/react-router";

import { Sheet, SheetContent, SheetTitle } from "@/components/ui/sheet";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import { SidebarNav, navItems } from "@/components/app/sidebar-nav";
import { cn } from "@/lib/utils";

export function AppShell({ children }: { children: ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const [commandOpen, setCommandOpen] = useState(false);
  const navigate = useNavigate();
  const pathname = useRouterState({ select: (s) => s.location.pathname });

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key.toLowerCase() === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setCommandOpen((o) => !o);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  return (
    <div className="min-h-screen bg-background">
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-40 hidden border-r border-sidebar-border bg-sidebar transition-[width] duration-300 lg:block",
          collapsed ? "w-0 overflow-hidden" : "w-[280px]",
        )}
      >
        <SidebarNav />
      </aside>

      <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
        <SheetContent side="left" className="w-[280px] bg-sidebar p-0">
          <SheetTitle className="sr-only">Navigation</SheetTitle>
          <SidebarNav onNavigate={() => setMobileOpen(false)} />
        </SheetContent>
      </Sheet>

      <div className={cn("transition-[padding] duration-300", collapsed ? "lg:pl-0" : "lg:pl-[280px]")}>
        <header className="sticky top-0 z-30 h-[72px] border-b border-border bg-background/70 backdrop-blur-xl">
          <div className="grid h-full grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-3 px-4 sm:px-6">
            <button
              type="button"
              aria-label="Toggle navigation"
              onClick={() => {
                if (window.innerWidth < 1024) setMobileOpen(true);
                else setCollapsed((c) => !c);
              }}
              className="grid size-10 place-items-center rounded-xl text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
            >
              <Menu className="size-5" />
            </button>

            <div className="flex min-w-0 justify-center">
              <button
                type="button"
                onClick={() => setCommandOpen(true)}
                className="flex h-10 w-full max-w-md min-w-0 items-center gap-2 rounded-full border border-border bg-card px-4 text-sm text-muted-foreground shadow-soft transition-colors hover:border-primary/40 focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
              >
                <Search className="size-4 shrink-0" aria-hidden="true" />
                <span className="truncate">Search anything...</span>
                <kbd className="ml-auto hidden shrink-0 rounded-md border border-border px-1.5 py-0.5 text-[11px] font-medium sm:block">
                  Ctrl + K
                </kbd>
              </button>
            </div>

            <div className="flex shrink-0 items-center gap-2">
              <button
                type="button"
                aria-label="Notifications"
                className="relative grid size-10 place-items-center rounded-xl text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
              >
                <Bell className="size-5" />
                <span className="absolute top-2 right-2 size-2 rounded-full bg-destructive" />
              </button>

              <DropdownMenu>
                <DropdownMenuTrigger className="flex items-center gap-2 rounded-full py-1 pr-2 pl-1 transition-colors hover:bg-muted focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none">
                  <span className="grid size-8 place-items-center rounded-full bg-primary text-sm font-semibold text-primary-foreground">
                    A
                  </span>
                  <span className="hidden text-sm font-medium sm:block">Account</span>
                  <ChevronDown className="size-4 text-muted-foreground" aria-hidden="true" />
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-52">
                  <DropdownMenuLabel>
                    <p className="text-sm font-semibold">Account</p>
                    <p className="text-xs font-normal text-muted-foreground">API-backed workspace</p>
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onSelect={() => navigate({ to: "/settings" })}>
                    Settings
                  </DropdownMenuItem>
                  <DropdownMenuItem onSelect={() => navigate({ to: "/history" })}>
                    My history
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem>Logout</DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </header>

        <motion.main
          key={pathname}
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.28, ease: "easeOut" }}
          className="mx-auto w-full max-w-[1400px] p-4 sm:p-6"
        >
          {children}
        </motion.main>
      </div>

      <CommandDialog open={commandOpen} onOpenChange={setCommandOpen}>
        <CommandInput placeholder="Search pages, claims and sources..." />
        <CommandList>
          <CommandEmpty>No results found.</CommandEmpty>
          <CommandGroup heading="Pages">
            {navItems.map((item) => (
              <CommandItem
                key={item.to}
                value={item.label}
                onSelect={() => {
                  setCommandOpen(false);
                  navigate({ to: item.to });
                }}
              >
                <item.icon className="size-4" aria-hidden="true" />
                {item.label}
              </CommandItem>
            ))}
          </CommandGroup>
        </CommandList>
      </CommandDialog>
    </div>
  );
}
