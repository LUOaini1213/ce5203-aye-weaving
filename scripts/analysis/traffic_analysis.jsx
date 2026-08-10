import { useState } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar, ReferenceLine } from "recharts";

const TIME = [0.5,1.5,2.5,3.5,4.5,5.5,6.5,7.5,8.5,9.5,10.5,11.5,12.5,13.5,14.5,15.5,16.5,17.5,18.5,19.5,20.5,21.5,22.5,23.5,24.5,25.5,26.5,27.5,28.5,29.5,30.5,31.5,32.5,33.5,34.5,35.5,36.5,37.5,38.5,39.5,40.5,41.5,42.5,43.5,44.5,45.5,46.5,47.5,48.5,49.5,50.5,51.5,52.5,53.5,54.5,55.5,56.5,57.5,58.5,59.5,60.5,61.5,62.5,63.5];
const DELAY_W = [4.7,6.6,7.7,9.0,9.4,11.0,10.1,6.9,7.7,11.4,16.1,28.8,13.6,29.3,52.0,36.7,29.4,20.2,18.6,33.4,16.2,23.9,30.1,14.7,9.2,4.7,11.8,14.9,9.2,6.9,8.3,14.0,11.3,15.2,23.3,34.6,58.7,40.5,18.2,16.6,45.7,42.2,57.4,28.6,18.5,45.1,63.6,28.1,33.4,34.2,54.1,46.3,53.2,62.6,44.9,111.2,91.6,65.8,86.9,81.5,53.6,28.5,30.5,10.8];
const DELAY_M = [4.9,6.3,7.6,8.7,10.0,9.4,6.7,7.2,7.9,8.1,7.1,16.6,12.1,12.6,16.2,39.1,28.6,20.5,10.8,10.4,14.4,12.9,12.8,23.5,14.3,5.6,7.4,7.8,8.0,7.4,7.1,5.9,10.0,9.6,8.6,12.6,20.1,46.6,60.3,37.8,18.5,33.2,50.7,59.6,24.9,12.8,31.2,45.6,44.6,19.6,29.6,44.7,30.3,40.9,44.3,35.6,56.5,58.2,60.5,83.3,66.0,51.5,24.7,23.9];
const QUEUE_W = [4.0,8.9,10.9,15.6,17.2,19.3,17.6,11.2,13.1,19.3,25.6,40.0,24.2,37.8,66.1,57.8,55.5,40.9,34.5,48.9,32.7,41.3,49.6,27.6,14.8,3.4,18.0,22.0,16.5,11.4,13.4,22.3,19.4,27.1,39.3,59.1,76.8,60.8,31.7,30.5,68.0,69.9,69.2,48.7,38.6,67.8,80.0,53.1,51.2,59.7,77.5,63.3,80.6,85.9,71.0,112.2,109.6,96.5,106.8,97.5,76.1,49.1,51.0,15.0];
const EXCESS_W = [1.2,8.6,10.5,14.5,18.3,19.9,18.5,11.1,12.8,19.9,24.3,40.6,24.9,35.0,62.0,61.5,54.8,45.8,34.3,46.7,36.8,39.1,50.5,30.2,20.6,-0.3,17.0,20.9,19.0,11.9,13.0,23.0,17.2,28.5,36.1,58.4,73.3,65.6,35.4,27.4,65.4,69.7,71.0,52.8,38.5,65.1,78.8,55.9,52.8,56.9,80.8,62.0,79.3,84.8,74.1,104.5,113.6,94.5,106.0,101.3,81.2,49.5,54.8,21.8];
const SPEED_W = [65.6,59.5,56.9,53.9,53.0,49.8,51.4,58.8,56.9,48.9,41.4,29.4,45.2,29.2,19.4,25.1,29.2,36.8,38.4,26.7,41.5,33.2,28.7,43.5,53.4,65.6,48.3,43.1,53.3,59.0,55.5,44.6,49.1,42.8,33.7,26.1,17.6,23.4,39.1,40.9,21.4,22.6,18.0,29.7,38.6,21.6,16.6,30.1,26.8,26.3,18.8,21.1,19.0,16.7,21.7,10.3,12.2,16.0,12.8,13.5,19.0,29.7,28.5,50.0];

