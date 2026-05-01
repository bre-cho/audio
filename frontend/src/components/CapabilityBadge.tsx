export function CapabilityBadge({ status }: { status: string }) {
  const label = status === 'ready' ? 'Sẵn sàng' : status === 'degraded' ? 'Giới hạn' : 'Đang khóa';
  return <span className={`capability-badge capability-${status}`}>{label}</span>;
}
