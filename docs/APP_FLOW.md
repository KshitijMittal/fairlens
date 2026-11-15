# FairLens v2 — App Flow

| | |
|---|---|
| **Version** | 2.3 (30 Oct: baseline TRD v2.4 — Gradio Space, Brevo reset) |
| **Status** | All 11 decisions closed. Implementation Plan written. |
| **Date** | 27 October 2026 |
| **Baseline** | `docs/PRD.md` v2.3 and `docs/TRD.md` v2.4 |
| **Next document** | `docs/IMPLEMENTATION_PLAN.md` (written; a change here requires a matching change there) |

---

## 0. How to read this document

- **Section 1** is the whole product as one sentence and one diagram.
- **Section 2** is the route map: ten URLs, and what each one is for.
- **Section 3** defines the small vocabulary of states used everywhere after it, so screen sections can be short.
- **Section 4** is the substance: one subsection per route, listing **every state that route can be in**, what the user sees in it, and what they can do.
- **Section 5** is every transition, as a table, so an implementation can be checked against it.
- **Section 6** covers the four things that happen across screens rather than inside one: the run log, failures, session expiry, and deletion.
- **This document does not specify layout, colour, typography or copy.** It says what is on a screen and what it does. `docs/UI_UX.md` decides how it looks and what the words are.
- A state that exists in this document but not in the build is a missing screen. A state in the build that is not here is either a bug or an undocumented decision.

---

## 1. The flow, in one sentence and one picture

> A visitor opens the site, runs one of three sample datasets without an account, watches the analysis work, gets a verdict with the groups who are affected, and either leaves with a repaired dataset and a printable report — or, for their own file, signs in first and gets the same thing saved to their history.

```
                       ┌──────────────────────────────┐
                       │  /  landing                  │
   anon ──────────────▶│  three sample cards          │
                       │  dropzone → sign-in prompt   │
                       └───────────┬──────────────────┘
                                   │ choose sample / choose file
                                   ▼
                    ┌──────────────────────────────┐
                    │  confirm card  (inline on /)  │
                    │  outcome · positive · groups  │
                    │  [Looks right]  [Change]      │
                    └───────────┬──────────────────┘
                                │ run
                                ▼
                    ┌──────────────────────────────┐
                    │  run log  (inline on /)       │
                    │  six stage lines             │
                    │  [Cancel]                     │
                    └───────┬──────────────┬────────┘
                       error│              │result
                            ▼              ▼
              ┌──────────────────┐   ┌──────────────────────────┐
              │ inline error     │   │ /analysis/{id}           │
              │ [one action]     │   │ verdict, checks, chart,  │
              │ work preserved   │   │ narrative, technical,    │
              └──────────────────┘   │ repairs, chat, report    │
                                      └──────┬─────────┬─────────┘
                                             │         │share
                                    repairs  │         ▼
                                             │   ┌──────────────────┐
                                             │   │ /shared/{token}  │
                                             │   │ same page, viewer│
                                             │   │ flag, no repairs │
                                             │   └──────────────────┘
                                             ▼
                                    ┌─────────────────────┐
                                    │ repair comparison   │
                                    │ + CSV download      │
                                    └─────────────────────┘
```

---

## 2. Route map

Ten routes. One of them is the product.

| Route | Who | Purpose | Needs a session |
|---|---|---|---|
| `/` | everyone | Landing. Run a sample, or upload your own file after signing in | no |
| `/analysis/[id]` | owner, or whoever holds an anonymous sample run id | The report: verdict, checks, chart, narrative, technical view, repairs, chat, report button | no for a sample run |
| `/shared/[token]` | anyone with the link | The same report, read-only, no repair controls | no |
| `/history` | owner | Every analysis this account has run | yes |
| `/login` | everyone | Google sign-in and email + password | no |
| `/signup` | everyone | Create a password account | no |
| `/reset` | everyone | Request a reset email | no |
| `/reset/confirm` | everyone | Consume the token and set a new password | no |
| `/account` | owner | Who you are, how you sign in, appearance, and delete the account | yes |
| `/privacy` | everyone | The privacy page Google requires to exist | no |

