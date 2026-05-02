import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { fetchSessionDiff, fetchSteps, type StepRow } from "@/api/client";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

type DiffPayload = {
  added_segments: Record<string, unknown>[];
  removed_segments: Record<string, unknown>[];
  token_count_delta: number;
};

export function StepDiffPage() {
  const { sessionId = "" } = useParams();
  const steps = useQuery({
    queryKey: ["steps", sessionId],
    queryFn: () => fetchSteps(sessionId),
    enabled: !!sessionId,
  });
  const llmSteps = useMemo(
    () => (steps.data ?? []).filter((s: StepRow) => s.step_type === "llm").sort((a, b) => a.step_index - b.step_index),
    [steps.data],
  );
  const [a, setA] = useState("");
  const [b, setB] = useState("");

  const diff = useQuery({
    queryKey: ["diff", sessionId, a, b],
    queryFn: () => fetchSessionDiff(sessionId, a, b),
    enabled: !!sessionId && !!a && !!b && a !== b,
  });

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <div className="flex flex-wrap items-baseline gap-3 text-sm">
        <Link to="/" className="text-zinc-500 hover:text-zinc-800">
          Sessions
        </Link>
        <span className="text-zinc-300">/</span>
        <Link to={`/sessions/${sessionId}`} className="text-zinc-500 hover:text-zinc-800">
          {sessionId.slice(0, 8)}…
        </Link>
        <span className="text-zinc-300">/</span>
        <span className="font-medium text-zinc-900">Compare LLM steps</span>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Select two LLM steps</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-sm">
          <p className="text-zinc-600">
            Compares <strong>context segments</strong> between two model calls (same session). Pick earlier step as
            &quot;Before&quot;, later as &quot;After&quot;.
          </p>
          <div className="flex flex-wrap items-end gap-4">
            <label className="flex flex-col gap-1">
              <span className="text-xs font-medium text-zinc-500">Before (step id)</span>
              <select
                className="min-w-[280px] rounded-md border border-zinc-200 bg-white px-2 py-2 font-mono text-xs"
                value={a}
                onChange={(e) => setA(e.target.value)}
              >
                <option value="">—</option>
                {llmSteps.map((s) => (
                  <option key={s.step_id} value={s.step_id}>
                    #{s.step_index} {s.step_id.slice(0, 8)}…
                  </option>
                ))}
              </select>
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-xs font-medium text-zinc-500">After (step id)</span>
              <select
                className="min-w-[280px] rounded-md border border-zinc-200 bg-white px-2 py-2 font-mono text-xs"
                value={b}
                onChange={(e) => setB(e.target.value)}
              >
                <option value="">—</option>
                {llmSteps.map((s) => (
                  <option key={`b-${s.step_id}`} value={s.step_id}>
                    #{s.step_index} {s.step_id.slice(0, 8)}…
                  </option>
                ))}
              </select>
            </label>
          </div>
          {a === b && a ? <p className="text-amber-700">Choose two different steps.</p> : null}
        </CardContent>
      </Card>

      {diff.isFetching && <p className="text-sm text-zinc-500">Computing diff…</p>}
      {diff.isError && <p className="text-sm text-red-600">Could not load diff (need two LLM steps with segments).</p>}
      {diff.data && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Segment diff</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            <p className="tabular-nums text-zinc-700">
              Estimated token delta (after − before):{" "}
              <strong>{(diff.data as DiffPayload).token_count_delta}</strong>
            </p>
            <div className="grid gap-6 lg:grid-cols-2">
              <div>
                <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-zinc-500">Added in &quot;after&quot;</h3>
                <SegmentTable rows={(diff.data as DiffPayload).added_segments} />
              </div>
              <div>
                <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-zinc-500">Removed vs &quot;before&quot;</h3>
                <SegmentTable rows={(diff.data as DiffPayload).removed_segments} />
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function SegmentTable({ rows }: { rows: Record<string, unknown>[] }) {
  if (rows.length === 0) return <p className="text-zinc-500">None</p>;
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Type</TableHead>
          <TableHead className="text-right">Tokens</TableHead>
          <TableHead>Preview</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {rows.map((r, i) => (
          <TableRow key={i}>
            <TableCell>
              <Badge variant="secondary">{String(r.segment_type ?? "")}</Badge>
            </TableCell>
            <TableCell className="text-right tabular-nums">{r.token_count != null ? String(r.token_count) : "—"}</TableCell>
            <TableCell className="max-w-xs truncate text-xs text-zinc-700">{String(r.text_preview ?? "")}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
