import { API_BASE } from "../lib/api";

export default function FeedPanel({ sourceId, sourceName, mode, updatedAt }) {
  const streamUrl = `${API_BASE}/video_feed?source_id=${encodeURIComponent(sourceId ?? "")}`;

  return (
    <section className="rounded-[2rem] border border-white/10 bg-white/5 p-4 shadow-panel backdrop-blur-md">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.34em] text-mist/50">
            Live Surveillance Feed
          </p>
          <h2 className="mt-2 font-display text-2xl text-white">{sourceName}</h2>
        </div>
        <div className="flex items-center gap-3 text-sm text-mist/70">
          <span className="rounded-full border border-cyan-300/20 bg-cyan-400/10 px-3 py-1">
            Pipeline: {mode}
          </span>
          <span>Updated: {updatedAt ? new Date(updatedAt).toLocaleTimeString() : "--"}</span>
        </div>
      </div>
      <div className="relative overflow-hidden rounded-[1.5rem] border border-white/10 bg-steel">
        <div className="pointer-events-none absolute inset-0 bg-grid bg-[size:34px_34px] opacity-25" />
        {sourceId ? (
          <img
            src={streamUrl}
            alt={sourceName}
            className="relative z-10 h-[460px] w-full object-cover lg:h-[540px]"
          />
        ) : (
          <div className="flex h-[460px] items-center justify-center text-mist/60">
            No source selected
          </div>
        )}
      </div>
    </section>
  );
}
