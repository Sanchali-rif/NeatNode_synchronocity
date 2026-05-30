import { useState, useEffect, useRef, useCallback } from 'react';
import BASE_URL from './api';
import './Result.css';

/** Forward vertical wheel to chat history when hovering tables that only scroll horizontally */
function ChatTableScroll({ children }) {
  const ref = useRef(null);

  const onWheel = useCallback((e) => {
    if (Math.abs(e.deltaY) <= Math.abs(e.deltaX)) return;

    const el = ref.current;
    const chat = el?.closest('.rp-chat-history');
    if (!el || !chat) return;

    const canScrollY = el.scrollHeight > el.clientHeight + 1;
    if (canScrollY) {
      const atTop = el.scrollTop <= 0;
      const atBottom = el.scrollTop + el.clientHeight >= el.scrollHeight - 1;
      if ((e.deltaY < 0 && !atTop) || (e.deltaY > 0 && !atBottom)) return;
    }

    chat.scrollTop += e.deltaY;
    e.preventDefault();
  }, []);

  return (
    <div ref={ref} className="rp-table-scroll rp-table-scroll--in-chat" onWheel={onWheel}>
      {children}
    </div>
  );
}


export default function ResultPage({ token, theme }) {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [expired, setExpired] = useState(false);
  const [question, setQuestion] = useState('');
  const [asking, setAsking] = useState(false);
  const [assistantResponse, setAssistantResponse] = useState(null);
  const [chatHistory, setChatHistory] = useState([]);
  const [downloadFormat, setDownloadFormat] = useState('csv');

  useEffect(() => {
    const root = document.documentElement;
    let scrollTimer;
    const onScroll = () => {
      root.classList.add('rp-is-scrolling');
      clearTimeout(scrollTimer);
      scrollTimer = setTimeout(() => root.classList.remove('rp-is-scrolling'), 180);
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => {
      window.removeEventListener('scroll', onScroll);
      clearTimeout(scrollTimer);
      root.classList.remove('rp-is-scrolling');
    };
  }, []);

  useEffect(() => {
    async function fetchResult() {
      try {
        const res = await fetch(`${BASE_URL}/api/result/${token}`);
        if (res.status === 404) { setExpired(true); return; }
        if (!res.ok) throw new Error('Failed to fetch result');
        const data = await res.json();
        setResult(data);
        setChatHistory(data.chat_history || []);
      } catch {
        setExpired(true);
      } finally {
        setLoading(false);
      }
    }
    fetchResult();
  }, [token]);

  const handleAsk = async () => {
    if (!question.trim()) return;
    setAsking(true);
    const formData = new FormData();
    formData.append('data_question', question);
    try {
      const res = await fetch(`${BASE_URL}/api/ask/${token}`, { method: 'POST', body: formData });
      if (!res.ok) throw new Error('Assistant error');
      const data = await res.json();
      setAssistantResponse(data.assistant);
      setChatHistory(data.chat_history);
      setQuestion('');
    } catch {
      // silently fail — could show error
    } finally {
      setAsking(false);
    }
  };

  const handleCardMouseMove = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    e.currentTarget.style.setProperty('--mouse-x', `${x}px`);
    e.currentTarget.style.setProperty('--mouse-y', `${y}px`);

    const centerX = rect.width / 2;
    const centerY = rect.height / 2;
    const percentX = (x - centerX) / centerX;
    const percentY = (y - centerY) / centerY;

    const maxTilt = 4;
    const tiltX = -percentY * maxTilt;
    const tiltY = percentX * maxTilt;

    e.currentTarget.style.transform = `perspective(1000px) rotateX(${tiltX}deg) rotateY(${tiltY}deg) translateY(-4px)`;
  };

  const handleCardMouseLeave = (e) => {
    e.currentTarget.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) translateY(0px)';
  };

  const downloadUrl = `${BASE_URL}/api/download-cleaned/${token}?format=${downloadFormat}`;

  if (loading) {
    return (
      <div className="rp-page" data-theme={theme}>
        <div className="rp-loading">
          <div className="rp-spinner" />
          <div className="rp-loading-text">Loading your cleaned dataset...</div>
        </div>
      </div>
    );
  }

  if (expired) {
    return (
      <div className="rp-page" data-theme={theme}>
        <div className="rp-expired">
          <div style={{ fontSize: 48 }}>⏱</div>
          <h2>Session expired</h2>
          <p>Your cleaned dataset is no longer in memory.<br />Please upload your CSV again to continue.</p>
          <a className="rp-back-btn" href="#upload">← Back to Upload</a>
        </div>
      </div>
    );
  }

  const rowsRemoved = result.raw_row_count - result.cleaned_row_count;

  return (
    <div className="rp-page" data-theme={theme}>
      <div className="rp-container">

      {/* ── HERO ── */}
      <div className="rp-hero">
        <div className="rp-hero-left">
          <div className="rp-eyebrow">
            <span className="rp-eyebrow-dot" />
            Cleaned successfully
          </div>
          <h1 className="rp-filename">{result.filename}</h1>
          <p className="rp-subtitle">
            Processed by NeatNode · {result.cleaned_row_count.toLocaleString()} rows ready for use
          </p>
        </div>
        <div className="rp-hero-actions">
          <a className="rp-back-btn" href="#upload" style={{ background: 'var(--bg-pill)', color: 'var(--text-secondary)', border: '1px solid var(--border-strong)', boxShadow: 'none' }}>
            ← New Upload
          </a>
          <select className="rp-select" value={downloadFormat} onChange={e => setDownloadFormat(e.target.value)}>
            <option value="csv">CSV</option>
            <option value="json">JSON</option>
            <option value="sql">SQL</option>
            <option value="python">Python</option>
          </select>
          <a href={downloadUrl} target="_blank" rel="noreferrer" className="rp-download-btn">
            ↓ Download
          </a>
        </div>
      </div>

      {/* ── STAT STRIP ── */}
      <div className="rp-stats">
        <div className="rp-stat">
          <span className="rp-stat-label">Rows cleaned</span>
          <span className="rp-stat-value green">{result.cleaned_row_count.toLocaleString()}</span>
          <span className="rp-stat-sub">from {result.raw_row_count.toLocaleString()} raw</span>
        </div>
        <div className="rp-stat">
          <span className="rp-stat-label">Rows removed</span>
          <span className={`rp-stat-value ${rowsRemoved > 0 ? 'amber' : 'green'}`}>{rowsRemoved.toLocaleString()}</span>
          <span className="rp-stat-sub">{result.removed_empty_rows} empty · {result.removed_duplicate_rows} dupe · {result.removed_outlier_rows} outlier</span>
        </div>
        <div className="rp-stat">
          <span className="rp-stat-label">Columns</span>
          <span className="rp-stat-value accent">{result.cleaned_column_count}</span>
          <span className="rp-stat-sub">from {result.raw_column_count} original</span>
        </div>
        <div className="rp-stat">
          <span className="rp-stat-label">Imputations</span>
          <span className="rp-stat-value">{(result.imputation_summary || []).length}</span>
          <span className="rp-stat-sub">columns with filled values</span>
        </div>
        {result.prompt_used && (
          <div className="rp-stat">
            <span className="rp-stat-label">Prompt used</span>
            <span className="rp-stat-value" style={{ fontSize: 13, fontWeight: 500, lineHeight: 1.4 }}>{result.prompt_used.slice(0, 60)}{result.prompt_used.length > 60 ? '…' : ''}</span>
          </div>
        )}
      </div>

      {/* ── BODY ── */}
      <div className="rp-body">
        {/* MAIN */}
        <div className="rp-main">

          {/* Data Visualisation */}
          {result.visualization_data && (
            <div>
              <div className="rp-section-title" style={{ marginBottom: '4px' }}>Data Visualisation</div>
              <p style={{ fontSize: '13px', color: 'var(--text-muted)', margin: '0 0 20px 0' }}>Before and after changes mapped with glassmorphic charts.</p>
              <div className="rp-viz-grid">

                {/* ── Card 1: Rows retained donut ── */}
                <div className="rp-viz-card" onMouseMove={handleCardMouseMove} onMouseLeave={handleCardMouseLeave}>
                  <div className="rp-viz-header">
                    <div className="rp-viz-title">Rows retained</div>
                    <div className="rp-viz-badge rp-viz-badge-green">{result.visualization_data.row_retained_percent}%</div>
                  </div>
                  <div className="rp-donut-wrapper">
                    <div
                      className="rp-donut-chart"
                    >
                      <div
                        className="rp-donut-chart-inner-ring"
                        style={{
                          background: `conic-gradient(
                            var(--accent) ${result.visualization_data.row_retained_percent * 3.6}deg,
                            rgba(255,255,255,0.06) ${result.visualization_data.row_retained_percent * 3.6}deg
                          )`,
                          borderRadius: '50%',
                        }}
                      />
                      <div className="rp-donut-inner">
                        <div className="rp-donut-label">Retained</div>
                        <div className="rp-donut-value">{result.visualization_data.row_retained_percent}%</div>
                      </div>
                    </div>
                    <div className="rp-donut-meta">
                      <div className="rp-donut-meta-row">
                        <div className="rp-donut-dot" style={{ background: 'var(--accent)', boxShadow: '0 0 6px var(--accent)' }} />
                        <span className="rp-donut-meta-label">Kept</span>
                        <span className="rp-donut-meta-val">{result.cleaned_row_count.toLocaleString()}</span>
                      </div>
                      <div className="rp-donut-meta-row">
                        <div className="rp-donut-dot" style={{ background: 'rgba(255,255,255,0.12)' }} />
                        <span className="rp-donut-meta-label">Removed</span>
                        <span className="rp-donut-meta-val">{(result.raw_row_count - result.cleaned_row_count).toLocaleString()}</span>
                      </div>
                      <div className="rp-donut-meta-row">
                        <div className="rp-donut-dot" style={{ background: 'var(--text-muted)' }} />
                        <span className="rp-donut-meta-label">Total</span>
                        <span className="rp-donut-meta-val">{result.raw_row_count.toLocaleString()}</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* ── Card 2: Columns before/after LED bar ── */}
                <div className="rp-viz-card" onMouseMove={handleCardMouseMove} onMouseLeave={handleCardMouseLeave}>
                  <div className="rp-viz-header">
                    <div className="rp-viz-title">Columns before &amp; after</div>
                    <div className="rp-viz-badge rp-viz-badge-accent">{result.cleaned_column_count}/{result.raw_column_count}</div>
                  </div>
                  <div className="rp-mini-bars">
                    <div className="rp-mini-bar-wrap">
                      <div className="rp-mini-bar-num">{result.raw_column_count}</div>
                      <div className="rp-mini-bar-track">
                        <div
                          className="rp-mini-bar-fill"
                          style={{
                            height: '100%',
                            background: 'rgba(255,255,255,0.25)',
                            color: 'rgba(255,255,255,0.25)' /* for drop-shadow */
                          }}
                        />
                      </div>
                      <div className="rp-mini-bar-lbl">Before</div>
                    </div>
                    <div className="rp-mini-bar-wrap">
                      <div className="rp-mini-bar-num" style={{ color: 'var(--green)' }}>{result.cleaned_column_count}</div>
                      <div className="rp-mini-bar-track">
                        <div
                          className="rp-mini-bar-fill"
                          style={{
                            height: `${Math.max(result.visualization_data.column_retained_percent, 10)}%`,
                            background: 'var(--green)',
                            color: 'var(--green)' /* for drop-shadow */
                          }}
                        />
                      </div>
                      <div className="rp-mini-bar-lbl">After</div>
                    </div>
                  </div>
                </div>

                {/* ── Card 3: Cleanup actions ── */}
                <div className="rp-viz-card rp-viz-card-full" onMouseMove={handleCardMouseMove} onMouseLeave={handleCardMouseLeave}>
                  <div className="rp-viz-header">
                    <div className="rp-viz-title">Cleanup actions</div>
                    <div className="rp-viz-badge rp-viz-badge-amber">{rowsRemoved} rows removed</div>
                  </div>
                  <div className="rp-neon-bar-group">
                    {result.visualization_data.action_cards.map((card, i) => {
                      const colors = [
                        'var(--accent)',
                        '#a855f7',
                        'var(--amber)',
                      ];
                      return (
                        <div className="rp-neon-bar-item" key={i}>
                          <div className="rp-neon-bar-top">
                            <span className="rp-neon-bar-label">{card.label}</span>
                            <span className="rp-neon-bar-val">{card.value}</span>
                          </div>
                          <div className="rp-neon-bar-track">
                            {card.value > 0 ? (
                              <div
                                className="rp-neon-bar-fill"
                                style={{
                                  width: `${Math.max(card.width, 3)}%`,
                                  background: colors[i],
                                  color: colors[i],
                                }}
                              />
                            ) : null}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* ── Card 4: Imputation fills ── */}
                {result.visualization_data.imputation_cards && result.visualization_data.imputation_cards.length > 0 && (
                  <div className="rp-viz-card rp-viz-card-full" onMouseMove={handleCardMouseMove} onMouseLeave={handleCardMouseLeave}>
                    <div className="rp-viz-header">
                      <div className="rp-viz-title">Missing-value fills</div>
                      <div className="rp-viz-badge rp-viz-badge-green">{result.visualization_data.imputation_cards.length} columns</div>
                    </div>
                    <div className="rp-neon-bar-group">
                      {result.visualization_data.imputation_cards.map((card, i) => (
                        <div className="rp-neon-bar-item" key={i}>
                          <div className="rp-neon-bar-top">
                            <span className="rp-neon-bar-label">{card.label}</span>
                            <span className="rp-neon-bar-val">{card.value}</span>
                          </div>
                          <div className="rp-neon-bar-track">
                            <div
                              className="rp-neon-bar-fill"
                              style={{
                                width: `${Math.max(card.width, 3)}%`,
                                background: 'var(--green)',
                                color: 'var(--green)',
                              }}
                            />
                          </div>
                          <div className="rp-neon-bar-desc">mode → &ldquo;{card.fill_value}&rdquo;</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

              </div>
            </div>
          )}

          {/* AI Summary */}
          {result.ai_summary && (
            <div>
              <div className="rp-section-title">AI Summary</div>
              <div className="rp-ai-card">{result.ai_summary}</div>
            </div>
          )}

          {/* Notes */}
          {result.summary_notes && result.summary_notes.length > 0 && (
            <div>
              <div className="rp-section-title">Cleaning Notes</div>
              {result.summary_notes.map((note, i) => (
                <div className="rp-note" key={i}>
                  <span className="rp-note-icon">⚑</span>
                  {note}
                </div>
              ))}
            </div>
          )}

          {/* Imputation */}
          {result.imputation_summary && result.imputation_summary.length > 0 && (
            <div>
              <div className="rp-section-title">Imputation Summary</div>
              <div className="rp-imp-grid">
                {result.imputation_summary.map((imp, i) => (
                  <div className="rp-imp-row" key={i}>
                    <span className="rp-imp-col">{imp.column}</span>
                    <span className="rp-imp-count">{imp.filled_count} filled</span>
                    <span className="rp-imp-strategy">{imp.strategy}</span>
                    <span className="rp-imp-fill">→ {imp.fill_value}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Cleaned Headers */}
          <div>
            <div className="rp-section-title">Column Headers ({result.cleaned_headers.length})</div>
            <div className="rp-headers">
              {result.cleaned_headers.map((h, i) => (
                <span className="rp-header-chip" key={i}>{h}</span>
              ))}
            </div>
          </div>

          {/* Preview Table */}
          {result.preview_rows && result.preview_rows.length > 0 && (
            <div>
              <div className="rp-section-title">Data Preview</div>
              <div className="rp-table-wrapper">
                <div className="rp-table-scroll" data-lenis-prevent-horizontal>
                  <table className="rp-table">
                    <thead>
                      <tr>
                        {result.cleaned_headers.map((h, i) => <th key={i}>{h}</th>)}
                      </tr>
                    </thead>
                    <tbody>
                      {result.preview_rows.map((row, i) => (
                        <tr key={i}>
                          {row.map((cell, j) => <td key={j}>{cell}</td>)}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="rp-table-footer">
                  Showing {result.preview_rows.length} of {result.cleaned_row_count.toLocaleString()} rows
                </div>
              </div>
            </div>
          )}
        </div>

        {/* SIDEBAR: Ask Assistant */}
        <div className="rp-sidebar">
          <div className="rp-chat-card">
            <div className="rp-chat-header">
              <div className="rp-chat-header-title">
                <span className="rp-chat-header-dot" />
                Ask the dataset
              </div>
              <span style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 500 }}>AI Core</span>
            </div>

            <div className="rp-chat-history" data-lenis-prevent>
              {chatHistory.length > 0 && (
                <>
                  {chatHistory.map((chat, i) => (
                    <div key={i} className={`rp-bubble ${chat.role === 'user' ? 'rp-bubble-user' : 'rp-bubble-assistant'}`}>
                      <div className="rp-bubble-role">{chat.role}</div>
                      {chat.content}
                    </div>
                  ))}
                </>
              )}

              {assistantResponse && (
                <div className="rp-assistant-response">
                  <h4>{assistantResponse.title}</h4>
                  <p>{assistantResponse.summary}</p>

                  {assistantResponse.detail_lines && assistantResponse.detail_lines.length > 0 && (
                    <ul>
                      {assistantResponse.detail_lines.map((line, i) => <li key={i}>{line}</li>)}
                    </ul>
                  )}

                  {assistantResponse.sql_like && (
                    <pre>{assistantResponse.sql_like}</pre>
                  )}

                  {assistantResponse.table_headers && assistantResponse.table_rows && (
                    <div className="rp-table-wrapper rp-table-wrapper--in-chat" style={{ marginTop: 12 }}>
                      <ChatTableScroll>
                        <table className="rp-table">
                          <thead>
                            <tr>{assistantResponse.table_headers.map((h, i) => <th key={i}>{h}</th>)}</tr>
                          </thead>
                          <tbody>
                            {assistantResponse.table_rows.map((row, i) => (
                              <tr key={i}>{row.map((cell, j) => <td key={j}>{cell}</td>)}</tr>
                            ))}
                          </tbody>
                        </table>
                      </ChatTableScroll>
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="rp-chat-input-bar">
              <textarea
                className="rp-chat-input"
                style={{ flex: 1, height: '36px', resize: 'none', background: 'transparent', border: 'none', color: 'var(--text-primary)', outline: 'none', fontFamily: 'inherit', fontSize: '13px', margin: 0 }}
                value={question}
                onChange={e => setQuestion(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleAsk(); } }}
                placeholder="e.g. What is the average salary?"
              />
              <button 
                className="rp-chat-send-btn" 
                onClick={handleAsk} 
                disabled={asking || !question.trim()}
              >
                {asking ? (
                  <div style={{ width: 14, height: 14, border: '2px solid rgba(255,255,255,0.3)', borderTopColor: 'white', borderRadius: '50%', animation: 'spin 0.7s linear infinite' }} />
                ) : (
                  <SendIcon />
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
    </div>
  );
}

// Simple Send Icon helper component
const SendIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <line x1="22" y1="2" x2="11" y2="13"></line>
    <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
  </svg>
);
