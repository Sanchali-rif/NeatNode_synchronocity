import { useState, useRef, useCallback } from "react";
import BASE_URL from './api';

const styles = `
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500&display=swap');

  :root {
    --bg: #ffffff;
    --bg-card-hover: #f9fafb;
    --bg-pill: #f3f4f6;
    --border: rgba(0,0,0,0.08);
    --border-strong: rgba(0,0,0,0.15);
    --text-primary: #0f172a;
    --text-secondary: #475569;
    --text-muted: #64748b;
    --accent: #4f46e5;
    --accent-glow: rgba(79, 70, 229, 0.15);
    --accent-soft: rgba(79, 70, 229, 0.1);
    --green: #059669;
    --green-soft: rgba(5, 150, 105, 0.12);
    --amber: #d97706;
    --amber-soft: rgba(217, 119, 6, 0.12);
    --text-stroke: rgba(0,0,0,0.2);
  }

  [data-theme="dark"] {
    --bg: #0a0b0f;
    --bg-card-hover: #161920;
    --bg-pill: #1a1d26;
    --border: rgba(255,255,255,0.07);
    --border-strong: rgba(255,255,255,0.12);
    --text-primary: #f0f0f5;
    --text-secondary: #8a8d9e;
    --text-muted: #50546a;
    --accent: #4f6ef7;
    --accent-glow: rgba(79,110,247,0.15);
    --accent-soft: rgba(79,110,247,0.1);
    --green: #2dd9a4;
    --green-soft: rgba(45,217,164,0.1);
    --amber: #f5a623;
    --amber-soft: rgba(245,166,35,0.1);
    --text-stroke: rgba(255,255,255,0.3);
  }

  .nn-page {
    min-height: 100vh;
    display: grid;
    grid-template-columns: 1fr 1fr;
    padding-top: 80px;
    background: var(--bg);
    color: var(--text-primary);
    font-family: 'Inter', sans-serif;
    -webkit-font-smoothing: antialiased;
  }

  .nn-left {
    padding: 5rem 4rem 4rem 5rem;
    display: flex;
    flex-direction: column;
    justify-content: center;
    border-right: 1px solid var(--border);
    position: relative;
    overflow: hidden;
  }

  .nn-left::after {
    content: '';
    position: absolute;
    bottom: -120px;
    left: -80px;
    width: 420px;
    height: 420px;
    background: radial-gradient(circle, var(--accent-glow) 0%, transparent 70%);
    pointer-events: none;
  }

  .nn-eyebrow {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 1.5rem;
  }

  .nn-eyebrow-dot {
    display: inline-block;
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--accent);
    flex-shrink: 0;
  }

  .nn-h1 {
    font-family: 'Inter', sans-serif;
    font-size: clamp(2.2rem, 3.5vw, 3.2rem);
    font-weight: 900;
    line-height: 1.08;
    letter-spacing: -0.04em;
    color: var(--text-primary);
    margin-bottom: 1.25rem;
  }

  .nn-h1-outline {
    font-style: normal;
    color: transparent;
    -webkit-text-stroke: 1.5px var(--text-stroke);
  }

  .nn-h1-highlight {
    font-style: normal;
    color: var(--accent);
  }

  .nn-desc {
    font-size: 15px;
    color: var(--text-secondary);
    line-height: 1.7;
    max-width: 460px;
    margin-bottom: 2.5rem;
  }

  .nn-badges {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-bottom: 3rem;
  }

  .nn-badge {
    display: flex;
    flex-direction: column;
    gap: 3px;
    padding: 12px 18px;
    background: var(--bg-pill);
    border: 1px solid var(--border);
    border-radius: 10px;
  }

  .nn-badge-label {
    font-size: 10px;
    font-weight: 500;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--text-muted);
  }

  .nn-badge-value {
    font-size: 13px;
    font-weight: 500;
    color: var(--text-primary);
  }

  .nn-features {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .nn-feature-card {
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.1rem 1.4rem;
    transition: background 0.2s, border-color 0.2s;
    cursor: default;
  }

  .nn-feature-card:hover {
    background: var(--bg-card-hover);
    border-color: var(--border-strong);
  }

  .nn-feature-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 5px;
  }

  .nn-feature-icon {
    width: 28px;
    height: 28px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .nn-feature-icon svg {
    width: 14px;
    height: 14px;
  }

  .fi-blue  { background: var(--accent-soft); color: var(--accent); }
  .fi-green { background: var(--green-soft);  color: var(--green); }
  .fi-amber { background: var(--amber-soft);  color: var(--amber); }

  .nn-feature-title {
    font-size: 14px;
    font-weight: 500;
    color: var(--text-primary);
  }

  .nn-feature-desc {
    font-size: 13px;
    color: var(--text-secondary);
    line-height: 1.55;
    padding-left: 38px;
  }

  .nn-right {
    padding: 5rem 5rem 4rem 4rem;
    display: flex;
    flex-direction: column;
    justify-content: center;
    gap: 1.5rem;
    position: relative;
    overflow: hidden;
  }

  .nn-right::before {
    content: '';
    position: absolute;
    top: -100px;
    right: -100px;
    width: 360px;
    height: 360px;
    background: radial-gradient(circle, var(--accent-glow) 0%, transparent 70%);
    pointer-events: none;
  }

  .nn-upload-zone {
    border: 1.5px dashed var(--border-strong);
    border-radius: 16px;
    padding: 3.5rem 2rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 12px;
    text-align: center;
    cursor: pointer;
    transition: border-color 0.25s, background 0.25s;
    position: relative;
    overflow: hidden;
  }

  .nn-upload-zone::after {
    content: '';
    position: absolute;
    inset: 0;
    background: radial-gradient(ellipse at 50% 0%, var(--accent-glow) 0%, transparent 65%);
    opacity: 0;
    transition: opacity 0.3s;
    pointer-events: none;
  }

  .nn-upload-zone:hover,
  .nn-upload-zone.drag-over {
    border-color: var(--accent);
    background: var(--accent-soft);
  }

  .nn-upload-zone:hover::after,
  .nn-upload-zone.drag-over::after { opacity: 1; }

  .nn-upload-icon {
    width: 56px;
    height: 56px;
    background: var(--bg-pill);
    border: 1px solid var(--border-strong);
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background 0.25s, border-color 0.25s;
    position: relative;
    z-index: 1;
  }

  .nn-upload-zone:hover .nn-upload-icon,
  .nn-upload-zone.drag-over .nn-upload-icon {
    background: var(--accent-soft);
    border-color: var(--accent);
  }

  .nn-upload-icon svg {
    width: 22px;
    height: 22px;
    stroke: var(--text-secondary);
    transition: stroke 0.25s;
  }

  .nn-upload-zone:hover .nn-upload-icon svg,
  .nn-upload-zone.drag-over .nn-upload-icon svg { stroke: var(--accent); }

  .nn-upload-primary {
    font-size: 15px;
    font-weight: 500;
    color: var(--text-primary);
    position: relative;
    z-index: 1;
  }

  .nn-upload-primary span {
    color: var(--accent);
    text-decoration: underline;
  }

  .nn-upload-hint {
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    color: var(--text-muted);
    letter-spacing: 0.02em;
    position: relative;
    z-index: 1;
  }

  .nn-file-name {
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    color: var(--green);
    background: var(--green-soft);
    padding: 6px 16px;
    border-radius: 20px;
    position: relative;
    z-index: 1;
  }

  .nn-divider {
    border: none;
    border-top: 1px solid var(--border);
  }

  .nn-prompt-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 10px;
  }

  .nn-prompt-label {
    font-size: 10px;
    font-weight: 500;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    color: var(--text-muted);
  }

  .nn-prompt-optional {
    font-size: 11px;
    color: var(--text-muted);
    background: var(--bg-pill);
    padding: 2px 9px;
    border-radius: 20px;
    border: 1px solid var(--border);
  }

  .nn-textarea {
    width: 100%;
    background: var(--bg-pill);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 14px 16px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12.5px;
    color: var(--text-secondary);
    resize: none;
    outline: none;
    line-height: 1.65;
    transition: border-color 0.2s, color 0.2s;
  }

  .nn-textarea::placeholder { color: var(--text-muted); }

  .nn-textarea:focus {
    border-color: var(--accent);
    color: var(--text-primary);
  }

  .nn-prompt-hint {
    font-size: 12px;
    color: var(--text-muted);
    line-height: 1.55;
    margin-top: 10px;
  }

  .nn-cta {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    background: var(--accent);
    color: #fff;
    font-family: 'Inter', sans-serif;
    font-size: 15px;
    font-weight: 500;
    border: none;
    border-radius: 13px;
    padding: 16px 24px;
    cursor: pointer;
    letter-spacing: -0.01em;
    position: relative;
    overflow: hidden;
    transition: filter 0.2s, transform 0.15s;
  }

  .nn-cta::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: rgba(255,255,255,0.2);
  }

  .nn-cta:hover:not(:disabled) { filter: brightness(1.1); }
  .nn-cta:active:not(:disabled) { transform: scale(0.99); }
  .nn-cta:disabled { opacity: 0.6; cursor: not-allowed; }

  .nn-cta svg {
    width: 17px;
    height: 17px;
  }

  .nn-status {
    display: flex;
    align-items: center;
    gap: 7px;
    font-size: 12px;
    color: var(--text-muted);
    justify-content: center;
  }

  .nn-status-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: var(--green);
    box-shadow: 0 0 6px var(--green);
    flex-shrink: 0;
  }

  .nn-flash {
    position: fixed;
    top: 20px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 200;
    animation: fadeIn 0.2s ease;
    background: var(--bg);
    border: 1px solid var(--border-strong);
    border-radius: 12px;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: 500;
    backdrop-filter: blur(12px);
    display: flex;
    align-items: center;
    gap: 8px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.5);
  }

  .nn-flash-success { border-color: rgba(45,217,164,0.3); color: var(--green); }
  .nn-flash-error { border-color: rgba(245,166,35,0.3); color: var(--amber); }

  .nn-success-container {
    background: var(--green-soft);
    border: 1px solid rgba(45,217,164,0.2);
    border-radius: 12px;
    padding: 16px;
    animation: fadeIn 0.3s ease;
  }

  .nn-success-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
  }

  .nn-success-icon-bg {
    width: 22px;
    height: 22px;
    border-radius: 50%;
    background: rgba(45,217,164,0.2);
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .nn-success-title {
    font-weight: 700;
    font-size: 13px;
    color: var(--green);
  }

  .nn-success-formats {
    display: flex;
    gap: 7px;
    flex-wrap: wrap;
  }

  .nn-success-format-btn {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(45,217,164,0.2);
    border-radius: 8px;
    padding: 6px 14px;
    font-size: 11px;
    font-weight: 700;
    color: var(--green);
    text-decoration: none;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    transition: background 0.15s;
  }

  .nn-success-format-btn:hover {
    background: var(--green-soft) !important;
  }

  .nn-success-reset {
    margin-top: 12px;
    background: none;
    border: none;
    font-size: 11px;
    color: var(--text-secondary);
    cursor: pointer;
    padding: 0;
  }

  @media (max-width: 900px) {
    .nn-page {
      grid-template-columns: 1fr !important;
      padding-top: 70px;
    }
    .nn-left {
      padding: 3rem 2rem 2rem 2rem !important;
      border-right: none !important;
      border-bottom: 1px solid var(--border) !important;
    }
    .nn-right {
      padding: 3rem 2rem !important;
    }
  }
`;

