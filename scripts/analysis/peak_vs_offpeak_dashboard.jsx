import { useState } from "react";
import { AreaChart, Area, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ComposedChart, Bar, ReferenceLine } from "recharts";

// ── Off-Peak (E_weaving) ──
const OT=[0.5,1.5,2.5,3.5,4.5,5.5,6.5,7.5,8.5,9.5,10.5,11.5,12.5,13.5,14.5,15.5,16.5,17.5,18.5,19.5,20.5,21.5,22.5,23.5,24.5,25.5,26.5,27.5,28.5,29.5,30.5,31.5,32.5,33.5,34.5,35.5,36.5,37.5,38.5,39.5,40.5,41.5,42.5,43.5,44.5,45.5,46.5,47.5,48.5,49.5,50.5,51.5,52.5,53.5,54.5,55.5,56.5,57.5,58.5,59.5,60.5,61.5,62.5];
const OD=[6.4,6.1,6.2,7.4,7.4,7.0,6.5,6.3,7.0,6.7,8.1,15.4,10.9,7.9,9.3,5.9,6.1,5.4,7.0,6.3,7.3,8.1,8.1,6.7,7.0,6.2,13.6,7.6,8.0,6.8,6.4,7.1,9.2,7.8,10.8,12.9,19.1,23.9,40.8,36.7,29.6,22.4,24.9,29.5,13.0,21.3,39.7,51.6,32.4,11.1,14.0,16.6,14.2,17.4,9.1,7.7,7.5,6.2,6.5,6.9,6.5,7.3,9.6];
const OQ=[5.1,8.7,8.9,14.6,14.8,12.5,9.7,10.7,12.4,11.4,12.8,25.3,19.7,13.6,19.0,10.1,11.4,9.2,12.7,11.6,14.0,14.0,17.1,13.0,6.2,4.6,22.5,11.9,12.1,12.8,10.3,12.4,16.1,15.1,21.0,26.5,33.9,38.6,55.4,53.0,56.6,40.4,41.3,45.7,24.6,35.8,54.5,63.3,49.7,20.3,23.1,27.2,29.0,26.3,13.2,13.4,13.8,10.7,11.6,6.6,6.1,12.5,9.3];
const OE=[1.5,10.1,7.6,12.8,17.2,13.4,9.7,10.4,13.2,11.4,11.7,26.0,20.6,13.8,20.6,11.0,10.6,10.4,12.7,12.2,13.8,13.4,16.8,14.9,10.9,-1.2,23.7,13.6,10.9,14.5,9.1,13.4,16.1,14.4,19.1,29.0,32.4,39.8,53.7,53.8,57.1,41.8,43.0,43.5,27.3,35.1,52.9,61.2,54.3,22.3,23.7,27.3,28.4,29.3,14.2,12.8,14.1,11.2,12.0,11.0,2.5,11.5,14.6];
const OS=[60.5,61.2,60.9,57.6,57.5,58.6,59.9,60.7,58.7,59.5,55.9,42.6,49.9,56.3,53.0,61.7,61.2,63.1,58.6,60.6,57.9,56.0,56.0,59.6,58.8,60.9,45.1,57.2,56.1,59.3,60.4,58.6,53.5,56.6,50.1,46.3,37.9,33.2,23.2,25.0,29.0,34.6,32.5,29.2,46.2,35.6,23.7,19.5,27.4,49.5,44.5,40.9,44.2,39.9,53.7,56.8,57.5,61.0,60.2,59.0,60.0,57.8,52.5];
const OW=[0,0,0,0,2.2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1.3,0,1.3,0,0,0,0.2,0,0,0,24.9,23.8,154.4,171.4,86.7,10.4,9.5,184.2,0,0.6,260.2,650.2,282.1,0.2,0,0.8,0,0.4,0,0,0,0,0,0,0,0,0];

