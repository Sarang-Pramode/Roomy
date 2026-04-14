# Roomy — Design guidelines

## Principles

- **Local-first**: the UI should feel like a developer tool, not a marketing site.
- **Readable in seconds**: prioritize scanability (tables, monospace IDs, clear hierarchy).
- **Minimal chrome**: few borders, generous whitespace, neutral grayscale with one accent for links and primary actions.

## Visual language

- Typography: system UI stack; body 14–15px; session titles 18–20px semibold.
- Color: light background (`zinc-50` / white), text `zinc-900`, muted `zinc-500`, accent `zinc-800` for buttons.
- Density: information-dense tables for segments and steps; truncate long text with expand/collapse for raw JSON.

## Pages

1. **Sessions** — sortable list: id (short), agent name, model (when known), started, duration, total tokens, est. cost, status.
2. **Session detail** — vertical timeline of steps (icons for `llm` / `tool` / `retrieval` / `control`), cumulative token estimate in header.
3. **Step detail** — split layout: left timeline context; main panel with tabs **Overview** (latency, tokens, model), **Segments** (table: type, tokens, preview), **Raw** (formatted JSON).

## Components (shadcn-style)

- Use shadcn `Button`, `Card`, `Table`, `Tabs`, `Badge`, `Separator`, `ScrollArea`.
- Raw JSON in `ScrollArea` with `font-mono` text-sm.

## Accessibility

- Tables include `<th scope="col">`; icon-only buttons have `aria-label`.
- Focus states visible; respect `prefers-reduced-motion` for transitions.

## Empty and error states

- Empty sessions: short message + hint to run an instrumented agent.
- API errors: inline alert with retry for TanStack Query.