**Why `/account` exists.** The PRD requires account deletion to state exactly what is removed (F9-AC3). That needs a page with room for it, and burying the most destructive action in a footer or a dropdown is how people delete the wrong thing.

**Why there is no `/analysis/new`.** The run happens on `/` and the URL changes only when there is something to link to (A1). A temporary progress URL would break on refresh in a way users would read as a bug.

---

## 3. The vocabulary of states

Five generic states apply to any screen that loads data. They are listed once here and referred to by name below.

| State | What it means | What the user sees |
|---|---|---|
| **Loading** | A request is in flight and nothing is known yet | A skeleton of the real layout, not a spinner in the middle of an empty page. No layout shift when data lands |
| **Empty** | The request succeeded and there is nothing | One sentence saying so, plus the single action that would fill it |
| **Error** | The request failed | The failure, in the user's language, with one action (see §6.2) |
| **Forbidden** | Signed out, or not this account's resource | For a missing or someone else's resource: **the same not-found page**. A 403 would confirm the resource exists |
| **Stale** | Data was loaded, then a second request for it failed | The old data stays on screen with a small banner saying it may be out of date and one retry. Never blank a page the user is reading |

Two rules that apply to every screen:

1. **No screen shows a number that is not in the payload.** Not a computed percentage, not a client-side average, not a rounded-up count.
2. **No screen is blank while waiting.** Every waiting state has the shape of what is coming.

---

## 4. Screen by screen

### 4.1 `/` — landing

The only screen an anonymous visitor needs, and the busiest screen in the app: it holds upload, confirmation and the run, in place, without navigation.

**Regions.** Header (sign in / account), a one-paragraph statement of what the product does, three sample cards, the dropzone area, and — once a file exists — the confirmation card or the run log in that same space.

#### States

| State | Trigger | What is shown | Available actions |
|---|---|---|---|
| **Signed out, idle** | default for a new visitor | Three sample cards, each naming the dataset, what it demonstrates, and which checks it is expected to fail. Where the dropzone would be, one line: *to analyse your own file, sign in*. | Run a sample · Sign in · Create account · Read privacy |
| **Signed in, idle** | session present | The same, with a working dropzone replacing the sign-in line | Run a sample · Drop or choose a file · Sign out |
| **Dragging over** | dragenter on the dropzone | Dropzone highlights; copy changes to the file rules (CSV or XLSX, up to 50 MB) | Drop |
| **File chosen, inspecting** | file dropped | The filename, size, and a short indeterminate progress line. The confirm card is not yet shown, because nothing is known about the file | Cancel |
| **Confirmation card** | inspect succeeded | Outcome column in words · which value counts as positive, with counts · the groups being compared, with counts (usually two; age banding gives six) · what happened to any numeric demographic (age banded, and the bands are stated) · how many other columns are factors · one primary action, one secondary | **Looks right — run the analysis** · **Change** |
| **Changing** | `Change` pressed | The same card, with the three selectors, the positive-value choice, the demographic choice, and the age-band editor revealed. Each change re-renders the card's summary before running | Update · Back to summary · Run |
| **Needs sampling choice** | inspect found more than 50,000 rows and at most 100,000 | A choice card, not an error: the row count, the offer to analyse a random 50,000-row sample, analyse everything, or cancel. States that sampling is random, widens the intervals and does not skew the gap | Analyse a sample · Analyse everything · Cancel |
| **Needs sheet choice** | XLSX with more than one sheet | The sheet names, with the first one preselected | Choose sheet · Cancel |
| **Blocked by a data problem** | outcome and demographic are the same column; a single-value column; a positive value that leaves a group empty | The specific reason in one sentence, with **Change** highlighted. Never a generic failure | Change · Choose another file |
| **Running** | run started | The run log (§6.1) replaces the card. The confirmed meaning stays visible above it as a single line so the user can see what is being analysed | Cancel |
| **Run failed** | terminal `error` frame | The log greys out, an error panel appears beneath it (§6.2). The confirmed meaning is still visible | The one action for that error class |
| **Passed through** | `result` frame | Nothing — the app navigates to `/analysis/{id}` | — |