// ── Peak (E_weaving) ──
const PT=[0.5,1.5,2.5,3.5,4.5,5.5,6.5,7.5,8.5,9.5,10.5,11.5,12.5,13.5,14.5,15.5,16.5,17.5,18.5,19.5,20.5,21.5,22.5,23.5,24.5,25.5,26.5,27.5,28.5,29.5,30.5,31.5,32.5,33.5,34.5,35.5,36.5,37.5,38.5,39.5,40.5,41.5,42.5,43.5,44.5,45.5,46.5,47.5,48.5,49.5,50.5,51.5,52.5,53.5];
const PD=[6.2,7.5,12.2,15.6,23.5,47.0,47.5,20.9,23.7,40.6,31.4,51.2,37.9,11.4,7.8,6.5,9.4,10.0,20.2,21.2,33.4,48.6,34.9,25.5,24.3,23.8,36.6,21.3,15.3,25.3,40.6,27.0,32.0,45.5,14.5,17.4,22.8,36.2,37.4,12.5,25.2,42.2,43.7,12.3,18.3,27.6,69.9,30.8,13.8,8.6,10.0,8.1,8.2,11.2];
const PQ=[6.0,13.6,21.9,29.7,46.5,69.7,66.3,47.0,43.7,61.6,53.9,62.2,30.9,10.8,10.2,13.7,20.1,17.9,32.0,42.7,58.8,63.8,51.3,43.1,43.0,41.2,53.8,37.5,33.0,46.1,62.9,45.8,47.7,54.7,28.9,34.1,39.5,55.1,52.4,24.8,41.5,68.3,54.6,20.9,33.3,39.3,45.0,22.1,13.2,6.8,8.0,6.4,6.5,6.1];
const PE=[1.2,14.6,18.5,30.4,44.9,67.1,68.1,48.6,44.7,60.0,55.9,63.1,36.2,11.9,8.6,12.6,21.2,17.1,29.7,41.9,57.4,65.1,52.0,43.8,43.6,42.8,50.3,41.5,34.0,43.1,62.5,50.2,46.6,52.9,32.0,33.5,40.8,51.7,57.9,24.9,38.3,66.4,59.3,21.8,31.7,41.5,46.8,24.3,14.3,7.8,8.0,6.4,6.4,8.0];
const PS=[60.8,57.4,47.5,42.3,33.5,20.9,20.8,36.0,33.4,23.3,27.9,19.5,24.5,48.8,56.6,60.0,52.8,51.7,36.6,35.6,26.8,20.4,26.0,32.0,32.9,33.3,25.1,35.7,42.7,32.1,23.3,30.8,27.5,21.5,43.9,39.9,34.2,25.3,24.8,47.1,32.2,22.6,22.1,47.4,38.8,30.4,15.3,28.3,44.7,54.5,51.4,55.8,55.5,49.2];
const PW=[0.2,0,0,0,3.6,206.5,505.2,10.8,4.1,232.9,43.8,53.7,48.1,0,0,0,0,0.2,39.5,1.7,35.8,88.4,25.1,0.8,0,0.4,310.4,107.9,0,41.2,104.6,63.8,1.2,77.9,58.9,3.3,2.6,97.2,189.2,0,1.1,151.9,427.1,59.6,34.3,18.2,4.2,0,0,0,0,0,0,0];

// Build unified data arrays
const offpeak = OT.map((t,i)=>({ t, d:OD[i], q:OQ[i], e:OE[i], s:OS[i], w:OW[i] }));
const peak = PT.map((t,i)=>({ t, d:PD[i], q:PQ[i], e:PE[i], s:PS[i], w:PW[i] }));

// Merge into single timeline for overlay chart
const maxLen = Math.max(OT.length, PT.length);
const merged = [];
for (let i = 0; i < maxLen; i++) {
  const row = { t: (i < OT.length ? OT[i] : PT[i]) };
  if (i < OT.length) { row.od=OD[i]; row.oq=OQ[i]; row.oe=OE[i]; row.os=OS[i]; row.ow=OW[i]; }
  if (i < PT.length) { row.pd=PD[i]; row.pq=PQ[i]; row.pe=PE[i]; row.ps=PS[i]; row.pw=PW[i]; }
  merged.push(row);
}

const C = {
  peak: "#ef4444", offpeak: "#38bdf8", peakFill: "#ef444418", offpeakFill: "#38bdf818",
  bg: "#0a0c12", card: "#12151e", border: "#1c2030", text: "#c8cdd8", dim: "#555d70",
  amber: "#f59e0b", green: "#22c55e", purple: "#a78bfa",
};

const KPI = [
  { key:"delay", label:"Avg Delay", unit:"s/veh", pk:"21.9", op:"10.0", icon:"⏱", color:C.peak },
  { key:"queue", label:"Avg Queue", unit:"veh", pk:"36.2", op:"20.6", icon:"🚗", color:C.amber },
  { key:"wait", label:"Time in Queue", unit:"s/veh", pk:"0.68", op:"0.34", icon:"⏳", color:C.purple },
  { key:"excess", label:"Excess Accum.", unit:"veh", pk:"36.5", op:"21.0", icon:"📊", color:C.green },
];

