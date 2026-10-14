import { useState, useCallback } from "react";

const ANTHROPIC_MODEL = "claude-sonnet-4-20250514";

// ── Utility: parse CSV/Excel-like text ──────────────────────────────────────
function parseCSV(text) {
  const lines = text.trim().split("\n");
  if (lines.length < 2) return { headers: [], rows: [] };
  const parseRow = (line) => {
    const cols = [];
    let cur = "", inQ = false;
    for (let i = 0; i < line.length; i++) {
      const c = line[i];
      if (c === '"') { inQ = !inQ; }
      else if (c === "," && !inQ) { cols.push(cur.trim()); cur = ""; }
      else cur += c;
    }
    cols.push(cur.trim());
    return cols;
  };
  const headers = parseRow(lines[0]);
  const rows = lines.slice(1).map(l => {
    const cols = parseRow(l);
    const obj = {};
    headers.forEach((h, i) => obj[h] = cols[i] || "");
    return obj;
  });
  return { headers, rows };
}

function downloadCSV(data, filename) {
  if (!data.length) return;
  const headers = Object.keys(data[0]);
  const csv = [headers.join(","), ...data.map(row =>
    headers.map(h => `"${(row[h] || "").toString().replace(/"/g, '""')}"`).join(",")
  )].join("\n");
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a"); a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}

// ── Column Mapper ────────────────────────────────────────────────────────────
function ColMapper({ headers, mapping, onChange }) {
  const field = (label, key, hint) => (
    <div style={{ marginBottom: 14 }}>
      <label style={{ display: "block", fontSize: 11, fontWeight: 700, letterSpacing: 1, color: "#a0a0b0", marginBottom: 6, textTransform: "uppercase" }}>{label}</label>
      <select value={mapping[key] || ""} onChange={e => onChange(key, e.target.value)}
        style={{ width: "100%", padding: "10px 14px", background: "#1a1a2e", border: "1px solid #2a2a4a", borderRadius: 8, color: mapping[key] ? "#e0e0ff" : "#606080", fontSize: 13, appearance: "none", cursor: "pointer" }}>
        <option value="">{hint}</option>
        {headers.map(h => <option key={h} value={h}>{h}</option>)}
      </select>
    </div>
  );
  return (
    <div>
      {field("Review Title Column", "title", "Select title column…")}
      {field("Review Body Column", "body", "Select review text column…")}
      {field("Star Rating Column", "rating", "Select rating column…")}
    </div>
  );
}

// ── Main App ─────────────────────────────────────────────────────────────────
export default function App() {
  const [stage, setStage] = useState("upload"); // upload | map | processing | results
  const [fileText, setFileText] = useState("");
  const [headers, setHeaders] = useState([]);
  const [allRows, setAllRows] = useState([]);
  const [mapping, setMapping] = useState({ title: "", body: "", rating: "" });
  const [results, setResults] = useState([]);
  const [progress, setProgress] = useState({ done: 0, total: 0, currentIssue: "" });
  const [error, setError] = useState("");
  const [dragOver, setDragOver] = useState(false);

  // ── File ingestion ──────────────────────────────────────────────────────
  const handleFile = useCallback(async (file) => {
    setError("");
    if (!file) return;
    const ext = file.name.split(".").pop().toLowerCase();
    if (ext === "csv") {
      const text = await file.text();
      const { headers, rows } = parseCSV(text);
      setHeaders(headers); setAllRows(rows); setFileText(text);
      setStage("map");
    } else if (["xlsx", "xls"].includes(ext)) {
      // Use SheetJS from CDN via dynamic import trick
      const reader = new FileReader();
      reader.onload = async (e) => {
        try {
          // Load SheetJS dynamically
          if (!window.XLSX) {
            await new Promise((res, rej) => {
              const s = document.createElement("script");
              s.src = "https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js";
              s.onload = res; s.onerror = rej;
              document.head.appendChild(s);
            });
          }
          const wb = window.XLSX.read(e.target.result, { type: "array" });
          const ws = wb.Sheets[wb.SheetNames[0]];
          const json = window.XLSX.utils.sheet_to_json(ws, { defval: "" });
          if (!json.length) { setError("Sheet appears empty."); return; }
          const hdrs = Object.keys(json[0]);
          setHeaders(hdrs); setAllRows(json);
          setStage("map");
        } catch (err) { setError("Failed to parse Excel file: " + err.message); }
      };
      reader.readAsArrayBuffer(file);
    } else {
      setError("Please upload a .csv, .xlsx, or .xls file.");
    }
  }, []);

  const onDrop = (e) => { e.preventDefault(); setDragOver(false); handleFile(e.dataTransfer.files[0]); };

  // ── Classification ──────────────────────────────────────────────────────
  const classify = async () => {
    if (!mapping.body || !mapping.rating) { setError("Please map the review body and rating columns."); return; }
    setError("");

    const negative = allRows.filter(r => {
      const rating = parseFloat(r[mapping.rating]);
      return !isNaN(rating) && rating < 4;
    });

    if (!negative.length) { setError("No reviews with rating < 4 found."); return; }

    setStage("processing");
    setProgress({ done: 0, total: negative.length, currentIssue: "Discovering issue categories…" });

    // Step 1: Discover categories from a sample
    const sample = negative.slice(0, Math.min(50, negative.length)).map((r, i) =>
      `${i + 1}. Title: ${r[mapping.title] || ""}\n   Review: ${r[mapping.body] || ""}`
    ).join("\n\n");

    let categories = [];
    try {
      const catRes = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: ANTHROPIC_MODEL, max_tokens: 1000,
          messages: [{
            role: "user",
            content: `You are an expert at analyzing negative product reviews. Read these reviews and identify the distinct issue categories that customers are complaining about. Be consistent and use clear, standardized category names (e.g. "Digestive Issues", "Overpriced", "Bad Taste", "Poor Packaging", "No Effect", "Side Effects", "Bad Smell", "Wrong Product").

Return ONLY a JSON array of category strings, nothing else. Example: ["Digestive Issues","Overpriced","Bad Taste"]

Reviews:
${sample}`
          }]
        })
      });
      const catData = await catRes.json();
      const catText = catData.content?.[0]?.text || "[]";
      const clean = catText.replace(/```json|```/g, "").trim();
      categories = JSON.parse(clean);
    } catch (e) {
      setError("Failed to discover categories. Check your API access."); setStage("map"); return;
    }

    // Step 2: Classify each review in batches
    const BATCH = 10;
    const classified = [];

    for (let i = 0; i < negative.length; i += BATCH) {
      const batch = negative.slice(i, i + BATCH);
      const batchText = batch.map((r, idx) =>
        `${idx + 1}. Title: ${r[mapping.title] || ""}\n   Review: ${r[mapping.body] || ""}`
      ).join("\n\n");

      setProgress(p => ({ ...p, done: i, currentIssue: `Classifying reviews ${i + 1}–${Math.min(i + BATCH, negative.length)}…` }));

      try {
        const res = await fetch("https://api.anthropic.com/v1/messages", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            model: ANTHROPIC_MODEL, max_tokens: 1000,
            messages: [{
              role: "user",
              content: `You are classifying negative product reviews. Available categories: ${categories.join(", ")}.

For each review below, assign the SINGLE most dominant issue. If none of the categories fit, create a new concise category name.

Return ONLY a JSON array of objects like: [{"index":1,"category":"Digestive Issues"},{"index":2,"category":"Overpriced"}]

Reviews:
${batchText}`
            }]
          })
        });
        const data = await res.json();
        const txt = data.content?.[0]?.text || "[]";
        const clean = txt.replace(/```json|```/g, "").trim();
        const parsed = JSON.parse(clean);
        batch.forEach((row, idx) => {
          const match = parsed.find(p => p.index === idx + 1);
          classified.push({ ...row, Issue_Category: match?.category || "Uncategorized" });
        });
      } catch (e) {
        batch.forEach(row => classified.push({ ...row, Issue_Category: "Error" }));
      }
    }

    setResults(classified);
    setProgress({ done: negative.length, total: negative.length, currentIssue: "Done!" });
    setStage("results");
  };

  // ── Issue summary ───────────────────────────────────────────────────────
  const issueSummary = results.reduce((acc, r) => {
    acc[r.Issue_Category] = (acc[r.Issue_Category] || 0) + 1; return acc;
  }, {});
  const sortedIssues = Object.entries(issueSummary).sort((a, b) => b[1] - a[1]);
  const maxCount = sortedIssues[0]?.[1] || 1;

  // ── Styles ───────────────────────────────────────────────────────────────
  const s = {
    app: { minHeight: "100vh", background: "#0d0d1a", color: "#e0e0ff", fontFamily: "'DM Sans', 'Segoe UI', sans-serif", padding: "40px 20px", display: "flex", flexDirection: "column", alignItems: "center" },
    card: { background: "#13132a", border: "1px solid #2a2a4a", borderRadius: 16, padding: "32px 36px", width: "100%", maxWidth: 680 },
    title: { fontSize: 28, fontWeight: 800, letterSpacing: -0.5, marginBottom: 4, background: "linear-gradient(135deg, #a78bfa, #60a5fa)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" },
    sub: { color: "#6060a0", fontSize: 14, marginBottom: 32 },
    btn: { padding: "12px 28px", borderRadius: 10, border: "none", fontWeight: 700, fontSize: 14, cursor: "pointer", letterSpacing: 0.3 },
    primaryBtn: { background: "linear-gradient(135deg, #7c3aed, #3b82f6)", color: "#fff" },
    ghostBtn: { background: "transparent", color: "#6060a0", border: "1px solid #2a2a4a" },
    dropzone: { border: "2px dashed", borderColor: dragOver ? "#7c3aed" : "#2a2a4a", borderRadius: 14, padding: "48px 32px", textAlign: "center", cursor: "pointer", transition: "all 0.2s", background: dragOver ? "#1a0f3a" : "transparent" },
    tag: (color) => ({ display: "inline-block", padding: "2px 10px", borderRadius: 20, fontSize: 11, fontWeight: 700, background: color + "22", color, letterSpacing: 0.5 }),
    bar: (pct, color) => ({ height: 8, borderRadius: 4, background: color, width: `${pct}%`, transition: "width 0.6s ease" }),
  };

  const COLORS = ["#a78bfa","#60a5fa","#34d399","#f472b6","#fb923c","#facc15","#38bdf8","#c084fc","#4ade80","#f87171"];

  return (
    <div style={s.app}>
      <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700;800&display=swap" rel="stylesheet" />

      {/* Header */}
      <div style={{ textAlign: "center", marginBottom: 36 }}>
        <div style={s.title}>Review Issue Classifier</div>
        <div style={s.sub}>Upload negative reviews → AI discovers & classifies issues → Export CSV</div>
        {/* Steps */}
        <div style={{ display: "flex", gap: 8, justifyContent: "center", marginTop: 16 }}>
          {["Upload", "Map Columns", "Classify", "Results"].map((step, i) => {
            const stageIdx = { upload: 0, map: 1, processing: 2, results: 3 }[stage];
            const active = i === stageIdx, done = i < stageIdx;
            return (
              <div key={step} style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <div style={{ width: 24, height: 24, borderRadius: "50%", background: done ? "#7c3aed" : active ? "#3b82f6" : "#1a1a2e", border: `2px solid ${active ? "#3b82f6" : done ? "#7c3aed" : "#2a2a4a"}`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 11, fontWeight: 700, color: active || done ? "#fff" : "#404060" }}>
                  {done ? "✓" : i + 1}
                </div>
                <span style={{ fontSize: 12, color: active ? "#e0e0ff" : done ? "#7c3aed" : "#404060", fontWeight: active ? 700 : 500 }}>{step}</span>
                {i < 3 && <div style={{ width: 24, height: 1, background: "#2a2a4a" }} />}
              </div>
            );
          })}
        </div>
      </div>

      {/* ── UPLOAD ── */}
      {stage === "upload" && (
        <div style={s.card}>
          <div style={s.dropzone}
            onDragOver={e => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={onDrop}
            onClick={() => document.getElementById("fi").click()}>
            <input id="fi" type="file" accept=".csv,.xlsx,.xls" style={{ display: "none" }} onChange={e => handleFile(e.target.files[0])} />
            <div style={{ fontSize: 40, marginBottom: 16 }}>📂</div>
            <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 8 }}>Drop your file here or click to browse</div>
            <div style={{ color: "#505080", fontSize: 13 }}>Supports .csv, .xlsx, .xls</div>
          </div>
          {error && <div style={{ marginTop: 16, padding: "12px 16px", background: "#2d0a0a", border: "1px solid #7f1d1d", borderRadius: 10, color: "#fca5a5", fontSize: 13 }}>{error}</div>}
        </div>
      )}

      {/* ── MAP ── */}
      {stage === "map" && (
        <div style={s.card}>
          <div style={{ marginBottom: 24 }}>
            <div style={{ fontWeight: 700, fontSize: 17, marginBottom: 4 }}>Map Your Columns</div>
            <div style={{ color: "#505080", fontSize: 13 }}>{allRows.length} rows detected. Tell us which columns to use.</div>
          </div>
          <ColMapper headers={headers} mapping={mapping} onChange={(k, v) => setMapping(m => ({ ...m, [k]: v }))} />
          {error && <div style={{ marginBottom: 16, padding: "12px 16px", background: "#2d0a0a", border: "1px solid #7f1d1d", borderRadius: 10, color: "#fca5a5", fontSize: 13 }}>{error}</div>}
          <div style={{ display: "flex", gap: 12, marginTop: 8 }}>
            <button style={{ ...s.btn, ...s.ghostBtn }} onClick={() => { setStage("upload"); setError(""); }}>← Back</button>
            <button style={{ ...s.btn, ...s.primaryBtn, flex: 1 }} onClick={classify}>🤖 Classify Reviews</button>
          </div>
        </div>
      )}

      {/* ── PROCESSING ── */}
      {stage === "processing" && (
        <div style={{ ...s.card, textAlign: "center" }}>
          <div style={{ fontSize: 48, marginBottom: 20 }}>⚙️</div>
          <div style={{ fontWeight: 700, fontSize: 18, marginBottom: 8 }}>Classifying Reviews…</div>
          <div style={{ color: "#505080", fontSize: 13, marginBottom: 24 }}>{progress.currentIssue}</div>
          <div style={{ background: "#0d0d1a", borderRadius: 10, height: 10, overflow: "hidden", marginBottom: 12 }}>
            <div style={{ ...s.bar(progress.total ? (progress.done / progress.total) * 100 : 0, "linear-gradient(90deg,#7c3aed,#3b82f6)") }} />
          </div>
          <div style={{ color: "#6060a0", fontSize: 13 }}>{progress.done} / {progress.total} reviews processed</div>
        </div>
      )}

      {/* ── RESULTS ── */}
      {stage === "results" && (
        <div style={{ width: "100%", maxWidth: 720 }}>
          {/* Summary card */}
          <div style={{ ...s.card, marginBottom: 20 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 24 }}>
              <div>
                <div style={{ fontWeight: 800, fontSize: 18, marginBottom: 4 }}>Issue Breakdown</div>
                <div style={{ color: "#505080", fontSize: 13 }}>{results.length} negative reviews classified into {sortedIssues.length} categories</div>
              </div>
              <button style={{ ...s.btn, ...s.primaryBtn }} onClick={() => downloadCSV(results, "classified_reviews.csv")}>⬇ Export CSV</button>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              {sortedIssues.map(([issue, count], i) => (
                <div key={issue}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                      <span style={s.tag(COLORS[i % COLORS.length])}>{issue}</span>
                    </div>
                    <span style={{ fontWeight: 700, fontSize: 14, color: COLORS[i % COLORS.length] }}>{count} <span style={{ color: "#404060", fontWeight: 400 }}>reviews</span></span>
                  </div>
                  <div style={{ background: "#0d0d1a", borderRadius: 6, height: 8, overflow: "hidden" }}>
                    <div style={s.bar((count / maxCount) * 100, COLORS[i % COLORS.length])} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Review table */}
          <div style={s.card}>
            <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 16 }}>Classified Reviews</div>
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid #2a2a4a" }}>
                    {[mapping.title && "Title", mapping.rating && "Rating", "Issue Category"].filter(Boolean).map(h => (
                      <th key={h} style={{ padding: "10px 12px", textAlign: "left", color: "#6060a0", fontWeight: 700, fontSize: 11, letterSpacing: 1, textTransform: "uppercase" }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {results.slice(0, 50).map((r, i) => {
                    const catIdx = sortedIssues.findIndex(([k]) => k === r.Issue_Category);
                    return (
                      <tr key={i} style={{ borderBottom: "1px solid #1a1a30" }}>
                        {mapping.title && <td style={{ padding: "10px 12px", color: "#c0c0e0", maxWidth: 220, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{r[mapping.title]}</td>}
                        {mapping.rating && <td style={{ padding: "10px 12px", color: "#f87171", fontWeight: 700 }}>{'★'.repeat(Math.floor(parseFloat(r[mapping.rating]) || 0))}</td>}
                        <td style={{ padding: "10px 12px" }}><span style={s.tag(COLORS[catIdx % COLORS.length])}>{r.Issue_Category}</span></td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              {results.length > 50 && <div style={{ textAlign: "center", color: "#404060", fontSize: 12, padding: "12px 0" }}>Showing 50 of {results.length} — export CSV for full data</div>}
            </div>
          </div>

          <div style={{ textAlign: "center", marginTop: 20 }}>
            <button style={{ ...s.btn, ...s.ghostBtn }} onClick={() => { setStage("upload"); setResults([]); setAllRows([]); setHeaders([]); setMapping({ title: "", body: "", rating: "" }); }}>
              ← Start Over
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
