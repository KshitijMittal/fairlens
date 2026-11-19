# FairLens — UI/UX Specification

| | |
|---|---|
| **Version** | 3.3 (19 Nov: the dropzone is the hero; landing preview and separate upload panel removed) |
| **Status** | **Built.** R1–R4 landed in the working tree; §13.4 lists the few places the code is simpler than this spec |
| **Baseline** | `docs/PRD.md` v2.3, `docs/TRD.md` v2.4, `docs/APP_FLOW.md` v2.3, `docs/BACKEND_SCHEMA.md` v2.2 |
| **Relationship to the code** | Copy in §7 is server-authored and must match `backend/app/core/report_text.py`. Everything else is frontend-only |

---

## 0. How to read this document

- **§1–§2** say what the interface is for and what it looks like in one sentence. Read these before changing anything.
- **§3–§5** are the system: type, colour, space, and the information architecture of every screen.
- **§6** is component-by-component anatomy. **§7** is the copy, and it is not editable by the person implementing it.
- **§8–§11** are constraints: motion, print, accessibility, performance. **§12–§13** are risks and the migration plan.

Where this document and the running code disagree, the code is what users see; the delta is listed in §13.4. Do not quote a target as shipped.

---

## 1. Principles

### 1.1 What was wrong with v2.2

Named, so the next version does not repeat it:

1. **Type carried the personality, and the personality was wrong.** A 56 px single-weight serif read as a magazine, not a tool.
2. **Sparse pages read as unfinished.** 96 px gaps and two content blocks left the landing looking like a placeholder.
3. **It did not look like software.** Documents instead of product surfaces; no chrome, no density, no clear action hierarchy.
4. **Hierarchy was flat.** Headline, samples and upload had similar weight; the eye had nowhere to land.
5. **The report was prose-heavy.** Long sentences between figures made the verdict hard to scan.

### 1.2 The five rules for v3.0

| Rule | Consequence |
|---|---|
| **The verdict in one glance** | Every report opens with the state, the headline, and three figures. Detail comes after |
| **Density with air** | 64 px between sections, 24 px inside panels. Air is structure, not emptiness |
| **Serif is gone** | One sans family for everything, one mono family for data. Hierarchy comes from size, weight and colour |
| **Chrome is quiet** | One app bar, hairline borders, no shadows, no gradients. The data is the only loud thing |
| **No decoration without meaning** | No illustrations, no stock imagery, no invented logos, no KPI-tile dashboard, no feature grid of icons |

### 1.3 Voice

Short, plain, active. A sentence states a fact or an action. Numbers beat adjectives. The product never congratulates the user and never apologises for a finding.

---

## 2. Direction: precise product UI

### 2.1 References, and what is borrowed

| Reference | Borrowed | Not borrowed |
|---|---|---|
| **Linear** | Dense rows, calm neutral chrome, one accent, keyboard-first polish | Command palette, sidebar navigation (the app has three screens) |
| **Vercel dashboard** | Neutral zinc palette, monospace metadata, 8 px radii, flat panels | Dark-first styling as the only mode |
| **Stripe dashboard** | Form and table discipline, inline errors, clear primary/secondary actions | Marketing illustration, multi-level navigation |
| **GitHub Primer** | Accessibility baseline, focus treatment, disabled states | Comment threads, avatars, labels-as-decorations |

### 2.2 What it looks like in one sentence

**A neutral, tightly-set data tool: white and zinc surfaces, hairline borders, one blue accent, all-sans type, numbers in tabular figures, and a single clear action per screen.**

### 2.3 What changed from v2.2

| Area | v2.2 | v3.0 |
|---|---|---|
| Display type | Instrument Serif, one weight | Geist Sans 600; serif deleted |
| Base type | IBM Plex Sans 17/27 | Geist Sans 15/24 |
| Data type | none | Geist Mono 13/20 for IDs, thresholds, engine facts |
| Page ground | warm paper `#faf9f6` | neutral `#fafafa` |
| Accent | petrol `#123b4f` | blue `#2563eb` (links, focus, selection) |
| Surfaces | flat panels, 2 px radius | panels and cards, 8 px radius, 1 px border, no shadow |
| Section rhythm | 96 px | 64 px |
| Landing | hero + two sections | app bar + hero with the dropzone + samples + footer |
| Report order | verdict → groups → checks → method | verdict + KPI → checks → groups → meaning → repairs (M4) → method, with a sticky aside |
| Contents strip | designed, never built | built as the report aside |
| Verdict rows | editorial rows, no chips | check rows with state chips and figures in a fixed grid |

---

## 3. Type

### 3.1 Families

| Role | Family | Weights | Source |
|---|---|---|---|
| Interface and display | **Geist Sans** | 400, 500, 600 | SIL OFL 1.1, self-hosted woff2, Latin subset, `swap` |
| Data and metadata | **Geist Mono** | 400, 500 | Same licence, Latin subset |

Rules:

- **Two files minimum, four maximum.** Geist Sans 400, 500, 600 and Geist Mono 400. No italic — nothing in the product needs emphasis that a weight cannot carry.
- **No third family.** Geist Mono is used only for identifiers, thresholds, engine facts, JSON and file facts. It is never used for prose.
- **Every figure is tabular.** `font-variant-numeric: tabular-nums` on all numbers, including chart labels and tables.
- **Fallbacks are metric-compatible.** `font-family: var(--font-sans), "Inter", system-ui, sans-serif` and `var(--font-mono), ui-monospace, monospace`.

### 3.2 Scale