const data = TIME.map((t, i) => ({
  time: t, delay_w: DELAY_W[i], delay_m: DELAY_M[i], queue_w: QUEUE_W[i],
  excess_w: EXCESS_W[i], speed_w: SPEED_W[i],
}));

const SUMMARY = [
  { label: "Avg Delay", value: "27.0 s", sub: "per vehicle on weaving section", icon: "⏱" },
  { label: "Avg Queue Length", value: "45.1 veh", sub: "≈ 248 m on weaving section", icon: "🚗" },
  { label: "Avg Time in Queue", value: "3.12 s", sub: "stopped (speed < 0.1 m/s)", icon: "⏳" },
  { label: "Avg Excess Accumulation", value: "45.4 veh", sub: "above free-flow optimal", icon: "📊" },
];

const EDGE_SUMMARY = [
  { edge: "E_weaving", ff: "14.9s", avgTT: "45.6s", delay: "30.7s", timeLoss: "148,562s" },
  { edge: "E_main_in", ff: "14.4s", avgTT: "39.0s", delay: "24.6s", timeLoss: "85,562s" },
  { edge: "E_on_ramp_1", ff: "6.2s", avgTT: "10.2s", delay: "4.0s", timeLoss: "3,829s" },
  { edge: "E_on_ramp_2", ff: "3.7s", avgTT: "6.3s", delay: "2.6s", timeLoss: "2,714s" },
  { edge: "E_main_out", ff: "14.4s", avgTT: "19.8s", delay: "5.4s", timeLoss: "8,969s" },
  { edge: "E_off_ramp", ff: "9.9s", avgTT: "12.5s", delay: "2.6s", timeLoss: "1,490s" },
];

