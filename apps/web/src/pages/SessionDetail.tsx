import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { fetchFindings, fetchSession, fetchSteps } from "@/api/client";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export function SessionDetailPage() {
  const { sessionId = "" } = useParams();
  const s = useQuery({ queryKey: ["session", sessionId], queryFn: () => fetchSession(sessionId), enabled: !!sessionId });
  const steps = useQuery({
    queryKey: ["steps", sessionId],
    queryFn: () => fetchSteps(sessionId),
    enabled: !!sessionId,
  });
  const findings = useQuery({
    queryKey: ["findings", sessionId],
    queryFn: () => fetchFindings(sessionId),
    enabled: !!sessionId,
  });

  if (s.isLoading || steps.isLoading) return <p className="p-6 text-sm text-zinc-500">Loading…</p>;
  if (s.isError) return <p className="p-6 text-sm text-red-600">Session not found.</p>;

  const meta = s.data as Record<string, string>;
  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <div className="flex flex-wrap items-baseline gap-3">
        <Link to="/" className="text-sm text-zinc-500 hover:text-zinc-800">
          Sessions
        </Link>
        <span className="text-zinc-300">/</span>
        <h1 className="font-mono text-lg font-semibold">{sessionId.slice(0, 8)}…</h1>
        <Badge variant="outline">{meta.status}</Badge>
      </div>
      <p className="text-sm text-zinc-600">
        Agent <span className="font-medium text-zinc-900">{meta.agent_name}</span> · {meta.started_at}
      </p>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Findings</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          {findings.isLoading && <p className="text-zinc-500">Loading findings…</p>}
          {(findings.data ?? []).length === 0 && !findings.isLoading && (
            <p className="text-zinc-500">No findings for this session.</p>
          )}
          {(findings.data ?? []).map((f) => (
            <div key={f.finding_id} className="rounded-md border border-zinc-100 bg-zinc-50/80 p-3">
              <div className="flex items-center gap-2">
                <Badge variant={f.severity === "warning" ? "default" : "secondary"}>{f.severity}</Badge>
                <span className="font-mono text-xs text-zinc-500">{f.finding_type}</span>
              </div>
              <p className="mt-1 text-zinc-800">{f.explanation}</p>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Step timeline</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>#</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Latency</TableHead>
                <TableHead>Status</TableHead>
                <TableHead />
              </TableRow>
            </TableHeader>
            <TableBody>
              {(steps.data ?? []).map((st) => (
                <TableRow key={st.step_id}>
                  <TableCell className="tabular-nums">{st.step_index}</TableCell>
                  <TableCell>
                    <Badge variant="outline">{st.step_type}</Badge>
                  </TableCell>
                  <TableCell className="tabular-nums text-zinc-600">{st.latency_ms ?? "—"} ms</TableCell>
                  <TableCell>{st.status}</TableCell>
                  <TableCell className="text-right">
                    <Link
                      className="text-sm text-zinc-900 underline-offset-4 hover:underline"
                      to={`/sessions/${sessionId}/steps/${st.step_id}`}
                    >
                      Open
                    </Link>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