| Token | Size / line | Weight | Tracking | Use |
|---|---|---|---|---|
| `figure-xl` | 40 / 44 | 600 | -0.03em | The single biggest number on a screen (report KPI strip) |
| `display` | 40 / 44 | 600 | -0.03em | Landing `h1`; report verdict headline |
| `h1` | 32 / 40 | 600 | -0.02em | Auth and utility page `h1` |
| `h2` | 24 / 32 | 600 | -0.015em | Section titles |
| `h3` | 18 / 26 | 600 | -0.01em | Card and panel titles |
| `body` | 15 / 24 | 400 | 0 | Everything readable |
| `body-strong` | 15 / 24 | 500 | 0 | Row names, field values, lead-ins |
| `small` | 13 / 20 | 400 | 0 | Supporting lines, captions, links in nav |
| `label` | 12 / 16 | 500 | 0.06em, uppercase | Eyebrows, table headers, KPI labels, form section labels |
| `figure` | 24 / 30 | 600 | -0.02em | Check-row figures, table totals |
| `mono` | 13 / 20 | 400 | 0 | IDs, thresholds, engine version, file facts |

Line length: body text is capped at **68ch**. No paragraph in the report exceeds **two lines** at 1440 px; anything longer becomes a list or moves into the method.

### 3.3 Hierarchy without decoration

- Size does the work: `display` → `h2` → `body-strong` → `body` → `small`.
- Weight only steps 400 → 500 → 600. Nothing is 700.
- Colour steps `ink` → `ink-muted` → `ink-faint`. A heading and its supporting line differ in size and colour, never in underline or colour alone.
- The only uppercase text is `label`. Nothing else shouts.

---

## 4. Colour and theme

### 4.1 Light tokens

| Token | Value | Use |
|---|---|---|
| `--canvas` | `#fafafa` | Page ground |
| `--surface` | `#ffffff` | Panels, cards, inputs, app bar |
| `--sunken` | `#f4f4f5` | Inset areas, table hover, disabled fill |
| `--ink` | `#18181b` | Primary text and primary button fill |
| `--ink-muted` | `#52525b` | Supporting text |
| `--ink-faint` | `#71717a` | Labels, metadata, placeholders |
| `--hairline` | `#e4e4e7` | Borders, rules, table lines |
| `--hairline-strong` | `#d4d4d8` | Hover borders, input focus-adjacent |
| `--accent` | `#2563eb` | Links, focus ring, selected controls |
| `--accent-hover` | `#1d4ed8` | Link and button hover |
| `--accent-tint` | `#eff6ff` | Selection and informational tint |
| `--fail` | `#b91c1c` | Fail text and glyph |
| `--fail-tint` | `#fef2f2` | Fail banner and chip fill |
| `--warn` | `#92400e` | Warn text and glyph |
| `--warn-tint` | `#fffbeb` | Warn banner and chip fill |
| `--inconclusive` | `#475569` | Inconclusive text and glyph |
| `--inconclusive-tint` | `#f1f5f9` | Inconclusive banner and chip fill |
| `--pass` | `#15803d` | Pass text and glyph |
| `--pass-tint` | `#f0fdf4` | Pass banner and chip fill |

### 4.2 Dark tokens

Equal weight, not an inversion. The verdict hues are lightened; the ground is neutral near-black.

| Token | Value |
|---|---|
| `--canvas` | `#09090b` |
| `--surface` | `#111113` |
| `--sunken` | `#18181b` |
| `--ink` | `#fafafa` |
| `--ink-muted` | `#a1a1aa` |
| `--ink-faint` | `#8b8b94` |
| `--hairline` | `#27272a` |
| `--hairline-strong` | `#3f3f46` |
| `--accent` | `#60a5fa` |
| `--accent-hover` | `#93c5fd` |
| `--accent-tint` | `#10243d` |
| `--fail` | `#fca5a5` |
| `--fail-tint` | `#2a1416` |
| `--warn` | `#fcd34d` |
| `--warn-tint` | `#2a2110` |
| `--inconclusive` | `#cbd5e1` |
| `--inconclusive-tint` | `#1e293b` |
| `--pass` | `#86efac` |
| `--pass-tint` | `#12261a` |

### 4.3 How the theme is resolved (shipped)

| Cookie value | What the server renders | What supplies the colours |
|---|---|---|
| `light` | `<html lang="en" data-theme="light">` | Light tokens |
| `dark` | `<html lang="en" data-theme="dark">` | Dark tokens |
| `system` or absent | `<html lang="en">` | `@media (prefers-color-scheme: dark)` |

The cookie is read in the root layout before the first byte, so there is no flash and no inline script (TRD §11.1 keeps `script-src 'self'`). Tokens live on `:root`; every screen shares one theme. Every route is dynamic as a result — accepted because the whole app is themed. The control itself is `/account`, M5 (A17).

### 4.4 Verdict colour usage

- The state is always carried by **a word, a glyph and a colour**, in that order. Colour alone never encodes state (A2).
- A tinted panel is the only large area of verdict colour. Text sits at full state colour on its own tint.
- The accent blue never appears inside a verdict panel. State colours never appear on buttons, links or focus rings.
- Pass is never used for “success” of an unrelated action; success text is `--ink-muted`.

### 4.5 Contrast budget

Asserted in both themes by `contrast.spec.ts`:

- Each verdict colour on its own tint, and on `canvas` — eight pairs.
- `ink` on `canvas`.
- `ink-muted` on `canvas`.
- `accent` on `canvas`.
- Every pair ≥ 4.5:1. Any palette edit that breaks one fails CI.

---

## 5. Space, layout and information architecture

### 5.1 Spacing scale

4 px base: `4 · 8 · 12 · 16 · 24 · 32 · 48 · 64`.

| Use | Value |
|---|---|
| Inside a control | 12 |
| Label to input | 6 |
| Between related controls | 16 |
| Panel padding | 20 (compact) / 24 (default) |
| Between blocks in a section | 32 |
| Between sections | 64 |
| App bar height | 56 |
| Page gutter, mobile / tablet / desktop | 24 / 40 / 64 |
| Container max width | 1120 px (70rem) |
| Report reading column | 720 px max; 690 at 1280 px once the aside and gutter are taken out |
| Report aside | 280 px, 48 px gap |
| Body measure | 68ch |

Radii: `8px` panels, cards, inputs; `6px` chips and buttons; `4px` small marks. No pills. No shadows anywhere; hover is a border and a fill change.