const tabs = ["Delay", "Queue Length", "Excess Accumulation", "Speed"];

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState(0);

  const chartConfigs = [
    { data, lines: [{ key: "delay_w", name: "E_weaving", color: "#e74c3c" }, { key: "delay_m", name: "E_main_in", color: "#3498db" }], yLabel: "Delay (s)", title: "Average Delay per Vehicle" },
    { data, lines: [{ key: "queue_w", name: "E_weaving Queue", color: "#e67e22" }], yLabel: "Queue (vehicles)", title: "Queue Length (Weaving Section)" },
    { data, lines: [{ key: "excess_w", name: "E_weaving Excess", color: "#8e44ad" }], yLabel: "Excess Vehicles", title: "Excess Accumulation (Weaving Section)" },
    { data, lines: [{ key: "speed_w", name: "E_weaving Speed", color: "#27ae60" }], yLabel: "Speed (km/h)", title: "Average Speed (Weaving Section)" },
  ];

  const cfg = chartConfigs[activeTab];

  return (
    <div style={{ fontFamily: "'Segoe UI', system-ui, sans-serif", background: "#0f1117", color: "#e0e0e0", minHeight: "100vh", padding: "24px" }}>
      <div style={{ maxWidth: 960, margin: "0 auto" }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, color: "#fff", marginBottom: 4 }}>
          SUMO Simulation — Traffic Performance Analysis
        </h1>
        <p style={{ fontSize: 13, color: "#888", marginBottom: 24 }}>
          Off-peak period · Weaving bottleneck section · 5,496 vehicles · 3,840s simulation
        </p>

        {/* Summary Cards */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 28 }}>
          {SUMMARY.map((s, i) => (
            <div key={i} style={{ background: "#1a1d27", borderRadius: 10, padding: "16px 14px", border: "1px solid #2a2d3a" }}>
              <div style={{ fontSize: 12, color: "#888", marginBottom: 6 }}>{s.icon} {s.label}</div>
              <div style={{ fontSize: 22, fontWeight: 700, color: ["#e74c3c","#e67e22","#3498db","#8e44ad"][i] }}>{s.value}</div>
              <div style={{ fontSize: 11, color: "#666", marginTop: 4 }}>{s.sub}</div>
            </div>
          ))}
        </div>

        {/* Tab Navigation */}
        <div style={{ display: "flex", gap: 4, marginBottom: 16 }}>
          {tabs.map((tab, i) => (
            <button key={i} onClick={() => setActiveTab(i)}
              style={{
                padding: "8px 16px", borderRadius: 6, border: "none", cursor: "pointer",
                fontSize: 13, fontWeight: activeTab === i ? 600 : 400,
                background: activeTab === i ? "#2a2d3a" : "transparent",
                color: activeTab === i ? "#fff" : "#888",
              }}>{tab}</button>
          ))}
        </div>

        {/* Chart */}
        <div style={{ background: "#1a1d27", borderRadius: 12, padding: "20px 16px 12px", border: "1px solid #2a2d3a", marginBottom: 28 }}>
          <h3 style={{ fontSize: 14, fontWeight: 600, color: "#ccc", margin: "0 0 16px 8px" }}>{cfg.title}</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={cfg.data} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2d3a" />
              <XAxis dataKey="time" stroke="#666" tick={{ fontSize: 11 }} label={{ value: "Time (min)", position: "insideBottom", offset: -2, fontSize: 11, fill: "#888" }} />
              <YAxis stroke="#666" tick={{ fontSize: 11 }} label={{ value: cfg.yLabel, angle: -90, position: "insideLeft", fontSize: 11, fill: "#888" }} />
              <Tooltip contentStyle={{ background: "#1a1d27", border: "1px solid #333", borderRadius: 8, fontSize: 12 }} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              {activeTab === 3 && <ReferenceLine y={90} stroke="#e74c3c" strokeDasharray="5 5" label={{ value: "Speed Limit (90 km/h)", fill: "#e74c3c", fontSize: 10 }} />}
              {cfg.lines.map(l => (
                <Line key={l.key} type="monotone" dataKey={l.key} name={l.name} stroke={l.color} strokeWidth={2} dot={false} />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Edge Detail Table */}
        <div style={{ background: "#1a1d27", borderRadius: 12, padding: 20, border: "1px solid #2a2d3a" }}>
          <h3 style={{ fontSize: 14, fontWeight: 600, color: "#ccc", margin: "0 0 14px 0" }}>Delay Breakdown by Edge</h3>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
            <thead>
              <tr style={{ borderBottom: "1px solid #333" }}>
                {["Edge", "Free-flow TT", "Avg Travel Time", "Avg Delay/veh", "Total TimeLoss"].map(h => (
                  <th key={h} style={{ padding: "8px 10px", textAlign: "left", color: "#888", fontWeight: 500, fontSize: 12 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {EDGE_SUMMARY.map((r, i) => (
                <tr key={i} style={{ borderBottom: "1px solid #222", background: i < 2 ? "#1e1520" : "transparent" }}>
                  <td style={{ padding: "8px 10px", fontWeight: 600, color: i === 0 ? "#e74c3c" : i === 1 ? "#3498db" : "#aaa" }}>{r.edge}</td>
                  <td style={{ padding: "8px 10px" }}>{r.ff}</td>
                  <td style={{ padding: "8px 10px" }}>{r.avgTT}</td>
                  <td style={{ padding: "8px 10px", fontWeight: 600, color: parseFloat(r.delay) > 20 ? "#e74c3c" : "#aaa" }}>{r.delay}</td>
                  <td style={{ padding: "8px 10px" }}>{r.timeLoss}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p style={{ fontSize: 11, color: "#666", marginTop: 12 }}>
            Network total delay: 251,126 veh·s · Average delay per vehicle (all edges): 45.7s
          </p>
        </div>

        {/* Formulas */}
        <div style={{ background: "#1a1d27", borderRadius: 12, padding: 20, border: "1px solid #2a2d3a", marginTop: 16, fontSize: 12, color: "#999", lineHeight: 1.8 }}>
          <h3 style={{ fontSize: 13, fontWeight: 600, color: "#ccc", margin: "0 0 8px 0" }}>Methodology</h3>
          <p><b style={{color:"#e74c3c"}}>Average Delay</b> = Avg Travel Time − Free-flow Travel Time; &nbsp; Free-flow TT = Edge Length / Speed Limit</p>
          <p><b style={{color:"#e67e22"}}>Average Queue Length</b> = Density × Edge Length × (1 − Speed / Free-flow Speed); estimated congested vehicle count</p>
          <p><b style={{color:"#3498db"}}>Average Time in Queue</b> = Total Waiting Time (speed &lt; 0.1 m/s) / Total Vehicles Entered</p>
          <p><b style={{color:"#8e44ad"}}>Average Excess Accumulation</b> = Actual Accumulation − Optimal Accumulation; &nbsp; Optimal = Flow Rate × Free-flow TT (Little's Law)</p>
        </div>
      </div>
    </div>
  );
}
