/** Hex colors aligned with ContextSegmentType (packages/roomy schema). */

const DEFAULT = "#71717a";

const BY_TYPE: Record<string, string> = {
  system_prompt: "#a855f7",
  developer_prompt: "#c084fc",
  guardrail_prompt: "#9333ea",
  user_message: "#22c55e",
  conversation_history: "#3b82f6",
  memory_summary: "#06b6d4",
  retrieved_document: "#60a5fa",
  tool_definition: "#fb923c",
  tool_result: "#f97316",
  scratchpad: "#eab308",
  output_parser_instructions: "#a78bfa",
  image: "#ec4899",
  unknown: DEFAULT,
};

export function segmentHex(segmentType: string): string {
  return BY_TYPE[segmentType] ?? DEFAULT;
}

export function segmentLabel(segmentType: string): string {
  return segmentType.replace(/_/g, " ");
}
