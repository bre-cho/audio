export async function getAudioStudioCapabilities() {
  const res = await fetch('/api/system/capabilities');
  if (!res.ok) throw new Error('Không tải được capability audio studio');
  return res.json();
}

export async function createVoiceRecipe(payload: unknown) {
  const res = await fetch('/api/voice-design/recipes', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Tạo công thức giọng nói thất bại');
  return res.json();
}
