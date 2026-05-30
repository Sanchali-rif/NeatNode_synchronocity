import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, Activity, Lightbulb, PlayCircle, Download } from 'lucide-react';

const steps = [
  {
    step: 'Step 1',
    title: 'Upload Dataset',
    content: 'Securely upload CSV, JSON, Parquet — or connect directly to your database.',
    icon: <Upload size={24} />,
    code: `# Upload your CSV to NeatNode\nimport requests\n\nresponse = requests.post(\n    "https://api.neatnode.app/upload",\n    files={"file": open("sales_2023.csv", "rb")}\n)\n\nprint(response.json())\n# → {"rows": 6000, "columns": 17, "status": "ready"}`
  },
  {
    step: 'Step 2',
    title: 'Auto Profiling',
    content: 'AI scans every column — detecting dtypes, nulls, outliers, and mixed-type anomalies.',
    icon: <Activity size={24} />,
    code: `# NeatNode · Auto Profiling\n\nfor col in df.columns:\n    print(f"{col}: {df[col].dtype} | nulls: {df[col].isnull().sum()}")\n\n# → age: float64 | nulls: 1529\n# → gender: object | nulls: 478\n# → blood_group: object | nulls: 1023`
  },
  {
    step: 'Step 3',
    title: 'Strategy Selection',
    content: 'A tailored cleaning strategy is proposed. Review and approve each action before anything runs.',
    icon: <Lightbulb size={24} />,
    code: `# NeatNode · Strategy Selection\n\nstrategy = {\n    "age": "fill with median",\n    "gender": "fill with mode",\n    "blood_group": "fill with mode"\n}\n\n# Review and approve before anything runs\nprint("Proposed strategy:", strategy)\n# → Approve? (yes/no): yes`
  },
  {
    step: 'Step 4',
    title: 'Pipeline Execution',
    content: 'Approve and execute. Transformations run in parallel, tracked in a full decision log.',
    icon: <PlayCircle size={24} />,
    code: `# NeatNode · Pipeline Execution\n\nfor col, strategy in approved_strategy.items():\n    if strategy == "fill with median":\n        df[col].fillna(df[col].median(), inplace=True)\n    elif strategy == "fill with mode":\n        df[col].fillna(df[col].mode()[0], inplace=True)\n\nprint(f"Pipeline complete: {len(df):,} rows cleaned")\n# → Pipeline complete: 5,566 rows cleaned`
  },
  {
    step: 'Step 5',
    title: 'Export & Reuse',
    content: 'Export your clean data and the reusable Python pipeline — CI/CD ready.',
    icon: <Download size={24} />,
    code: `# NeatNode · Export & Reuse\n\n# Export clean data\ndf.to_csv("sales_2023_clean.csv", index=False)\n\n# Export reusable pipeline\nwith open("pipeline.py", "w") as f:\n    f.write(pipeline_code)\n\nprint("Export complete — CI/CD ready")\n# → sales_2023_clean.csv saved\n# → pipeline.py saved`
  },
];

