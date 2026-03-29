import { useEffect, useMemo, useState } from "react";
import { api } from "./lib/api";
import AlertStrip from "./components/AlertStrip";
import ChallanCard from "./components/ChallanCard";
import ControlPanel from "./components/ControlPanel";
import FeedPanel from "./components/FeedPanel";
import PlateList from "./components/PlateList";
import StatCard from "./components/StatCard";

const emptyMetrics = {
  fps: 0,
  latency_ms: 0,
  traffic_density: "Low",
  counts: {},
  pending_challans: 0,
};

export default function App() {
  const [sources, setSources] = useState([]);
  const [selectedSource, setSelectedSource] = useState("");
  const [selectedVehicleType, setSelectedVehicleType] = useState("all");
  const [metadata, setMetadata] = useState({
    source_name: "",
    mode: "initializing",
    detections: [],
    metrics: emptyMetrics,
    alerts: [],
    last_updated: null,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    let isMounted = true;

    const bootstrap = async () => {
      try {
        const { data } = await api.get("/get_videos");
        if (!isMounted) {
          return;
        }
        setSources(data.videos);
        const initialSource = data.active_source_id ?? data.videos?.[0]?.id ?? "";
        setSelectedSource(initialSource);
      } catch (err) {
        setError("Unable to load video sources. Make sure the backend is running.");
      } finally {
        setLoading(false);
      }
    };

    bootstrap();
    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    if (!selectedSource) {
      return undefined;
    }

    let active = true;
    const syncSource = async () => {
      try {
        await api.post("/set_video", { source_id: selectedSource });
      } catch (err) {
        if (active) {
          setError("Unable to switch source.");
        }
      }
    };

    syncSource();

    const refresh = async () => {
      try {
        const { data } = await api.get("/metadata", {
          params: {
            source_id: selectedSource,
            vehicle_type: selectedVehicleType,
          },
        });
        if (!active) {
          return;
        }
        setMetadata((current) => ({
          ...current,
          ...data,
          metrics: {
            ...emptyMetrics,
            ...data.metrics,
          },
        }));
        setError("");
      } catch (err) {
        if (active) {
          setError("Live metadata polling failed.");
        }
      }
    };

    refresh();
    const intervalId = setInterval(refresh, 1500);

    return () => {
      active = false;
      clearInterval(intervalId);
    };
  }, [selectedSource, selectedVehicleType]);

  const latestDetection = useMemo(() => {
    const detections = metadata.detections ?? [];
    return (
      detections.find((item) => item.challan?.status === "Pending Challan") ??
      detections.find((item) => item.license_plate) ??
      detections[0] ??
      null
    );
  }, [metadata.detections]);

  const countsLabel = useMemo(() => {
    const counts = metadata.metrics?.counts ?? {};
    const entries = Object.entries(counts);
    if (!entries.length) {
      return "Waiting for detections";
    }
    return entries
      .map(([label, count]) => `${label}: ${count}`)
      .join(" • ");
  }, [metadata.metrics]);

  const handleExport = async () => {
    setExporting(true);
    try {
      window.open("http://127.0.0.1:8000/export_logs?format=csv", "_blank", "noopener,noreferrer");
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(103,232,249,0.18),_transparent_28%),linear-gradient(135deg,_#07111f_0%,_#0a1730_55%,_#140e1c_100%)] text-mist">
      <div className="mx-auto max-w-[1600px] px-4 py-6 md:px-6 lg:px-8">
        <header className="mb-8 rounded-[2rem] border border-white/10 bg-white/5 p-6 shadow-panel backdrop-blur-md">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl">
              <p className="text-xs uppercase tracking-[0.34em] text-cyan-100/60">
                Smart City Traffic Intelligence
              </p>
              <h1 className="mt-3 font-display text-4xl text-white md:text-5xl">
                Real-time traffic monitoring with automatic challan detection
              </h1>
              <p className="mt-4 max-w-2xl text-base text-mist/72">
                Monitor all four local CCTV feeds, inspect live detections, filter vehicle classes,
                and surface pending challans without leaving the dashboard.
              </p>
            </div>
            <div className="grid gap-3 sm:grid-cols-2 lg:min-w-[360px]">
              <StatCard
                label="Pending Challans"
                value={metadata.metrics?.pending_challans ?? 0}
                tone="warning"
                helper="Vehicles currently mapped to an unpaid penalty"
              />
              <StatCard
                label="Traffic Density"
                value={metadata.metrics?.traffic_density ?? "Low"}
                tone="accent"
                helper={countsLabel}
              />
            </div>
          </div>
        </header>

        <div className="grid gap-5 lg:grid-cols-4">
          <div className="lg:col-span-3">
            <FeedPanel
              sourceId={selectedSource}
              sourceName={metadata.source_name || "Loading source"}
              mode={metadata.mode || "initializing"}
              updatedAt={metadata.last_updated}
            />
          </div>
          <div className="space-y-5">
            <StatCard
              label="FPS"
              value={(metadata.metrics?.fps ?? 0).toFixed(1)}
              tone="success"
              helper="Current rendered stream performance"
            />
            <StatCard
              label="Latency"
              value={`${(metadata.metrics?.latency_ms ?? 0).toFixed(1)} ms`}
              helper="Latest inference loop time"
            />
            <AlertStrip alerts={metadata.alerts} />
          </div>
        </div>

        <div className="mt-5">
          <ControlPanel
            sources={sources}
            selectedSource={selectedSource}
            onSourceChange={setSelectedSource}
            selectedVehicleType={selectedVehicleType}
            onVehicleTypeChange={setSelectedVehicleType}
            onExport={handleExport}
            exporting={exporting}
          />
        </div>

        {error ? (
          <div className="mt-5 rounded-3xl border border-rose-300/20 bg-rose-400/10 px-4 py-3 text-sm text-rose-50">
            {error}
          </div>
        ) : null}

        {loading ? (
          <div className="mt-5 rounded-3xl border border-white/10 bg-white/5 p-8 text-center text-mist/70">
            Preparing traffic feeds...
          </div>
        ) : null}

        <div className="mt-5 grid gap-5 xl:grid-cols-[1.1fr_0.9fr]">
          <ChallanCard
            detection={latestDetection}
            selectedVehicleType={selectedVehicleType}
          />
          <PlateList
            detections={metadata.detections ?? []}
            selectedVehicleType={selectedVehicleType}
          />
        </div>
      </div>
    </div>
  );
}
