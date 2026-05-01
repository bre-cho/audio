export type CapabilityStatus = "ready" | "partial" | "disabled" | "blocked" | "planned";

export type Capability = {
  tool: string;
  provider: string;
  status: CapabilityStatus;
  reason?: string;
};

export async function fetchAudioCapabilities(): Promise<Capability[]> {
  const res = await fetch("/api/v1/audio-studio/capabilities");
  if (!res.ok) throw new Error("Không tải được capability matrix");
  return res.json();
}

export function isToolReady(capabilities: Capability[], tool: string): boolean {
  return capabilities.some((c) => c.tool === tool && c.status === "ready");
}

export function blockedReason(capabilities: Capability[], tool: string): string {
  const found = capabilities.find((c) => c.tool === tool);
  return found?.reason || "Module này chưa sẵn sàng production.";
}
