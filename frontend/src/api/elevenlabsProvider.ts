export async function getElevenLabsHealth() {
  const res = await fetch('/api/v1/providers/elevenlabs/health');
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getElevenLabsVoices() {
  const res = await fetch('/api/v1/providers/elevenlabs/voices');
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getElevenLabsUsage() {
  const res = await fetch('/api/v1/providers/elevenlabs/usage');
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
