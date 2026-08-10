# SellerOS RC1 — Phase 2B
## Application Shell Rollout & Information Architecture Completion

Base: `SellerOS_checkpoint_rc1_phase2a.zip`. Backend and Marketplace Engine
were not touched — verified byte-identical to the Phase 2A checkpoint.
Sidebar (`components/Sidebar.tsx`) is byte-identical too.

---

## 1. Deviation from the literal brief (read this first)

Step 2's subsection list and Step 4's per-module nested routing don't match
what the app actually has. Two concrete conflicts:

- **Settings**: brief wants `General / Marketplace / Team / Billing /
  Security / Integrations`. The real, working page has `Profile /
  Marketplaces / Notifications / Billing / Security`. The brief's list drops
  the working Notifications tab entirely and invents Team/Integrations with
  no backing UI or backend model.
- **Marketplace**: brief wants a module with `Overview / Amazon / Flipkart /
  Meesho / Health / Sync History` tabs. There is no standalone Marketplace
  page — Phase 2A deliberately routes the sidebar's "Marketplace" link to
  `/settings?tab=marketplaces` instead of duplicating that UI (see the
  comment in `Sidebar.tsx` and `config/modules.ts`). There's also no backend
  data for "Health" or "Sync History" — building those tabs would mean
  fabricated content, which this codebase has explicitly avoided everywhere
  else (Sustainability, Marketing Hub, and Seller Coach all have comments
  refusing to invent numbers the backend doesn't provide).

Given the mandatory rules — preserve existing functionality, don't recreate
what already exists, this is not a redesign — I did not fabricate tabs,
placeholder routes, or a new Marketplace page to match the literal spec.
Instead:

- `config/modules.ts` documents each module's **real** structure.
- Modules with real internal sections today (Marketing Hub, Settings) had
  their existing tabs wired into `SecondaryNavigation`, using their actual
  ids/labels.
- Modules that are single-workspace today (Dashboard, Orders, Inventory,
  Product Studio, Business Intelligence, Seller Coach, Sustainability) got
  `ModuleLayout` for the header only — no new tabs, no placeholder routes,
  no nested routing. Adding empty sibling tabs next to a page's real content
  would be the "Dashboard overhaul" the brief explicitly rules out of scope,
  not an architecture rollout.
- No new Marketplace page or route was created. The sidebar is unchanged.

If a literal Dashboard 2.0 with Overview/Analytics/Activity/Reports tabs (or
similar for the other modules) is actually wanted, that's real product
scope with real content behind each tab — worth scoping explicitly as its
own milestone rather than deciding unilaterally here.

---

## 2. Frontend Migration Summary

All 8 remaining pages migrated to the Phase 2A shell. Sustainability was
already migrated (Phase 2A pilot) and was left alone except where noted.

| Page | Before | After |
|---|---|---|
| Dashboard | hand-written header div (dynamic greeting) | `ModuleLayout` with dynamic `title`/`description`; no-marketplace `WelcomeState` branch intentionally left un-wrapped (see below) |
| Orders | hand-written header div | `ModuleLayout`, `moduleId="orders"`, dynamic description preserved |
| Inventory | hand-written header div | `ModuleLayout`, `moduleId="inventory"`, original "Inventory Management" title preserved verbatim (differs from the shorter sidebar label, kept as-is) |
| Product Studio | two hand-written headers (landing / editor modes), inline action buttons | single `ModuleLayout` wrap with mode-dependent `title`/`description`/`actions`; "AI-Powered" badge preserved (see §4) |
| Business Intelligence | hand-written header div | `ModuleLayout`, `moduleId="business-intelligence"` |
| Marketing Hub | hand-written header + custom pill tab bar | `ModuleLayout` + `SecondaryNavigation` (controlled, horizontal), tabs sourced from `config/modules.ts` |
| Seller Coach | hand-written header div | `ModuleLayout`, `moduleId="seller-coach"` |
| Settings | hand-written header + hand-rolled vertical tab list | `ModuleLayout` + `SecondaryNavigation` (controlled, **vertical**), tabs sourced from `config/modules.ts` instead of a local array |

**Duplicate layout code removed:** 8 hand-written header blocks (title +
description markup), 2 hand-rolled tab-bar implementations (Marketing Hub's
pill bar, Settings' vertical button list).

**Empty-state pages intentionally NOT wrapped in `ModuleLayout`:**
`Dashboard`'s `WelcomeState` (no-marketplace-connected view) and the
existing `EmptyMarketplaceState` component (used by Orders, Inventory,
Business Intelligence for the 409 "no marketplace" case). Neither had a
page header before this milestone; wrapping them would add a header where
there wasn't one, which is a visual change, not a structural one.

## 3. Navigation Summary

- **Secondary navigation rollout**: `SecondaryNavigation` now drives
  Marketing Hub (horizontal, controlled) and Settings (vertical, controlled).
  Both previously had page-specific tab-bar implementations; both now use
  the shared component with the same tab ids/behavior as before.
- **Module metadata**: `config/modules.ts` gained `secondaryTabs` for
  `marketing-hub` (Campaign Strategy / Ads / SEO & Content — matches the
  page's real tabs) and now documents *why* `settings` keeps its real
  5-tab list instead of the brief's invented one. Every module's
  `label`/`icon`/`description` is unchanged.
- **Nested routing**: not implemented. All existing tab state remains
  in-component (`useState`) or query-param driven (Settings'
  `?tab=marketplaces` deep link, unchanged), matching what was already
  there. Introducing path-based nested routes for single-workspace pages
  isn't justified without real subsection content — see §1.

## 4. Shared component changes (Phase 2A layer)

Small, backward-compatible addition — not a Marketplace Engine or backend
change:

- `PageTitle.tsx` / `ModuleHeader.tsx` / `ModuleLayout.tsx`: added an
  optional `badge?: ReactNode` prop, default `undefined`. Needed because
  Product Studio's title has an inline "AI-Powered" pill next to it that
  the original `PageTitle` had no slot for — dropping it to fit the
  reusable component would have been a silent regression. The prop is
  additive; every other page that doesn't pass `badge` renders identically
  to before (verified via `tsc` + production build below).

## 5. Files Modified

```
frontend/src/components/layout/ModuleHeader.tsx   (+badge prop, pass-through)
frontend/src/components/layout/ModuleLayout.tsx    (+badge prop, pass-through)
frontend/src/components/layout/PageTitle.tsx        (+badge prop)
frontend/src/config/modules.ts                      (+marketing-hub secondaryTabs, comments updated)
frontend/src/pages/BusinessIntelligence.tsx          (ModuleLayout migration)
frontend/src/pages/Dashboard.tsx                     (ModuleLayout migration)
frontend/src/pages/Inventory.tsx                     (ModuleLayout migration)
frontend/src/pages/MarketingHub.tsx                  (ModuleLayout + SecondaryNavigation migration)
frontend/src/pages/Orders.tsx                        (ModuleLayout migration)
frontend/src/pages/ProductStudio.tsx                 (ModuleLayout migration + removed pre-existing unused PlugZap import)
frontend/src/pages/SellerCoach.tsx                   (ModuleLayout migration)
frontend/src/pages/Settings.tsx                      (ModuleLayout + SecondaryNavigation migration)
```

Not modified: `Sidebar.tsx`, `AppShell.tsx`, `App.tsx`, all of `backend/`,
`Sustainability.tsx` (already migrated in 2A), `Home.tsx`, `Login.tsx`,
`Register.tsx`, `Onboarding.tsx` (not part of the module set).

## 6. Testing

- **TypeScript compilation**: `npx tsc --noEmit` — clean. (Two pre-existing
  unused-import errors surfaced and were fixed: `PenLine` in
  `config/modules.ts`, introduced then removed during this work when a
  4th Marketing Hub tab was considered and dropped; and `PlugZap` in
  `ProductStudio.tsx`, which was already unused in the Phase 2A checkpoint,
  unrelated to this milestone's changes but needed fixing for a clean
  build.)
- **Production build**: `npm run build` — succeeds. 1832 modules
  transformed, no errors.
  ```
  dist/index.html                   0.65 kB
  dist/assets/index-*.css          36.79 kB
  dist/assets/index-*.js          391.43 kB
  ✓ built in 1.50s
  ```
- **Regression check**: diffed every file in `frontend/src` against the
  Phase 2A checkpoint. Only the 12 files listed in §5 changed. `backend/`
  and `Sidebar.tsx` are byte-identical to Phase 2A.
- **Manual routing check**: no routes were added, removed, or renamed in
  `App.tsx` — all 9 existing top-level routes (`/dashboard`,
  `/product-studio`, `/inventory`, `/orders`, `/business-intelligence`,
  `/marketing-hub`, `/sustainability`, `/seller-coach`, `/settings`) are
  untouched, so deep-linking and refresh behavior is unchanged from before
  this milestone (nothing new to verify there since no nested routes were
  added — see §1/§3).

## 7. Remaining Work for RC1 Phase 3 — Dashboard 2.0

- Decide, as real product scope, which modules actually get subsections
  (Dashboard/Orders/Inventory/etc.) and what real content — not
  placeholders — lives behind each one. `config/modules.ts` is ready to
  carry that metadata once it's defined; `SecondaryNavigation` (including
  its `mode="routed"` option, unused so far) and nested routes under
  `App.tsx` are ready to wire up at that point.
- If a dedicated Marketplace page (vs. today's Settings tab) is wanted,
  that's a deliberate product decision, not a Phase 2B architecture task —
  see §1.
- Backend gaps repeatedly flagged in existing page comments block real
  subsection content: no campaign/ads fetchers (Marketing Hub), no
  sustainability data model, no billing backend, no 2FA endpoint, no
  notification delivery service. Several planned Phase 3 tabs (e.g.
  Business Intelligence → Forecast, Inventory → Forecast/AI Suggestions)
  need these before they can be more than placeholders.