### 5.2 Landing page

```
┌ app bar 56 ───────────────────────────────────────────────────────────────┐
│ FairLens                                            [Analyse a file]      │
├───────────────────────────────────────────────────────────────────────────┤
│ HERO — split, 64 top, 64 bottom                                           │
│                                                                           │
│  Data fairness, before training         ┌ dropzone ────────────────────┐  │
│  Know what your data teaches            │        ↑                    │  │
│  before a model learns it.              │ Drop a CSV or XLSX file      │  │
│                                         │ here, or click to browse     │  │
│  FairLens reads a CSV or XLSX, trains   │                              │  │
│  a throwaway model on it, and reports   └──────────────────────────────┘  │
│  where it would pass on unequal         CSV or XLSX · 50 MB · not kept    │
│  treatment — five checks, one verdict,  No file to hand? Run a sample     │
│  every figure explained.                                                  │
├───────────────────────────────────────────────────────────────────────────┤
│ SAMPLES — “Three datasets, three known answers”                           │
│ Three cards in a row: name · shape · one line · expected chip · [Run]      │
├───────────────────────────────────────────────────────────────────────────┤
│ FOOTER — privacy line · GitHub link · disclaimer                          │
└───────────────────────────────────────────────────────────────────────────┘
```

Section rules:

- **Three sections, and the tool is the hero.** The landing is the headline plus the dropzone, the samples, and the footer. The upload panel that used to sit below the samples is gone: it was a second copy of the same control, reached by a button that only scrolled (v3.3).
- **The dropzone is the primary action, not a button that finds it.** It sits in the hero's second column, open and visible. There is no "Analyse a file" button above it, and none below.
- **Signed out, the same dropzone opens sign-in.** It stays in place, keeps its size and wording, and reads `Click to sign in — samples need no account` as its hint. No file input is rendered in that state, so the zone cannot pick a file before there is a session.
- **The app-bar action opens the dialog** (signed out) or returns to this dropzone (signed in, `/#analyse`). It is navigation chrome; the page itself has one action.
- There is no report preview on the landing: the three sample cards already state what a run produces, so a static report beside the headline showed the same idea twice.
- Hero is the only section with two columns. Everything below is one column at 1120 px.
- Samples are cards because each is a self-contained object; the section is a 3-column grid at ≥1024, stacked below.
- No “trusted by”, no testimonials, no logo strip, no illustration.

### 5.3 Report page

```
┌ report app bar 56 ────────────────────────────────────────────────────────┐
│ FairLens   loans.csv                                 [FAIL]   New analysis │
├───────────────────────────────────────────────────┬───────────────────────┤
│ MAIN 720                                          │ ASIDE 280 (sticky)    │
│                                                   │                       │
│ 01 Verdict                                        │ On this page          │
│ [FAIL chip]                                       │ 01 Verdict            │
│ This data would teach a model to treat            │ 02 Checks             │
│ people unequally.                                 │ 03 Who is affected    │
│ One supporting sentence (server, ≤ 2 lines).      │ 04 What this means    │
│                                                   │ 05 What to do (M4)    │
│ ┌ 0.66 ─────────┬ 21 pts ────────┬ 900 ─────────┐ │ 06 Method             │
│ │ Lowest ratio  │ Model gap      │ Rows analysed│ │                       │
│ └───────────────┴────────────────┴──────────────┘ │ Dataset               │
│ Privacy line                                      │ loans.csv             │
│ ───────────────────────────────────────────────── │ 900 rows · 8 columns  │
│ 02 Checks  (five compact rows, expandable)        │ engine 2.0.0          │
│ ───────────────────────────────────────────────── │ 17 Nov 2026           │
│ 03 Who is affected  (chart + data table + groups) │                       │
│ ───────────────────────────────────────────────── │                       │
│ 04 What this means  (amplification + affected)    │                       │
│ ───────────────────────────────────────────────── │                       │
│ 05 What to do  — M4, absent until built           │                       │
│ ───────────────────────────────────────────────── │                       │
│ 06 Method  (collapsed technical view)             │                       │
└───────────────────────────────────────────────────┴───────────────────────┘
```

Rules:

- **Order is by question:** what is the verdict, why (checks), who (groups), what does it mean, what to do, how (method). Checks before the chart because “did it fail?” precedes “where?”.
- The KPI strip carries exactly three figures: the lowest check ratio with its check code, the model gap in percentage points, and the rows analysed. If a figure does not exist for a run, its slot is omitted, never filled with a dash.
- The aside is the contents strip, finally built: jump links plus dataset facts. It is sticky, 56 px from the top, and hidden below 1024 px where the facts move into the verdict panel as a `small` line.
- The technical section is a `details` disclosure, closed by default; printing opens it (§9).
- Section numbers are generated from the list, not typed. Today the list is 01 verdict, 02 checks, 03 who is affected, 04 what this means, 05 method; repairs (M4) insert as 05 and push method to 06.
- The app bar carries the brand and the account actions only. It does **not** repeat the dataset name or the verdict chip: the banner and the aside already show both, and a third copy on one screen is noise. The dataset facts sit in the aside, with a one-line header above the verdict for screens below 1024 px.

### 5.4 Auth and utility screens

