# FairLens v2 — UI/UX Specification

| | |
|---|---|
| **Version** | 2.2 (29 Oct: two-form check sentences, Inconclusive reason visible, print repairs conditional) |
| **Status** | All 19 decisions closed (16 interface, 3 dark theme). Implementation Plan written. |
| **Date** | 27 October 2026 |
| **Baseline** | `docs/PRD.md` v2.3, `docs/TRD.md` v2.4, `docs/APP_FLOW.md` v2.3 |
| **Next document** | `docs/IMPLEMENTATION_PLAN.md` (written; a change here requires a matching change there) |

---

## 0. How to read this document

- **Sections 1–5** are the system: the direction, the type, the colour, the space. Everything else is assembled from these.
- **Section 6** is the components, one anatomy each — where the numbers are, where the words are, what is loud.
- **Section 7** is the copy, written out verbatim. This is the section that must not be paraphrased during the build, because the words are the product.
- **Section 8** is the motion specification in exact durations.
- **Sections 9–11** are print, accessibility and performance — three things that get postponed until they are expensive.
- Anything a reviewer can check with a tape measure or a contrast tool has a number here. Anything that is a matter of taste is marked as revisitable.
- **R6 is closed in §7.3.** It was the last open question in the PRD.

---

## 1. Design principles

Four, and they exist to settle arguments rather than to sound good.

1. **This is a document, not a dashboard.** The product's output is something a person forwards to compliance and prints. Cards, badges and dense chrome belong to dashboards; rules, columns and marginal notes belong to documents.
2. **The number is the loudest thing in its row.** Type size is spent on figures and verdicts, not on labels, icons or decoration. If a label competes with a number, the label is wrong.
3. **Nothing moves that carries a figure.** Bars may grow; a value never counts up. Motion shows that work is happening, never that a fact is being computed live.
4. **Every state has a word.** Fail, Warn, Inconclusive, Pass appear as text in their own sentences. Colour and glyph are reinforcements, never the message.

---

## 2. Direction: editorial (U2)

### What it means concretely

| Trait | Implementation |
|---|---|
| Paper, not canvas | Warm off-white page background, pure white only for inset panels. No grey-blue dashboard surfaces anywhere |
| Rules, not cards | Sections separated by 1 px hairlines and space. A bordered box is used only where the content is genuinely inset: the confirmation block, table containers, the log |
| Serif for claims, sans for machinery | Headlines, verdicts and big figures are serif. Anything a user operates — buttons, inputs, tables, labels — is sans |
| Wide margins | 96 px of vertical space between sections, generous horizontal gutters. Empty space is the cheapest way to look considered |
| Sharp corners | 2 px radius on inputs and panels, 4 px on dialogs. No pills, no 16 px rounding |
| One accent | A single deep petrol colour for links, focus and active states. It never competes with the four verdict colours |
| No decoration | No gradient meshes, no glassmorphism, no illustrations, no stock imagery, no invented logos or testimonials |

### What it explicitly rejects

No sidebar navigation. No dashboard grid of KPI tiles. No avatars. No emoji in the interface. No decorative imagery of any kind. Every one of those would be a second design; the product needs one, executed well.

A dark theme is not in this list. It was rejected in the first draft and then decided the other way — see §4.2. It is the same document after dark, not a second design.

---

## 3. Type (U4)

### Families

| Role | Family | Weights | Why |
|---|---|---|---|
| Display and figures | **Instrument Serif** | 400 only, plus italic | High-contrast display face; makes a disparity figure read as a fact rather than a data point |
| Interface and tables | **IBM Plex Sans** | 400, 500, 600 | Designed for dense technical information; humanist enough to avoid the Inter-everywhere look |
| Nothing else | — | — | A third family is a download tax for a section most readers never open |

Both are free for commercial use, self-hosted through `next/font` with the `display` strategy set to `swap`, subset to Latin, two weight files each at most, and preloaded for the two faces used above the fold.

**Hierarchy without weights.** Instrument Serif ships one weight, so hierarchy comes from size, spacing and colour alone. That is a discipline rather than a limitation: nothing shouts by going bold.

**Revisitable.** This is the decision most likely to change once it is on screen. If the serif reads as dated in situ, the substitution is a like-for-like display serif and nothing else in the system moves. Recorded as a risk in §12 rather than pretended to be final.

### Scale

Base 17 px, ratio ~1.25, line heights tuned per role.

