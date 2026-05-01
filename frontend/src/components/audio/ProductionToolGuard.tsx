import React from "react";
import type { Capability } from "../../api/audioStudioV4";
import { isToolReady, blockedReason } from "../../api/audioStudioV4";

export function ProductionToolGuard({
  tool,
  capabilities,
  children,
}: {
  tool: string;
  capabilities: Capability[];
  children: React.ReactNode;
}) {
  const ready = isToolReady(capabilities, tool);
  if (ready) return <>{children}</>;
  return (
    <div className="rounded-2xl border p-4 opacity-80">
      <div className="font-semibold">{tool} đang bị khóa production</div>
      <div className="mt-1 text-sm">{blockedReason(capabilities, tool)}</div>
    </div>
  );
}