- **The sign-in surface is a dialog**, opened from the app bar or by clicking the hero dropzone while signed out — never by scrolling the visitor to a different part of the page. It is a native `<dialog>`: the browser supplies the focus trap, Escape, and the inert background.
- The dialog is 400 px wide, 12 px radius, `surface`, one hairline, no shadow; it rises 10 px and fades in 200 ms, and plays the reverse for 140 ms on close. The email field takes focus, not the close button.
- The dialog carries both modes. “Create one” and “Sign in” switch mode in place; no reload and no route change.
- `/login` and `/signup` still exist as 360 px columns and render the same `AuthForm`, so a bookmark, a reset link and the Google callback all keep working. They hold only `h1` at 32/40, one supporting line, the form and the links.
- Login: email, password, primary “Sign in”, secondary Google (only when the backend reports the provider), the mode switch and “Forgot your password?”.
- Signup: email, display name, password with live rules, primary “Create account”.
- Reset: either the request form or the new-password form, plus the confirmation state. Never both at once.
- A successful request replaces the form with a status block: a tick that draws itself, the address the link was sent to, “Change email”, and a way back. The copy says “if an account exists”, because the endpoint deliberately answers the same way for every address (F8-AC3) — a tick must not claim more than the server knows.
- A failed request shows the same mark in red inside the inline `notice`, above the action. Errors are inline, associated with the form, never a toast.
- Sign-in names the reason, because the visitor's next step differs: *No account uses this email* (sign up), *Incorrect password for this email* (retry or reset), *This account signs in with Google* (use the other button). Reset stays uniform; login does not, and the trade is recorded in APP_FLOW.

### 5.5 Confirmation and run log

Both replace the landing content in place once a file is selected, inside the 720 px column; the hero and lower sections disappear.

### 5.6 Responsive rules

| Breakpoint | Behaviour |
|---|---|
| ≥1081 | 64 px gutter, 1120 container, 720 + 48 + 280 report grid, sticky aside |
| 768–1080 | 40 px gutter, report goes one column and the aside moves under the method with a top hairline |
| 640-767 | 24 px gutter, landing hero stacks (dropzone below the copy), samples one column |
| <640 | One column everywhere; check rows stack code, name, figure and chip in one column; chart scrolls horizontally at 560 px min-width; app bar nav links collapse to "Sign in" + primary action |

The report's 720 + 48 + 280 measure needs 1048 px, so the single-column rule starts at 1080 rather than at a round device width — below it the aside would squeeze the reading column, not merely sit beside a narrower one.

Density rules: table rows are 40 px tall, check rows 64 px, cards 20 px padding. Touch targets are 44 px minimum whenever `(pointer: coarse)` matches, even though desktop buttons are 36 px.

---

## 6. Components

### 6.1 App bar

| Property | Specification |
|---|---|
| Height | 56 px, sticky, `surface`, 1 px bottom hairline |
| Brand | Wordmark only, 15/24 600, `ink`; links home |
| Primary action | 36 px, `ink` fill, 13/20 500 paper text, radius 6; “Analyse a file” |
| Signed out | One primary action, “Analyse a file”, which opens the auth dialog in place. No ghost “Sign in”: the primary already is it |
| Signed in | Display name or email, “Sign out” (ghost), primary action returning to the dropzone (`/#analyse`) |
| Mobile | Brand + primary action only |

### 6.2 Hero and dropzone

- Copy column: `display` headline (maximum 3 lines), `body` supporting line at `ink-muted` capped 52ch.
- Dropzone column: the product itself, `surface`, 1 px dashed `hairline-strong`, radius 8, 48/24 padding, capped at 440 px. One dashed frame only — the zone is the panel, with no border around a border.
- Under the zone: the constraint line and “No file to hand? Run a sample”, which links to the cards rather than repeating them.
- Signed out, no file input is rendered and the hint names the dialog it opens. The zone must never look disabled: the action is available, it just starts with sign-in, so it keeps `role="button"`, its tab stop, and its keyboard handling.
- There is no report preview. The sample cards below carry that job with real, runnable data (v3.3).

### 6.3 Sample card

| Element | Treatment |
|---|---|
| Container | `surface`, 1 px `hairline`, radius 8, padding 20, no shadow; hover `hairline-strong` |
| Title | `h3` 18/26 600 |
| Shape | `mono` 13/20 `ink-faint` — `1,440 rows · 6 columns` |
| Description | `small` 13/20 `ink-muted`, maximum 3 lines |
| Expected | State chip (`§6.8`) labelled `Expected: Pass` |
| Action | Secondary button “Run the analysis”, full width of the card footer |
| States | Busy: button reads “Running…” and is disabled; error: `notice` under the button |

### 6.4 Confirmation (shipped, restyled)

A two-column mapping panel, not a set of tiles:

```
┌ What we read ─────────────────┬ Tell us what it means ────────────────────┐
│ scholarship.csv               │ Outcome column     [ awarded        ▾ ]   │
│ 1,440 rows · 6 columns        │ Positive value     [ yes             ]    │
│ sheet: Awards                 │ Group column       [ region          ▾ ]  │
│ 2 groups · 1 factor column    │ □ Group ages into 10-year bands           │
└───────────────────────────────┴───────────────────────────────────────────┘
 Warnings / sampling choice, full width
 [Run analysis]  [Cancel]
```

- Left column is context: filename, rows × columns, sheet select when the workbook has more than one, group count, factor count, warnings.
- Right column is the task: outcome select, positive value input, group select, age-banding checkbox.
- Below 768 px the right column comes first; the left facts become a `small` line under the panel head.
- Group values stay behind a disclosure; **group rates are never shown here** (C1 spoiler).
- Warnings use the `warn` notice. A single-value demographic blocks the run with a `notice` and the claim “Change the demographic column to continue.”
- Above 50,000 rows, a required radio choice (sample vs all rows) disables Run analysis until chosen.
- `Change` is gone: the panel is always editable. The old read/edit toggle added a mode for no reason.

### 6.5 Run log (shipped, restyled)

A six-step stepper, not a scrolling list:

```
Running analysis                                 1 of 6        [Cancel]
▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
✓  Reading your file
✓  Cleaning and encoding
●  Training the stand-in model
○  Measuring fairness
○  Computing feature influence
○  Saving results
```

