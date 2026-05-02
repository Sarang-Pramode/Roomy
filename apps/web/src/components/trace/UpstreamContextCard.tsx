import { Link } from "react-router-dom";
import type { UpstreamStep } from "@/api/client";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export function UpstreamContextCard({
  sessionId,
  upstream,
  loading,
}: {
  sessionId: string;
  upstream: UpstreamStep[];
  loading: boolean;
}) {
  return (
    <Card className="border-zinc-800 bg-zinc-900/60 text-zinc-100">
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-semibold">Upstream context</CardTitle>
        <p className="text-xs font-normal text-zinc-500">
          Tool / retrieval / memory steps after the previous LLM call and before this one (heuristic).
        </p>
      </CardHeader>
      <CardContent className="space-y-2 text-sm text-zinc-400">
        {loading && <p className="text-zinc-500">Loading…</p>}
        {upstream.length === 0 && !loading && <p className="text-zinc-500">No tool or retrieval steps in this window.</p>}
        {upstream.length > 0 && (
          <Table>
            <TableHeader>
              <TableRow className="border-zinc-800 hover:bg-transparent">
                <TableHead className="text-zinc-500">#</TableHead>
                <TableHead className="text-zinc-500">Type</TableHead>
                <TableHead className="text-zinc-500">Summary</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {upstream.map((u) => (
                <TableRow key={String(u.step_id)} className="border-zinc-800 hover:bg-zinc-800/30">
                  <TableCell className="tabular-nums text-zinc-500">{Number(u.step_index)}</TableCell>
                  <TableCell>
                    <Badge variant="outline" className="border-zinc-700 text-zinc-300">
                      {String(u.step_type)}
                    </Badge>
                  </TableCell>
                  <TableCell className="max-w-xl text-xs">
                    {u.step_type === "tool" && Array.isArray(u.tool_calls) && u.tool_calls[0] ? (
                      <span className="text-zinc-300">
                        <span className="font-medium text-orange-400">
                          {String((u.tool_calls[0] as Record<string, unknown>).tool_name)}
                        </span>
                        {" · "}
                        {String((u.tool_calls[0] as Record<string, unknown>).tool_output_preview ?? "").slice(0, 140)}
                      </span>
                    ) : null}
                    {u.step_type === "retrieval" && Array.isArray(u.retrieval_events) && u.retrieval_events[0] ? (
                      <span className="text-zinc-300">
                        <span className="font-medium text-sky-400">
                          {String((u.retrieval_events[0] as Record<string, unknown>).retriever_name)}
                        </span>
                        {" · "}
                        {String((u.retrieval_events[0] as Record<string, unknown>).query_text ?? "").slice(0, 140)}
                      </span>
                    ) : null}
                    {u.step_type === "memory" ? <span className="text-zinc-600">memory step</span> : null}
                    <div className="mt-1">
                      <Link
                        className="text-violet-400 underline-offset-2 hover:underline"
                        to={`/sessions/${sessionId}/steps/${String(u.step_id)}`}
                      >
                        Open step
                      </Link>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