const EDGE_TABLE = [
  { e:"E_weaving",   pk_d:"21.9", op_d:"10.0", pk_q:"36.2", op_q:"20.6", pk_loss:"98,434", op_loss:"54,727" },
  { e:"E_main_in",   pk_d:"20.9", op_d:"5.8",  pk_q:"23.7", op_q:"10.5", pk_loss:"65,631", op_loss:"24,628" },
  { e:"E_main_out",  pk_d:"2.3",  op_d:"2.2",  pk_q:"6.3",  op_q:"6.0",  pk_loss:"6,867",  op_loss:"8,461" },
  { e:"E_on_ramp_1", pk_d:"3.1",  op_d:"1.8",  pk_q:"2.3",  op_q:"1.1",  pk_loss:"4,262",  op_loss:"2,254" },
  { e:"E_on_ramp_2", pk_d:"2.2",  op_d:"1.1",  pk_q:"1.5",  op_q:"0.7",  pk_loss:"2,943",  op_loss:"1,400" },
  { e:"E_off_ramp",  pk_d:"1.1",  op_d:"0.9",  pk_q:"1.5",  op_q:"1.3",  pk_loss:"1,594",  op_loss:"1,372" },
];

const Tip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: "#181c28", border: `1px solid ${C.border}`, borderRadius: 8, padding: "8px 12px", fontSize: 11 }}>
      <div style={{ color: C.dim, marginBottom: 5 }}>{label} min</div>
      {payload.map((p,i) => (
        <div key={i} style={{ color: p.color, marginBottom: 1 }}>{p.name}: <b>{p.value?.toFixed?.(1) ?? p.value}</b></div>
      ))}
    </div>
  );
};

const metrics = [
  { key:"delay", label:"Average Delay", yLabel:"Delay (s)", pk:"pd", op:"od" },
  { key:"queue", label:"Queue Length", yLabel:"Queue (vehicles)", pk:"pq", op:"oq" },
  { key:"wait", label:"Waiting Time per Interval", yLabel:"Waiting (s)", pk:"pw", op:"ow" },
  { key:"excess", label:"Excess Accumulation", yLabel:"Excess (vehicles)", pk:"pe", op:"oe" },
];

const Pct = ({ val }) => {
  const n = parseFloat(val);
  const col = n > 0 ? C.peak : C.green;
  return <span style={{ color: col, fontSize: 11, fontWeight: 600 }}>{n > 0 ? "+" : ""}{val}%</span>;
};

