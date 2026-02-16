import './ResultsPanel.css';

export default function ResultsPanel({ method, results }) {
    if (!results) return null;

    return (
        <div className="results-panel animate-fade-in">
            <h3 className="rp-title">📊 Analysis Results</h3>

            {/* Key Metrics */}
            <div className="rp-metrics">
                {method === 'aep' && <AepMetrics data={results} />}
                {method === 'electrical-losses' && <ElMetrics data={results} />}
                {method === 'turbine-energy' && <TieMetrics data={results} />}
                {method === 'wake-losses' && <WakeMetrics data={results} />}
            </div>

            {/* Chart */}
            {results.plot_base64 && (
                <div className="rp-chart glass-card">
                    <h4>Visualization</h4>
                    <img
                        src={`data:image/png;base64,${results.plot_base64}`}
                        alt="Analysis chart"
                        className="rp-chart-img"
                    />
                </div>
            )}

            {/* Turbine Table */}
            {(results.turbine_results || results.turbine_wake_losses) && (
                <div className="rp-table-wrap glass-card">
                    <h4>Per-Turbine Results</h4>
                    <table className="rp-table">
                        <thead>
                            <tr>
                                <th>Turbine</th>
                                <th>{method === 'wake-losses' ? 'Wake Losses (%)' : 'Gross Energy (GWh)'}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {Object.entries(results.turbine_results || results.turbine_wake_losses || {}).map(([id, val]) => (
                                <tr key={id}>
                                    <td className="rp-turbine-id">{id}</td>
                                    <td className="rp-turbine-val">{typeof val === 'number' ? val.toFixed(4) : val}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}

function AepMetrics({ data }) {
    return (
        <div className="grid-4">
            <MetricCard label="AEP" value={`${data.aep_gwh?.toFixed(2) || '—'}`} unit="GWh" color="teal" />
            <MetricCard label="Uncertainty" value={`${data.aep_uncertainty_pct?.toFixed(1) || '—'}`} unit="%" color="blue" />
            <MetricCard label="Simulations" value={data.num_sim || '—'} color="purple" />
            <MetricCard label="Resolution" value={data.time_resolution || '—'} color="orange" />
        </div>
    );
}

function ElMetrics({ data }) {
    return (
        <div className="grid-4">
            <MetricCard label="Mean Losses" value={`${data.mean_losses_pct?.toFixed(2) || '—'}`} unit="%" color="teal" />
            <MetricCard label="Median Losses" value={`${data.median_losses_pct?.toFixed(2) || '—'}`} unit="%" color="blue" />
            <MetricCard label="Std Dev" value={`${data.std_losses_pct?.toFixed(2) || '—'}`} unit="%" color="purple" />
            <MetricCard label="Simulations" value={data.num_sim || '—'} color="orange" />
        </div>
    );
}

function TieMetrics({ data }) {
    return (
        <div className="grid-4">
            <MetricCard label="Plant Gross" value={`${data.tie_gwh?.toFixed(2) || '—'}`} unit="GWh" color="teal" />
            <MetricCard label="Uncertainty" value={`${data.tie_uncertainty_pct?.toFixed(1) || '—'}`} unit="%" color="blue" />
            <MetricCard label="Turbines" value={Object.keys(data.turbine_results || {}).length} color="purple" />
            <MetricCard label="Simulations" value={data.num_sim || '—'} color="orange" />
        </div>
    );
}

function WakeMetrics({ data }) {
    return (
        <div className="grid-4">
            <MetricCard label="Mean Wake Loss" value={`${data.mean_wake_losses_pct?.toFixed(2) || '—'}`} unit="%" color="teal" />
            <MetricCard label="Std Dev" value={`${data.std_wake_losses_pct?.toFixed(2) || '—'}`} unit="%" color="blue" />
            <MetricCard label="Turbines" value={Object.keys(data.turbine_wake_losses || {}).length} color="purple" />
            <MetricCard label="Simulations" value={data.num_sim || '—'} color="orange" />
        </div>
    );
}

function MetricCard({ label, value, unit, color = 'teal' }) {
    const colors = {
        teal: '#14b8a6',
        blue: '#3b82f6',
        purple: '#a855f7',
        orange: '#f97316',
    };

    return (
        <div className="glass-card stat-card">
            <div className="stat-value" style={{ color: colors[color] || colors.teal, background: 'none', WebkitTextFillColor: 'unset' }}>
                {value}{unit && <span className="stat-unit">{unit}</span>}
            </div>
            <div className="stat-label">{label}</div>
        </div>
    );
}