| Property | Specification |
|---|---|
| Container | `surface`, 1 px `hairline`, radius 8, padding 20 |
| Progress | 4 px track, `sunken`; fill `accent`; width = completed steps / 6 |
| Step row | 40 px; glyph column 20 px; label `body` 15/24; completed `ink-muted`, current `ink` 500, pending `ink-faint` |
| Glyphs | `✓` completed in `pass`; `●` current in `accent`; `○` pending in `ink-faint`. Never colour alone — the glyph and weight also change |
| Counter | `label` “3 of 6”, right-aligned in the head |
| Live region | `aria-live="polite"` on the step list; `aria-current="step"` on the current row |
| Content | The six backend stage labels, unchanged (§7.4). No fold lines, no durations, no invented text |
| Cancel | Destructive text button, disabled once the result frame arrives |
| Motion | The current dot pulses at 1.2 s; reduced motion makes it static |

### 6.6 The five checks index (landing)

A five-row table, not cards. Columns: `C1`–`C5` in `mono`/`label`, the question in `body-strong`, one `small` line explaining what a failure would mean. Rows separated by hairlines. No icons.

### 6.7 Buttons, inputs, links (shipped, restyled)

| Element | Specification |
|---|---|
| Primary | `ink` fill, `canvas` text, radius 6, height 36 desktop / 44 coarse, padding 0 16 |
| Secondary | `surface` fill, 1 px `hairline-strong`, `ink` text; hover border `ink` |
| Ghost | Transparent, `ink-muted`; hover `sunken` fill |
| Destructive | `fail` text, transparent; filled only inside a delete dialog |
| Link | `accent`, underline on hover only, `text-underline-offset: 3px` |
| Text button | `accent`, 13/20 500, underline on hover; used for “New analysis”, disclosures |
| Input / select | 40 px, 1 px `hairline`, radius 8, `surface`, 15 px text (16 px on mobile to prevent zoom), padding 0 12 |
| Label | 13/20 500, `ink`, 6 px above the input; sentence case, not caps |
| Focus | 2 px `accent` ring at 2 px offset on every interactive element; never removed without a replacement |
| Disabled | `ink-faint` text, `sunken` fill, `hairline` border, `cursor: not-allowed`; never opacity-faded |
| Hover | 90 ms colour/border only. No lift, no scale, no shadow |

### 6.8 Verdict banner and chips

| Element | Specification |
|---|---|
| Banner | State tint fill, 1 px `hairline`, radius 8, padding 24; headline `display` 40/44 in `ink`; supporting sentence `body` in `ink-muted` |
| Chip | 24 px high, 6 px radius, state tint fill, 1 px state border, 12/16 500 uppercase, glyph + word + colour |
| KPI strip | Three equal columns inside the banner, separated by 1 px state-tinted hairlines; figure 24/30 600 tabular, label `label` in state colour at 70% |
| Order | Chip → headline → sentence → KPI strip → privacy line |
| Never | A full-saturation red panel; a colour-only state; a percentage without its denominator |

### 6.9 Check row

| Column | Width | Content |
|---|---|---|
| Marker | 56 px | `C1` in `mono`; `core` in `label` under it for C1, C2, C5 |
| Name and meaning | 1fr | Name in `body-strong`; meaning in `body` `ink-muted`, maximum two lines |
| Figure | 120 px, right | `figure` 24/30 tabular; interval in `small` under it |
| State | 132 px, right | Chip; threshold in `small` under it, one condition per line |

- Expanded detail: the method paragraph (server), then group counts. Full-width, `sunken` background, 16 px padding, 1 px top hairline.
- Inconclusive rows are always expanded (A2 / PRD F4-AC3).
- Hover changes the row background to `sunken`; focus draws the ring around the summary button.
- There are no cards between rows: one hairline, 64 px minimum height.

### 6.10 Chart

- Horizontal bars, 20 px high, 4 px right radius, `ink` fill for data and `ink-faint` outline for the model.
- Axis at 0–100%, ticks every 25%, 12/16 `ink-faint` tabular, one hairline baseline.
- CI whiskers: 1 px `ink`, 6 px caps; the number sits in the table, not on the bar.
- Group labels left, 13/20 `ink`, truncated at 20ch with a title attribute.
- Legend: one `small` line under the title, not a colour box grid.
- The data table is always present under the chart in a `details`, open on print.
- Mobile: the chart scrolls horizontally at 560 px min-width inside a bordered container; the table is the primary reading on small screens.

### 6.11 Technical appendix

Same ground, no dark panel, no monospace prose. Order: methodology note, metric table, per-group table, model card, encoding and proxy decisions, sampling record, JSON download (M5). Tables are 13/20, numbers right-aligned tabular, captions `small` above, headers `label`.

### 6.12 Report aside

| Element | Specification |
|---|---|
| Position | Sticky, top 72 px, width 280 px; hidden <1024 px |
| On this page | `label` heading, 13/20 links in `ink-muted`, current section in `ink` with a 2 px accent left rule |
| Dataset | `label` heading; filename in `body-strong` truncating at 28ch; `small` facts: rows × columns, engine version, date |
| Behaviour | Static jump links; no scroll listener and no scroll tracking. Highlighting the current section was cut: it costs an observer to repeat what the page position already says |
| Print | Hidden |

### 6.13 States

| State | Treatment |
|---|---|
| Inspecting a file | A 720 px panel with a 20 px indeterminate bar and “Reading your file…”, `aria-live="polite"` |
| Empty report | Impossible by construction; a missing result is a 404 page with a `h1`, one line and a link home |
| Error | `notice` (1 px `fail` border, `fail-tint`, 13/20) above the action that failed, with a retry where it makes sense |
| Auth failure | Inline notice, focus moved to the notice, form still filled |
| Long values | Truncate with ellipsis and a `title`; never wrap a chip or a filename into three lines |
| No JS | The report is server-rendered and the theme is server-resolved; only the landing interactions degrade |

### 6.14 Hero dropzone