#### Rules

- **A1** — the URL does not change until the result arrives.
- **A2** — an anonymous visitor never causes an upload request. The API's 401 rule is satisfied by never asking.
- **F2-AC6** — no analysis request is issued until *Looks right* is pressed.
- **Cancel** during a run aborts the request and returns the confirmation card with the file intact.
- The sample cards are ordinary links to an action, not pages; running a sample goes straight to the confirmation card, prefilled and correct with no input needed (F2-AC1).
- Sample runs are **not** silent: a signed-in user running a sample gets a history row labelled as a sample (A8). An anonymous user gets nothing stored (PRD F9-AC5). The anonymous result is held in a short-lived server-side cache keyed by the run id, so `/analysis/{id}` renders it, and it is gone within 30 minutes or on restart. No database row is ever written.

---

### 4.2 `/analysis/[id]` — the report

One page, four lead blocks, one skeleton (A5). This is where the product spends its credibility.

#### Regions, top to bottom

| Region | Content | Varies by verdict |
|---|---|---|
| Verdict banner | State word, one-sentence headline, icon plus colour | **Yes** — the lead block |
| Five checks | Name, state, figure, threshold, one plain sentence each | no (states differ, layout does not) |
| Chart | Selection rate by group, historical vs model | no |
| Who is affected | Sentences naming the actual groups and the gap, with its interval | no |
| Narrative | AI prose, or the template clearly labelled | no |
| Actions | Report (print), JSON, share, run repairs | **Partly** — repairs suppressed when Inconclusive |
| Technical view | Collapsed: metric table, per-group table, model card, encoding, influence, proxies, sampling record | no |
| Repairs | Comparison table and downloads | **Yes** — present only for Fail and Warn |
| Chat panel | Closed by default | no |

#### The four lead blocks

| Verdict | Opens with | Primary action | Repairs |
|---|---|---|---|
| **Fail** | Which groups are affected, by how much, and that training on this data would reproduce it | Run repairs | offered |
| **Warn** | The checks that warned, in a sentence, and what they do not mean | Read the warning, then repairs | offered |
| **Inconclusive** | The data problem, in plain words, with the reason from the fixed list | Understand why (nothing to fix here) | **suppressed**, with one line saying why |
| **Pass** | A short confirmation that all five checks passed, and what that does not guarantee | Download the report | not offered |

The checklist, chart, affected-groups paragraph, narrative and technical view are **identical components** in all four states. Only the lead block and the action set differ.

#### States

| State | Trigger | What is shown | Actions |
|---|---|---|---|
| **Loading** | direct navigation, or immediately after the run | The real layout as a skeleton: banner block, five check rows, chart area | none |
| **Fail / Warn / Inconclusive / Pass** | stored result | As above | Report · JSON · Share · (Repairs) |
| **Narrative missing** | no provider reachable and no cached text | The template narrative, visibly labelled as template-generated, complete in itself | Retry is **not** offered — the report is finished either way |
| **Influence unavailable** | SHAP failed | The technical view says the section is unavailable; everything else is intact | none |
| **Repairs: idle** | default | The comparison table appears once a strategy has been run; before that, the three strategies with a short description each | Run all three |
| **Repairs: needs file** | the file is not in this session (page reopened) and the analysis is not a sample | One line explaining the file was not kept, a file picker, and a note that it must be the same file | Choose file · Cancel |
| **Repairs: checking file** | file chosen | A short progress line | Cancel |
| **Repairs: wrong file** | fingerprint mismatch | A plain refusal: this is not the file this analysis was run on, with both fingerprints' first eight characters, and the option to choose again. **No repairs are shown for the wrong file** | Choose again |
| **Repairs: running** | strategies running | A per-strategy progress line; the comparison table fills in as each finishes | none |
| **Repairs: complete** | all three evaluated | Strategy, what changed, model parity, amplification, equal-opportunity gap, accuracy, verdict after, one-line summary, and a recommended marker where earned | Download CSV · Re-run all three |
| **Repairs: nothing helped** | no strategy moved the failing check | The comparison table plus one sentence saying no repair recovered the failing check on this data. No recommendation is invented | Download CSV anyway · Read technical view |
| **Share: none** | no active link | A short explanation of what a share link exposes and does not | Create link |
| **Share: active** | one or more links | Each link: created date, view count, copy, revoke. One line stating that a link shows aggregates only, never rows | Copy · Revoke |
| **Deleted elsewhere** | the analysis was removed in another tab, or an anonymous run id has expired | Not-found page | Back to history, or back to the samples |
| **Forbidden / missing** | wrong id, someone else's id, or deleted | The same not-found page | Back to history |

