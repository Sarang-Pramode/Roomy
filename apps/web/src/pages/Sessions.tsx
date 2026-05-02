import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { fetchSessions } from "@/api/client";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

function shortId(id: string) {
  return `${id.slice(0, 8)}…`;
}

export function SessionsPage() {
  const q = useQuery({
    queryKey: ["sessions"],
    queryFn: fetchSessions,
    // Live-ish updates while agents run in another terminal (no manual refresh)
    refetchInterval: 3000,
  });
  if (q.isLoading) return <p className="p-6 text-sm text-zinc-500">Loading sessions…</p>;
  if (q.isError) return <p className="p-6 text-sm text-red-600">Failed to load sessions.</p>;
  const rows = q.data ?? [];
  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Sessions</h1>
        <p className="text-sm text-zinc-500">Local traces from Roomy-instrumented LangChain runs.</p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Recent</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {rows.length === 0 ? (
            <p className="p-4 text-sm text-zinc-500">No sessions yet. Run `python agents/minimal_chain.py`.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Session</TableHead>
                  <TableHead>Agent</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Started</TableHead>
                  <TableHead className="text-right">Tokens</TableHead>
                  <TableHead className="text-right">Cost (est.)</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {rows.map((s) => (
                  <TableRow key={s.session_id}>
                    <TableCell className="font-mono text-xs">
                      <Link className="text-zinc-900 underline-offset-4 hover:underline" to={`/sessions/${s.session_id}`}>
                        {shortId(s.session_id)}
                      </Link>
                    </TableCell>
                    <TableCell>{s.agent_name}</TableCell>
                    <TableCell>
                      <Badge variant={s.status === "completed" ? "secondary" : "outline"}>{s.status}</Badge>
                    </TableCell>
                    <TableCell className="text-zinc-600">{s.started_at}</TableCell>
                    <TableCell className="text-right tabular-nums">{s.total_tokens ?? "—"}</TableCell>
                    <TableCell className="text-right tabular-nums">
                      {s.total_cost != null ? `$${Number(s.total_cost).toFixed(4)}` : "—"}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
