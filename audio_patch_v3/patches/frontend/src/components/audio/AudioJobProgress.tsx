import React from "react";

export function AudioJobProgress({ status, artifactUrl }: { status: string; artifactUrl?: string }) {
  return (
    <div className="rounded-xl border p-3 text-sm">
      <div>Trạng thái job: <strong>{status}</strong></div>
      {artifactUrl && <a className="underline" href={artifactUrl}>Mở artifact</a>}
    </div>
  );
}