| Token | Size / line | Family | Use |
|---|---|---|---|
| `display` | 56 / 60 | Serif | Landing headline only |
| `h1` | 40 / 44 | Serif | Verdict headline, page titles |
| `h2` | 30 / 36 | Serif | Section titles (the numbered ones) |
| `h3` | 22 / 28 | Sans 600 | Component titles, table captions |
| `lede` | 21 / 32 | Serif | First paragraph of the narrative |
| `body` | 17 / 27 | Sans | All interface and body text, measure capped at 66 characters |
| `small` | 15 / 22 | Sans | Thresholds, captions, secondary facts |
| `label` | 13 / 18, 0.06em caps | Sans 500 | Overlines, field labels, table headers |
| `figure` | 34 / 38 | Serif | The one big number in a block |
| `figure-sm` | 22 / 26 | Serif | Per-check figures |

**Numerals.** Display figures use Instrument Serif's natural figures. Every table uses IBM Plex Sans with `font-variant-numeric: tabular-nums` so columns align. No digit animation, ever — see §8.4.

---

## 4. Colour and theme (U3, D1–D3)

### 4.1 Light palette

| Token | Value | Use |
|---|---|---|
| `paper` | `#FAF9F6` | Page background |
| `surface` | `#FFFFFF` | Inset panels, log, table containers |
| `ink` | `#17161A` | Body text, headlines |
| `ink-muted` | `#55525C` | Secondary text, thresholds, dimmed log lines |
| `ink-faint` | `#8A8794` | Timestamps, disabled controls — never for content a reader needs |
| `hairline` | `#E3E0D8` | Section rules, table borders |
| `accent` | `#123B4F` | Links, focus rings, active states, the glyph field |

**Verdict colours.** Each state has a foreground, a tint for its panel, and a glyph. The glyph and the state word are always present; colour is the third signal, never the first.

| State | Foreground | Tint | Glyph |
|---|---|---|---|
| **Fail** | `#8C2F2A` | `#FBEDEB` | ✕ |
| **Warn** | `#8A5A12` | `#FBF3E4` | ! |
| **Inconclusive** | `#3E4C63` | `#EEF1F6` | ? |
| **Pass** | `#1F5A3D` | `#EAF3ED` | ✓ |

**Why Inconclusive is slate blue.** It cannot be green (that reads as pass), and it cannot be amber (that reads as warn). It needs a colour that belongs to neither, and a cool neutral is the only honest option. It is also the state most likely to be quietly mis-styled by a future change, so it gets its own named token rather than a fallback.

**Contrast.** Every foreground is at least 4.5:1 against its own tint and against `paper`; `ink` on `paper` is far above that. A script in the test suite asserts these pairs, so a palette edit that breaks accessibility fails CI rather than reaching a user.

**Colour-blind safety.** Fail and Pass are separated by lightness as well as hue, and both are always accompanied by a distinct glyph and the state word. Nothing in the product is conveyed by hue alone.

### 4.2 Dark theme (D1–D3)

**Warm night paper, not an inversion.** The light palette inverted produces mud and a blue-grey console. The dark theme is designed as its own set of values on the same structure: a warm near-black ground, warm off-white ink, the same hairline language, the same type.

| Token | Value | Use |
|---|---|---|
| `paper` | `#14120F` | Page background |
| `surface` | `#1B1915` | Inset panels, log, table containers |
| `ink` | `#EDEAE3` | Body text, headlines |
| `ink-muted` | `#A9A49B` | Secondary text, thresholds, dimmed log lines |
| `ink-faint` | `#7C7770` | Timestamps, disabled controls — never for content a reader needs |
| `hairline` | `#2E2A24` | Section rules, table borders |
| `accent` | `#7FB4C6` | Links, focus rings, active states, the glyph field |

The accent is re-cut rather than reused: `#123B4F` petrol on a near-black ground disappears entirely, so the dark theme uses a lightened version of the same hue.

**Verdict colours are re-cut, not reused.** The light values vibrate on a dark ground and lose contrast.

| State | Foreground | Tint | Glyph |
|---|---|---|---|
| **Fail** | `#E8A29A` | `#2A1B19` | ✕ |
| **Warn** | `#DDB173` | `#2A2318` | ! |
| **Inconclusive** | `#AEC0D6` | `#1D222B` | ? |
| **Pass** | `#92C4A8` | `#18241C` | ✓ |

