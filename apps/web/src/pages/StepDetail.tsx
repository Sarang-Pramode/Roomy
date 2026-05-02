import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { fetchFindings, fetchRaw, fetchSegments, fetchStep, fetchUpstream } from "@/api/client";
import { CompositionDonut } from "@/components/trace/CompositionDonut";
import type { SegmentSummary } from "@/components/trace/ContextWindowCard";
import { ContextWindowCard } from "@/components/trace/ContextWindowCard";
import { FindingsStrip } from "@/components/trace/FindingsStrip";
import { SegmentTimeline } from "@/components/trace/SegmentTimeline";
import { SegmentsDataTable } from "@/components/trace/SegmentsDataTable";
import { TopSegmentsList } from "@/components/trace/TopSegmentsList";
import { UpstreamContextCard } from "@/components/trace/UpstreamContextCard";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

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
  const findings = useQuery({
    queryKey: ["findings", sessionId],
    queryFn: () => fetchFindings(sessionId),
    enabled: !!sessionId,
  });
  const stypeEarly = (step.data as Record<string, unknown> | undefined)?.step_type;
  const upstream = useQuery({
    queryKey: ["upstream", stepId],
    queryFn: () => fetchUpstream(stepId),
    enabled: !!stepId && stypeEarly === "llm",
  });

  if (step.isLoading) return <p className="p-6 text-sm text-zinc-500">Loading step…</p>;
  if (step.isError) return <p className="p-6 text-sm text-red-400">Step not found.</p>;

  const data = step.data as Record<string, unknown>;
  const llm = data.llm_call as Record<string, string | null> | undefined;
  let summary: SegmentSummary | null = null;
  if (llm?.segment_summary_json) {
    try {
      summary = JSON.parse(llm.segment_summary_json) as SegmentSummary;
    } catch {
      summary = null;
    }
  }

  const segList = segments.data ?? [];

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6 pb-16">
      <div className="flex flex-wrap items-baseline gap-3 text-sm">
        <Link to="/" className="text-zinc-500 hover:text-zinc-300">
          Sessions
        </Link>
        <span className="text-zinc-600">/</span>
        <Link to={`/sessions/${sessionId}`} className="text-zinc-500 hover:text-zinc-300">
          {sessionId.slice(0, 8)}…
        </Link>
        <span className="text-zinc-600">/</span>
        <span className="font-mono font-medium text-zinc-100">step {String(data.step_index)}</span>
        <Badge variant="outline" className="border-zinc-700 text-zinc-300">
          {String(data.step_type)}
        </Badge>
      </div>

      <Card className="border-zinc-800 bg-zinc-900/60 text-zinc-100">
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Overview</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 text-sm sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <p className="text-zinc-500">Latency</p>
            <p className="text-lg font-medium tabular-nums text-zinc-100">
              {data.latency_ms != null ? `${data.latency_ms} ms` : "—"}
            </p>
          </div>
          <div>
            <p className="text-zinc-500">Input tokens (rep / est)</p>
            <p className="text-lg font-medium tabular-nums text-zinc-100">
              {llm ? `${llm.input_tokens_reported ?? "—"} / ${llm.input_tokens_estimated ?? "—"}` : "—"}
            </p>
          </div>
          <div>
            <p className="text-zinc-500">Output tokens (rep / est)</p>
            <p className="text-lg font-medium tabular-nums text-zinc-100">
              {llm ? `${llm.output_tokens_reported ?? "—"} / ${llm.output_tokens_estimated ?? "—"}` : "—"}
            </p>
          </div>
          <div>
            <p className="text-zinc-500">Cost (est. USD)</p>
            <p className="text-lg font-medium tabular-nums text-zinc-100">
              {llm?.cost_estimate_usd != null ? `$${Number(llm.cost_estimate_usd).toFixed(5)}` : "—"}
            </p>
          </div>
        </CardContent>
      </Card>

      {String(data.step_type) === "llm" && (
        <>
          <div className="grid gap-4 lg:grid-cols-3">
            <div className="space-y-4 lg:col-span-2">
              <ContextWindowCard summary={summary} />
              <SegmentTimeline segments={segList} />
            </div>
            <div className="space-y-4">
              <TopSegmentsList summary={summary} />
              <Card className="border-zinc-800 bg-zinc-900/60 text-zinc-100">
                <CardHeader className="pb-2">
                  <CardTitle className="text-base font-semibold">Composition</CardTitle>
                  <p className="text-xs font-normal text-zinc-500">Same data as the bar, radial view.</p>
                </CardHeader>
                <CardContent className="flex justify-center py-2">
                  <CompositionDonut summary={summary} />
                </CardContent>
              </Card>
            </div>
          </div>

          {findings.data && findings.data.length > 0 && <FindingsStrip findings={findings.data} stepId={stepId} />}
        </>
      )}

      {String(data.step_type) === "llm" && (
        <UpstreamContextCard sessionId={sessionId} upstream={upstream.data ?? []} loading={upstream.isLoading} />
      )}

      <Tabs defaultValue="segments" className="w-full">
        <TabsList className="border border-zinc-800 bg-zinc-900 p-1 text-zinc-400">
          <TabsTrigger
            value="segments"
            className="data-[state=active]:bg-zinc-800 data-[state=active]:text-zinc-100 data-[state=active]:shadow-none"
          >
            Segments
          </TabsTrigger>
          <TabsTrigger
            value="raw"
            className="data-[state=active]:bg-zinc-800 data-[state=active]:text-zinc-100 data-[state=active]:shadow-none"
          >
            Raw JSON
          </TabsTrigger>
        </TabsList>
        <TabsContent value="segments" className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-4">
          {segments.isLoading && <p className="text-sm text-zinc-500">Loading segments…</p>}
          {!segments.isLoading && <SegmentsDataTable segments={segList} />}
        </TabsContent>
        <TabsContent value="raw" className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-4">
          {raw.isError && <p className="text-sm text-zinc-500">No raw LLM payload for this step.</p>}
          {raw.data && (
            <pre className="max-h-[520px] overflow-auto rounded-lg border border-zinc-800 bg-zinc-950 p-4 font-mono text-xs leading-relaxed text-zinc-300">
              {JSON.stringify(raw.data, null, 2)}
            </pre>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
