export default function ChallanCard({ detection, selectedVehicleType }) {
  const challan = detection?.challan;

  return (
    <section className="rounded-[2rem] border border-white/10 bg-white/5 p-5 shadow-panel backdrop-blur-md">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-mist/55">Challan Details</p>
          <h3 className="mt-2 font-display text-2xl text-white">
            {selectedVehicleType === "all"
              ? "Latest flagged vehicle"
              : `${selectedVehicleType} focus`}
          </h3>
        </div>
        <span className="rounded-full border border-white/10 bg-white/10 px-3 py-1 text-sm text-mist/75">
          {detection?.object_type ?? "No match"}
        </span>
      </div>

      {detection ? (
        <div className="mt-6 space-y-4">
          <div className="rounded-3xl border border-white/10 bg-steel/75 p-4">
            <p className="text-sm text-mist/65">License plate</p>
            <p className="mt-1 font-display text-3xl text-white">
              {detection.license_plate ?? "Not available"}
            </p>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="rounded-3xl border border-white/10 bg-white/5 p-4">
              <p className="text-sm text-mist/65">Challan status</p>
              <p className="mt-1 text-lg font-medium text-white">
                {challan?.status ?? "No Pending Challan"}
              </p>
            </div>
            <div className="rounded-3xl border border-white/10 bg-white/5 p-4">
              <p className="text-sm text-mist/65">Fine amount</p>
              <p className="mt-1 text-lg font-medium text-white">
                ₹{challan?.fine_amount ?? 0}
              </p>
            </div>
            <div className="rounded-3xl border border-white/10 bg-white/5 p-4">
              <p className="text-sm text-mist/65">Violation reason</p>
              <p className="mt-1 text-lg font-medium text-white">
                {challan?.violation_type ?? "None"}
              </p>
            </div>
            <div className="rounded-3xl border border-white/10 bg-white/5 p-4">
              <p className="text-sm text-mist/65">Detected at</p>
              <p className="mt-1 text-lg font-medium text-white">
                {new Date(detection.timestamp).toLocaleString()}
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div className="mt-6 rounded-3xl border border-dashed border-white/15 bg-white/5 p-8 text-sm text-mist/70">
          No detection matches the current filter yet. Keep the live feed running and the card will update automatically.
        </div>
      )}
    </section>
  );
}