The Inconclusive state keeps its cool neutral in both themes, which is the point of giving it a named token: it must never drift towards green or amber when a palette is retuned.

**Contrast doubles.** Eight pairs are asserted instead of four — each verdict foreground against its own tint and against `paper`, in each theme. `ink` on `paper` is asserted in both themes as well. A palette edit that breaks either theme fails CI.

### 4.3 How the theme is resolved

| Cookie value | What the server renders | What supplies the colours |
|---|---|---|
| `light` | `<html lang="en" data-theme="light">` | The light tokens |
| `dark` | `<html lang="en" data-theme="dark">` | The dark tokens |
| `system` or absent | `<html lang="en">` with no attribute | `@media (prefers-color-scheme: dark)` selects the dark tokens |

**No JavaScript and no flash.** The cookie is read in the root layout before the first byte of HTML, so the correct theme is present immediately. When the preference is `system` there is nothing to resolve on the client at all — plain CSS media queries do it. There is no inline pre-paint script, so the CSP in TRD §11.1 needs no exception, and the theme works with JavaScript disabled.

The attribute sits on `<html>` and the tokens on `:root`, so the header, the page ground and every screen share one theme. The cost is that every route renders dynamically, which is accepted because every screen is themed; there is no static route left to protect. The control lives in `/account` (D3), so an explicit override only exists for someone who is signed in anyway.

---

## 5. Space and layout (U5)

### Spacing scale

4 px base: `4 · 8 · 12 · 16 · 24 · 32 · 48 · 64 · 96`

| Use | Value |
|---|---|
| Inside a control | 12 |
| Between related elements | 16 |
| Between blocks in a section | 32 |
| Between sections | 96 |
| Page gutter, desktop / mobile | 64 / 24 |
| Main column max width | 78rem (1248 px) |
| Prose measure | 66ch |

### Report page

```
┌──────────────────────────────────────────────────────────────┐
│  contents strip (sticky)                                     │
│  ──────────────────────────────────────────────────────────  │
│  01  The verdict                ← lead block                 │
│  ──────────────────────────────────────────────────────────  │
│  02  Who is affected            ← chart                      │
│  ──────────────────────────────────────────────────────────  │
│  03  What the model does        ← checks                     │
│  ──────────────────────────────────────────────────────────  │
│  04  What to do about it        ← repairs (M4)               │
│  ──────────────────────────────────────────────────────────  │
│  05  The method                 ← technical                  │
└──────────────────────────────────────────────────────────────┘
```

- Numbered sections (`01`–`05`) in `label` caps at `ink-faint`, title in `h2`. M3 ships `01`–`04` with the method as `04`; M4 inserts repairs as `04` and renumbers the method to `05`.
- The contents strip is not built yet. The page is a single column at every width, with the navigation deferred to the same milestone as the chat panel, neither of which is in M3.
- Below 768 px everything is one column, tables scroll horizontally inside their container rather than shrinking type.

---

## 6. Components

### 6.1 Verdict banner

The lead block. Anatomy, top to bottom:

1. `label` overline: glyph, then the state word in caps (`FAIL`, `WARN`, `INCONCLUSIVE`, `PASS`).
2. `h1` headline, serif — see §7.1 for the exact words.
3. One `body` sentence of consequence.
4. Hairline.
5. The action set for this state.

Rendered on the tint panel, full column width, with 32 px padding. The verdict is the only place in the product where a tinted panel spans the full width.

### 6.2 Check row

One row per check, five rows, no cards:

```
┌─────────────────────────────────────────────────────────────────┐
│ C1  Historical disparity          Fail      Ratio 0.66          │
│     The decisions already in your data do not treat these       │
│     groups equally.                       Threshold ≥ 0.90      │
│                                                            ▸    │
└─────────────────────────────────────────────────────────────────┘
```

| Element | Treatment |
|---|---|
| Identifier | `label` caps, `ink-faint` — `C1`…`C5`, with `core` appended for C1, C2, C5. The marker means *this check answers the headline question*; it does **not** imply the check weighs more in the verdict (PRD §8.5) |
| Name | `body` 500 ink |
| State | State word in the verdict colour plus its glyph, no pill |
| Figure | `figure-sm` serif, right-aligned; interval beside it in `small` where one exists |
| Meaning | `body`, `ink-muted`, maximum two lines |
| Threshold | `small`, `ink-faint`, right-aligned under the figure |
| Disclosure | Expands to the full metric, its interval, the method and the group counts. Collapsed by default; never collapsed for an Inconclusive check (PRD F4-AC3) |

