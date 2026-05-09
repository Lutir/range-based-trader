# Range Scanner — Design Rules
## The North Star for Every UI Decision

*Compiled from studying Apple, Linear, Stripe, Notion, Figma, Airbnb, Spotify, Vercel, Arc Browser, Craft, Things 3, Bear, Calm, Superhuman, Mercury, Ramp, Loom, Pitch, Raycast, Framer, Readwise, Obsidian, Todoist, Medium, Squarespace, Wealthfront, Robinhood, Monzo, Revolut, N26, Coinbase, Duolingo, Strava, Nike Run Club, Peloton, Sonos, Tesla app, TradingView, Bloomberg, and others — plus formal UX research, WCAG 2.1/2.2 AA accessibility standards, and Japandi design philosophy.*

---

## Part 1 — Typography

---

### Rule 1 — Use One Type Family, Two Faces Maximum
**Principle:** Use Inter (or a comparable humanist sans-serif) for all UI text. Use JetBrains Mono (or similar geometric monospace) exclusively for numbers, tickers, code, and prices. Never introduce a third typeface.

**Why it works:** Cognitive load research (Miller, 1956; Sweller, 1988) shows the brain spends measurable effort switching between visual contexts. Two well-chosen faces cover every reading job in a financial dashboard: prose for explanations, monospace for data. Every additional typeface competes for attention and degrades perceived quality. Apple uses SF Pro + SF Mono. Stripe uses Inter exclusively. Bloomberg limits itself to two faces across the entire terminal.

**How to apply in our app:**
- All labels, headings, narratives, sidebar text: `Inter`
- All ticker symbols, prices, scores, percentages, any number in a table or metric card: `JetBrains Mono`
- The `font-family` in our CSS already follows this — enforce it strictly on every new element.
- When adding score displays or price columns, always wrap in `font-family: 'JetBrains Mono', monospace;`

**Examples:** Stripe (Inter throughout), Linear (Inter + mono for shortcuts), TradingView (custom mono for all price data).

---

### Rule 2 — Lock the Type Scale to a Ratio
**Principle:** Use a consistent modular type scale. Our scale: 0.7rem (labels/captions) → 0.75rem (metadata) → 0.85rem (secondary text) → 0.9rem (body small) → 0.95rem (body) → 1.05rem (h3) → 1.3rem (h2) → 1.8rem (h1). Never invent ad hoc sizes.

