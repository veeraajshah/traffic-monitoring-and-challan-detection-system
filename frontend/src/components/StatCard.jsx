export default function StatCard({ label, value, tone = "default", helper }) {
  const tones = {
    default: "from-white/12 to-white/5 border-white/10",
    accent: "from-cyan-400/18 to-blue-500/8 border-cyan-300/20",
    warning: "from-orange-400/18 to-rose-500/8 border-orange-300/20",
    success: "from-emerald-400/18 to-teal-500/8 border-emerald-300/20",
  };

  return (
    <div
      className={`rounded-3xl border bg-gradient-to-br ${tones[tone]} p-5 shadow-panel backdrop-blur-sm`}
    >
      <p className="text-xs uppercase tracking-[0.3em] text-mist/55">{label}</p>
      <p className="mt-3 font-display text-3xl text-white">{value}</p>
      {helper ? <p className="mt-2 text-sm text-mist/65">{helper}</p> : null}
    </div>
  );
}
