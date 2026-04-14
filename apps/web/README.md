# Roomy web UI

Vite + React + TypeScript + Tailwind + shadcn-style primitives (Radix Tabs, CVA).

## Development

With the API running (`roomy serve --db …` from the Python package):

```bash
npm install
npm run dev
```

The dev server proxies `/sessions`, `/steps`, and `/health` to `http://127.0.0.1:8765`.

## Production build

```bash
npm run build
```

Serve `dist/` behind any static host; configure it to reverse-proxy API routes to the Roomy FastAPI process.