#### Rules

- **A5** — the skeleton is one thing to build. If a check renders differently inside a Fail than inside a Pass, that is a bug.
- **A6** — repairs run without friction when the file is still in memory; with a fingerprint check when it is not. A sample run never asks for a file: the server still has the bundled CSV, and an anonymous sample run keeps its comparison in memory rather than writing child analyses.
- **A7** — this page and `/shared/[token]` are the same components with a viewer flag.
- **F5-AC1** — the technical view contains no control that changes data or triggers computation. The repairs section is outside it.
- **F4-AC3** — an Inconclusive check is never rendered in the pass colour and never collapsed.
- **Inconclusive suppresses repairs even when four checks passed.** Under PRD §8.5 a single unjudgeable check decides the verdict, so this state is more common than it used to be. Repairs stay hidden because none of the three strategies can create positives, negatives or rows; the one line offered instead says which check could not be judged and why.
- The JSON download is a straight download of the stored payload; nothing is recomputed to produce it (F5-AC4).
- The **Report** button opens a two-item menu (short report / full report with method) and then prints (§6.4).

---

### 4.3 `/shared/[token]` — the read-only report

The same page with the viewer flag. Deliberately not a second design.

| State | What is shown | Actions |
|---|---|---|
| **Loading** | The report skeleton | none |
| **Valid token** | Identical layout, with a small banner: *shared view — read only*. No edit, delete, repair controls, or history link | Report (print) · JSON · Technical view · Chat |
| **Where repairs would be** | If the owner ran repairs: the comparison table, read-only, with no download buttons. If not: one line saying the dataset was not stored, so repairs can only be run by the person who uploaded it | none |
| **Chat** | Available, grounded in this report only, rate-limited per visitor, and never written to the owner's transcript | Ask a question |
| **Revoked or unknown token** | Not-found page. Never an error page, never a "this link was revoked" page — the second tells an outsider the link once existed | none |

**Rules**

- **F7-AC1** — the verdict and every figure match the owner's view exactly, because they are the same components reading the same payload.
- **F7-AC3** — nothing reachable from this route can return a row of the uploaded file, because no rows exist.
- A viewer's chat question does not create an analysis, a history row, a share link or a chat row. The answer is returned and discarded, so the shared page stays read-only.

---

### 4.4 `/history` — what this account has run

| State | What is shown | Actions |
|---|---|---|
| **Loading** | Rows as skeletons, matching the real row height | none |
| **Empty** | One sentence and the three samples as a starting point | Run a sample · Upload a file |
| **With analyses** | Newest first. Each row: dataset name, date, verdict badge, the checks that decided it. Long lists page at 20 with *load more* | Open · Delete · Filter samples |
| **Samples filtered out** | The same list without sample rows, with the filter visible so it is obvious why rows are missing | Show samples |
| **Delete confirm** | A dialog naming the analysis and what it removes | Delete · Cancel |
| **Deleted** | The row disappears in place; no page reload, no toast that outlives the action | — |
| **Error** | Stale rule (§3): the list stays, a banner says it may be out of date | Retry |