export default function PipelineSection() {
  const [currentFeature, setCurrentFeature] = useState(0);

  return (
    <section id="pipeline" style={{ background: 'var(--bg-surface)', position: 'relative', padding: '6rem 2rem' }}>
      <div className="container" style={{ maxWidth: '1200px', margin: '0 auto' }}>

        {/* Header */}
        <div style={{ position: 'relative', textAlign: 'center', marginBottom: '4rem' }}>
          <div style={{ position: 'relative', zIndex: 10 }}>
            <div style={{ marginBottom: '1.25rem' }}>
              <span className="pill-badge">How It Works</span>
            </div>
            <h2 style={{ fontSize: 'clamp(2rem, 4vw, 2.75rem)', fontWeight: 800, color: 'var(--text-heading)' }}>
              Five Steps to Clean Data
            </h2>
            <p style={{ marginTop: '1rem', color: 'var(--text-body)', fontSize: '1.1rem', maxWidth: '600px', margin: '1rem auto 0' }}>
              Neatnode helps you upload, profile, clean, and export your dataset faster than ever before.
            </p>
          </div>

          <div style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            width: '300px',
            height: '200px',
            background: 'var(--accent-primary-gradient)',
            filter: 'blur(120px)',
            opacity: 0.15,
            pointerEvents: 'none',
            zIndex: 0
          }}></div>
        </div>

        <hr style={{ background: 'var(--border-solid)', height: '1px', border: 'none', width: '50%', margin: '0 auto 4rem' }} />

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: '4rem',
          alignItems: 'center'
        }}>
          {/* Left: Steps List */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            {steps.map((feature, index) => {
              const isActive = index === currentFeature;
              return (
                <motion.div
                  key={index}
                  onMouseEnter={() => setCurrentFeature(index)}
                  onClick={() => setCurrentFeature(index)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '1.5rem',
                    cursor: 'pointer'
                  }}
                  initial={{ opacity: 0.3, x: -20 }}
                  animate={{
                    opacity: isActive ? 1 : 0.3,
                    x: 0,
                    scale: isActive ? 1.05 : 1,
                  }}
                  transition={{ duration: 0.5 }}
                >
                  <motion.div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      width: '56px',
                      height: '56px',
                      borderRadius: '50%',
                      border: isActive ? '2px solid var(--accent-primary)' : '2px solid var(--border-solid)',
                      background: isActive ? 'var(--bg-surface-alt)' : 'var(--bg-surface)',
                      color: isActive ? 'var(--accent-primary)' : 'var(--text-muted)',
                      boxShadow: isActive ? '0 0 15px rgba(91, 73, 233, 0.3)' : 'none',
                      flexShrink: 0
                    }}
                  >
                    {feature.icon}
                  </motion.div>

                  <div style={{ flex: 1 }}>
                    <h3 style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-heading)', marginBottom: '0.25rem' }}>
                      {feature.title}
                    </h3>
                    <p style={{ color: 'var(--text-body)', fontSize: '0.95rem', lineHeight: 1.5, margin: 0 }}>
                      {feature.content}
                    </p>
                  </div>
                </motion.div>
              );
            })}
          </div>

          {/* Right: Code Terminal Viewer */}
          <div style={{
            position: 'relative',
            height: '420px',
            borderRadius: '16px',
            border: '1px solid var(--border-solid)',
            boxShadow: 'var(--shadow-card-hover)',
            overflow: 'hidden',
            background: 'var(--bg-surface)',
          }}>
            <AnimatePresence mode="wait">
              {steps.map((feature, index) =>
                index === currentFeature && (
                  <motion.div
                    key={index}
                    style={{
                      position: 'absolute',
                      inset: 0,
                      display: 'flex',
                      flexDirection: 'column',
                      background: '#1e1e2e'
                    }}
                    initial={{ y: 80, opacity: 0, rotateX: -15 }}
                    animate={{ y: 0, opacity: 1, rotateX: 0 }}
                    exit={{ y: -80, opacity: 0, rotateX: 15 }}
                    transition={{ duration: 0.5, ease: 'easeInOut' }}
                  >
                    {/* Window chrome */}
                    <div style={{
                      display: 'flex', alignItems: 'center', gap: '8px',
                      padding: '14px 18px', background: '#11111b',
                      borderBottom: '1px solid rgba(255,255,255,0.05)',
                    }}>
                      <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#ff5f57' }} />
                      <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#febc2e' }} />
                      <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#28c840' }} />
                      <div style={{ marginLeft: '8px', fontSize: '12px', color: '#6c7086', fontFamily: 'monospace' }}>
                        neatnode · {feature.title.toLowerCase().replace(' & ', '_').replace(' ', '_')}.py
                      </div>
                    </div>

                    {/* Code area */}
                    <div style={{ padding: '1.75rem', flex: 1, overflowY: 'auto' }}>
                      <pre style={{
                        margin: 0, fontFamily: '"Fira Code", "Cascadia Code", monospace',
                        fontSize: '13.5px', lineHeight: 1.7, color: '#cdd6f4',
                        whiteSpace: 'pre-wrap'
                      }}>
                        {feature.code.split('\n').map((line, li) => {
                          if (line.startsWith('#') || line.startsWith('# ')) {
                            return <div key={li} style={{ color: '#6c7086' }}>{line}</div>;
                          }
                          if (line.includes('import ') || line.includes('from ')) {
                            return <div key={li} style={{ color: '#cba6f7' }}>{line}</div>;
                          }
                          if (line.includes('.') && line.includes('(')) {
                            const parts = line.split('(');
                            return <div key={li}><span style={{ color: '#89b4fa' }}>{parts[0]}</span><span style={{ color: '#cdd6f4' }}>({parts.slice(1).join('(')}</span></div>;
                          }
                          if (line.startsWith('# ✓')) {
                            return <div key={li} style={{ color: '#a6e3a1' }}>{line}</div>;
                          }
                          return <div key={li}>{line}</div>;
                        })}
                      </pre>
                    </div>

                  </motion.div>
                )
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </section>
  );
}