The threshold is always visible without expanding. A number whose limit is hidden is a number a reader cannot judge.

### 6.3 The chart

| Property | Specification |
|---|---|
| Form | Horizontal grouped bars, two per group, sorted ascending by the historical rate |
| Axis | 0–100%, ticks at 0/25/50/75/100, gridlines at `hairline`. **Never truncated** |
| Bar | 14 px high, 6 px gap within a group, 20 px between groups |
| Marks | Historical: filled `ink` at 85% opacity. Model: 2 px outlined, `accent`. Both labelled in words in the legend |
| Interval | 2 px line with end caps, `ink-muted`, drawn through each bar at its estimate |
| Group labels | `body` sans left of the axis, 120 px column, never truncated — wrapped if needed |
| Call-out | The least-advantaged group gets a `label` note in `ink-muted` beneath its label |
| Prohibited | 3D, drop shadows, gradient fills, truncated axes, pie charts, dual axes, animation of the values |

Accessibility: the chart has a text alternative naming the groups and their rates, and a full data table behind a disclosure. A canvas of bars is invisible to a screen reader; the numbers must exist as text.

### 6.4 Confirmation block (U7)

What ships is a `surface` panel, not the three-line strip drawn in the first draft. The head is the question in `h2` with a `Change` text button on the right. Below it, four `tile`s in a responsive grid:

```
┌──────────────────────────────────────────────────────────────┐
│  Confirm what this data means                         Change │
│  ┌──────────────────┐  ┌──────────────────┐                  │
│  │ OUTCOME COLUMN   │  │ DEMOGRAPHIC      │                  │
│  │ approved         │  │ sex              │                  │
│  │ Positive: …      │  │ 2 groups  ▸      │                  │
│  └──────────────────┘  └──────────────────┘                  │
│  ┌──────────────────┐  ┌──────────────────┐                  │
│  │ AGE BANDING      │  │ FACTOR COLUMNS   │                  │
│  │ Not available    │  │ None             │                  │
│  └──────────────────┘  └──────────────────┘                  │
│  900 rows × 8 columns                                        │
│  [ Run analysis ]                         [ Cancel ]          │
└──────────────────────────────────────────────────────────────┘
```

- Label in `label` caps; the value in `body` at `ink`; the counts in `small` at `ink-muted`.
- `Change` is a text button, not an icon, and swaps the tiles for the edit form: outcome select, positive value, demographic select, the age-banding checkbox, then Run analysis and Cancel.
- Group values sit behind a `details` disclosure, with their row counts. **Group rates are never shown here.** That is check C1; showing it would spoil the verdict on the screen before the verdict.
- A multi-sheet workbook adds a sheet select below the tiles, and above 50,000 rows a required radio choice disables Run analysis until one is picked.
- Warnings render in the `warn` notice block above the actions; a single-value demographic column blocks the run until the column changes.

### 6.5 Run log (U11, U12)

| Property | Specification |
|---|---|
| Container | `surface` panel, head with `Running analysis` and a destructive-text `Cancel`, body fixed at 220 px and scrolling internally |
| Line | One row per stage: a dot, the server's stage label at `body` 500 `ink`, and `Stage n of 6` in `small` at `ink-muted` |
| Dot | 8 px, `ink` while the stage is live, `pass` green on `saving` |
| Waiting | A `ping` frame renders as a tinted `inconclusive` row reading `Waiting for stage to complete…` |
| Overflow | Oldest lines leave the top of the panel; the panel never grows the page |
| Live region | `aria-live="polite"` on the list |
| Content rule | No verdict figures and no findings. The only numerals are the stage counter |

The glyph field, the `fold n of 5` lines and the collapse of the confirmed meaning above the log were drawn in the first draft and are not shipped: the stream carries six stage frames, so there are no folds to show, and the card is replaced by the log rather than collapsed above it.

Under `prefers-reduced-motion` no transition is applied; the rows simply appear. There is no motion in the shipped log today.

### 6.6 Technical appendix

Same paper, same type, no dark panel and no monospace.

