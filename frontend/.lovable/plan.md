## AI Hallucination Mitigation System — UI Build

A pixel-faithful, production-quality AI SaaS dashboard matching the reference image, built as a fully interactive frontend with realistic mock data (no backend yet).

### Stack note (important)
This project runs on **TanStack Start + TanStack Router**, not React Router. Routing will use TanStack file routes — same URLs, same behavior, but React Router won't be installed. Everything else matches your spec: React 19 + Vite, TypeScript, Tailwind v4, shadcn/ui, Lucide, Framer Motion, Recharts, React Flow.

### Design system
Tokens defined in `src/styles.css` (oklch equivalents of your hex values):
- primary `#6C4CF5`, secondary `#8B7BFF`, accent `#ECE9FF`, background `#F8F9FD`, card white
- text `#1E1E2E` / `#6B7280`; success `#22C55E`, warning `#F59E0B`, error `#EF4444`
- radius 16px, soft card shadow + hover elevation shadow, 24px spacing scale
- Inter loaded via `<link>` in the root route; full dark-mode variant for the toggle

### App shell
- Fixed 280px sidebar: product mark + title, 9 nav items with active purple pill state, bottom promo card ("AI Accuracy, Built on Real Evidence" + illustration), dark-mode switch, logout
- Sticky 72px navbar with blur: hamburger (collapses sidebar to icon rail / off-canvas on mobile), centered search with `Ctrl + K` hint and command palette, notification bell, avatar + username dropdown
- Shared layout route wrapping all pages, with Framer Motion page transitions

### Pages
1. **Dashboard** `/` — welcome heading with robot illustration, Start New Verification card (input + upload + purple CTA), 4 stat cards with hover lift, Recent Verifications table with colored result badges + "View all", System Overview 4-step flow with arrows
2. **New Verification** `/new-verification` — two columns: claim textarea with `0/4000` counter and example chips; upload card with drag-drop zone, Browse Files, uploaded-file row with size + remove; retrieval-source select; Advanced Options accordion; wide Verify / Ask button
3. **Ask a Question** `/ask` — chat interface, New Chat button, purple user bubbles, white assistant cards with sources list + View Sources, sticky composer with send button, typing animation, auto-scroll
4. **Answer Details** `/answer/$id` — question, answer, result badge, confidence score with animated progress bar + High label, supporting-evidence accordion with View buttons, Share action
5. **History** `/history` — search, result filter, filter icon, table (Type / Claim / Result / Confidence / Date / view action), pagination
6. **Uploads** `/uploads` — drag-drop uploader with progress, documents table (filename, type, date, status, size, preview, delete)
7. **Knowledge Graph** `/knowledge-graph` — React Flow canvas, purple custom nodes, curved edges, zoom/pan/minimap, node search, click opens entity detail side panel
8. **Sources** `/sources` — cards for Wikipedia, Research Papers, Uploaded Documents, Government Sources, Books with snippet, relevance score bar, Open Source button
9. **Settings** `/settings` and **About Us** `/about` — consistent styled pages so every sidebar link resolves

### Data
Typed mock fixtures in `src/data/` (verifications, chat threads, evidence, graph nodes, uploads, sources) driving all pages, plus loading skeletons. Wiring to Lovable Cloud (real storage, auth, AI verification) is a natural next step once the UI is approved.

### Quality
- Reusable components per section (`StatCard`, `ResultBadge`, `SectionCard`, `DataTable`, `ConfidenceBar`, `EvidenceAccordion`, …)
- Framer Motion fade/slide-up on mount, hover lift, animated bars, micro-interactions
- Responsive: sidebar collapses, grids stack, tables become cards on mobile
- Accessibility: semantic HTML, ARIA labels, keyboard nav, visible focus rings, contrast-checked palette
- Per-route `head()` metadata with unique titles/descriptions
