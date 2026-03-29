function challanTone(status) {
  if (status === "Pending Challan") {
    return "border-orange-300/20 bg-orange-400/10 text-orange-50";
  }
  return "border-emerald-300/20 bg-emerald-400/10 text-emerald-50";
}

export default function PlateList({ detections, selectedVehicleType }) {
  const filtered = detections.filter((item) =>
    selectedVehicleType === "all" ? item.license_plate : item.object_type === selectedVehicleType,
  );

  return (
    <section className="rounded-[2rem] border border-white/10 bg-white/5 p-5 shadow-panel backdrop-blur-md">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-mist/55">Number Plate Stream</p>
          <h3 className="mt-2 font-display text-2xl text-white">
            {selectedVehicleType === "all"
              ? "All detected vehicle plates"
              : `${selectedVehicleType} plates`}
          </h3>
        </div>
        <span className="rounded-full border border-white/10 bg-white/10 px-3 py-1 text-sm text-mist/75">
          {filtered.length} visible
        </span>
      </div>

      <div className="mt-5 space-y-3">
        {filtered.length ? (
          filtered.map((item) => (
            <div
              key={`${item.object_id}-${item.timestamp}`}
              className="rounded-3xl border border-white/10 bg-steel/70 p-4"
            >
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="font-display text-2xl text-white">{item.license_plate ?? "N/A"}</p>
                  <p className="mt-1 text-sm text-mist/60">
                    {item.object_type} • confidence {(item.confidence * 100).toFixed(0)}%
                  </p>
                </div>
                <span
                  className={`rounded-full border px-3 py-1 text-sm ${challanTone(item.challan?.status)}`}
                >
                  {item.challan?.status ?? "No Challan"}
                </span>
              </div>
            </div>
          ))
        ) : (
          <div className="rounded-3xl border border-dashed border-white/15 bg-white/5 p-8 text-sm text-mist/70">
            No plates available for the current filter yet.
          </div>
        )}
      </div>
    </section>
  );
}
