export default function AlertStrip({ alerts }) {
  if (!alerts?.length) {
    return (
      <div className="rounded-3xl border border-emerald-300/15 bg-emerald-400/10 px-4 py-3 text-sm text-emerald-100">
        Monitoring stable. No traffic or challan alerts in the latest cycle.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {alerts.map((alert) => (
        <div
          key={alert}
          className="rounded-3xl border border-orange-300/20 bg-orange-400/10 px-4 py-3 text-sm text-orange-50"
        >
          {alert}
        </div>
      ))}
    </div>
  );
}