**Rules**

- **A8** — samples are saved for signed-in users, marked with a chip, and filterable. Nothing a user ran silently vanishes.
- Sample rows behave like any other row: openable, printable, deletable.
- Deleting an analysis immediately invalidates its share links; a viewer who reloads gets not-found (F9-AC2).

---

### 4.5 Auth screens

Four small screens with more failure states than their size suggests.

#### `/login`

| State | What is shown | Actions |
|---|---|---|
| **Idle** | Continue with Google · or email and password · links to create an account and to reset | Sign in |
| **Submitting** | The form disabled with a progress line; the fields keep their values | — |
| **Wrong credentials** | One message for both wrong password and unknown email: *email or password is incorrect*. Never which | Retry |
| **Rate limited** | How long to wait, in minutes | — |
| **Google unavailable** | The Google button disabled with a line saying email sign-in still works | Sign in with password |
| **Session already valid** | Straight redirect to `/` | — |

#### `/signup`

| State | What is shown | Actions |
|---|---|---|
| **Idle** | Email, password, and one line stating that password accounts depend on an email sender and that Google sign-in is the more durable option (PRD F8) | Create account |
| **Password too short** | The rule, stated plainly and before submission where possible | — |
| **Duplicate email** | *An account with this email already exists*, plus a link to sign in | Sign in |
| **Created** | Signed in and redirected to `/` | — |

**Known asymmetry, accepted deliberately.** Signup reveals whether an address already has an account, while password reset does not (F8-AC3). Hiding it would require either sending a message on every signup — making the least reliable dependency a prerequisite for registering — or returning a silent success that leaves a returning user with no feedback. The reset path, which is the one actually attacked for enumeration, stays uniform.

#### `/reset`

| State | What is shown | Actions |
|---|---|---|
| **Idle** | One field | Send reset link |
| **Submitted** | The same confirmation whether or not the address exists: *if that address has an account, a link is on its way* (F8-AC3), plus a line to check spam — free-tier mail from a shared relay often lands there | — |
| **Rate limited** | How long to wait | — |

#### `/reset/confirm`

| State | What is shown | Actions |
|---|---|---|
| **Valid token** | New password field and the rule | Set password |
| **Expired or used** | One sentence, plus a link to request another. Never says which token state it was | Request a new link |
| **Weak password** | The rule, inline | — |
| **Success** | Signed in, redirected to `/`, one line confirming the password changed and other sessions were signed out | — |

---

### 4.6 `/account`

| State | What is shown | Actions |
|---|---|---|
| **Signed in with password** | Email, how you sign in, the appearance preference, and the delete section | Change password · Theme · Delete account |
| **Signed in with Google** | Email, *you sign in with Google*, the appearance preference, and the delete section. No password form | Theme · Delete account |
| **Theme changed** | The page re-renders in the new theme immediately, because this is the page you are on. The choice is stored in a cookie and applies to every signed-in route from the next request onwards | System · Light · Dark |
| **Delete: confirm** | Exactly what goes: the count of analyses, share links and chat messages, plus the categories, plus *this cannot be undone*. A text field requiring the phrase `delete my account` | Delete everything · Cancel |
| **Deleting** | Progress line | — |
| **Deleted** | Signed out, landing page, one line confirming the account and its data are gone | — |

**Rules**

- **A9** — no email round-trip for deletion. The most irreversible action must not depend on the least reliable part of the stack.
- The typed phrase is compared case-insensitively after trimming; anything else leaves the button disabled.
- Deleting the account from here signs out every other session, because the sessions rows are gone.
- The **theme preference** (System / Light / Dark) lives here and nowhere else. Share-link viewers have no account, so they follow their operating system; there is no control for them. Changing the theme is a deliberate visit to this page, not a control in the header.
- The theme is stored in a cookie and applied while the page is rendered, so there is no flash on reload and no script involved.

---

## 5. Every transition

`from` → `event` → `to`. Anything not in this table is not a transition and is a bug.

