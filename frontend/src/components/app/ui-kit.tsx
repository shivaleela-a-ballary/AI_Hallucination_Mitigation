import type { ReactNode } from "react";
import { motion } from "motion/react";

import { cn } from "@/lib/utils";
import type { VerificationResult } from "@/lib/api";

export function SectionCard({
  title,
  description,
  action,
  className,
  bodyClassName,
  children,
}: {
  title?: string;
  description?: string;
  action?: ReactNode;
  className?: string;
  bodyClassName?: string;
  children: ReactNode;
}) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      className={cn("card-soft overflow-hidden", className)}
    >
      {(title || action) && (
        <header className="grid grid-cols-[minmax(0,1fr)_auto] items-start gap-3 p-5 pb-0">
          <div className="min-w-0">
            {title && <h2 className="truncate text-base font-bold">{title}</h2>}
            {description && <p className="mt-1 text-sm text-muted-foreground">{description}</p>}
          </div>
          {action}
        </header>
      )}
      <div className={cn("p-5", bodyClassName)}>{children}</div>
    </motion.section>
  );
}

export function PageHeader({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <header className="mb-6 grid grid-cols-[minmax(0,1fr)_auto] items-center gap-4">
      <div className="min-w-0">
        <h1 className="truncate text-2xl font-bold tracking-tight">{title}</h1>
        {description && <p className="mt-1 text-sm text-muted-foreground">{description}</p>}
      </div>
      {action}
    </header>
  );
}

const resultStyles: Record<string, { label: string; className: string }> = {
  supported: { label: "Supported", className: "bg-success-soft text-success" },
  refuted: { label: "Refuted", className: "bg-danger-soft text-destructive" },
  contradicted: { label: "Refuted", className: "bg-danger-soft text-destructive" },
  "not-enough-info": { label: "Not Enough Info", className: "bg-warning-soft text-warning" },
  "not enough info": { label: "Not Enough Info", className: "bg-warning-soft text-warning" },
  uncertain: { label: "Uncertain", className: "bg-warning-soft text-warning" },
  unverified: { label: "Unverified", className: "bg-muted text-muted-foreground" },
  neutral: { label: "Neutral", className: "bg-muted text-muted-foreground" },
};

export function ResultBadge({ result, className }: { result?: string | VerificationResult; className?: string }) {
  const key = (result || "unverified").toString().toLowerCase().trim();
  const style = resultStyles[key] || {
    label: key ? key.charAt(0).toUpperCase() + key.slice(1).replace(/[-_]/g, " ") : "Unverified",
    className: "bg-muted text-muted-foreground",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md px-2 py-1 text-xs font-semibold whitespace-nowrap",
        style.className,
        className,
      )}
    >
      {style.label}
    </span>
  );
}

export function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const tone = value >= 0.7 ? "bg-success" : value >= 0.4 ? "bg-warning" : "bg-destructive";
  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-muted" role="presentation">
      <motion.div
        initial={{ width: 0 }}
        animate={{ width: `${pct}%` }}
        transition={{ duration: 0.8, ease: "easeOut" }}
        className={cn("h-full rounded-full", tone)}
      />
    </div>
  );
}
