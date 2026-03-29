const vehicleOptions = [
  { value: "all", label: "All" },
  { value: "car", label: "Car" },
  { value: "motorcycle", label: "Bike" },
  { value: "bus", label: "Bus" },
  { value: "truck", label: "Truck" },
  { value: "person", label: "Person" },
];

export default function ControlPanel({
  sources,
  selectedSource,
  onSourceChange,
  selectedVehicleType,
  onVehicleTypeChange,
  onExport,
  exporting,
}) {
  return (
    <section className="rounded-[2rem] border border-white/10 bg-white/5 p-5 shadow-panel backdrop-blur-md">
      <div className="grid gap-5 lg:grid-cols-[1.2fr_1fr_auto]">
        <label className="space-y-3">
          <span className="text-xs uppercase tracking-[0.3em] text-mist/55">
            Camera or Video Source
          </span>
          <select
            value={selectedSource}
            onChange={(event) => onSourceChange(event.target.value)}
            className="w-full rounded-2xl border border-white/10 bg-steel px-4 py-3 text-base text-white outline-none transition focus:border-cyan-300/40"
          >
            {sources.map((source) => (
              <option key={source.id} value={source.id}>
                {source.name}
              </option>
            ))}
          </select>
        </label>

        <label className="space-y-3">
          <span className="text-xs uppercase tracking-[0.3em] text-mist/55">
            Vehicle Filter
          </span>
          <select
            value={selectedVehicleType}
            onChange={(event) => onVehicleTypeChange(event.target.value)}
            className="w-full rounded-2xl border border-white/10 bg-steel px-4 py-3 text-base text-white outline-none transition focus:border-cyan-300/40"
          >
            {vehicleOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <button
          type="button"
          onClick={onExport}
          disabled={exporting}
          className="self-end rounded-2xl border border-cyan-300/20 bg-cyan-300/10 px-5 py-3 font-medium text-cyan-50 transition hover:bg-cyan-300/20 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {exporting ? "Exporting..." : "Export CSV"}
        </button>
      </div>
    </section>
  );
}
