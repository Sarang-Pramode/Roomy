import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Link, Navigate, Route, Routes } from "react-router-dom";
import { SessionDetailPage } from "@/pages/SessionDetail";
import { SessionsPage } from "@/pages/Sessions";
import { StepDiffPage } from "@/pages/StepDiff";
import { StepDetailPage } from "@/pages/StepDetail";

const qc = new QueryClient();

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <BrowserRouter>
        <header className="border-b border-zinc-200 bg-white">
          <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
            <Link to="/" className="text-sm font-semibold tracking-tight text-zinc-900">
              Roomy
            </Link>
            <span className="text-xs text-zinc-400">LangChain context observatory</span>
          </div>
        </header>
        <Routes>
          <Route path="/" element={<SessionsPage />} />
          <Route path="/sessions/:sessionId" element={<SessionDetailPage />} />
          <Route path="/sessions/:sessionId/diff" element={<StepDiffPage />} />
          <Route path="/sessions/:sessionId/steps/:stepId" element={<StepDetailPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
