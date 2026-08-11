import { createFileRoute } from "@tanstack/react-router";

import { AppShell } from "@/components/app/app-shell";
import { PageHeader, SectionCard } from "@/components/app/ui-kit";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { currentUser, retrievalSources } from "@/data/mock";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export const Route = createFileRoute("/settings")({
  head: () => ({
    meta: [
      { title: "Settings — AI Hallucination Mitigation System" },
      {
        name: "description",
        content: "Manage your profile, default retrieval sources and verification preferences.",
      },
      { property: "og:title", content: "Settings — AI Hallucination Mitigation System" },
      { property: "og:description", content: "Profile and verification preferences." },
    ],
  }),
  component: SettingsPage,
});

function SettingsPage() {
  return (
    <AppShell>
      <PageHeader title="Settings" description="Manage your profile and verification preferences." />

      <div className="grid gap-6 lg:grid-cols-2">
        <SectionCard title="Profile">
          <div className="flex flex-col gap-4">
            <div>
              <Label htmlFor="name">Full name</Label>
              <Input id="name" defaultValue={currentUser.name} className="mt-2 h-11 rounded-xl" />
            </div>
            <div>
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" defaultValue={currentUser.email} className="mt-2 h-11 rounded-xl" />
            </div>
            <Button className="mt-2 w-fit rounded-xl">Save changes</Button>
          </div>
        </SectionCard>

        <SectionCard title="Verification defaults">
          <div className="flex flex-col gap-5">
            <div>
              <Label>Default retrieval source</Label>
              <Select defaultValue={retrievalSources[0]}>
                <SelectTrigger className="mt-2 h-11 w-full rounded-xl">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {retrievalSources.map((s) => (
                    <SelectItem key={s} value={s}>
                      {s}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <label className="flex items-center justify-between gap-4 text-sm font-medium">
              Always build a knowledge graph
              <Switch defaultChecked />
            </label>
            <label className="flex items-center justify-between gap-4 text-sm font-medium">
              Require at least two sources
              <Switch defaultChecked />
            </label>
            <label className="flex items-center justify-between gap-4 text-sm font-medium">
              Email me weekly accuracy reports
              <Switch />
            </label>
          </div>
        </SectionCard>
      </div>
    </AppShell>
  );
}