| From | Event | To |
|---|---|---|
| `/` signed out | sample clicked | `/` confirmation card (prefilled) |
| `/` signed out | dropzone / sign-in line clicked | `/login` |
| `/login` | success | `/` signed in, idle |
| `/` signed in | file dropped | `/` inspecting |
| `/` inspecting | inspect ok | `/` confirmation card |
| `/` inspecting | inspect failed | `/` error, file preserved |
| `/` inspecting | over 50k rows | `/` sampling choice |
| `/` inspecting | XLSX, several sheets | `/` sheet choice |
| `/` confirmation card | *Change* | `/` changing |
| `/` confirmation card | run | `/` running |
| `/` changing | run | `/` running |
| `/` confirmation card | cancel / choose another | `/` idle |
| `/` running | `stage` frame | `/` running, next line appended |
| `/` running | `result` frame | `/analysis/{id}` loading → verdict |
| `/` running | `error` frame | `/` run failed |
| `/` running | cancel | `/` confirmation card |
| `/` run failed | retry (class-dependent) | `/` running |
| `/` run failed | choose another file | `/` idle |
| `/` run failed | `unauthenticated` | `/login`, and the file must be chosen again |
| `/analysis/{id}` | report → short | print dialog, then back |
| `/analysis/{id}` | report → full | print dialog with technical expanded, then back |
| `/analysis/{id}` | JSON | download, page unchanged |
| `/analysis/{id}` | create share link | `/analysis/{id}`, link row added |
| `/analysis/{id}` | revoke | `/analysis/{id}`, link gone |
| `/analysis/{id}` | repair, file in memory | repairs running → complete |
| `/analysis/{id}` | repair, file absent | needs file → checking → running → complete |
| `/history` | open | `/analysis/{id}` |
| `/history` | delete | confirm → row removed |
| `/shared/{token}` | any | stays; no navigation exists except the print dialog |
| `/account` | theme changed | `/account`, re-rendered in the new theme |
| any authed route | session expired | `/login`, with a return note |

---

## 6. Cross-cutting behaviour

### 6.1 The run log (A3)

The log is an appended list, not a checklist. Upcoming stages are never pre-revealed.

| Property | Behaviour |
|---|---|
| Line set | Six stages — reading your file, cleaning and encoding, training the stand-in model, measuring fairness, computing feature influence, saving results. No per-fold lines: the folds finish inside the training stage |
| Appearance | New line animates in at the bottom; the line above fades to grey and stays. The block has a fixed height and scrolls so the newest line stays visible, so the page never jumps |
| Indicator | A small animated element on the live line. CSS animation, no image asset, and it stops entirely under `prefers-reduced-motion` |
| Accessibility | `aria-live="polite"` on the log container. The current stage is also the text of the line, so nothing depends on the animation |
| Content rule | **No numbers and no findings.** Seven frames total: six stages and one result. A figure in the log is a defect — it either spoils the verdict or puts a number where no later screen will show it |
| Idle protection | A server `ping` frame every 5 seconds keeps the connection observably alive; the client shows nothing for it |
| Cancellation | Cancel aborts the request and returns to the confirmation card with everything intact |
| Buffered proxy | If TRD Gate G1 finds the proxy buffers, frames arrive together at the end and the log renders **all lines complete at once**. It must not replay them slowly to imitate liveness |

### 6.2 Failures (A4)

One inline panel, always in the same place, always with one action.

| Error class | Example | Action offered | What survives |
|---|---|---|---|
| Unsupported file | Not a CSV or XLSX, not tabular | Choose another file | Nothing — there was never a card |
| Too large | Over 50 MB, over 100,000 rows | Sample the file, or choose another | The file |
| Too few rows or columns | Under 50 rows, under 2 columns | Choose another file | The file |
| Ambiguous confirmation | Same column for outcome and group; single-value column | Change | File and card |
| Budget exceeded | The run passed 55 seconds | Sample the file and retry | File and confirmations |
| Unauthenticated | Session expired during the run | Sign in again — **and the file must be re-chosen**, stated plainly because the browser loses it | Nothing |
| Rate limited | Six analyses in an hour | Wait, with the time | File and confirmations |
| Internal | Anything unhandled | Retry | File and confirmations |