- No outer panel: the zone itself is the bordered object, 1 px dashed `hairline-strong`, radius 8, `surface`, 48/24 padding in the hero, 160 px high elsewhere.
- Icon 24 px `ink-faint`, title `body-strong`, hint `small`.
- Drag over: border `accent`, background `accent-tint`.
- Keyboard: the zone is a button, Enter/Space opens the file picker; the hidden input is labelled.
- Constraints line under the zone: “CSV or XLSX · up to 50 MB · read in memory, not kept”.
- Signed out: no file input; the hint reads `Click to sign in — samples need no account` and the click opens the auth dialog.
- Errors: client-side `notice` under the zone, never a browser alert. An error body is rendered through `web/lib/apiError.ts`, because FastAPI's `detail` may be a string, a list, or a nested object — printing the object produced `[object Object]` (v3.3).

### 6.15 Footer

59 px of content on the landing only: privacy line and disclaimer in `small` `ink-muted`, and a GitHub link. No engine version on the landing: it would be a second, silently-stale copy of a value the report already prints from the payload. On the report, the same lines sit under the method section. No sitemap, no social links.

---

## 7. The copy (verbatim)

These strings are the product. They may be re-worded deliberately, but not paraphrased by whoever implements them. §7.1–§7.3, §7.5 and §7.6 are server-authored and must match `backend/app/core/report_text.py`.

### 7.1 The four lead blocks

**Fail**

> **FAIL**
> **This data would teach a model to treat people unequally.**
> One or more of the five checks failed. Training on this data as it is would reproduce the disparity the data already contains.

**Warn**

> **WARN**
> **This data is usable, but there is something you should read first.**
> No check failed, and at least one is close enough to the line to be worth understanding before you train.

**Inconclusive**

> **INCONCLUSIVE**
> **There is not enough here to judge.**
> One or more checks could not be decided honestly. That is a finding about the data, not a failure of the analysis.

Two shapes reach this block, and the copy above is true of both: a **thin group** — too few rows, or an interval so wide it says nothing (C1, C2, C5) — or a **check that cannot be computed at all** because a group has no positives or no negatives, which is how C4 goes Inconclusive. The second is the more common case. Checks that are Inconclusive are never collapsed (PRD F4-AC3).

A Pass cannot coexist with an unjudgeable check: PRD §8.5 makes any Inconclusive check decide the verdict. The Pass headline is literally true every time it appears.

**Pass**

> **PASS**
> **All five checks passed.**
> No group is treated substantially differently in this data by these five measures. That is not a guarantee of fairness in every sense — the limits are explained in the method.

### 7.2 The five check sentences

Each check has two forms: one for **Fail or Warn**, one for **Pass**. C3 is handled in §7.3. An Inconclusive row carries the reason phrase from PRD §8.4 instead.

| Check | When the check finds a problem (Fail or Warn) | When it does not (Pass) |
|---|---|---|
| C1 Historical disparity | The decisions already in your data do not treat these groups equally. | The decisions already in your data treat these groups about equally. |
| C2 Model disparity | A model trained on this data would not treat them equally either. | A model trained on this data would treat them about equally. |
| C3 Amplification | See §7.3. | See §7.3. |
| C4 Equal opportunity | People with similar qualifications are not recognised at the same rate. | People with similar qualifications are recognised at about the same rate. |
| C5 Sample adequacy | There are not enough rows in each group for these numbers to be worth reading. | There are enough rows in each group for these numbers to be worth reading. |

Each sentence is followed, in `small`, by the figure, its interval and the threshold — never replaced by them.

### 7.3 The amplification sentence (R6 — resolved)

Three forms, one shape. The direction is the only thing that changes.

**When the model widens the gap (Warn or Fail):**

> **The model makes the gap wider.**
> Your data already shows a 21-point gap between men and women. A model trained on it widens that gap to 34 points. It learned the pattern and pushed harder than the data did.

**When the model leaves the gap roughly where it is (Pass, within ±0.05):**

> **The model keeps the gap where it already is.**
> Your data shows a 21-point gap between men and women. A model trained on it shows 22 points. It reproduced the pattern without adding to it — which means removing the disparity means fixing the data, not the model.

**When the model narrows the gap (Pass, by 5 points or more):**

> **The model narrows the gap.**
> Your data shows a 21-point gap between men and women. A model trained on it shows 12 points. The disparity is smaller than the one the data already contains — but it has not disappeared.

Every figure is injected by the server after generation, never written by a language model. Group names come from the user's file (`female`/`male` render as women/men).

### 7.4 The six stage labels

These are the labels the backend streams. The stepper prints them unchanged; it adds only the counter.

```
Reading your file
Cleaning and encoding
Training the stand-in model
Measuring fairness
Computing feature influence
Saving results
```

No findings and no figures. The counter (`3 of 6`) is interface state, not content.

### 7.5 The privacy line

Shown under the verdict and in the footer:

> We processed your file in memory and did not keep it. What is saved is the numbers on this page — and deleting your account removes them.

### 7.6 The threshold disclaimer

Every screen and every print:

> These limits are our defaults, based on the common 80% rule. They are not a legal determination.

### 7.7 Landing copy (frontend, editable)

| Place | String |
|---|---|
| Eyebrow | Data fairness, before training |
| `h1` | Know what your data teaches before a model learns it. |
| Hero body | FairLens reads a CSV or XLSX, trains a throwaway model on it, and reports where it would pass on unequal treatment — five checks, one verdict, every figure explained. |
| Dropzone | Drop a CSV or XLSX file here, or click to browse |
| Dropzone hint, signed out | Click to sign in — samples need no account |
| Dropzone hint, signed in | Maximum 50 MB |
| Constraints | CSV or XLSX · up to 50 MB · read in memory, not kept |
| Sample link | No file to hand? Run a sample |
| Samples title | Three datasets, three known answers |
| Samples body | Run one to see the full report without uploading anything. |
| Sample action | Run the analysis |
| Footer | Privacy line (§7.5) · GitHub · disclaimer |

---

## 8. Motion

### 8.1 Tokens

| Token | Value | Use |
|---|---|---|
| `--ease` | `cubic-bezier(0.2, 0, 0, 1)` | Everything |
| `--fast` | 90 ms | Hover, focus, colour |
| `--base` | 160 ms | Disclosure, chip and state changes |
| `--reveal` | 200 ms | Report section entrance, 30 ms stagger |
| `--pulse` | 1.2 s | The current step dot only |