**Why it works:** A modular scale (Robert Bringhurst's work on the "elements of typographic style") creates visual rhythm — the eye learns the hierarchy pattern and navigates faster. Violating the scale breaks rhythm without the reader knowing why. Every major design system (Apple HIG, Material 3, IBM Carbon) is built on a ratio-locked scale.

**How to apply:**
- The five sizes in our current CSS match this scale — do not deviate.
- If a new UI element needs text, pick the closest step down from context.
- Resist the urge to make something "slightly bigger" — use the next defined step or accept the existing one.

**Examples:** Apple's SF type system, IBM Carbon Design System, Material 3.

---

### Rule 3 — Tighten Tracking on Large Headings, Loosen on Caps
**Principle:** Headings at 1.3rem+ should have `letter-spacing: -0.01em` to `-0.02em`. All-caps labels (like metric card labels) should have `letter-spacing: 0.05em` to `0.08em`.

**Why it works:** At large optical sizes, the default letter spacing between characters appears too loose — designers call this "floating letters." Tightening it makes headings cohere into a word-shape rather than a string of letters. Conversely, capitals set in small sizes need more air because capital letters are already dense forms. This is why our metric card labels ("SCORE", "SUPPORT") use `0.05em` tracking and our h1 uses `-0.02em`.

**How to apply:**
- Any heading class: ensure negative tracking is applied.
- Any uppercase label: ensure positive tracking `0.05em+`.
- This is already in our CSS — enforce on every new metric card or heading.

**Examples:** Linear (headlines at -0.02em), Stripe (section labels at 0.08em), Vercel (h1 at -0.03em).

---

### Rule 4 — Line Height 1.5–1.7 for Body Text, 1.2–1.3 for Headings
**Principle:** Narrative/reasoning text gets `line-height: 1.65`. Short display labels and headings get `line-height: 1.2`. Never use default browser line-height (1.2) for body text — it is unreadable at paragraph length.

**Why it works:** Readability research (Legge & Bigelow, 2011) shows 1.5–1.7x line height maximizes reading speed and comprehension for Latin text at typical screen sizes. Our "Analysis" narrative blocks are 3–5 sentences — they need generous leading. Headings are 1–5 words and don't need it.

**How to apply:**
- Our `p, li, .stMarkdown` already sets `line-height: 1.6` — keep it.
- The narrative div blocks in scanner.py and detail.py use `line-height: 1.8` — appropriate.
- Score breakdown tables and short labels: line-height can be 1.2–1.3.

---

### Rule 5 — Minimum 14px for All Interactive or Readable Text
**Principle:** No interactive label, tooltip content, or readable body text below 14px (0.875rem). Decorative/legal footnotes may go to 11px minimum. On HiDPI screens 14px renders sharply; below it, sub-pixel rendering creates blur.

**Why it works:** WCAG 2.1 SC 1.4.4 requires text to be resizable to 200% without loss of function. The empirical floor for comfortable reading on a 96dpi screen is 14px. Our current "disclaimer" text at `0.7rem` (11.2px) is near the limit — acceptable only because it is truly supplementary, not informational.

**How to apply:**
- Sidebar navigation: `0.95rem` — correct.
- Metric card labels at `0.75rem` (12px): acceptable for a CAPS label; could be nudged to `0.8rem`.
- Never create new text classes below `0.75rem` unless it is a decorative separator.

---

## Part 2 — Color

---

### Rule 6 — Use Warm Neutrals as the Base, Not Cold Grays
**Principle:** Our background palette (`#FAF8F5`, `#F0EDE8`, `#E8E4DF`) is intentionally warm — slightly yellow-brown, not blue-gray. This is non-negotiable. Every new component must use colors from or adjacent to this warm neutral family.

**Why it works:** Cool grays (`#F5F5F5`, `#EEEEEE`) are the default of every SaaS template and feel generic. Warm neutrals — the palette of stone, linen, unbleached cotton, aged paper — register subconsciously as crafted and intentional. This is the foundation of Japandi design and is used deliberately by Notion, Bear, Linear (light mode), Craft, Readwise, and Things 3. The warmth also reduces eye strain under extended use because pure white on a bright screen creates the highest possible contrast ratio, which fatigues.

**How to apply:**
- Background: `#FAF8F5` (main), `#F0EDE8` (sidebar), `#F5F2EE` (cards), `#E8E4DF` (borders/hover states).
- Never introduce `#FFFFFF` as a background. Never use `#F5F5F5` or any cool-cast gray.
- If Streamlit forces a white default somewhere, override it in CSS.

**Examples:** Notion (warm `#FFFEF9`), Bear (warm `#F8F6F1`), Craft (`#FBF9F6`), Linear light mode.

---

### Rule 7 — The One Accent Rule
**Principle:** One accent color only: `#5B8A72` (muted sage green). It is used for: primary buttons, progress bars, active states, positive indicators, and left-border accents on narrative cards. No second accent color is permitted unless the semantic meaning demands it (e.g., a warning amber).

**Why it works:** Multiple accent colors divide visual attention. The eye naturally seeks the highest-contrast or most saturated element in a composition — that is what the accent color does. If two elements compete for this role, neither wins, and the hierarchy collapses. Japandi and Scandinavian design philosophy codifies this as "one material moment per composition." Linear uses a single purple accent. Stripe uses a single blue-violet. Mercury uses a single blue-green.

**How to apply:**
- `#5B8A72`: primary buttons, progress fills, "positive" metric deltas, left-border accents, active nav state.
- `#C27D5E` (muted terracotta): secondary accent for warnings, "pressing resistance" verdicts, "moderate risk" states only.
- These two are our complete accent palette. They are both muted (low saturation), intentionally — neither screams.
- If a third color is needed, look to semantic badges (see Rule 13) not new accents.

**Examples:** Linear (electric purple as sole accent), Stripe (indigo-blue), Mercury Banking (blue-green).

---

### Rule 8 — Semantic Color Coding for Financial Values
**Principle:** Positive values = muted green (`#2D5F3B` text, `#D4EDDA` background). Negative values = muted red-rose (`#721C24` text, `#F8D7DA` background). Neutral/watchlist = warm amber (`#664D03` text, `#FFF3CD` background). Caution/information = muted teal (`#0C5460` text, `#D1ECF1` background).

**Why it works:** Financial apps have a universal color contract: green = up/good, red = down/bad. Deviating from this contract creates dangerous cognitive dissonance in a data-heavy tool. However, the specific shades matter: saturated `#00FF00` and `#FF0000` create eye fatigue and have poor contrast. Muted, desaturated versions of these hues carry the semantic signal without the aggression. Wealthfront, Mercury, and Monzo all use muted green/red systems.

**How to apply:**
- Our current badge system (`badge-excellent`, `badge-broken`, etc.) follows this correctly.
- When showing score deltas, gain/loss numbers, or change indicators: apply these semantic classes.
- Never use raw green or raw red (`#00FF00`, `#FF0000`, `#008000`, `#CC0000`).
- Colorblind consideration: always pair color with a label or icon — never rely on color alone (WCAG 1.4.1).

**Examples:** Monzo (forest green/rose red), Robinhood (green/red with white text), Wealthfront (muted green for gains), Revolut (their semantic color tokens are publicly documented).

---

### Rule 9 — Maintain WCAG AA Contrast on All Text
**Principle:** Normal text (below 18px or 14px bold): minimum 4.5:1 contrast ratio against background. Large text (18px+ or 14px+ bold): minimum 3:1. Interactive element boundaries: minimum 3:1.

**Why it works:** WCAG 2.1 Level AA is the legal standard for accessibility in many jurisdictions and represents the point at which the majority of users with low vision can read comfortably. Beyond compliance, adequate contrast correlates with faster reading speed for all users. Our warm neutrals require careful checking because warm colors can fool the eye — `#B8B2A8` on `#FAF8F5` is only ~2.5:1 and should not carry essential information.

**How to apply:**
- Main body text `#4A4540` on `#FAF8F5`: passes AA at ~8.2:1.
- Secondary text `#7A756E` on `#FAF8F5`: ~4.6:1 — borderline passes AA; do not go lighter.
- Muted text `#B8B2A8` on `#FAF8F5`: ~2.5:1 — use only for decorative or legal text, never for data.
- When in doubt, use https://webaim.org/resources/contrastchecker/ before shipping.
- The sidebar `#F0EDE8` background raises the floor — `#7A756E` text on it needs verification.

**Examples:** Stripe's design system includes contrast checks in all token documentation. Linear publishes accessible color tokens.

---

### Rule 10 — Dark Mode Is a First-Class Decision, Not an Afterthought
**Principle:** If dark mode is added, it must use our warm neutral vocabulary in the dark register: `#1C1A17` (background), `#242220` (card), `#2E2B27` (elevated surface), `#4A4540` (border), with text at `#E8E4DF` (primary) and `#9A948C` (secondary). Never use pure black (`#000000`) as a dark mode base.

**Why it works:** Pure black backgrounds create an extreme luminance ratio with white text that causes the halation effect — bright text "bleeds" into the dark background on most LCD panels. Warm near-blacks (with a slight brown/yellow cast) reduce this. This is why Apple uses `#1C1C1E` not pure black. Our light mode is warm, so our dark mode must mirror the same temperature.

**How to apply:**
- Currently not implemented — this is a future decision point.
- If Streamlit dark mode is toggled by users, our CSS overrides may need a `@media (prefers-color-scheme: dark)` block.
- The color mapping: light `#FAF8F5` → dark `#1C1A17`, light `#F5F2EE` → dark `#242220`, light `#E8E4DF` → dark `#2E2B27`.

**Examples:** Bear (warm `#1A1916` dark background), Obsidian (configurable warm dark), Readwise (warm sepia dark mode option).

---

## Part 3 — Space and Layout

---

### Rule 11 — Whitespace Is a Design Element, Not Wasted Space
**Principle:** Generous whitespace between sections communicates that content is organized and that each section is complete in itself. Our standard section gap is `2rem` (margin-top on h2). Card padding is `16px–24px`. Never compress padding to fit more content — remove content instead.

**Why it works:** Jakob Nielsen's research on information scent shows users scan pages by searching for boundaries between content zones. Whitespace provides those boundaries more clearly than lines or boxes. Apple's design language is built on the idea that "what is not there is as important as what is." Removing a low-value section creates more clarity than adding padding. Japandi design calls this "ma" — negative space with intentional meaning.

**How to apply:**
- The `2rem` margin-top on h2 (in our CSS) creates section breathing room — never reduce this.
- Between metric rows (`st.columns`), add a small `st.markdown("")` spacer if sections feel compressed.
- If a page feels cluttered, the answer is removal, not compression. Audit which sections are truly needed.
- Progress bars, dividers (`---`), and borders should separate sections — not compensate for insufficient whitespace.

**Examples:** Apple (minimal padding and vast surrounding space), Notion (wide margin + single-column reading area), Linear (section separation through space, not lines).

---

### Rule 12 — Respect the Reading Width
**Principle:** Narrative text blocks (the AI analysis paragraphs) should max out at approximately 70–80 characters per line. In our wide-layout Streamlit app, this means narrative divs should not span more than ~700px or roughly 60% of the main content width on large screens.

**Why it works:** The optimal line length for comfortable reading is 50–75 characters (Baymard Institute, 2012; multiple typography studies). Below 50, the eye makes too many returns. Above 80, it loses its place. Our current narrative blocks (`border-left: 3px solid`) span the full column width — on large monitors this becomes an 100-character line, which is fatiguing. Medium, Bear, and Notion all enforce a narrow content column for prose specifically.

**How to apply:**
- Wrap narrative divs with `max-width: 720px`.
- The score breakdown tables and data grids CAN span full width — that is appropriate for tabular data.
- Charts and visualizations: full width is correct.
- Only prose paragraphs need the max-width constraint.

**Examples:** Medium (740px content column), Bear (600px note width), Craft (680px body column).

---

### Rule 13 — Use a 4px or 8px Spacing Grid
**Principle:** All padding, margin, gap, and sizing values must be multiples of 4px (4, 8, 12, 16, 20, 24, 32, 40, 48, 64). No `7px`, `11px`, `13px`, or other arbitrary values.

**Why it works:** A consistent spatial grid means every element aligns with every other element without explicit alignment rules. The eye detects misalignment at even 1px on a HiDPI screen. Google Material Design, Figma's default grid, and Apple's HIG all use the 8px base grid (or 4px for fine adjustments). Components built on a grid will always look intentional together; components on arbitrary values will always look slightly off.

**How to apply:**
- Check existing CSS: our `padding: 16px 20px` (good), `border-radius: 10px` (acceptable), `margin-top: -8px` (good), `padding: 4px 12px` (good).
- When writing new inline styles, mentally check: is this a multiple of 4?
- Exception: `border-radius` values like `20px` for pills are fine as optical choices, not grid choices.

**Examples:** Figma's own interface (8px grid everywhere), Linear (4px grid), Stripe's component library.

---

### Rule 14 — Information Hierarchy: Most Important First, Always
**Principle:** On every screen, the most important piece of information must be visually dominant and positioned at the top-left (for left-to-right language users). The reading sequence should mirror the decision-making sequence: verdict → score → evidence → detail.

**Why it works:** The F-pattern and Z-pattern eye-tracking research (Nielsen Norman Group) shows users begin at top-left and scan rightward, then down. Information placed outside this path will be missed or read last. In the Ticker Detail page, the verdict banner (`EXCELLENT RANGE`) correctly appears before the score grid, which appears before the score breakdown table — this mirrors how a trader actually processes information.

**How to apply:**
- Ticker Detail: verdict banner → score row → range structure → risk indicators → trend indicators → price chart → score breakdown. This is correct — maintain this order.
- Scanner page: summary metrics → ranked results → narratives. Correct.
- Never put a "configuration" section below results. Config belongs above scan, results below.
- If adding new sections, ask: where does this fall in the decision hierarchy?

**Examples:** Robinhood (stock detail: price dominant, graph, then fundamentals), Wealthfront (portfolio value first, allocation second), Bloomberg Terminal (headline prices in the top strip).

---

### Rule 15 — Scannable Tables: Numbers Right-Aligned, Text Left-Aligned
**Principle:** In all financial tables, numerical columns must be right-aligned. Text columns (Ticker, Verdict, Reason) must be left-aligned. Column headers align with their column content.

**Why it works:** Right-alignment of numbers allows the eye to use the right edge as a vertical ruler — values then differ at the most significant position (leftmost digit), making comparison instant. When numbers are left-aligned, the decimal points are scattered and comparison requires active scanning. Bloomberg Terminal, every spreadsheet application, and every financial data provider uses right-aligned numerals. This is not aesthetic preference — it is the physics of numeric pattern recognition.

**How to apply:**
- Streamlit's `st.dataframe` with `st.column_config.NumberColumn` automatically right-aligns — use it for all numeric columns.
- The `st.column_config.ProgressColumn` is an exception — it is a bar visualization.
- The "Range" column (`$284.10 – $294.20`) should be right-aligned or monospaced so the dollar amounts line up.
- The "Reason" column is text — left-aligned, which it already is.

**Examples:** Bloomberg, Excel, TradingView's watchlist table, every brokerage platform.

---

### Rule 16 — Use Progress Bars and Visual Encoding for Scalar Scores
**Principle:** Score values (0–100) must use a visual encoding — our `st.column_config.ProgressColumn` — not raw numbers in a text column. The visual bar allows instant relative comparison between rows.

**Why it works:** Pre-attentive processing research (Treisman & Gelade, 1980) shows humans perceive length, area, and color differences before conscious attention engages. A row of 74, 68, 61, 55 requires reading and mental comparison. The equivalent bar chart is processed in a single fixation. TradingView's screening tables, Robinhood's performance visualizations, and Strava's activity comparisons all exploit this.

**How to apply:**
- Score and Entry columns: `ProgressColumn` — already implemented.
- Width%, Rotation, Gap% could also benefit from subtle bar encoding if the table gets complex.
- The `ProgressColumn` also prevents negative numbers from rendering as red warnings — keep min_value=0.

---

### Rule 17 — Fixed Column Widths for Scannable Tables
**Principle:** In the scanner results table, the Ticker column must be narrow and fixed. Score and Entry are narrow. Verdict is medium. Reason is wide. Giving each column an appropriate fixed width prevents the table from re-flowing as data changes.

**Why it works:** When column widths vary based on content, the table shifts layout on each scan, forcing the user to re-learn the visual structure. Fixed proportional widths mean the user learns the layout once: "Ticker is always column 1, narrow; Reason is always the last wide column." This is how Bloomberg Terminal, spreadsheets, and TradingView tables behave — the layout is a learned interface pattern.

**How to apply:**
- `st.column_config.TextColumn("Ticker", width="small")` — already in use.
- Extend this principle to Verdict (`width="medium"`), Risk (`width="small"`), Reason (`width="large"`).
- If adding columns, assign a width; never leave it unspecified.

---

## Part 4 — Components and Interaction

---

### Rule 18 — Every Interactive Element Needs a Hover State
**Principle:** Every clickable or interactive element must have a distinct visual hover state that signals affordance before the click. Minimum: a subtle background color shift. Better: a slight transform or shadow change. Our buttons already use `translateY(-1px)` + shadow on hover — this pattern should apply to all interactive elements.

**Why it works:** Gibson's theory of affordances (1977) and modern UX research both confirm that users need visual confirmation that an element is interactive before committing to a click. Without hover states, interactive elements feel "flat" and unresponsive. This is a primary reason why Superhuman, Linear, and Raycast feel alive — every interaction point responds to approach, not just to commitment.

**How to apply:**
- Buttons: `translateY(-1px)` + `box-shadow` — already implemented.
- Sidebar nav items: `background: #E8E4DF` on hover — already implemented.
- Table rows: `cursor: pointer` + subtle background shift if rows become clickable (e.g., click row to go to Detail page).
- Any clickable ticker in results should show `cursor: pointer` and a hover highlight.
- Transition duration: `0.15s` for micro-transitions, `0.2s` for slightly larger ones. Never exceed `0.3s` for hover states.

**Examples:** Raycast (every list item has a hover card state), Linear (row hover is instant and obvious), Stripe dashboard (hover reveals action icons).

---

### Rule 19 — Loading States Must Be Honest and Informative
**Principle:** Never show a bare spinner. Always show: what is happening, how far along we are (if measurable), and an estimated scope. Our current `st.progress()` with text messages ("Fetching market data (parallel)...") is correct — maintain and extend this pattern.

**Why it works:** Nielsen's "Response Time Limits" research (1993) established that anything over 1 second needs a visual indicator, and anything over 10 seconds needs a progress indicator with feedback. Without this, users cannot distinguish between "working" and "broken." Perceived performance (how fast something feels) can be significantly better than actual performance when progress communication is good. Superhuman is famous for its skeleton screens. Loom uses animated illustrations during upload.

**How to apply:**
- Scanner: `st.progress(0, text="Fetching market data...")` → `progress(0.7, text="Analyzing structures...")` → `progress.empty()`. Correct.
- Detail page: `st.spinner(f"Fetching and analyzing {ticker}...")` — acceptable for a short operation.
- Backtest page: if it runs long, add phased progress similar to the scanner.
- Never use `st.spinner` for operations expected to exceed 5 seconds — use `st.progress` with text.

**Examples:** Loom (detailed upload progress with step names), Linear (skeleton UI during data load), Notion (blocks appear progressively as data loads).

---

### Rule 20 — Empty States Are Teaching Moments
**Principle:** Every empty state (no results, no charts, no data) must: (1) explain why it is empty, (2) tell the user what to do, (3) show a visual that reinforces the message — a symbol or illustrative element, not just text. Our Charts page empty state with the `◧` symbol and `code` block showing the command is the right pattern.

**Why it works:** Empty states are the most underutilized opportunity in UX design (Luke Wroblewski, 2012). A blank page says "broken." A designed empty state says "ready — here is what to do." Users who encounter a well-designed empty state are far more likely to take the suggested action than users who encounter a blank space. Duolingo, Todoist, and Strava all have memorable empty states that function as micro-onboarding.

**How to apply:**
- Charts page: already correct.
- Scanner results with no matches: `st.info("No range candidates found. Try a different universe or lower the filters.")` — acceptable, but could be enhanced with a suggestion to try specific other universes.
- Settings page with no API key: should show a clear "Set your API key to get started" state, not a broken form.
- Pattern: large symbol or icon (our geometric shapes work well), heading, explanation, action.

**Examples:** Duolingo (streak empty state with owl), Todoist (empty task list with encouraging message), Notion (new page template picker).

---

### Rule 21 — Error Messages Must Diagnose and Prescribe
**Principle:** Every error message must answer three questions: what went wrong, why it went wrong, and what the user can do about it. Never show a raw exception. Never show a message that ends in "." when it should end in a concrete action.

**Why it works:** Error messages that provide no corrective path create what psychologists call "learned helplessness" — the user feels powerless and abandons the task. Krug's usability research shows users are far more forgiving of errors when the fix is obvious. Stripe's error messages are the gold standard in the industry: specific, non-blaming, with a concrete suggested action.

**How to apply:**
- `st.error(f"Insufficient data for {ticker}.")` — add: "This ticker may be too new or delisted. Try AAPL or MSFT to test the tool."
- `st.error("Invalid close price")` — too technical. Change to: "Could not get valid price data for {ticker}. It may be delisted or have a data gap."
- For API failures in data.py: surface a clear "API key may be invalid or rate-limited. Check Settings." message.
- Always end error messages with what to try next, not what went wrong.

**Examples:** Stripe ("The card number is incomplete. Double-check and try again."), Linear (specific error + action link), Vercel (deployment errors with log links).

---

### Rule 22 — Micro-interactions Signal Correctness
**Principle:** Small interactions — button press feedback, state changes, transitions — must feel instant and physical. Our `transform: translateY(-1px)` on button hover is correct. Every state change (scan complete, filter applied) must have a perceptible but brief visual transition.

**Why it works:** Micro-interactions (Dan Saffer, 2013) provide the "feel" layer of an application. They communicate cause and effect — "I pressed this button and something happened." Without them, interfaces feel hollow and mechanical. The absence of micro-interactions is the primary reason generic enterprise software feels cold. Raycast, Craft, and Calm are masters of this: every action produces a satisfying physical metaphor.

**How to apply:**
- Button press: already has hover `transform` + shadow — this is the micro-interaction.
- After scan completes: the progress bar disappearing and results appearing is the micro-interaction — do not add an explicit animation on top.
- Badge rendering: the CSS `transition` on sidebar nav items is correct.
- Streamlit's capabilities here are limited (server-rendered) — use CSS transitions on elements that change state in the browser without a round-trip.

**Examples:** Raycast (every action has haptic-like visual spring), Craft (smooth editor transitions), Linear (instant keyboard responses).

---

### Rule 23 — Badges and Pills for Categorical State
**Principle:** Categorical states (verdict labels, risk levels, edge positions) must always appear as visual badges/pills — colored background + colored text — never as plain text. Plain text labels in data-dense environments are invisible.

**Why it works:** Categorical data needs pre-attentive visual encoding. Color + shape (the pill) creates a visual token the eye can locate and classify without reading. TradingView's signal badges, Robinhood's recommendation labels, and Linear's status labels all use this pattern. Plain text in a crowded table is just more text.

**How to apply:**
- Our `.verdict-badge`, `.badge-excellent`, etc. classes are correct — use them for all verdict rendering.
- When displaying risk levels (LOW/MEDIUM/HIGH) and breakout risk in tables, consider applying badge styling.
- The "Verdict" column in our scanner table currently renders as plain text — wrapping in badge HTML would improve scannability significantly.
- Pill border-radius: `20px` for status badges (oval), `6px` for category tags (rectangular rounded).

**Examples:** Linear (status pill in every issue row), GitHub (label badges on PRs), Jira (colored status indicators), TradingView (signal badges).

---

### Rule 24 — Expanders and Progressive Disclosure for Depth
**Principle:** Hide detail by default. Surface only what is needed to make a decision. Deeper analysis, methodology explanations, score breakdowns, and legends should live in expanders or secondary views. Our "How to use this page" expander and "Detailed Analysis (top 10)" expander are correct applications of this principle.

**Why it works:** Progressive disclosure (Bruner, 1960; popularized in UX by Don Norman) reduces the initial cognitive burden by hiding complexity. Users who want depth can access it, but the default view presents only decision-relevant information. Stripe's dashboard is the master class: everything is summary-first, with expandable detail rows. Linear hides metadata behind hover states.

**How to apply:**
- "How to use this page": already an expander — correct.
- Detailed narratives: already behind an expander — correct.
- Score breakdown table in Detail page: this is already revealed via a page section rather than buried, which is appropriate since the Detail page's whole purpose is depth.
- Settings page: group advanced thresholds behind an "Advanced" expander, not inline with basic settings.

**Examples:** Stripe (transaction detail drawer), Linear (metadata panel on issue), Notion (inline page preview on hover).

---

### Rule 25 — Navigation Must Show Current State
**Principle:** The active navigation item must be visually unambiguous — distinct from all inactive items through at least two visual cues (color + weight, color + border, weight + background). One cue (color only) fails for colorblind users and is borderline even for others.

**Why it works:** Users need constant wayfinding signals in multi-page applications. If the active page is not obviously marked, users disoriented by using browser back/forward lose their place. Arc Browser, Linear, and Notion all use strong active state indicators: background fill + font weight change. WCAG 1.4.1 requires that information conveyed by color alone is not the sole differentiator.

**How to apply:**
- Our sidebar `st.radio` currently uses Streamlit's default active state, which is a color-only change (the green accent dot). This is borderline.
- Add a CSS rule for the selected radio label: `font-weight: 600; background-color: #E8E4DF; color: #2D2A26;`
- The current page context should also appear in the page title (already true: "Scanner", "Ticker Detail" titles).

**Examples:** Arc Browser (bold active tab with background), Linear (filled background + heavier text), Things 3 (selected sidebar item gets filled background).

---

## Part 5 — Data Visualization

---

### Rule 26 — Charts Must Have One Clear Message
**Principle:** Each chart should be designed to answer one specific question. Our price chart in Detail page answers: "Where is price relative to the range?" It shows: Price, Support, Resistance, Midpoint. Four lines, one message. If a chart is answering three questions, it should be three charts.

**Why it works:** Edward Tufte's "data-ink ratio" principle: every mark on a chart should carry information or be removed. Multiple competing messages in one chart force the viewer to mentally separate and serially process them. Bloomberg Terminal charts are the extreme (highly dense) — but Bloomberg users are trained specialists. For our app, one clear message per chart serves the decision-making workflow.

**How to apply:**
- The line chart in Detail: Price + Support + Resistance + Midpoint = correct. Four lines is the maximum.
- If adding volume bars or ADX overlays: consider a second separate chart, not an overlay on the price chart.
- The exported PNG charts (in Charts page) from `charts.py` should have a clear title stating the message ("AAPL — Range Structure Active, 6.2% Width").
- Never add trendlines, moving averages, volume, and range lines all to the same chart without a deliberate visual hierarchy separating them.

**Examples:** TradingView (primary chart + separate indicator sub-panels), Wealthfront (portfolio performance: single line, no overlays), Strava (pace chart: single metric, clear).

---

### Rule 27 — Color-Encode the Range Position Consistently
**Principle:** Across all visualizations, support = green (`#5B8A72`), resistance = terracotta (`#C27D5E`). This mapping must be applied everywhere a range boundary appears: charts, metric card labels, badges, position indicators.

**Why it works:** Color-coding must be consistent or it costs the user re-learning effort on every screen. Once users learn "green = support" they leverage that in every decision. Inconsistency forces conscious re-evaluation. Monzo uses consistent green for credits and red for debits everywhere — the user never has to wonder.

**How to apply:**
- Detail page position indicator: `#5B8A72` at left (support label), `#C27D5E` at right (resistance label) — already correct.
- Charts exported by `charts.py`: support line should be `#5B8A72`, resistance line `#C27D5E`.
- Any future chart overlays in the Streamlit line chart: `color` parameter for Support series = `#5B8A72`, Resistance = `#C27D5E`.
- Badge colors for "PRESSING SUPPORT" vs "PRESSING RESISTANCE" already follow this convention.

---

### Rule 28 — Numbers: Format for Instant Recognition
**Principle:** Prices always show two decimal places (`$284.10`). Percentages show one decimal place (`6.2%`). Dollar volumes use abbreviated notation (`$4.8B`, `$120M`). Scores are integers (`74`). Never show `0.0621` when you mean `6.2%`. Never show `4800000000` when you mean `$4.8B`.

**Why it works:** The brain's numerical processing uses pattern recognition: `$4.8B` is two characters + a scale suffix, processed in one fixation. `4800000000` requires counting digits, which is serial processing. Kahneman's System 1/System 2 model: formatted numbers engage the fast recognition system; unformatted numbers force slow counting. Bloomberg, every financial terminal, and every professional finance app abbreviates large numbers.

**How to apply:**
- Current issue: `avg_dollar_volume` in the scanner table renders as a raw large integer (e.g., `4800000000`). This must be formatted.
- Add a helper function: `def fmt_dollar_vol(n): return f"${n/1e9:.1f}B" if n >= 1e9 else f"${n/1e6:.0f}M"`.
- Score columns: already formatted as integers via `ProgressColumn format="%d"`.
- Width%, Gap%, position: already `:.1f` — correct.
- The `"Range"` column showing `$284.10 – $294.20` uses `:.1f` for support/resistance; could be argued to use `:.2f` for precision since users will reference these prices exactly.

---

### Rule 29 — The Position-in-Range Indicator Is The Highest-Value Visualization
**Principle:** The horizontal gradient bar showing price position within a range (in the Detail page) is the most important visual element of the entire app. It must be immediately comprehensible to anyone who glances at it without reading any label.

**Why it works:** Spatial metaphors (left = low/support, right = high/resistance) align with universal intuition. This visualization encodes four pieces of information simultaneously: the existence of a range, the boundaries, the current price location, and the relative distance from each edge — in a single pre-attentive visual unit. This is the kind of "one glance" information design that Apple obsesses over, Robinhood uses for portfolio allocation, and Wealthfront uses for goal progress.

**How to apply:**
- The current implementation with the gradient background and dot cursor is correct and should be preserved exactly.
- Extend this to the scanner results table: instead of a text "Edge" column, consider a mini inline position indicator (a tiny progress bar representing position, 0% = support, 100% = resistance).
- Color gradient (`#5B8A72` → white → `#C27D5E`) already reinforces the semantic color convention from Rule 27.

---

### Rule 30 — Sub-Scores as a Breakdown Chart, Not a Table
**Principle:** The score breakdown in the Detail page is currently rendered as a `st.dataframe` table. This should ideally be a horizontal bar chart — one bar per component, sorted by contribution, with the weight shown as a label. A bar chart lets the user see instantly which components are dragging or boosting the score.

**Why it works:** Tabular score breakdowns require reading each row individually and mentally mapping the number to its position on a 0-100 scale. A bar chart makes this spatial — long bar = high score, short bar = low score — and sorting by value reveals the dominant factors immediately. Wealthfront's portfolio breakdown, Strava's training load analysis, and TradingView's indicator summaries all use bar charts for multi-component scoring, not tables.

**How to apply:**
- Replace or supplement `st.dataframe(score_data)` with `st.bar_chart` or a Plotly horizontal bar chart.
- Sort descending by Score value.
- Color bars: scores above 60 = `#5B8A72`, 40-60 = `#B8860B`, below 40 = `#C27D5E`.
- Keep the current table below the chart for users who want the exact numbers and weight explanations.

**Examples:** Wealthfront (allocation breakdown bars), Strava (fitness/freshness bar chart), TradingView's oscillator panels.

---

## Part 6 — Japandi Design Specifics

---

### Rule 31 — Form Follows Function, Then Stop
**Principle:** Every visual element must earn its place by performing a function. If removing a design element does not hurt usability or information delivery, remove it. Our sidebar "Quick Guide" panel serves a function (orienting new users). The disclaimer at the bottom serves a function (legal/ethical clarity). The `◐` logo serves a function (identity/recognition). Decorative separators beyond a single `---` do not earn their place.

**Why it works:** Japanese "wabi-sabi" aesthetic philosophy holds that beauty emerges from the natural, imperfect, and incomplete — not from ornamentation. Scandinavian "functionalism" says the same thing from an engineering angle. Both traditions converge on: add nothing that does not serve. The cleanest apps (Linear, Notion, Things 3, Bear) feel luxurious precisely because there is nothing wasted in them.

**How to apply:**
- When tempted to add a visual flourish (gradient header, decorative icon, colored section divider), ask: "What function does this perform?"
- The geometric symbols (`◐`, `◉`, `◎`, `◧`) in our nav serve a function — they are quick visual identifiers that distinguish nav items faster than text alone. Keep them.
- If a section header could be removed because the content makes the section obvious, remove the header.
- Resist the "just one more metric" temptation. The Detail page is already at the density limit.

**Examples:** Things 3 (every element is functional), Bear (nothing decorative — the app is the content), Linear (zero decorative chrome — the UI is the work surface).

---

### Rule 32 — Use Asymmetry Intentionally
**Principle:** Not every column layout needs to be equal-width. Our sidebar (narrow) + main content (wide) is the correct macro-asymmetry. Within pages, `col1, col2, col3, col4 = st.columns([2, 1, 1, 1])` (Scanner config row) is correct asymmetry — the most complex input (universe selector) gets the most space.

**Why it works:** Rigid equal-column grids create a monotonous visual rhythm that flattens hierarchy. Asymmetric layouts guide the eye through a deliberate sequence. Japanese design tradition favors odd numbers and imbalanced compositions because they feel more natural and alive than symmetrical ones. Airbnb's card layouts, Pitch's slide editor, and Figma's panel layout all use intentional asymmetry.

**How to apply:**
- `st.columns([2, 1, 1, 1])` for the scan config row — already correct.
- `st.columns([1, 3])` for the button + info row — already correct.
- `st.columns([2, 1])` for the ticker input + lookback in Detail page — correct.
- The metric rows (`st.columns(4)`, `st.columns(5)`) use equal width — appropriate because the metrics are all equal in importance.
- Never use `st.columns(3)` when two columns at `[2, 1]` would better reflect the weight of the content.

**Examples:** Airbnb (search bar wider than filters), Figma (canvas dominant, panels secondary), Pitch (main editor 70%, outline panel 30%).

---

### Rule 33 — Muted Palette with One Moment of Color
**Principle:** The overall color impression must be quiet. `#FAF8F5`, `#F5F2EE`, `#E8E4DF`, `#4A4540`, `#7A756E` are all muted. The single moment of color is the sage green `#5B8A72` on primary interactive elements and positive states. Everything else defers to it.

**Why it works:** A muted base makes accents more powerful. If everything is colorful, nothing is. If only one element is colored, it becomes the focal point with zero effort. This is the Japandi color theory, the same principle applied in Muji product design, and the reason Apple's product photos use white backgrounds with a single color-accented product. Wealthfront uses this: a gray-dominant dashboard with one blue-green accent for calls to action.

**How to apply:**
- The sage green `#5B8A72` should appear on: buttons (primary), progress bars, active nav states, left-border accents on narrative cards, and positive metric changes. That is it.
- Terracotta `#C27D5E` is reserved for: pressing resistance verdicts, warning states only.
- When adding new UI components, default to the neutral palette. Only reach for the accent when the element is a primary call to action or a primary data signal.

**Examples:** Muji (beige + one accent per product), Wealthfront (gray interface + one blue accent), Bear (warm white + one teal accent link), Monzo (gray + hot coral for primary action only).

---

### Rule 34 — Natural Language Over Technical Labels
**Principle:** Wherever possible, replace technical field names with natural language descriptions. "EMA20_SLOPE_PCT" becomes "EMA Slope". "RANGE_WIDTH_PCT" becomes "Width". "CONTAINMENT_RATIO" becomes "Containment". Tooltips provide the technical definition for users who want it.

**Why it works:** Technical labels are efficient for developers but create cognitive translation overhead for users. The user first reads the label, then must map it to a concept. Natural language labels short-circuit this: "Containment" immediately implies "how much price stayed inside." Notion pioneered this with database properties — "Created time" not "created_at_timestamp". Linear uses "Status" not "state_id".

**How to apply:**
- Our current column headers are already following this ("Score", "Entry", "Verdict", "Edge", "Risk", "Range", "Width%", "Rot.", "Gaps%", "Price") — all acceptable.
- The `help=` parameter on `st.metric` and `st.number_input` is the right place for technical depth.
- In the score breakdown table, "What it measures" column is natural language — keep this column.
- Watch for any new metric or field additions that use snake_case or technical naming.

**Examples:** Notion (natural language everywhere, technical IDs hidden), Linear (plain English status and label names), Things 3 (no technical UI vocabulary at all).

---

### Rule 35 — Less Navigation, More Context
**Principle:** Five navigation items (Scanner, Ticker Detail, Charts, Backtest, Settings) is the maximum for this application. Never add a sixth top-level nav item. If new functionality is needed, embed it in an existing page as a section or tab, not a new top-level destination.

**Why it works:** Navigation depth is a cognitive overhead tax. Every additional nav item requires users to mentally model what is in it, whether it is where they need to go, and whether they have been there before. Nielsen's research on menu depth shows usability drops measurably above 5-7 primary navigation items. Arc Browser's "pinned tabs" philosophy, Linear's sidebar discipline, and Things 3's minimal area list all demonstrate that fewer navigation items, with rich context within them, outperforms broad shallow navigation.

**How to apply:**
- Five pages: Scanner, Detail, Charts, Backtest, Settings. This is the limit.
- If "Watchlist" or "Alerts" are needed later: embed in the Scanner page as a saved-results section, not a new nav item.
- If "Portfolio" analysis is needed: embed in Detail page as a multi-ticker mode, not a new nav item.
- Backtest page can expand internally with tabs (e.g., "Run Backtest" | "Historical Results") rather than splitting into two nav items.

**Examples:** Things 3 (four areas only), Bear (one main list + search), Craft (minimal sidebar), Readwise (five top-level items maximum).

---

## Part 7 — Accessibility and Inclusivity

---

### Rule 36 — Color Is Never the Only Differentiator
**Principle:** Every piece of information communicated by color must also be communicated by text, icon, or pattern. The "EXCELLENT RANGE" badge is green + text label (correct). The Position-in-Range dot uses position (spatial) + the label text "Support / Resistance" (correct). A color-only indicator with no text is a WCAG 1.4.1 failure.

**Why it works:** 8% of males and 0.5% of females have some form of color vision deficiency (Birch, 2012). Deuteranopia (inability to distinguish red-green) is most common — it directly affects our green/red semantic color system. Beyond colorblindness, low-light conditions, aging, and screen glare all reduce color differentiation. Designing without color as the sole signal protects all these users.

**How to apply:**
- All verdict badges: text + color — correct.
- Score columns: numerical value + progress bar — correct.
- The position indicator dot: position + text labels — correct.
- Any future "alert" or "notification" system: must use icon + color + text, not color alone.
- Consider adding a "colorblind mode" toggle in Settings that swaps green/red for blue/orange.

---

### Rule 37 — Focus States for Keyboard Navigation
**Principle:** Every interactive element must have a visible `:focus` state for keyboard navigation. Streamlit handles most of this, but custom HTML buttons or clickable elements rendered with `unsafe_allow_html=True` must have explicit focus styles.

**Why it works:** WCAG 2.1 SC 2.4.7 requires all interactive elements to have a visible focus indicator. This is not optional — it is the primary navigation mechanism for keyboard users, screen reader users, and motor-impaired users who cannot use a mouse. It also helps power users who prefer keyboard over mouse.

**How to apply:**
- Our `unsafe_allow_html=True` div elements (the narrative cards, verdict banner) are currently not interactive, so no focus state is needed.
- If we ever make table rows clickable (to navigate to Detail), they must have `:focus-visible { outline: 2px solid #5B8A72; outline-offset: 2px; }`.
- Streamlit's built-in inputs handle this correctly — do not override default focus styles with `outline: none`.

---

### Rule 38 — Meaningful Link and Button Text
**Principle:** Button labels must describe the action and its result, not just the verb. "Run Scan" (correct) vs. "Submit" (wrong). "Analyze" (acceptable) vs. "Go" (wrong). Never use "Click here", "Learn more" (without context), or single-word verbs without objects.

**Why it works:** Screen readers announce links and buttons as: "[link text], link" or "[button text], button." If the link text is "Click here," the screen reader user hears "Click here, link" — which tells them nothing about where they are going or what will happen. Clear button labels also reduce the need for supplementary explanatory text, which makes the UI more efficient for all users.

**How to apply:**
- "Run Scan" — correct, describes action (Run) and object (Scan).
- "Analyze" — acceptable in context (the button is below a ticker input field, so context is clear).
- If adding export functionality: "Export CSV" not "Export" or "Save".
- If adding a reset function: "Clear Scan Results" not "Reset".

---

### Rule 39 — Font Size Must Respect System Preferences
**Principle:** All font sizes must be specified in `rem` (relative to root em) or `em` (relative to parent), never in `px`. Our CSS already does this (`0.75rem`, `0.95rem`, etc.) — maintain it absolutely.

**Why it works:** WCAG 2.1 SC 1.4.4 requires text to be resizable to 200% without loss of content or functionality. Users who set their browser base font size to 20px (a common accessibility accommodation) need relative units to have this respected. `px` units ignore the user's system preference; `rem` units honor it. This is the most commonly violated accessibility rule in finance apps.

**How to apply:**
- All existing CSS uses `rem` — correct and non-negotiable.
- The inline style values in Python strings (e.g., `style="font-size: 2.5rem;"`) also use rem — correct.
- Never use `font-size: 12px` or any px font-size in new code. If you need ~12px, write `0.75rem`.
- Exception: `border-width`, `border-radius`, `padding` in `px` are acceptable since these are not text elements.

---

### Rule 40 — Adequate Touch Targets
**Principle:** All interactive elements must have a minimum touch target of 44x44px (Apple HIG) or 48x48px (Material Design). This applies even in a desktop-first app because many users now access web apps from touch-enabled laptops or external displays with styluses.

**Why it works:** WCAG 2.5.5 (AAA) recommends 44x44px for all interactive targets. Even at AA, targets below 24x24px are problematic. For financial data apps where precision matters (clicking the right row, tapping the correct button), undersized targets create errors. The 44px standard was derived from the average adult fingertip width.

**How to apply:**
- Streamlit buttons get `padding: 10px 24px` — this creates a target of approximately 40px tall, which is borderline. Acceptable for desktop, adequate for most touch devices.
- If adding icon-only buttons in the future, wrap them in a div with `min-width: 44px; min-height: 44px`.
- The sidebar nav radio buttons have `padding: 8px 12px` — the full label width makes the target adequate.

---

## Part 8 — Onboarding and First-Time Experience

---

### Rule 41 — The First Screen Must Show Value, Not Setup
**Principle:** A new user opening the dashboard for the first time must immediately understand what the app does and feel invited to act. The Scanner page (the default landing page) should show something — even a cached or demo result — not an empty configuration form.

**Why it works:** First impressions in UX are formed within 50 milliseconds (Lindgaard et al., 2006). An app that greets a new user with a form and no output signals "this is work before value." An app that greets a new user with example results signals "here is what this can do — you are already in." This is why Stripe shows a demo dashboard before you create an account, and why Linear shows a sample workspace on first load.

**How to apply:**
- On first load with no session state and no API key: show a banner explaining what the scanner does, with a brief GIF or screenshot of sample results.
- Better: pre-load a small set of demo results (maybe 5 tickers hard-coded with fictional values) so the Scanner page is never blank.
- The "How to use this page" expander is good but insufficient — it is behind a click. The default view should communicate value without requiring any interaction.
- Settings page: if the API key is not set, redirect here automatically and show a clear onboarding checklist.

**Examples:** Stripe (demo dashboard before signup), Linear (sample workspace), Notion (template picker on first page creation).

---

### Rule 42 — Inline Help Over External Documentation
**Principle:** Every `help=` tooltip parameter on inputs and metrics must be filled. Every ambiguous score or metric must have an inline explanation available without leaving the page. Never write "See docs for details" — the docs are the `help=` text.

**Why it works:** Users do not read documentation. Nielsen's usability research consistently shows documentation-reading rates below 5% for utility applications. Inline contextual help (tooltips, help text) is accessed at approximately 15-25% rates when placed at the point of need. The delta between "docs" and "inline tooltip" represents the gap between "supported" and "confused" for most users.

**How to apply:**
- All existing `st.metric`, `st.number_input`, `st.select_slider` calls already have `help=` parameters — this pattern must be maintained for every new input.
- When adding a new score component or metric, write the help text before or alongside the code, not as an afterthought.
- The score breakdown table already has a "What it measures" column — this is the inline documentation for the scoring model.
- Help text should answer: "What is this?" and "What is a good value?" in one sentence.

**Examples:** Notion (every block type has an inline description), Linear (every field has a tooltip in settings), Stripe (every API parameter has an inline description in the docs, not a separate page).

---

### Rule 43 — Settings Page: Progressive Disclosure of Complexity
**Principle:** The Settings page must be organized in tiers: (1) Essential — API key, must set up to use the app; (2) Common — threshold adjustments that most users might want; (3) Advanced — expert parameter tuning, hidden behind an expander. Present tier 1 first, always. Never present tier 3 before tier 1 is configured.

**Why it works:** Settings pages are the most commonly cited source of anxiety in user research on enterprise software (Baymard, 2019). Users confronted with 30 configuration options before they have entered their API key feel overwhelmed and often abandon setup. Tiered disclosure means experts find what they need, and novices see only what they must set.

**How to apply:**
- Settings top section: API Key (required, with clear "why this is needed" text).
- Middle section: Scanner defaults (lookback, min dollar volume, top N) — these are the "common" adjustments.
- Advanced expander: individual threshold values (ADX cutoffs, ATR ranges, rotation count minimums, etc.).
- Add a "Reset to defaults" button in the Advanced section.

**Examples:** macOS System Settings (essential settings surfaced, advanced hidden in disclosure triangles), Linear (settings organized as: Profile → Preferences → Advanced), Vercel (project settings: essential → git → advanced).

---

## Part 9 — Performance and Perceived Speed

---

### Rule 44 — Batch Heavy Work, Never Block the UI
**Principle:** Any operation expected to take more than 500ms must be asynchronous with visible progress feedback. Our `fetch_bars_batch` with `max_workers=10` is the correct approach — parallel fetching with a progress bar. Never run sequential blocking loops without feedback.

**Why it works:** The psychological contract with a loading indicator is: "I know you are busy, I will wait." Breaking this contract — showing no feedback during a long operation — creates the perception that the app has crashed. Our scan already correctly uses phased progress (0% → 70% fetch → 100% analyze). The 70/30 split reflects the actual time distribution, which makes the bar feel accurate, not arbitrary.

**How to apply:**
- Scanner: already correct (parallel fetch + progress bar).
- Detail page: `st.spinner` is correct for short single-ticker analysis.
- If Backtest page runs a multi-period backtest, it must use `st.progress` with step-by-step updates.
- Session state caching of scan results (already implemented) means subsequent renders are instant — preserve this.

**Examples:** Loom (accurate progress bars for upload/processing), Linear (instant UI with background sync), Notion (optimistic updates with background save).

---

### Rule 45 — Cache Aggressively, Invalidate Explicitly
**Principle:** Any data fetched from the API that does not change frequently (daily OHLCV bars) should be cached with `@st.cache_data` with an appropriate TTL. The cache key must include the parameters that affect the result (ticker + lookback). Cache invalidation must be user-initiated (a "Refresh" button), not automatic on every rerender.

**Why it works:** Streamlit re-renders the entire page on every user interaction. Without caching, every slider adjustment in the Scanner config would re-fetch all market data, creating intolerable latency. `st.cache_data` with a TTL allows us to trade some data freshness for massive perceived speed improvement. The user-initiated refresh button gives control without creating automatic re-fetch anxiety.

**How to apply:**
- `fetch_bars` and `fetch_bars_batch` should be wrapped with `@st.cache_data(ttl=3600)` — 1 hour TTL is appropriate for daily bars.
- The session state approach (`st.session_state["scan_results"]`) already provides page-level caching for scan results.
- Add a "Refresh Data" button that clears the cache for the current scan (using `st.cache_data.clear()`).

**Examples:** Notion (instant page loads due to aggressive client-side caching), Linear (offline-first with background sync), Robinhood (market data cached with visible "Last updated" timestamp).

---

## Part 10 — Finance and Data App Specific

---

### Rule 46 — Show Timestamps on All Market Data
**Principle:** Every metric, result, and data display that comes from fetched market data must show a "data as of" timestamp. Our current scanner results do not show when the data was fetched. This is a financial data app — data age is critical information.

**Why it works:** Financial decisions made on stale data can be dangerous. Professional financial tools (Bloomberg, TradingView, Robinhood) all show data timestamps prominently. Even Wealthfront shows "portfolio value as of market close." In our app, results cached in session state could be hours old if the user leaves the tab open. Users must see data age to make appropriate decisions.

**How to apply:**
- After scan completes, store `st.session_state["scan_timestamp"] = datetime.now()`.
- Display it above the results table: "Data fetched at 14:32:07 EST · 87 tickers analyzed"
- On the Detail page after analysis: small timestamp below the verdict banner.
- Format: "as of [HH:MM] today" for same-day, "as of [Date]" for cached older results.

**Examples:** Bloomberg (timestamp on every quote), TradingView (last updated on every chart), Robinhood (market close timestamp on positions).

---

### Rule 47 — Distinguish Score From Signal: Never Conflate
**Principle:** The Range Quality Score (0-100, structural quality) and the Entry Quality Score (0-100, timing quality) must never be combined or averaged into a single "total" score displayed to users. They answer different questions. Display both, separately, with separate labels.

**Why it works:** In financial analysis, confusing structure with timing is a fundamental error. A stock can have an excellent structure score (80/100) but a poor entry score (20/100) because price is stuck mid-range. Combining these into "score: 50" communicates neither piece of information correctly. Our current implementation already shows both separately — this rule is to preserve this discipline and guard against future "let's simplify to one score" pressure.

**How to apply:**
- Scanner table: "Score" (range quality) and "Entry" (entry quality) — correct, keep separate.
- Detail page: four metric tiles showing Range Quality + Entry Quality + Structure + Regime — correct.
- If ever creating a summary view or email report: show both scores with labels, not a combined value.
- The only valid aggregation: sort by a weighted combination for the ranked list, but display the components separately.

---

### Rule 48 — Risk Indicators Get Prominent Placement
**Principle:** Any indicator that represents risk or a reason NOT to trade (Breakout Risk, Gap Frequency, Compression) must be visible without scrolling in the Detail page. Risk information must not be buried below reward information.

**Why it works:** Prospect theory (Kahneman & Tversky, 1979) shows humans are loss-averse but cognitively discount risk information that requires effort to access. If risk indicators are buried below the fold, users will process rewards first and risks never. Professional financial analysis standards (and regulations) require risk disclosure at the point of decision, not in a footnote. Bloomberg's risk metrics are in the same view as price data.

**How to apply:**
- Detail page current order: Verdict → Scores → Range Structure → Risk Indicators. The risk indicators are visible without scrolling on most screens — acceptable.
- Do not reorder to push risk below score breakdown.
- Consider making Breakout Risk a more visually prominent element — currently it is one of four equal-sized metrics in a row. If it is HIGH, it could trigger a more prominent warning state.
- Add a brief "Risk Note" line to the verdict banner when breakout risk is HIGH or gap frequency is >25%.

**Examples:** Bloomberg (risk metrics alongside returns, never below), Wealthfront (risk indicator on portfolio page is always visible), Coinbase (volatility warnings surfaced with asset prices).

---

### Rule 49 — Table Density for Expert Users
**Principle:** The scanner results table should be dense — many rows, many columns — because expert users (traders) are data-dense users who have high tolerance for information density. Do not reduce column count below what is shown. Do not pad rows. Height `min(600, 50 + len(rows) * 35)` is the correct density target.

**Why it works:** Bloomberg Terminal has the highest information density of any financial product and is beloved by its users precisely because of it. The user research principle of "information foraging theory" (Pirolli & Card, 1999) shows expert users in information-rich domains are efficient searchers who prefer dense displays over paginated thin displays. Bloomberg, TradingView's screener, and institutional order management systems all maximize information density. Our app targets a similar expert user.

**How to apply:**
- Current scanner table density: correct. Preserve it.
- The `height=min(600, 50 + len(rows) * 35)` calculation creates appropriate scroll behavior — keep it.
- The legend below the table (Score, Entry, Rot., Gaps% explained) is the right density trade-off: dense table + accessible legend.
- Only reduce density if user research shows confusion — not as a default design choice.

**Examples:** Bloomberg Terminal (extreme density), TradingView screener (dense with 15+ columns), Robinhood (low density, but Robinhood targets retail beginners, not our use case).

---

### Rule 50 — The Disclaimer Is a Design Element
**Principle:** "Not financial advice. Structure filter only." must appear on every page that shows results or analysis, not just in the sidebar. It must be visually subdued (small, muted color) but present. It is never the first thing read, but always findable.

**Why it works:** Beyond legal necessity, the disclaimer serves a UX function: it calibrates user expectations about what the app is and is not. Users who understand "this is a structure filter, not a prediction tool" interpret results correctly. Users who believe it is a signal system will misuse high scores as buy signals. The placement (subdued in sidebar) is a deliberate design choice — visible but not dominant, because it is not the main message.

**How to apply:**
- Sidebar footer: already present — correct.
- Scanner results section: add a one-line note below the results table: "Scores indicate structural quality, not trading recommendations."
- Detail page: already present in the subtitle line. Consider adding to the verdict banner's sub-text for high-score results.
- Never make the disclaimer visually compete with the data — it should be `color: #B8B2A8`, `font-size: 0.75rem`.

---

## Quick Reference Checklist

When adding any new UI component to the app, verify:

- [ ] Typography: Is it Inter or JetBrains Mono? Is the font size on the scale?
- [ ] Color: Is the background from the warm neutral palette? Is the accent from `#5B8A72` or `#C27D5E` only?
- [ ] Contrast: Does all text pass WCAG AA (4.5:1 for normal, 3:1 for large)?
- [ ] Space: Are all padding/margin values multiples of 4px?
- [ ] Hierarchy: Does the most important information appear first?
- [ ] Interaction: Does it have a hover state? A loading state if async?
- [ ] Empty state: What does this component look like with no data?
- [ ] Error: Does the error state explain what happened AND what to do?
- [ ] Accessibility: Is color the only differentiator? If yes, add a text/icon fallback.
- [ ] Data: Are numbers formatted (not raw floats or large integers)?
- [ ] Timestamp: Is fetched data timestamped?
- [ ] Disclaimer: Is risk/non-advice language present when showing results?

---

## Appendix — Color Tokens

| Token | Value | Usage |
|---|---|---|
| `--bg-primary` | `#FAF8F5` | Main app background |
| `--bg-secondary` | `#F0EDE8` | Sidebar background |
| `--bg-card` | `#F5F2EE` | Metric cards, narrative blocks |
| `--bg-border` | `#E8E4DF` | All borders, dividers, hover backgrounds |
| `--text-primary` | `#2D2A26` | Headings, dominant text |
| `--text-secondary` | `#4A4540` | Body text, labels |
| `--text-muted` | `#7A756E` | Secondary labels, metadata |
| `--text-ghost` | `#B8B2A8` | Disclaimers, decorative text only |
| `--accent-primary` | `#5B8A72` | Primary buttons, progress, positive, active nav |
| `--accent-hover` | `#4A7360` | Hover state of primary accent |
| `--accent-secondary` | `#C27D5E` | Warnings, resistance zone, moderate risk |
| `--positive-bg` | `#D4EDDA` | Excellent/positive badge background |
| `--positive-text` | `#2D5F3B` | Excellent/positive badge text |
| `--warning-bg` | `#FFF3CD` | Watchlist/amber badge background |
| `--warning-text` | `#664D03` | Watchlist/amber badge text |
| `--negative-bg` | `#F8D7DA` | Broken/negative badge background |
| `--negative-text` | `#721C24` | Broken/negative badge text |
| `--info-bg` | `#D1ECF1` | Info/pressing badge background |
| `--info-text` | `#0C5460` | Info/pressing badge text |

---

## Appendix — Type Scale

| Step | Size | Usage |
|---|---|---|
| Display | 1.8rem | Page titles (h1) |
| Heading | 1.3rem | Section headings (h2) |
| Subheading | 1.05rem | Sub-section headings (h3) |
| Body | 0.95rem | Navigation, primary body text |
| Body Small | 0.9rem | Secondary narrative text |
| Label | 0.85rem | Input labels, table headers |
| Caption | 0.75rem | Metric card labels (all-caps + wide tracking) |
| Footnote | 0.7rem | Disclaimers, legal text only |

---

*These rules represent the design contract for the Range Scanner dashboard. Every pull request that modifies the UI should be evaluated against this document. When rules conflict, the higher-numbered rule in Part 7 (Accessibility) always wins.*
