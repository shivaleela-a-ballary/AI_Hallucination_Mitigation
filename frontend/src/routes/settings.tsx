import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  Database,
  Shield,
  Sliders,
  User,
  CheckCircle2,
  AlertCircle,
  Save,
  LogIn,
  Activity,
  Layers,
  Sparkles,
  Server,
} from "lucide-react";

import { AppShell } from "@/components/app/app-shell";
import { PageHeader, SectionCard } from "@/components/app/ui-kit";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { api, type HealthResponse } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { toast } from "sonner";

export const Route = createFileRoute("/settings")({
  head: () => ({ meta: [{ title: "Settings & Profile — AI Hallucination Mitigation System" }] }),
  component: SettingsPage,
});

function SettingsPage() {
  const { user, settings, isAuthenticated, updateProfile, updateSettings, openAuthModal } = useAuth();

  // Profile form state
  const [fullName, setFullName] = useState(user?.full_name || "");
  const [bio, setBio] = useState("");
  const [savingProfile, setSavingProfile] = useState(false);

  // Settings form state
  const [minSimilarity, setMinSimilarity] = useState(settings?.default_min_similarity ?? 0.45);
  const [topK, setTopK] = useState(settings?.default_top_k ?? 5);
  const [preferredModel, setPreferredModel] = useState(
    settings?.preferred_model ?? "sentence-transformers/all-MiniLM-L6-v2"
  );
  const [autoSaveHistory, setAutoSaveHistory] = useState(settings?.auto_save_history ?? true);
  const [savingSettings, setSavingSettings] = useState(false);

  // Backend & MongoDB Health
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState("");
  const [refreshingHealth, setRefreshingHealth] = useState(false);

  useEffect(() => {
    if (user) {
      setFullName(user.full_name || "");
    }
  }, [user]);

  useEffect(() => {
    if (settings) {
      setMinSimilarity(settings.default_min_similarity);
      setTopK(settings.default_top_k);
      setPreferredModel(settings.preferred_model);
      setAutoSaveHistory(settings.auto_save_history);
    }
  }, [settings]);

  const loadHealth = async () => {
    setRefreshingHealth(true);
    try {
      const data = await api.health();
      setHealth(data);
      setHealthError("");
    } catch {
      setHealthError("Unable to reach backend service.");
    } finally {
      setRefreshingHealth(false);
    }
  };

  useEffect(() => {
    void loadHealth();
  }, []);

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isAuthenticated) {
      openAuthModal("login");
      return;
    }
    setSavingProfile(true);
    try {
      await updateProfile({ full_name: fullName.trim(), bio: bio.trim() });
    } finally {
      setSavingProfile(false);
    }
  };

  const handleSaveSettings = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isAuthenticated) {
      toast.info("Settings saved locally for this session. Sign in to sync across devices.");
      return;
    }
    setSavingSettings(true);
    try {
      await updateSettings({
        default_min_similarity: minSimilarity,
        default_top_k: topK,
        preferred_model: preferredModel,
        auto_save_history: autoSaveHistory,
      });
    } finally {
      setSavingSettings(false);
    }
  };

  return (
    <AppShell>
      <PageHeader
        title="Settings & Profile"
        description="Manage your account profile, AI verification thresholds, and MongoDB Atlas database status."
      />

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left 2 columns: Profile & AI Settings */}
        <div className="space-y-6 lg:col-span-2">
          {/* User Profile Card */}
          <SectionCard
            title="User Profile"
            className="relative overflow-hidden"
          >
            {isAuthenticated && user ? (
              <form onSubmit={handleSaveProfile} className="space-y-5">
                <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 pb-4 border-b border-border">
                  <div className="grid size-16 shrink-0 place-items-center rounded-2xl bg-primary text-xl font-bold text-primary-foreground shadow-md">
                    {(user.full_name || user.username || "U").charAt(0).toUpperCase()}
                  </div>
                  <div className="space-y-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <h3 className="text-lg font-bold truncate">{user.full_name || user.username}</h3>
                      <span className="inline-flex items-center rounded-full bg-primary/10 px-2 py-0.5 text-xs font-semibold text-primary">
                        {user.role || "User"}
                      </span>
                    </div>
                    <p className="text-sm text-muted-foreground truncate">{user.email}</p>
                    <p className="text-xs text-muted-foreground">
                      Username: <code className="text-foreground font-mono">@{user.username}</code>
                    </p>
                  </div>
                </div>

                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-1.5">
                    <Label htmlFor="profile-fullname" className="text-xs font-medium">
                      Display Name
                    </Label>
                    <Input
                      id="profile-fullname"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      placeholder="Your full name"
                      className="h-10 rounded-xl"
                    />
                  </div>

                  <div className="space-y-1.5">
                    <Label htmlFor="profile-email" className="text-xs font-medium">
                      Email Address (Synced from MongoDB)
                    </Label>
                    <Input
                      id="profile-email"
                      value={user.email}
                      disabled
                      className="h-10 rounded-xl bg-muted/50 cursor-not-allowed opacity-80"
                    />
                  </div>
                </div>

                <div className="flex justify-end pt-2">
                  <Button type="submit" disabled={savingProfile} className="rounded-xl h-10 px-5">
                    <Save className="size-4 mr-2" />
                    {savingProfile ? "Saving..." : "Save Profile"}
                  </Button>
                </div>
              </form>
            ) : (
              <div className="flex flex-col items-center justify-center p-6 text-center space-y-3">
                <div className="grid size-12 place-items-center rounded-full bg-primary/10 text-primary">
                  <User className="size-6" />
                </div>
                <div className="space-y-1">
                  <h3 className="font-semibold text-base">You are in Guest Mode</h3>
                  <p className="text-sm text-muted-foreground max-w-md">
                    Sign in or create an account to access persistent user profiles and sync your claim history to MongoDB Atlas.
                  </p>
                </div>
                <div className="flex gap-3 pt-2">
                  <Button onClick={() => openAuthModal("login")} className="rounded-xl">
                    <LogIn className="size-4 mr-2" /> Sign In
                  </Button>
                  <Button variant="outline" onClick={() => openAuthModal("register")} className="rounded-xl">
                    Create Account
                  </Button>
                </div>
              </div>
            )}
          </SectionCard>

          {/* AI Verification Parameters Card */}
          <SectionCard title="Verification & AI Model Settings">
            <form onSubmit={handleSaveSettings} className="space-y-5">
              <div className="grid gap-5 sm:grid-cols-2">
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <Label htmlFor="min-similarity" className="text-xs font-medium">
                      Evidence Similarity Threshold
                    </Label>
                    <span className="font-mono text-xs font-semibold text-primary">
                      {Math.round(minSimilarity * 100)}%
                    </span>
                  </div>
                  <input
                    id="min-similarity"
                    type="range"
                    min="0.2"
                    max="0.9"
                    step="0.05"
                    value={minSimilarity}
                    onChange={(e) => setMinSimilarity(parseFloat(e.target.value))}
                    className="w-full accent-primary cursor-pointer"
                  />
                  <p className="text-xs text-muted-foreground">
                    Minimum semantic similarity required before evidence is accepted.
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="top-k" className="text-xs font-medium">
                    Evidence Retrieval Top-K
                  </Label>
                  <Select
                    value={String(topK)}
                    onValueChange={(val) => setTopK(parseInt(val, 10))}
                  >
                    <SelectTrigger id="top-k" className="h-10 rounded-xl">
                      <SelectValue placeholder="Select top-k" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="3">Top 3 documents</SelectItem>
                      <SelectItem value="5">Top 5 documents (Recommended)</SelectItem>
                      <SelectItem value="8">Top 8 documents</SelectItem>
                      <SelectItem value="10">Top 10 documents</SelectItem>
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-muted-foreground">
                    Number of candidate passages extracted during dense retrieval.
                  </p>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="pref-model" className="text-xs font-medium">
                  Embedding Model
                </Label>
                <Select
                  value={preferredModel}
                  onValueChange={(val) => setPreferredModel(val)}
                >
                  <SelectTrigger id="pref-model" className="h-10 rounded-xl font-mono text-xs">
                    <SelectValue placeholder="Select model" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="sentence-transformers/all-MiniLM-L6-v2">
                      sentence-transformers/all-MiniLM-L6-v2 (Default Fast)
                    </SelectItem>
                    <SelectItem value="sentence-transformers/all-mpnet-base-v2">
                      sentence-transformers/all-mpnet-base-v2 (High Precision)
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="flex items-center justify-between p-3 rounded-xl bg-muted/40 border border-border">
                <div className="space-y-0.5">
                  <Label htmlFor="auto-save" className="text-sm font-medium cursor-pointer">
                    Auto-save Verification History
                  </Label>
                  <p className="text-xs text-muted-foreground">
                    Automatically record all verified claims to MongoDB Atlas
                  </p>
                </div>
                <Switch
                  id="auto-save"
                  checked={autoSaveHistory}
                  onCheckedChange={setAutoSaveHistory}
                />
              </div>

              <div className="flex justify-end pt-2">
                <Button type="submit" disabled={savingSettings} className="rounded-xl h-10 px-5">
                  <Save className="size-4 mr-2" />
                  {savingSettings ? "Saving..." : "Save Preferences"}
                </Button>
              </div>
            </form>
          </SectionCard>
        </div>

        {/* Right column: MongoDB Atlas & System Status */}
        <div className="space-y-6">
          {/* MongoDB Atlas Status Card */}
          <SectionCard title="MongoDB Atlas Storage">
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 rounded-xl bg-muted/50 border border-border">
                <div className="flex items-center gap-3">
                  <div className={`grid size-9 place-items-center rounded-xl ${
                    health?.mongodb_connected ? "bg-emerald-500/10 text-emerald-500" : "bg-amber-500/10 text-amber-500"
                  }`}>
                    <Database className="size-4.5" />
                  </div>
                  <div>
                    <p className="text-xs font-semibold">Database Engine</p>
                    <p className="text-xs text-muted-foreground">{health?.mongodb_mode || "Checking..."}</p>
                  </div>
                </div>
                <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-semibold ${
                  health?.mongodb_connected
                    ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                    : "bg-amber-500/10 text-amber-600 dark:text-amber-400"
                }`}>
                  <span className={`size-1.5 rounded-full ${health?.mongodb_connected ? "bg-emerald-500 animate-pulse" : "bg-amber-500"}`} />
                  {health?.mongodb_connected ? "Connected" : "Fallback Mode"}
                </span>
              </div>

              <div className="space-y-2">
                <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Atlas Collections
                </p>
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div className="rounded-xl border border-border bg-card p-2.5">
                    <p className="text-base font-bold text-foreground">{health?.stats?.users_count ?? 0}</p>
                    <p className="text-[11px] text-muted-foreground">users</p>
                  </div>
                  <div className="rounded-xl border border-border bg-card p-2.5">
                    <p className="text-base font-bold text-foreground">{health?.stats?.history_count ?? 0}</p>
                    <p className="text-[11px] text-muted-foreground">history</p>
                  </div>
                  <div className="rounded-xl border border-border bg-card p-2.5">
                    <p className="text-base font-bold text-foreground">{health?.stats?.settings_count ?? 0}</p>
                    <p className="text-[11px] text-muted-foreground">settings</p>
                  </div>
                </div>
              </div>

              <div className="rounded-xl border border-border/80 bg-accent/30 p-3 space-y-1.5 text-xs text-muted-foreground">
                <div className="flex items-center gap-1.5 font-semibold text-foreground">
                  <Layers className="size-3.5 text-primary" />
                  <span>3-Collection Architecture</span>
                </div>
                <p className="leading-relaxed">
                  All user profiles, verifications, and custom preferences are indexed and segregated per user account.
                </p>
              </div>

              <Button
                variant="outline"
                size="sm"
                onClick={() => void loadHealth()}
                disabled={refreshingHealth}
                className="w-full rounded-xl"
              >
                <Activity className="size-3.5 mr-2" />
                {refreshingHealth ? "Checking..." : "Refresh MongoDB Status"}
              </Button>
            </div>
          </SectionCard>

          {/* Backend AI System Status */}
          <SectionCard title="AI Verification Stack">
            <dl className="space-y-3 text-sm">
              <div className="flex justify-between items-center">
                <dt className="text-muted-foreground">Backend API</dt>
                <dd className="font-semibold text-xs inline-flex items-center gap-1 text-emerald-600 dark:text-emerald-400">
                  <CheckCircle2 className="size-3.5" /> Running
                </dd>
              </div>
              <div className="flex justify-between items-center">
                <dt className="text-muted-foreground">SciFact Corpus</dt>
                <dd className="text-xs font-medium">
                  {health?.scifact_corpus_available ? (
                    <span className="text-emerald-600 dark:text-emerald-400">Available</span>
                  ) : (
                    <span className="text-amber-500">Unavailable</span>
                  )}
                </dd>
              </div>
              <div className="flex justify-between items-center">
                <dt className="text-muted-foreground">SciFact Local Model</dt>
                <dd className="text-xs font-medium">
                  {health?.scifact_model_available ? (
                    <span className="text-emerald-600 dark:text-emerald-400">Available</span>
                  ) : (
                    <span className="text-muted-foreground">Baseline Mode</span>
                  )}
                </dd>
              </div>
            </dl>
          </SectionCard>
        </div>
      </div>
    </AppShell>
  );
}