export default function Dashboard() {
  const [tab, setTab] = useState("delay");
  const m = metrics.find(x => x.key === tab);

  return (
    <div style={{ fontFamily: "'DM Sans', system-ui, sans-serif", background: C.bg, color: C.text, minHeight: "100vh", padding: "20px 24px" }}>
      <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet" />
      <div style={{ maxWidth: 940, margin: "0 auto" }}>

        {/* Header */}
        <div style={{ marginBottom: 20 }}>
          <h1 style={{ fontSize: 21, fontWeight: 700, color: "#fff", margin: 0 }}>
            Traffic Performance: <span style={{ color: C.peak }}>Peak</span> vs <span style={{ color: C.offpeak }}>Off-Peak</span>
          </h1>
          <p style={{ fontSize: 12, color: C.dim, margin: "4px 0 0" }}>
            E_weaving bottleneck · Peak: 4,493 veh / 45 min · Off-Peak: 5,496 veh / 63 min · Identical vehicle parameters
          </p>
        </div>

        {/* KPI Cards */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10, marginBottom: 20 }}>
          {KPI.map(k => {
            const active = tab === k.key;
            const change = ((parseFloat(k.pk) - parseFloat(k.op)) / parseFloat(k.op) * 100).toFixed(0);
            return (
              <div key={k.key} onClick={() => setTab(k.key)} style={{
                background: active ? "#1a1e2e" : C.card, borderRadius: 10, padding: "14px 12px", cursor: "pointer",
                border: `1.5px solid ${active ? k.color + "60" : C.border}`, transition: "all 0.15s",
              }}>
                <div style={{ fontSize: 11, color: C.dim, marginBottom: 8 }}>{k.icon} {k.label}</div>
                <div style={{ display: "flex", alignItems: "baseline", gap: 12 }}>
                  <div>
                    <div style={{ fontSize: 10, color: C.peak, marginBottom: 2 }}>Peak</div>
                    <div style={{ fontSize: 22, fontWeight: 700, color: C.peak, lineHeight: 1 }}>{k.pk}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: 10, color: C.offpeak, marginBottom: 2 }}>Off-Peak</div>
                    <div style={{ fontSize: 22, fontWeight: 700, color: C.offpeak, lineHeight: 1 }}>{k.op}</div>
                  </div>
                </div>
                <div style={{ fontSize: 10, color: C.dim, marginTop: 6 }}>{k.unit} · <Pct val={change} /> vs off-peak</div>
              </div>
            );
          })}
        </div>

        {/* Tabs */}
        <div style={{ display: "flex", gap: 3, marginBottom: 2 }}>
          {metrics.map(x => (
            <button key={x.key} onClick={() => setTab(x.key)} style={{
              padding: "6px 14px", borderRadius: "7px 7px 0 0", border: "none", cursor: "pointer", fontSize: 12, fontWeight: tab === x.key ? 600 : 400,
              background: tab === x.key ? C.card : "transparent", color: tab === x.key ? "#fff" : C.dim,
              borderBottom: tab === x.key ? `2px solid ${C.peak}` : "none",
            }}>{x.label}</button>
          ))}
        </div>

        {/* Main Chart */}
        <div style={{ background: C.card, borderRadius: "0 10px 10px 10px", padding: "16px 12px 8px", border: `1px solid ${C.border}`, marginBottom: 16 }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: "#fff", marginBottom: 12, paddingLeft: 8 }}>{m.label} — Peak vs Off-Peak</div>
          <ResponsiveContainer width="100%" height={280}>
            {tab === "wait" ? (
              <ComposedChart data={merged} margin={{ top: 8, right: 16, bottom: 4, left: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={C.border} />
                <XAxis dataKey="t" stroke={C.dim} tick={{ fontSize: 10 }} label={{ value: "Time (min)", position: "insideBottom", offset: -2, fontSize: 10, fill: C.dim }} />
                <YAxis stroke={C.dim} tick={{ fontSize: 10 }} label={{ value: m.yLabel, angle: -90, position: "insideLeft", fontSize: 10, fill: C.dim }} />
                <Tooltip content={<Tip />} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Bar dataKey={m.pk} name="Peak" fill={C.peak} fillOpacity={0.5} radius={[2,2,0,0]} />
                <Bar dataKey={m.op} name="Off-Peak" fill={C.offpeak} fillOpacity={0.4} radius={[2,2,0,0]} />
              </ComposedChart>
            ) : (
              <AreaChart data={merged} margin={{ top: 8, right: 16, bottom: 4, left: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={C.border} />
                <XAxis dataKey="t" stroke={C.dim} tick={{ fontSize: 10 }} label={{ value: "Time (min)", position: "insideBottom", offset: -2, fontSize: 10, fill: C.dim }} />
                <YAxis stroke={C.dim} tick={{ fontSize: 10 }} label={{ value: m.yLabel, angle: -90, position: "insideLeft", fontSize: 10, fill: C.dim }} />
                <Tooltip content={<Tip />} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Area type="monotone" dataKey={m.pk} name="Peak" stroke={C.peak} fill={C.peak} fillOpacity={0.12} strokeWidth={2} />
                <Area type="monotone" dataKey={m.op} name="Off-Peak" stroke={C.offpeak} fill={C.offpeak} fillOpacity={0.08} strokeWidth={2} />
              </AreaChart>
            )}
          </ResponsiveContainer>
        </div>

        {/* Speed Profile */}
        <div style={{ background: C.card, borderRadius: 10, padding: "14px 12px 8px", border: `1px solid ${C.border}`, marginBottom: 16 }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: "#fff", marginBottom: 8, paddingLeft: 8 }}>Speed Profile — E_weaving</div>
          <ResponsiveContainer width="100%" height={160}>
            <LineChart data={merged} margin={{ top: 4, right: 16, bottom: 4, left: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={C.border} />
              <XAxis dataKey="t" stroke={C.dim} tick={{ fontSize: 9 }} />
              <YAxis stroke={C.dim} tick={{ fontSize: 9 }} domain={[0, 80]} label={{ value: "km/h", angle: -90, position: "insideLeft", fontSize: 9, fill: C.dim }} />
              <Tooltip content={<Tip />} />
              <Legend wrapperStyle={{ fontSize: 10 }} />
              <Line type="monotone" dataKey="ps" name="Peak" stroke={C.peak} strokeWidth={1.8} dot={false} />
              <Line type="monotone" dataKey="os" name="Off-Peak" stroke={C.offpeak} strokeWidth={1.8} dot={false} />
              <ReferenceLine y={76} stroke={C.dim} strokeDasharray="5 5" label={{ value: "Free-flow 76 km/h", fill: C.dim, fontSize: 8 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Comparison Table */}
        <div style={{ background: C.card, borderRadius: 10, padding: "16px 14px", border: `1px solid ${C.border}`, marginBottom: 16 }}>
          <h3 style={{ fontSize: 13, fontWeight: 600, color: "#fff", margin: "0 0 10px" }}>Per-Edge Comparison</h3>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11 }}>
            <thead>
              <tr style={{ borderBottom: `1px solid ${C.border}` }}>
                <th style={{ padding: "6px 8px", textAlign: "left", color: C.dim, fontWeight: 500 }}>Edge</th>
                <th colSpan={2} style={{ padding: "6px 8px", textAlign: "center", color: C.dim, fontWeight: 500 }}>Avg Delay (s/veh)</th>
                <th colSpan={2} style={{ padding: "6px 8px", textAlign: "center", color: C.dim, fontWeight: 500 }}>Avg Queue (veh)</th>
                <th colSpan={2} style={{ padding: "6px 8px", textAlign: "center", color: C.dim, fontWeight: 500 }}>Total TimeLoss (s)</th>
              </tr>
              <tr style={{ borderBottom: `1px solid ${C.border}` }}>
                <th></th>
                <th style={{ padding: "3px 8px", fontSize: 10, color: C.peak, fontWeight: 600 }}>Peak</th>
                <th style={{ padding: "3px 8px", fontSize: 10, color: C.offpeak, fontWeight: 600 }}>Off-Peak</th>
                <th style={{ padding: "3px 8px", fontSize: 10, color: C.peak, fontWeight: 600 }}>Peak</th>
                <th style={{ padding: "3px 8px", fontSize: 10, color: C.offpeak, fontWeight: 600 }}>Off-Peak</th>
                <th style={{ padding: "3px 8px", fontSize: 10, color: C.peak, fontWeight: 600 }}>Peak</th>
                <th style={{ padding: "3px 8px", fontSize: 10, color: C.offpeak, fontWeight: 600 }}>Off-Peak</th>
              </tr>
            </thead>
            <tbody>
              {EDGE_TABLE.map((r, i) => {
                const hot = i < 2;
                return (
                  <tr key={i} style={{ borderBottom: `1px solid ${C.border}10` }}>
                    <td style={{ padding: "6px 8px", fontWeight: 600, color: hot ? C.amber : C.text }}>{r.e}</td>
                    <td style={{ padding: "6px 8px", textAlign: "center", color: parseFloat(r.pk_d)>10 ? C.peak : C.text, fontWeight: parseFloat(r.pk_d)>10?600:400 }}>{r.pk_d}</td>
                    <td style={{ padding: "6px 8px", textAlign: "center" }}>{r.op_d}</td>
                    <td style={{ padding: "6px 8px", textAlign: "center", color: parseFloat(r.pk_q)>20 ? C.peak : C.text, fontWeight: parseFloat(r.pk_q)>20?600:400 }}>{r.pk_q}</td>
                    <td style={{ padding: "6px 8px", textAlign: "center" }}>{r.op_q}</td>
                    <td style={{ padding: "6px 8px", textAlign: "center" }}>{r.pk_loss}</td>
                    <td style={{ padding: "6px 8px", textAlign: "center" }}>{r.op_loss}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          <div style={{ display: "flex", gap: 24, fontSize: 10, color: C.dim, marginTop: 10, lineHeight: 1.7 }}>
            <span><span style={{color:C.peak}}>■</span> Peak total timeLoss: <b style={{color:C.text}}>179,731 s</b> · 4,493 veh · Avg <b style={{color:C.text}}>40.0 s/veh</b></span>
            <span><span style={{color:C.offpeak}}>■</span> Off-Peak total timeLoss: <b style={{color:C.text}}>92,842 s</b> · 5,496 veh · Avg <b style={{color:C.text}}>16.9 s/veh</b></span>
          </div>
        </div>

        {/* Methodology */}
        <div style={{ background: C.card, borderRadius: 10, padding: "12px 14px", border: `1px solid ${C.border}`, fontSize: 11, color: C.dim, lineHeight: 1.9 }}>
          <h3 style={{ fontSize: 12, fontWeight: 600, color: C.text, margin: "0 0 4px" }}>Methodology</h3>
          <p><b style={{color:C.peak}}>Average Delay</b> = Actual TT − Free-flow TT (Edge Length ÷ Speed Limit)</p>
          <p><b style={{color:C.amber}}>Queue Length</b> = Density × Length × (1 − v/v_ff) — congested vehicle count</p>
          <p><b style={{color:C.purple}}>Time in Queue</b> = Waiting time per interval where vehicle speed &lt; 0.1 m/s (full stop)</p>
          <p><b style={{color:C.green}}>Excess Accumulation</b> = Actual − Optimal accumulation (Little's Law: N* = λ × W_ff)</p>
        </div>
      </div>
    </div>
  );
}