### 8.2 What animates

| Surface | Motion | Length |
|---|---|---|
| Report sections | rise 8 px and fade once on mount, 30 ms apart | 200 ms |
| Check row detail | height transition on a fixed end state | 160 ms |
| Chart bars | grow from the axis, once | 300 ms |
| Current run-log dot | pulse | 1.2 s loop |
| Buttons, inputs | border/background colour | 90 ms |
| Button press | 1 px translate down while held | instant |
| Sample card hover | 2 px lift and `hairline-strong` border | 160 ms |
| Auth dialog | rise 10 px + fade in; reverse on close | 200 / 140 ms |
| Dialog backdrop | fade in / out with the dialog | 200 / 140 ms |
| Reset result | tick or cross draws its stroke once | 320 ms (200 ms inline) |
| Anchor links | smooth scroll to the section | browser |

### 8.3 What never animates

Numbers. A figure that counts up implies the number is being computed while you watch. It is not. No confetti, no bounce, no looping decoration: the tick is a statement that the request was accepted, drawn once.

### 8.4 Restraint

No parallax, no scroll-jacking, no cursor effects, no page transitions, no skeleton shimmer on the report (it is server-rendered). The inspecting panel may show an indeterminate bar — it reflects real work.

### 8.5 Reduced motion

`prefers-reduced-motion: reduce` removes every entrance, height transition, draw, lift and pulse; disclosures open and close instantly; the chart renders at its final size; anchor jumps are instant. The dialog still opens and closes, without the rise.

### 8.6 Print

Print is light, static and complete (see §9). No animation survives print.

---

## 9. Print

| Property | Specification |
|---|---|
| Technical sections | Rendered and hidden until print, never conditionally mounted |
| Page | A4, 18 mm margins, white ground, `print-color-adjust: exact` on verdict panels |
| Theme | Always the light palette (§8.6); a dark-theme print is a black page |
| Hidden | App bar, aside, action buttons, disclosures' controls, repair controls |
| Kept | Verdict, KPI strip, five checks with thresholds, chart, affected groups, amplification, method, dataset name, date, footer |
| Breaks | `break-inside: avoid` on check rows and comparisons; `break-before: page` before the method |
| Filename | `FairLens — loans.csv — 2026-11-17` |
| Footer | The §7.6 disclaimer on every page |

---

## 10. Accessibility checklist

| # | Requirement |
|---|---|
| A1 | Text contrast ≥ 4.5:1; large text ≥ 3:1; asserted over the token pairs |
| A2 | No information by colour alone — every state carries a word and a glyph |
| A3 | Focus visible on every interactive element, 2 px ring, never suppressed |
| A4 | Full keyboard operation: dropzone, disclosures, stepper and forms; no traps |
| A5 | The run log is a polite live region; `aria-current="step"` on the current row |
| A6 | The chart has a text alternative and a data table |
| A7 | Tables have captions and scoped headers |
| A8 | `prefers-reduced-motion` honoured everywhere |
| A9 | 200% zoom without horizontal scrolling or clipped content |
| A10 | Touch targets ≥ 44 px on coarse pointers |
| A11 | Headings in order; one `h1` per page |
| A12 | Form errors associated via `aria-describedby` and announced |
| A13 | No auto-playing media; no reading time limits |
| A14 | Print legible in greyscale — the verdict word and glyph survive without colour |
| A15 | Every token pair meets contrast in both themes (eight verdict pairs, plus ink, muted and accent on canvas) |
| A16 | Theme correct in the first paint; no JavaScript required to resolve it |
| A17 | The theme control has an accessible name and exposes its three states (M5) |
| A18 | Hover-only affordances have a focus and static equivalent |

---

## 11. Performance budget

| Budget | Target |
|---|---|
| Font files | 4 maximum, ≤ 200 KB total, woff2, Latin subset, `swap` |
| JavaScript on the report route | ≤ 180 KB gzipped above the framework baseline |
| Animation | `transform` and `opacity` only |
| Scroll work | `IntersectionObserver` only; no scroll listeners |
| Layout shift | Zero from fonts (size-adjust fallback) and reveals (no height change) |
| Chart | One inline SVG component; no charting runtime |
| Images | None. The product has no photography, illustration or logos |
| Theme | Custom properties and one media query; no client script |

---

## 12. Risks and what is revisitable

| # | Risk | Response |
|---|---|---|
| R-1 | **Taste risk moves now to density.** A neutral product UI can read as generic if spacing and hierarchy are not exact | The reference set is narrow and the components are fixed; screenshots at 1280 and 375 are part of acceptance |
| R-2 | **The hero dropzone is the only way in**, so a fault there removes the product's main action | `upload.spec` drops a real file end to end, `anonymous.spec` asserts the signed-out zone opens the dialog, and a failed request renders its sentence under the zone instead of failing silently |
| R-3 | **Geist may not be available under the free constraint** | SIL OFL 1.1, served from `web/fonts` (one variable Sans file, one Mono file, 39 KB total). The font files are the only build dependency; if they cannot be shipped, the fallback is the metric-compatible system stack in §3.1 and no token changes |
| R-4 | **Density can hide content.** Small type and 40 px rows exclude people | Minimum 13 px for supporting text, 15 px body, 4.5:1 everywhere, 44 px touch targets, zoom tested |
| R-5 | `print-color-adjust: exact` is not universally honoured | A14 asserts greyscale legibility so the verdict survives either way |
| R-6 | **A second palette is a second thing to keep correct.** A hardcoded hex looks right in one theme and wrong in the other | Components reference tokens only. `contrast.spec.ts` asserts both themes; the literal-hex lint rule arrives with M7's CI, until then it is review |

---

## 13. Migration

### 13.1 Order

