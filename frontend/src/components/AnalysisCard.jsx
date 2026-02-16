import './AnalysisCard.css';

const COLOR_MAP = {
    teal: { bg: 'rgba(20, 184, 166, 0.1)', border: 'rgba(20, 184, 166, 0.25)', text: '#14b8a6' },
    blue: { bg: 'rgba(59, 130, 246, 0.1)', border: 'rgba(59, 130, 246, 0.25)', text: '#3b82f6' },
    purple: { bg: 'rgba(168, 85, 247, 0.1)', border: 'rgba(168, 85, 247, 0.25)', text: '#a855f7' },
    orange: { bg: 'rgba(249, 115, 22, 0.1)', border: 'rgba(249, 115, 22, 0.25)', text: '#f97316' },
};

export default function AnalysisCard({ analysis, delay = 0, onClick }) {
    const colors = COLOR_MAP[analysis.color] || COLOR_MAP.teal;

    return (
        <div
            className="analysis-card glass-card animate-slide-up"
            style={{ animationDelay: `${delay}s`, '--card-accent': colors.text, '--card-bg': colors.bg, '--card-border': colors.border }}
            onClick={onClick}
            role="button"
            tabIndex={0}
        >
            <div className="ac-icon">{analysis.icon}</div>
            <div className="ac-abbr" style={{ background: colors.bg, color: colors.text, borderColor: colors.border }}>
                {analysis.abbr}
            </div>
            <h4 className="ac-title">{analysis.title}</h4>
            <p className="ac-desc">{analysis.description}</p>
            <div className="ac-action" style={{ color: colors.text }}>
                Run Analysis →
            </div>
        </div>
    );
}
