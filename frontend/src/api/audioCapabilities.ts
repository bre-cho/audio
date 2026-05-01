export type CapabilityStatus = "ready" | "partial" | "disabled" | "blocked" | "planned";

export type CapabilityState = {
  capability: string;
  status: CapabilityStatus;
  provider?: string | null;
  reason: string;
  requires_api_key?: boolean;
};

export async function fetchAudioCapabilities(): Promise<Record<string, CapabilityState>> {
  const res = await fetch("/api/v1/system-capabilities-v2/");
  if (!res.ok) throw new Error(`Capability fetch failed: ${res.status}`);
  const data = await res.json();
  return data.capabilities ?? data;
}