const features = [
  {
    color: "fi-blue",
    title: "Rule-based cleaning model",
    desc: "Deterministic, explainable, and easy to extend — ideal for messy production data.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
      </svg>
    ),
  },
  {
    color: "fi-green",
    title: "Header normalization",
    desc: "Whitespace, casing, and symbols get normalized into stable, consistent column names.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M4 7V4h16v3" /><path d="M9 20h6" /><path d="M12 4v16" />
      </svg>
    ),
  },
  {
    color: "fi-amber",
    title: "Row hygiene",
    desc: "Empty rows, duplicate rows, and noisy cell values are removed automatically.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="3 6 5 6 21 6" /><path d="M19 6l-1 14H6L5 6" />
        <path d="M10 11v6" /><path d="M14 11v6" />
      </svg>
    ),
  },
];

const badges = [
  { label: "Model type", value: "Deterministic" },
  { label: "Cleaning scope", value: "Headers + rows" },
  { label: "Output", value: "Normalized CSV" },
];

const UploadIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
    <polyline points="17 8 12 3 7 8" />
    <line x1="12" y1="3" x2="12" y2="15" />
  </svg>
);

export default function NeatNodeUploadPage({ theme = "light" }) {
  const [file, setFile] = useState(null);
  const [prompt, setPrompt] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const [status, setStatus] = useState("idle");
  const [flashMsg, setFlashMsg] = useState(null);
  const fileInputRef = useRef();

  const showFlash = (type, text) => {
    setFlashMsg({ type, text });
    setTimeout(() => setFlashMsg(null), 4500);
  };

  const handleFile = useCallback((f) => {
    if (!f) return;
    if (!f.name.toLowerCase().endsWith(".csv")) {
      showFlash("error", "Only .csv files are supported.");
      return;
    }
    setFile(f);
  }, []);

  const onDrop = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
    handleFile(e.dataTransfer.files[0]);
  }, [handleFile]);

  const onDragOver = (e) => { e.preventDefault(); setDragOver(true); };
  const onDragLeave = () => setDragOver(false);

  const openPicker = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleSubmit = async () => {
    if (!file) {
      showFlash("error", "Please choose a CSV file before uploading.");
      return;
    }
    setStatus("loading");

    const fd = new FormData();
    fd.append("csv_file", file);
    if (prompt.trim()) {
      fd.append("cleaning_prompt", prompt.trim());
    } else {
      fd.append("cleaning_prompt", prompt); // the original code appended it even if empty
    }

    try {
      const res = await fetch(`${BASE_URL}/api/upload`, {
        method: "POST",
        body: fd
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error || 'Upload failed');
      }

      const data = await res.json();
      window.location.hash = `#result/${data.token}`;
      setStatus("idle");
    } catch (err) {
      showFlash("error", err.message || "Could not reach the server.");
      setStatus("idle");
    }
  };

  return (
    <>
      <style>{styles}</style>
      <div className="nn-page" data-theme={theme}>

        {/* ── FLASH ── */}
        {flashMsg && (
          <div className={`nn-flash ${flashMsg.type === "success" ? "nn-flash-success" : "nn-flash-error"}`}>
            <span>{flashMsg.type === "success" ? "✓" : "✕"}</span>
            {flashMsg.text}
          </div>
        )}

        {/* ── LEFT ── */}
        <div className="nn-left">
          <div className="nn-eyebrow">
            <span className="nn-eyebrow-dot" />
            CSV Cleaning Model
          </div>

          <h1 className="nn-h1">
            Upload messy CSV data,<br />
            get <em className="nn-h1-highlight">clean</em> data back.
          </h1>

          <p className="nn-desc">
            A rule-based engine that normalizes headers, trims values, removes empty rows,
            and drops duplicates — deterministic, explainable, and ready to extend.
          </p>

          <div className="nn-badges">
            {badges.map((b) => (
              <div className="nn-badge" key={b.label}>
                <span className="nn-badge-label">{b.label}</span>
                <span className="nn-badge-value">{b.value}</span>
              </div>
            ))}
          </div>

          <div className="nn-features">
            {features.map((f) => (
              <div className="nn-feature-card" key={f.title}>
                <div className="nn-feature-header">
                  <div className={`nn-feature-icon ${f.color}`}>{f.icon}</div>
                  <span className="nn-feature-title">{f.title}</span>
                </div>
                <p className="nn-feature-desc">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* ── RIGHT ── */}
        <div className="nn-right">

          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            style={{ display: "none" }}
            onChange={(e) => { if (e.target.files[0]) handleFile(e.target.files[0]); }}
          />

          <div
            className={`nn-upload-zone${dragOver ? " drag-over" : ""}`}
            role="button"
            tabIndex={0}
            aria-label="Upload CSV file"
            onClick={openPicker}
            onKeyDown={(e) => e.key === "Enter" && openPicker()}
            onDrop={onDrop}
            onDragOver={onDragOver}
            onDragLeave={onDragLeave}
          >
            <div className="nn-upload-icon"><UploadIcon /></div>

            {file ? (
              <span className="nn-file-name">{file.name}</span>
            ) : (
              <>
                <p className="nn-upload-primary">
                  Drop your CSV here or{" "}
                  <span style={{ color: "var(--accent)", textDecoration: "underline" }}>browse</span>
                </p>
                <span className="nn-upload-hint">.csv files only</span>
              </>
            )}
          </div>

          <hr className="nn-divider" />

          <div>
            <div className="nn-prompt-header">
              <span className="nn-prompt-label">Cleaning prompt</span>
              <span className="nn-prompt-optional">Optional</span>
            </div>
            <textarea
              className="nn-textarea"
              rows={4}
              placeholder={"e.g. clean the data, remove outliers,\\nand keep the most useful rows for analysis."}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
            />
            <p className="nn-prompt-hint">
              Leave blank to use the built-in flow.
            </p>
          </div>

          <button
            className="nn-cta"
            disabled={status === "loading"}
            onClick={handleSubmit}
          >
            {status === "loading" ? (
              <>
                <div style={{ width: 15, height: 15, border: "2px solid rgba(255,255,255,0.3)", borderTopColor: "white", borderRadius: "50%", animation: "spin 0.7s linear infinite" }} />
                Processing…
              </>
            ) : (
              <>
                <UploadIcon />
                Upload CSV
              </>
            )}
          </button>

          <div className="nn-status">
            <div className="nn-status-dot" />
            Engine ready
          </div>

        </div>
      </div>
    </>
  );
}