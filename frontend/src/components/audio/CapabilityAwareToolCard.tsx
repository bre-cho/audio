import React from "react";
import type { CapabilityState } from "../../api/audioCapabilities";

type Props = {
  title: string;
  description: string;
  capability?: CapabilityState;
  children?: React.ReactNode;
};

export function CapabilityAwareToolCard({ title, description, capability, children }: Props) {
  const ready = capability?.status === "ready";
  return (
    <section className="rounded-2xl border p-4 shadow-sm bg-white">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold">{title}</h3>
          <p className="text-sm text-gray-600">{description}</p>
        </div>
        <span className={`rounded-full px-3 py-1 text-xs ${ready ? "bg-green-100" : "bg-gray-100"}`}>
          {capability?.status ?? "unknown"}
        </span>
      </div>
      {!ready && (
        <div className="mt-3 rounded-xl bg-amber-50 p-3 text-sm text-amber-900">
          {capability?.reason ?? "Capability chưa sẵn sàng."}
        </div>
      )}
      <div className={!ready ? "pointer-events-none mt-4 opacity-50" : "mt-4"}>{children}</div>
    </section>
  );
}