1. **Methodology note first**, in `body`: the model is a stand-in trained on this data, its purpose is to measure what the data teaches, and it is not meant to be shipped. This is stated above the tables, not in a footnote (PRD F5-AC3).
2. Metric table: metric, value, interval, threshold, state. Tabular figures.
3. Per-group table: group, n, selection rate, TPR, FPR, accuracy, each with intervals where computed.
4. Model card: a labelled definition list — algorithm, hyperparameters, folds, out-of-fold accuracy, positive label, row counts, engine version, date.
5. Encoding decisions, the proxy table, the sampling record.
6. JSON: a download button, plus an optional inline view for reading a single field.

Tables have captions, `th` with `scope`, and right-aligned numeric columns.

### 6.7 Buttons, inputs, links

| Element | Specification |
|---|---|
| Primary | Filled `ink`, paper text, 2 px radius, 44 px min height |
| Secondary | Hairline border, ink text, transparent fill |
| Destructive | Text in the Fail colour; filled only inside the delete dialog |
| Text button | Accent colour, no underline until hover, then a plain underline |
| Input | 1 px `hairline` border, `surface` fill, 2 px radius, 44 px height, label above in `label` caps |
| Focus | 2 px `accent` ring at 2 px offset, always visible, never animated away, never suppressed by an outline reset |
| Disabled | `ink-faint` text, no opacity change on the whole control — a control that fades out of existence is a control people miss |

---

## 7. The copy (verbatim)

These strings are the product. They may be re-worded deliberately, but not paraphrased by whoever implements them.

### 7.1 The four lead blocks (U2, U5)

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

Two shapes reach this block, and the copy above is true of both: a **thin group** — too few rows, or an interval so wide it says nothing (C1, C2, C5) — or a **check that cannot be computed at all** because a group has no positives or no negatives, which is how C4 goes Inconclusive. The second is the more common case. Below the block, the checks that are Inconclusive are never collapsed (PRD F4-AC3), so the reason is always visible in the row itself.

A Pass therefore cannot coexist with an unjudgeable check: PRD §8.5 makes any Inconclusive check decide the verdict. The Pass headline "All five checks passed" is literally true every time it appears.

**Pass**

> **PASS**
> **All five checks passed.**
> No group is treated substantially differently in this data by these five measures. That is not a guarantee of fairness in every sense — the limits are explained in the method.

### 7.2 The five check sentences

Each check has two forms: one for **Fail or Warn**, one for **Pass**. C3 is handled in §7.3 because a Pass can mean two different things there. An Inconclusive row carries the reason phrase from PRD §8.4 instead.

| Check | When the check finds a problem (Fail or Warn) | When it does not (Pass) |
|---|---|---|
| C1 Historical disparity | The decisions already in your data do not treat these groups equally. | The decisions already in your data treat these groups about equally. |
| C2 Model disparity | A model trained on this data would not treat them equally either. | A model trained on this data would treat them about equally. |
| C3 Amplification | See §7.3. | See §7.3. |
| C4 Equal opportunity | People with similar qualifications are not recognised at the same rate. | People with similar qualifications are recognised at about the same rate. |
| C5 Sample adequacy | There are not enough rows in each group for these numbers to be worth reading. | There are enough rows in each group for these numbers to be worth reading. |

Each sentence is followed, in `small`, by the figure, its interval, and the threshold — never instead of them.

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

Every figure in these sentences is injected by the server after generation, never written by a language model, and the group names come from the user's own file (`female`/`male` render as women/men).

### 7.4 The seven log lines

```
Reading your file…
Cleaning the data…
Training a model on your data…
Training fold 3 of 5…
Checking the groups…
Measuring what drove the decisions…
Writing the report…
```

No digits. No findings. The fold line appears only inside training.

### 7.5 The privacy line

Shown under the verdict and in the report footer:

> We processed your file in memory and did not keep it. What is saved is the numbers on this page — and deleting your account removes them.

### 7.6 The threshold disclaimer

Every report footer, screen and print:

> These limits are our defaults, based on the common 80% rule. They are not a legal determination.

---

## 8. Motion (U10–U16)

### 8.1 Tokens

| Token | Value | Use |
|---|---|---|
| `ease` | `cubic-bezier(0.2, 0, 0, 1)` | Everything. One curve, no exceptions |
| `fast` | 120 ms | State changes, colour transitions |
| `base` | 220 ms | Log lines, small movements |
| `slow` | 380 ms | Panel transform |
| `reveal` | 300 ms | Section entrances |
| `stagger` | 60 ms | Between siblings |

