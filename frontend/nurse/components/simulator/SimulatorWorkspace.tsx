"use client";

import { Pause, Play, RotateCcw, SkipForward } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { exportRunCsv, exportRunJson, formatSimClock, generateCohort, projectState, runSimulation, SCENARIOS, SIMULATION_SEED } from "@/lib/simulation";
import { Button } from "@epicenter/shared/ui/Button";
import { PageHeader } from "@epicenter/shared/ui/PageHeader";

import { ClinicFlow, type ClinicView } from "./ClinicFlow";
import styles from "./Simulator.module.css";

const SCENARIO_ID = "single_ticket" as const;
const SPEEDS = [1, 2, 5, 10, 20, 50];

function gcd(left: number, right: number): number {
  let a = Math.abs(left);
  let b = Math.abs(right);
  while (b !== 0) {
    const next = a % b;
    a = b;
    b = next;
  }
  return a || 1;
}

function formatRatio(fast: number, slow: number): string {
  if (fast === 0 && slow === 0) return "—";
  const divisor = gcd(fast, slow);
  return `${fast / divisor} : ${slow / divisor}`;
}

function download(filename: string, contents: string, type: string) {
  const blob = new Blob([contents], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

export function SimulatorWorkspace() {
  const [speed, setSpeed] = useState(10);
  const [playing, setPlaying] = useState(false);
  const [time, setTime] = useState(0);
  const [clinicView, setClinicView] = useState<ClinicView>("queue");

  const scenario = SCENARIOS[SCENARIO_ID];
  const cohort = useMemo(() => generateCohort(SIMULATION_SEED, scenario.bookedCount, scenario.walkInCount), [scenario.bookedCount, scenario.walkInCount]);
  const run = useMemo(() => runSimulation(SCENARIO_ID, { cohort }), [cohort]);
  const projected = useMemo(() => projectState(run, time), [run, time]);

  useEffect(() => {
    setTime(0);
    setPlaying(false);
  }, [run.snapshotHash]);

  useEffect(() => {
    if (!playing) return;
    const intervalMs = Math.max(16, Math.round(240 / speed));
    const step = speed >= 20 ? 2 : 1;
    const timer = window.setInterval(() => {
      setTime((current) => {
        const next = Math.min(run.scenario.durationMinutes, current + step);
        if (next >= run.scenario.durationMinutes) setPlaying(false);
        return next;
      });
    }, intervalMs);
    return () => window.clearInterval(timer);
  }, [playing, run.scenario.durationMinutes, speed]);

  function stepOnce() {
    const nextEvent = run.events.find((event) => event.time > time);
    setTime(nextEvent ? nextEvent.time : run.scenario.durationMinutes);
    setPlaying(false);
  }

  function reset() {
    setTime(0);
    setPlaying(false);
  }

  const metrics = projected.metrics;

  return (
    <div className={styles.page}>
      <PageHeader title="Simulator" />

      <div className={styles.toolbar}>
        <label>
          View
          <select onChange={(event) => setClinicView(event.target.value as ClinicView)} value={clinicView}>
            <option value="queue">Queue</option>
            <option value="overview">Whole Overview</option>
          </select>
        </label>
        <label>
          Speed
          <select onChange={(event) => setSpeed(Number(event.target.value))} value={speed}>
            {SPEEDS.map((value) => (
              <option key={value} value={value}>
                {value}×
              </option>
            ))}
          </select>
        </label>
        <div className={styles.playback}>
          <Button icon={playing ? <Pause aria-hidden="true" size={16} /> : <Play aria-hidden="true" size={16} />} onClick={() => setPlaying((value) => !value)} type="button">
            {playing ? "Pause" : "Run"}
          </Button>
          <Button icon={<SkipForward aria-hidden="true" size={16} />} onClick={stepOnce} type="button" variant="secondary">
            Step
          </Button>
          <Button icon={<RotateCcw aria-hidden="true" size={16} />} onClick={reset} type="button">
            Reset
          </Button>
        </div>
      </div>

      <div className={styles.clockRow}>
        <strong aria-live="polite">{formatSimClock(time)}</strong>
        <input
          aria-label="Simulation time"
          max={run.scenario.durationMinutes}
          min={0}
          onChange={(event) => {
            setPlaying(false);
            setTime(Number(event.target.value));
          }}
          type="range"
          value={time}
        />
      </div>

      <div className={styles.layout}>
        <ClinicFlow instant={speed >= 10} state={projected} view={clinicView} />
        <aside aria-label="Live metrics" className={styles.metrics}>
          <h2>Live metrics</h2>
          <dl>
            <div>
              <dt>In clinic</dt>
              <dd>{metrics.inClinic}</dd>
            </div>
            <div>
              <dt>Completed</dt>
              <dd>{metrics.completed}</dd>
            </div>
            <div>
              <dt>Fast counter</dt>
              <dd>{metrics.fastCounterPatients}</dd>
            </div>
            <div>
              <dt>Slow counter</dt>
              <dd>{metrics.slowCounterPatients}</dd>
            </div>
            <div>
              <dt>Fast : slow</dt>
              <dd>{formatRatio(metrics.fastCounterPatients, metrics.slowCounterPatients)}</dd>
            </div>
          </dl>
        </aside>
      </div>

      <section aria-label="Event timeline" className={styles.timeline}>
        <h2>Recent events</h2>
        <ol>
          {run.events
            .filter((event) => event.time <= time)
            .slice(-8)
            .reverse()
            .map((event) => (
              <li key={event.sequence}>
                <time>{formatSimClock(event.time)}</time>
                <span>{event.message}</span>
              </li>
            ))}
        </ol>
        <div className={styles.exportRow}>
          <Button className={styles.exportButton} onClick={() => download(`simulator-${SCENARIO_ID}.json`, exportRunJson(run), "application/json")} type="button" variant="quiet">
            Export JSON
          </Button>
          <Button className={styles.exportButton} onClick={() => download(`simulator-${SCENARIO_ID}.csv`, exportRunCsv(run), "text/csv")} type="button" variant="quiet">
            Export CSV
          </Button>
        </div>
      </section>
    </div>
  );
}
