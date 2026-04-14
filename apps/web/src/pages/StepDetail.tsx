import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { fetchRaw, fetchSegments, fetchStep } from "@/api/client";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

type Summary = {
  total_input_tokens_estimated?: number;
  percent_by_segment_type?: Record<string, number>;
  top_segments?: { segment_type: string; token_count: number | null }[];
};

function CompositionBar({ summary }: { summary: Summary | null }) {
  const pct = summary?.percent_by_segment_type;
  if (!pct || Object.keys(pct).length === 0) return <p className="text-sm text-zinc-500">No segment summary.</p>;
  const entries = Object.entries(pct).sort((a, b) => b[1] - a[1]);
  const palette = ["bg-zinc-800", "bg-zinc-500", "bg-zinc-400", "bg-zinc-300", "bg-zinc-200"];
  return (
    <div className="space-y-2">
      <div className="flex h-3 w-full overflow-hidden rounded-full bg-zinc-100">
        {entries.map(([k, v], i) => (
          <div
            key={k}
            title={`${k}: ${v.toFixed(1)}%`}
            className={palette[i % palette.length]}
            style={{ width: `${Math.max(v, 0)}%` }}
          />
        ))}
      </div>
      <ul className="flex flex-wrap gap-3 text-xs text-zinc-600">
        {entries.map(([k, v], i) => (
          <li key={k} className="flex items-center gap-1">
            <span className={`h-2 w-2 rounded-full ${palette[i % palette.length]}`} />
            {k} ({v.toFixed(0)}%)
          </li>
        ))}
      </ul>
    </div>
  );
}

export function StepDetailPage() {
  const { sessionId = "", stepId = "" } = useParams();
  const step = useQuery({ queryKey: ["step", stepId], queryFn: () => fetchStep(stepId), enabled: !!stepId });
  const segments = useQuery({
    queryKey: ["segments", stepId],
    queryFn: () => fetchSegments(stepId),
    enabled: !!stepId,
  });
  const raw = useQuery({
    queryKey: ["raw", stepId],
    queryFn: () => fetchRaw(stepId),
    enabled: !!stepId,
    retry: false,
  });

  if (step.isLoading) return <p className="p-6 text-sm text-zinc-500">Loading step…</p>;
  if (step.isError) return <p className="p-6 text-sm text-red-600">Step not found.</p>;

  const data = step.data as Record<string, unknown>;
  const llm = data.llm_call as Record<string, string | null> | undefined;
  let summary: Summary | null = null;
  if (llm?.segment_summary_json) {
    try {
      summary = JSON.parse(llm.segment_summary_json) as Summary;
    } catch {
      summary = null;
    }
  }

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
        <span className="font-mono font-medium text-zinc-900">step {String(data.step_index)}</span>
        <Badge variant="outline">{String(data.step_type)}</Badge>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Overview</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 text-sm sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <p className="text-zinc-500">Latency</p>
            <p className="text-lg font-medium tabular-nums">{data.latency_ms != null ? `${data.latency_ms} ms` : "—"}</p>
          </div>
          <div>
            <p className="text-zinc-500">Input tokens (rep / est)</p>
            <p className="text-lg font-medium tabular-nums">
              {llm
                ? `${llm.input_tokens_reported ?? "—"} / ${llm.input_tokens_estimated ?? "—"}`
                : "—"}
            </p>
          </div>
          <div>
            <p className="text-zinc-500">Output tokens (rep / est)</p>
            <p className="text-lg font-medium tabular-nums">
              {llm
                ? `${llm.output_tokens_reported ?? "—"} / ${llm.output_tokens_estimated ?? "—"}`
                : "—"}
            </p>
          </div>
          <div>
            <p className="text-zinc-500">Cost (est. USD)</p>
            <p className="text-lg font-medium tabular-nums">
              {llm?.cost_estimate_usd != null ? `$${Number(llm.cost_estimate_usd).toFixed(5)}` : "—"}
            </p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Context composition</CardTitle>
        </CardHeader>
        <CardContent>
          <CompositionBar summary={summary} />
        </CardContent>
      </Card>

      <Tabs defaultValue="segments">
        <TabsList>
          <TabsTrigger value="segments">Segments</TabsTrigger>
          <TabsTrigger value="raw">Raw</TabsTrigger>
        </TabsList>
        <TabsContent value="segments">
          {segments.isLoading && <p className="text-sm text-zinc-500">Loading segments…</p>}
          {(segments.data ?? []).length === 0 && !segments.isLoading && (
            <p className="text-sm text-zinc-500">No segments (non-LLM step or capture pending).</p>
          )}
          {(segments.data ?? []).length > 0 && (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>#</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead className="text-right">Tokens</TableHead>
                  <TableHead>Preview</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(segments.data ?? []).map((r) => (
                  <TableRow key={r.segment_id}>
                    <TableCell className="tabular-nums">{r.order_index}</TableCell>
                    <TableCell>
                      <Badge variant="secondary">{r.segment_type}</Badge>
                    </TableCell>
                    <TableCell className="text-right tabular-nums">{r.token_count ?? "—"}</TableCell>
                    <TableCell className="max-w-xl whitespace-pre-wrap text-xs text-zinc-700">
                      {r.text_preview}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </TabsContent>
        <TabsContent value="raw">
          {raw.isError && <p className="text-sm text-zinc-500">No raw LLM payload for this step.</p>}
          {raw.data && (
            <pre className="max-h-[480px] overflow-auto rounded-lg border border-zinc-200 bg-zinc-50 p-4 font-mono text-xs leading-relaxed text-zinc-800">
              {JSON.stringify(raw.data, null, 2)}
            </pre>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
