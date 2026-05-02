import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { fetchFindings, fetchSession, fetchSteps } from "@/api/client";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export function SessionDetailPage() {
  const { sessionId = "" } = useParams();
  const s = useQuery({
    queryKey: ["session", sessionId],
    queryFn: () => fetchSession(sessionId),
    enabled: !!sessionId,
    refetchInterval: (query) => {
      const d = query.state.data as Record<string, string> | undefined;
      return d?.status === "running" ? 2000 : false;
    },
  });
  const sessionStatus = (s.data as Record<string, string> | undefined)?.status;
  const steps = useQuery({
    queryKey: ["steps", sessionId],
    queryFn: () => fetchSteps(sessionId),
    enabled: !!sessionId,
    refetchInterval: sessionStatus === "running" ? 2000 : false,
  });
  const findings = useQuery({
    queryKey: ["findings", sessionId],
    queryFn: () => fetchFindings(sessionId),
    enabled: !!sessionId,
    refetchInterval: sessionStatus === "running" ? 4000 : false,
  });

  if (s.isLoading || steps.isLoading) return <p className="p-6 text-sm text-zinc-500">Loading…</p>;
  if (s.isError) return <p className="p-6 text-sm text-red-400">Session not found.</p>;

  const meta = s.data as Record<string, string>;
  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6 pb-16">
      <div className="flex flex-wrap items-baseline gap-3">
        <Link to="/" className="text-sm text-zinc-500 hover:text-zinc-300">
          Sessions
        </Link>
        <span className="text-zinc-600">/</span>
        <h1 className="font-mono text-lg font-semibold text-zinc-100">{sessionId.slice(0, 8)}…</h1>
        <Badge variant="outline" className="border-zinc-700 text-zinc-300">
          {meta.status}
        </Badge>
      </div>
      <p className="text-sm text-zinc-500">
        Agent <span className="font-medium text-zinc-200">{meta.agent_name}</span> · {meta.started_at}
      </p>

      <p className="text-sm">
        <Link className="text-violet-400 underline-offset-4 hover:underline" to={`/sessions/${sessionId}/diff`}>
          Compare two LLM steps (segment diff)
        </Link>
      </p>

      <Card className="border-zinc-800 bg-zinc-900/60 text-zinc-100">
        <CardHeader>
          <CardTitle className="text-base text-zinc-100">Findings</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          {findings.isLoading && <p className="text-zinc-500">Loading findings…</p>}
          {(findings.data ?? []).length === 0 && !findings.isLoading && (
            <p className="text-zinc-500">No findings for this session.</p>
          )}
          {(findings.data ?? []).map((f) => (
            <div key={f.finding_id} className="rounded-md border border-zinc-800 bg-zinc-950/60 p-3">
              <div className="flex items-center gap-2">
                <Badge variant={f.severity === "warning" ? "default" : "secondary"}>{f.severity}</Badge>
                <span className="font-mono text-xs text-zinc-500">{f.finding_type}</span>
              </div>
              <p className="mt-1 text-zinc-300">{f.explanation}</p>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card className="border-zinc-800 bg-zinc-900/60 text-zinc-100">
        <CardHeader>
          <CardTitle className="text-base text-zinc-100">Step timeline</CardTitle>
          <p className="text-xs font-normal font-medium text-zinc-500">
            Open an <span className="text-violet-400">llm</span> step for the context dashboard (composition, segments, timeline).
          </p>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow className="border-zinc-800 hover:bg-transparent">
                <TableHead className="text-zinc-500">#</TableHead>
                <TableHead className="text-zinc-500">Type</TableHead>
                <TableHead className="text-zinc-500">Latency</TableHead>
                <TableHead className="text-zinc-500">Status</TableHead>
                <TableHead />
              </TableRow>
            </TableHeader>
            <TableBody>
              {(steps.data ?? []).map((st) => {
                const isLlm = st.step_type === "llm";
                return (
                  <TableRow
                    key={st.step_id}
                    className={`border-zinc-800 ${isLlm ? "bg-violet-950/25 hover:bg-violet-950/35" : "hover:bg-zinc-800/40"}`}
                  >
                    <TableCell className="tabular-nums text-zinc-400">{st.step_index}</TableCell>
                    <TableCell>
                      <Badge
                        variant="outline"
                        className={
                          isLlm ? "border-violet-500/50 text-violet-300" : "border-zinc-700 text-zinc-400"
                        }
                      >
                        {st.step_type}
                      </Badge>
                    </TableCell>
                    <TableCell className="tabular-nums text-zinc-500">{st.latency_ms ?? "—"} ms</TableCell>
                    <TableCell className="text-zinc-400">{st.status}</TableCell>
                    <TableCell className="text-right">
                      <Link
                        className={`text-sm underline-offset-4 hover:underline ${isLlm ? "text-violet-400" : "text-zinc-400"}`}
                        to={`/sessions/${sessionId}/steps/${st.step_id}`}
                      >
                        {isLlm ? "Open trace" : "Open"}
                      </Link>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
