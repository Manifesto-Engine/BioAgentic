import Layout from '@theme/Layout';

const FEATURES = [
  {
    icon: '🫀',
    title: 'Heartbeat',
    desc: 'Continuous pulse loop with watchdog recovery. 10-second lifecycle driving all organ phases.',
  },
  {
    icon: '🧠',
    title: 'Brain',
    desc: 'Rule-based reasoning engine. Optionally backed by LLM for deeper pattern analysis and autonomous decisions.',
  },
  {
    icon: '🛡️',
    title: 'Immune System',
    desc: 'Pipeline health tracking with automatic quarantine after consecutive failures. Self-healing by default.',
  },
  {
    icon: '🧠',
    title: 'Cortex',
    desc: 'Persistent memory with Ebbinghaus decay. Stores, recalls, and consolidates knowledge over time.',
  },
];

const TERMINAL_LINES = [
  { type: 'cmd', text: '$ uvicorn main:app --port 8000' },
  { type: 'dim', text: 'INFO     BioAgentic — birth sequence initiated' },
  { type: 'bright', text: 'INFO     🫀 Heartbeat started — pulse every 10s' },
  { type: 'bright', text: 'INFO     🧠 Brain online — local LLM inference connected (Ollama)' },
  { type: 'bright', text: 'INFO     🛡️ Immune system armed' },
  { type: 'bright', text: 'INFO     🧠 Cortex loaded — 0 memories' },
  { type: 'dim', text: 'INFO     Application startup complete.' },
  { type: 'cmd', text: '█' },
];

function FeatureCard({ icon, title, desc }) {
  return (
    <div className="feature-card">
      <span className="feature-card__icon">{icon}</span>
      <div className="feature-card__title">{title}</div>
      <div className="feature-card__desc">{desc}</div>
    </div>
  );
}

function TerminalPreview() {
  return (
    <div className="terminal-preview">
      <div className="terminal-preview__header">
        <span className="terminal-preview__dot terminal-preview__dot--red" />
        <span className="terminal-preview__dot terminal-preview__dot--yellow" />
        <span className="terminal-preview__dot terminal-preview__dot--green" />
      </div>
      <div className="terminal-preview__body">
        {TERMINAL_LINES.map((line, i) => (
          <div key={i} className={line.type}>{line.text}</div>
        ))}
      </div>
    </div>
  );
}

export default function Home() {
  return (
    <Layout
      title="BioAgentic — Cultivate Autonomous AI Agents"
      description="A living AI agent runtime. Four organs, one heartbeat. Clone it, run it, watch it breathe.">

      {/* ── Hero ──────────── */}
      <header className="hero--manifesto">
        <div className="container">
          <h1>BioAgentic</h1>
          <p>
            Cultivate autonomous, biologically-inspired AI agents.
            Four organs. One heartbeat. Clone it, run it, watch it breathe.
          </p>
          <a className="hero__cta" href="/docs/quickstart">
            Deploy in 5 Minutes →
          </a>
          <TerminalPreview />
        </div>
      </header>

      {/* ── Features ─────── */}
      <section className="features-section">
        <div className="features-grid">
          {FEATURES.map((f, i) => (
            <FeatureCard key={i} {...f} />
          ))}
        </div>
      </section>
    </Layout>
  );
}