| Step | Work | Exit |
|---|---|---|
| **R1** | Tokens, type, radii, app bar. Delete Instrument Serif and the serif classes | Every screen renders in Geist; contrast and theme specs pass with updated token names |
| **R2** | Landing rebuild: hero, sample cards, footer (v3.2 and v3.3 then cut the preview and the separate upload panel; the dropzone is the hero) | Landing matches §5.2; signed-out and signed-in states both live |
| **R3** | Report restructure: KPI strip, checks before chart, aside, section numbers | §5.3 order; traceability spec still green; print opens the method |
| **R4** | Confirmation mapping panel, run-log stepper, auth restyle, doc/test sync, screenshots | All Playwright specs updated and green; `tsc` and `npm run build` clean; 1280/375 light/dark shots |

### 13.2 What gets deleted

- `web/fonts/instrument-serif-*.woff2` and its `localFont` block.
- `.lede`, `.serif`, `.display` serif rules; `.tile` grid; `.sample` flex rows; the old `.report h1` scale.
- The editorial copy blocks that only repeated the checks in prose.
- `ConfirmationCard`'s read/edit mode toggle.
- `HeroPreview` and the `.preview*` rules; the `.auth-prompt` block and the `.upload` panel with its scroll-to button (v3.3).

### 13.3 Acceptance

- A stranger can state the verdict within five seconds of the report loading.
- The landing has no section that exists only to fill space; every block answers a question or performs an action.
- No screen uses a font the app does not self-host.
- Every figure on every screen can be traced to the payload (`traceability.spec.ts`).
- Both themes, 375 px and 200% zoom are screenshot-checked.

### 13.4 Deltas as built

R1–R4 landed on 18 Nov 2026. These are the places the code is deliberately simpler than the text above; none of them changes what the product says.

| Area | As built | Why |
|---|---|---|
| Hero | Copy plus the dropzone; no preview, so `HeroPreview` was deleted | Three buttons named the same action and only scrolled to a fourth copy of it; the tool now *is* the hero (v3.3) |
| Report app bar | Brand and account actions only | The banner and aside already carry the state and the dataset; §5.3 now says so |
| Aside | Static jump links; current section is not highlighted | An observer to repeat the page position was not worth the script |
| Landing footer | Privacy line, disclaimer, GitHub; no engine version | The report prints the engine from the payload; the landing would print a stale literal |
| Landing copy | British spelling throughout (`Analyse`, `analysed`) | One spelling for the product; the old `Analyze` string and its test were changed |
| Print | Tokens forced to the light palette in `@media print`; disclosures opened by CSS | Matches §9 without a second render path |
| Session state | One `AuthProvider` probe shared by the app bar and the landing | Two copies of `/v1/me` on every page load was one too many |
| Sign-in surfaces | One `AuthForm` rendered by `/login`, `/signup` and the dialog | Three copies of the same form drifted apart; now they cannot |
| Reset tick | Drawn SVG stroke, not an icon font or a GIF | Two paths, ~1 KB, and it inherits `currentColor` in both themes |

### 13.5 Verified

| Check | Result |
|---|---|
| `npx tsc --noEmit` | clean |
| `npm run build` | clean; `/analysis/[id]` ships 137 B of route JS |
| `npx playwright test` | 17 of 17 pass on `BASE_URL=http://localhost:3001` |
| Contrast | eight verdict pairs plus `ink`, `ink-muted` and `accent` on canvas, both themes |
| Fonts | two woff2 files, 39 KB, self-hosted, no Google Fonts request at runtime |
| Widths | checked at 1280 and 375 px; the report and the landing both hold their gutters, the hero dropzone sits under the copy at 375, and the 375 px check rows are one column |

---

## 14. Traceability

| Decision | Where enforced | PRD / App Flow it serves |
|---|---|---|
| R6 amplification copy | §7.3 | PRD R6, §8.2 C3, F4-AC5 |
| Verdict coding | §4.4, §6.8, A1–A2 | F4-AC1, F4-AC3, accessibility |
| Typescale and families | §3, §11 | Performance budget, S2 |
| Landing structure | §5.2 | S2 (verdict in under 60 s), truthfulness |
| Report order and KPI strip | §5.3 | F4, F5, F7-AC4 |
| Confirmation mapping | §6.4 | F2, F2-AC2, F2-AC3 |
| Chart and interval | §6.10 | F4 chart requirement, §8.3 intervals, S3 |
| Technical appendix | §6.11 | F5, F5-AC2, F5-AC3 |
| Motion | §8 | TRD T8, App Flow A3, A11 |
| Print | §9 | F7-AC4, F7-AC5, F7-AC6, A11 |
| Theme | §4.3, A15–A17 | D1–D3; no product impact |
| Accessibility | §10 | F4-AC3, TRD T10 |

---

## 15. Change log

| Version | Date | Change |
|---|---|---|
| 3.3 | 19 Nov 2026 | **The dropzone is the hero**: the upload section and its scroll-to button are gone, the app bar keeps one action, and the landing preview is removed because the sample cards already say what a run produces. Signed out, the same dropzone opens the dialog. API detail objects render as their sentence instead of [object Object]. 17 specs green |
| 2.2 | 16 Nov 2026 | Editorial direction; report components; shell tokens; html-level theme |
| **3.0** | **17 Nov 2026** | **Precise product redesign: serif removed, neutral palette, new landing and report structure, mapping panel, stepper. Design target; build remains 2.2 until R4** |
| **3.1** | **18 Nov 2026** | **R1–R4 built: Geist self-hosted, new landing and report order, KPI strip, aside, mapping panel, stepper, auth column; 13 specs green. §13.4 records the six places the code is simpler** |
| **3.2** | **18 Nov 2026** | **Landing cut from six sections to four; hero preview now the loan run; sign-in is one native dialog opened from the app bar, hero and upload prompt; reset gets a drawn tick/cross with the address and “Change email”; press, lift, dialog and draw motion added; docs and specs updated. 16 specs green** |

*End of UI/UX v3.2.*
