import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { fetchHealth, fetchSessions } from "@/api/client";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

function shortId(id: string) {
  return `${id.slice(0, 8)}…`;
}

export function SessionsPage() {
  const health = useQuery({ queryKey: ["health"], queryFn: fetchHealth, staleTime: 10_000, retry: false });
  const q = useQuery({
    queryKey: ["sessions"],
    queryFn: fetchSessions,
    refetchInterval: 3000,
  });
  if (q.isLoading) return <p className="p-6 text-sm text-zinc-400">Loading sessions…</p>;
  if (q.isError) return <p className="p-6 text-sm text-red-400">Failed to load sessions.</p>;
  const rows = q.data ?? [];
  const h = health.data;

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-100">Sessions</h1>
        <p className="text-sm text-zinc-500">Local traces from Roomy-instrumented LangChain runs.</p>
      </div>

      {h?.db_path && (
        <div className="rounded-lg border border-zinc-800 bg-zinc-900/80 px-4 py-3 text-xs text-zinc-400">
          <p className="font-medium text-zinc-300">API database</p>
          <p className="mt-1 break-all font-mono text-zinc-400">{h.db_path}</p>
          <p className="mt-1 text-zinc-500">
            {(h.session_count ?? 0)} session{(h.session_count ?? 0) === 1 ? "" : "s"} in this file. Your agent must write to the{" "}
            <span className="text-zinc-300">same</span> path — e.g.{" "}
            <code className="rounded bg-zinc-950 px-1 text-zinc-300">roomy serve --db &apos;…/examples/traces.db&apos;</code> when using{" "}
            <code className="rounded bg-zinc-950 px-1 text-zinc-300">examples/web_chatbot.py</code> (it prints the path on startup).
          </p>
        </div>
      )}

      <Card className="border-zinc-800 bg-zinc-900/50">
        <CardHeader>
          <CardTitle className="text-base text-zinc-100">Recent</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {rows.length === 0 ? (
            <div className="space-y-3 p-4 text-sm text-zinc-500">
              <p>No sessions in this database yet.</p>
              <ol className="list-decimal space-y-2 pl-5 text-zinc-400">
                <li>
                  Start the API on the <span className="text-zinc-300">same SQLite file</span> your agent uses, e.g.{" "}
                  <code className="rounded bg-zinc-950 px-1 font-mono text-xs text-zinc-300">
                    roomy serve --db &quot;$PWD/examples/traces.db&quot; --port 8765
                  </code>
                </li>
                <li>
                  From <code className="rounded bg-zinc-950 px-1">apps/web</code>:{" "}
                  <code className="rounded bg-zinc-950 px-1 font-mono text-xs">npm run dev</code> (proxies to port 8765).
                </li>
                <li>
                  Run your agent (e.g. <code className="rounded bg-zinc-950 px-1 font-mono text-xs">python examples/web_chatbot.py</code>) and
                  refresh — or use <code className="rounded bg-zinc-950 px-1 font-mono text-xs">roomy dashboard</code> after Vite is up.
                </li>
              </ol>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="border-zinc-800 hover:bg-transparent">
                  <TableHead className="text-zinc-400">Session</TableHead>
                  <TableHead className="text-zinc-400">Agent</TableHead>
                  <TableHead className="text-zinc-400">Status</TableHead>
                  <TableHead className="text-zinc-400">Started</TableHead>
                  <TableHead className="text-right text-zinc-400">Tokens</TableHead>
                  <TableHead className="text-right text-zinc-400">Cost (est.)</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {rows.map((s) => (
                  <TableRow key={s.session_id} className="border-zinc-800 hover:bg-zinc-800/40">
                    <TableCell className="font-mono text-xs">
                      <Link className="text-violet-400 underline-offset-4 hover:underline" to={`/sessions/${s.session_id}`}>
                        {shortId(s.session_id)}
                      </Link>
                    </TableCell>
                    <TableCell className="text-zinc-300">{s.agent_name}</TableCell>
                    <TableCell>
                      <Badge variant={s.status === "completed" ? "secondary" : "outline"}>{s.status}</Badge>
                    </TableCell>
                    <TableCell className="text-zinc-500">{s.started_at}</TableCell>
                    <TableCell className="text-right tabular-nums text-zinc-300">{s.total_tokens ?? "—"}</TableCell>
                    <TableCell className="text-right tabular-nums text-zinc-300">
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