Only `transform` and `opacity` are animated. Anything that changes layout — height, margin, width of text — is either avoided or animated on a wrapper with a fixed end state, because a browser cannot composite a layout change and the result stutters on a shared CPU.

### 8.2 The sequence, in order

| Moment | What happens | Duration |
|---|---|---|
| Press **Run** | Card's three lines collapse to the single anchor line; contents crossfade inside the panel | 380 ms |
| Log lines | Fade and rise 8 px; previous line dims | 220 ms, 60 ms stagger |
| Glyph field | Scans continuously | 1.4 s loop |
| Result arrives | Log folds to a finished strip | 380 ms |
| Verdict banner | Rise 12 px and fade | 500 ms |
| Check rows | Stagger in | 60 ms apart |
| Chart bars | Grow from the axis | 600 ms |
| Narrative | Fade | 300 ms |
| **Total reveal** | | **~1.2 s** |

Identical in all four verdict states. Making Fail hit harder than Pass would be drama applied to somebody's unequal treatment.

### 8.3 Scroll

- Sections rise 12 px and fade once, on first entry, 40 ms stagger within a section, never re-animating.
- The chart alone parallaxes, capped at 12 px. Nothing else moves with scroll.
- No scroll-jacking. Scroll position and speed are never intercepted.
- No reveals on tables, the technical appendix, or the repairs comparison.
- Content is visible by default; the fade is added only after the observer confirms it runs, so a JavaScript failure leaves a readable document.

### 8.4 What never animates

| Banned | Why |
|---|---|
| Numbers counting up | Reads as a live measurement; these are computed facts |
| Chart values transitioning between states | A disparity that slides from one value to another is a number being edited |
| Table rows entering | Readers scan; motion breaks the scan |
| Auto-rotating anything | Content that moves on its own steals attention from content that matters |
| Parallax on text | It reduces readability measurably |

### 8.5 Reduced motion

`prefers-reduced-motion: reduce` disables every row in §8.2 and §8.3: no transforms, no fades, no parallax, no glyph scanning, no chart growth. State changes become instant and the log renders as plain lines. **This is a manual checklist item** — no automated tool detects a motion violation, which is why it is written down.

### 8.6 Print

`@media print` forces the final state of every animation: bars at full height, sections at full opacity, no transforms. Without this the PDF catches a half-grown chart, which is a bug that looks like a design failure.

It also forces the **light palette**, whatever the theme: a dark-theme print is a black page, and a report forwarded to compliance is a paper document. `@media print` therefore re-declares the light tokens rather than relying on the theme attribute being absent.

---

## 9. Print

| Rule | Detail |
|---|---|
| Trigger | One **Report** button with two outputs, short and full, both through one stylesheet and `window.print()` |
| Switched by | `data-print="full"` on the root element, set immediately before printing |
| Technical sections | Rendered but hidden, never conditionally mounted — content not in the DOM cannot be printed |
| Page | A4, 18 mm margins, `paper` background dropped to white, `print-color-adjust: exact` on verdict panels |
| Theme | Always the light palette, regardless of the viewer's theme (§8.6). A dark-mode print is a black page |
| Hidden | Navigation, action bar, chat panel, repair controls, buttons, contents strip |
| Kept | Verdict, five checks with thresholds, chart, affected groups, narrative, the repair comparison when one exists, dataset name, date, footer |
| Breaks | `break-inside: avoid` on check rows and comparison rows; `break-before: page` before the technical appendix in the full output |
| Filename | `document.title` set during print — `FairLens — loans.csv — 2026-10-27` |
| Footer | The §7.6 disclaimer, on both outputs, every time |

---

## 10. Accessibility checklist

Every line is testable. Section 13 maps each to how it is checked.

| # | Requirement |
|---|---|
| A1 | Text contrast ≥ 4.5:1; large text ≥ 3:1; asserted by a script over the token pairs |
| A2 | No information conveyed by colour alone — every state carries a glyph and a word |
| A3 | Focus visible on every interactive element, 2 px ring, never `outline: none` without a replacement |
| A4 | Full keyboard operation: dropzone reachable and operable by keyboard, dialogs trap focus and return it, no keyboard traps elsewhere |
| A5 | The log is a polite live region; copy confirmations are announced |
| A6 | Charts have a text alternative and a data table |
| A7 | Tables have captions and scoped headers |
| A8 | `prefers-reduced-motion` honoured everywhere (§8.5) |
| A9 | 200% zoom without horizontal scrolling or clipped content |
| A10 | Touch targets ≥ 44 px |
| A11 | Headings in order; one `h1` per page |
| A12 | Form errors associated with their inputs via `aria-describedby`, and announced |
| A13 | No auto-playing media, no time limits on reading (the 55 s budget applies to computation, not to the user) |
| A14 | Print output is legible in greyscale — the verdict word and glyph survive with the colour stripped |
| A15 | Every token pair meets contrast in **both** themes (eight verdict pairs, plus ink on paper) |
| A16 | The theme is correct in the first paint: no flash on reload, and no JavaScript required to resolve it |
| A17 | The theme control has an accessible name and exposes its three states to assistive technology |