Every panel shows: one sentence a non-technical reader understands, the request id in small text for support, and never a stack trace, exception name or SQL (PRD F1-AC6).

Failures from the stream arrive **after** HTTP 200, so the panel is the only signal. The client treats a stream that ends without a terminal frame as an internal error rather than waiting forever.

### 6.3 Session expiry

- A background request returns `401` → the page keeps whatever is on screen, shows a banner offering sign-in, and the user returns to the same URL afterwards.
- A `401` **mid-run** is the one case where work is lost: the file must be re-chosen. Said plainly, not glossed.
- A `401` on a share link cannot happen; those routes need no session.

### 6.4 Print (A11)

One button, two outputs, one stylesheet, switched by `data-print="full"` on the root element immediately before `window.print()`.

| Output | Contains |
|---|---|
| **Short report** | Verdict, five checks with thresholds, chart, narrative, the repair comparison when one exists, dataset name, date, footer |
| **Full report with method** | All of the above plus the technical view as an appendix: metric table, per-group table, model card, encoding decisions, influence, proxies, sampling record |

| Requirement | Why |
|---|---|
| Technical sections are **rendered but hidden**, never conditionally mounted | A collapsed disclosure that is not in the DOM cannot be printed, and the full report would come out empty |
| `document.title` set during print | The saved file is named for the dataset and date, not `localhost` |
| `print-color-adjust: exact` on the verdict badge | Otherwise the colour prints as grey and the most important signal disappears on paper |
| Nav, action bar, chat, repair controls hidden | A printed report is a document, not a screenshot |
| No page break inside the check table or the comparison table | A split table is unreadable on paper |
| Footer on both outputs | The *defaults, not a legal determination* statement is required on every print (F7-AC5) |

The share page offers the same button, so a forwarded report can be forwarded on paper.

---

## 7. What this document deliberately does not cover

| Not here | Where |
|---|---|
| Colours, type, spacing, iconography | `docs/UI_UX.md` |
| The actual words of the verdict headline and the amplification sentence | `docs/UI_UX.md` — this is PRD R6, still open |
| Chart marks, the interval whisker, tooltips | `docs/UI_UX.md` |
| Table columns and API field names | `docs/BACKEND_SCHEMA.md` |
| Order of construction, file by file | `docs/IMPLEMENTATION_PLAN.md` |
| Mobile application | Out of scope (PRD §4). The web app is responsive, which is a layout concern |

---

## 8. Traceability

| App Flow decision | PRD / TRD it serves |
|---|---|
| A1 nav model | F2-AC6, F3, TRD T4 |
| A2 sign-in wall | F8-AC5, Q10 half wall, TRD T7 |
| A3 run log | TRD T4 and Gate G1, PRD F4 |
| A4 error landing | F1-AC6, F12, TRD §7.3 in-band errors |
| A5 verdict layouts | F4-AC1, F4-AC3, §8.5 precedence |
| A6 repair flow | F6, F6-AC2, F6-AC7, §10 no retention |
| A7 share view | F7-AC1, F7-AC3, F5-AC2, F10 chat on share |
| A8 history | F9, F11-AC4, F9-AC5 |
| A9 deletion gate | F9-AC1, F9-AC3, PRD R1 (reset mail independent of the session) |
| A10 chat placement | F10, F10-AC4 |
| A11 print | F7-AC4, F7-AC5, F7-AC6 |
| `/account` route | F9-AC3 |
| Not-found for ownership mismatch | **Amends TRD §8.2**: a resource belonging to another account returns `not_found` (404), not `forbidden` (403), because a 403 confirms the resource exists. The `forbidden` row stays for cases where existence is already known |

---

*End of App Flow v2.3. The Implementation Plan is written and starts after day zero.*