---

## 11. Performance budget

The Space shares a CPU and the first visit may follow a cold start, so the interface has to be cheap.

| Budget | Target |
|---|---|
| Font files | 4 maximum, ~180 KB total, woff2, Latin subset, `swap` |
| JavaScript on the report route | ≤ 180 KB gzipped above the framework baseline |
| Animation | `transform` and `opacity` only; nothing that triggers layout |
| Scroll handling | `IntersectionObserver` only — no scroll event listeners, no per-frame work |
| Layout shift | Zero from fonts (size-adjust fallbacks) and zero from reveals (no height changes) |
| Chart | One SVG component; no charting runtime beyond Recharts |
| Images | None. The product has no photography, no illustration, no logos |
| Theme resolution | CSS custom properties and one media query. No JavaScript, no inline script, no extra font weight |

---

## 12. Risks and what is revisitable

| # | Risk | Response |
|---|---|---|
| R-1 | **The serif may look dated in situ.** Type is the decision most often changed after seeing it running | Substitution is one token; nothing else in the system depends on the family. This is the file to change first |
| R-2 | Full motion plus parallax on a shared free-tier CPU | Ordered degradation: drop parallax first, then section reveals, then the glyph field animation. The stagger sequence and the transform panel stay, because they carry meaning |
| R-3 | Instrument Serif ships one weight, so hierarchy rests entirely on size | Deliberate. If a second weight is ever wanted, the family change comes with it |
| R-4 | The glyph field risks looking like a hacker cliché | Kept to 96 × 36 px, ink-weight, no green, no glow. If it reads wrong, it becomes a static glyph and nothing else changes |
| R-5 | `print-color-adjust: exact` is not universally honoured | A14 asserts the document is legible in greyscale, so the printed verdict survives without colour either way |
| R-6 | **A second palette is a second thing to keep correct.** The failure is silent: a hardcoded hex looks right in one theme and wrong in the other | Components may only reference tokens, never literal colours. `contrast.spec.ts` asserts both themes now; the lint rule that fails a literal hex arrives with M7's CI, until then it is review |

---

## 13. Traceability

| Decision | Where enforced | PRD / App Flow it serves |
|---|---|---|
| U1 R6 copy | §7.3 | PRD R6, §8.2 C3, F4-AC5 |
| U2 editorial direction | §1, §2, §5 | F4, F7 print, the "not a dashboard" claim |
| U3 verdict coding | §4, §10 A1–A2 | F4-AC1, F4-AC3, accessibility |
| U4 typefaces | §3, §11 | Performance budget, S2 |
| U5 layout | §5 | F4, F5, F7-AC4 |
| U6 landing | §2, §7 | S2 (verdict in under 60 s), truthfulness |
| U7 confirmation block | §6.4 | F2, F2-AC2, F2-AC3 |
| U8 chart | §6.3 | F4 chart requirement, §8.3 intervals, S3 |
| U9 technical appendix | §6.6 | F5, F5-AC2, F5-AC3 |
| U10–U16 motion | §8 | TRD T8, App Flow A3, A11 |
| Print rules | §9 | F7-AC4, F7-AC5, F7-AC6, A11 |
| Accessibility checklist | §10 | F4-AC3, the axe assertions in TRD T10 |
| Motion ban on numbers | §8.4 | PRD principle 2 (every number traceable, none invented) |
| D1–D3 dark theme | §4.2, §4.3, §8.6, §9, §10 A15–A17 | A user preference with no product impact; recorded here because it changes every colour token |
| Print is always light | §8.6, §9 | F7-AC4, F7-AC5 — a forwarded report is a paper document |

---

*End of UI/UX v2.2. The Implementation Plan is written and starts after day zero.*
