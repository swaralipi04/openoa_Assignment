import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { loadExampleData } from '../api';
import AnalysisCard from '../components/AnalysisCard';
import './Dashboard.css';

const ANALYSES = [
    {
        id: 'aep',
        title: 'Annual Energy Production',
        abbr: 'AEP',
        description: 'Monte Carlo simulation to estimate long-term annual energy production with uncertainty quantification.',
        icon: '⚡',
        color: 'teal',
        endpoint: 'aep',
    },
    {
        id: 'electrical-losses',
        title: 'Electrical Losses',
        abbr: 'EL',
        description: 'Quantify energy losses between turbine generators and the revenue meter at plant interconnection.',
        icon: '🔌',
        color: 'blue',
        endpoint: 'electrical-losses',
    },
    {
        id: 'turbine-energy',
        title: 'Turbine Gross Energy',
        abbr: 'TIE',
        description: 'Long-term gross energy production for each turbine using reanalysis-based wind resource estimation.',
        icon: '💨',
        color: 'purple',
        endpoint: 'turbine-energy',
    },
    {
        id: 'wake-losses',
        title: 'Wake Losses',
        abbr: 'WL',
        description: 'Assess energy losses from turbine wake interactions using directional wind analysis.',
        icon: '🌀',
        color: 'orange',
        endpoint: 'wake-losses',
    },
];

export default function Dashboard() {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);
    const [status, setStatus] = useState(null);

    const handleQuickStart = async () => {
        setLoading(true);
        setStatus(null);
        try {
            const res = await loadExampleData();
            const datasetId = res.data.dataset_id;
            setStatus({ type: 'success', message: `Dataset "${datasetId}" loaded! Redirecting...` });
            setTimeout(() => navigate('/analysis', { state: { datasetId } }), 1200);
        } catch (err) {
            setStatus({ type: 'error', message: err.response?.data?.detail || 'Failed to load example data' });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="dashboard">
            {/* Hero */}
            <section className="hero">
                <div className="hero-bg" />
                <div className="container hero-content">
                    <div className="hero-badge animate-fade-in">Open Source Wind Energy Analytics</div>
                    <h1 className="hero-title animate-fade-in">
                        Operational Analysis for<br />
                        <span className="gradient-text">Wind Energy Plants</span>
                    </h1>
                    <p className="hero-subtitle animate-fade-in">
                        Powered by NREL's OpenOA library — run Monte Carlo AEP, electrical losses,
                        turbine gross energy, and wake loss analyses on your wind farm data.
                    </p>
                    <div className="hero-actions animate-fade-in">
                        <button className="btn btn-primary btn-lg" onClick={handleQuickStart} disabled={loading}>
                            {loading ? <><span className="spinner" /> Loading...</> : '🚀 Quick Start with Example Data'}
                        </button>
                        <button className="btn btn-secondary btn-lg" onClick={() => navigate('/data')}>
                            📁 Upload Your Data
                        </button>
                    </div>
                    {status && (
                        <div className={`hero-status ${status.type}`}>
                            {status.type === 'success' ? '✅' : '❌'} {status.message}
                        </div>
                    )}
                </div>
            </section>

            {/* Stats */}
            <section className="container stats-section">
                <div className="grid-4">
                    <div className="glass-card stat-card animate-slide-up">
                        <div className="stat-value">4</div>
                        <div className="stat-label">Analysis Methods</div>
                    </div>
                    <div className="glass-card stat-card animate-slide-up" style={{ animationDelay: '0.1s' }}>
                        <div className="stat-value">UQ</div>
                        <div className="stat-label">Uncertainty Quantification</div>
                    </div>
                    <div className="glass-card stat-card animate-slide-up" style={{ animationDelay: '0.2s' }}>
                        <div className="stat-value">v3.2</div>
                        <div className="stat-label">OpenOA Version</div>
                    </div>
                    <div className="glass-card stat-card animate-slide-up" style={{ animationDelay: '0.3s' }}>
                        <div className="stat-value">API</div>
                        <div className="stat-label">RESTful Interface</div>
                    </div>
                </div>
            </section>

            {/* Analysis Cards */}
            <section className="container analyses-section">
                <h2 className="section-title">Available Analyses</h2>
                <p className="section-subtitle">Select an analysis to learn more or navigate to the Analysis page to run it.</p>
                <div className="grid-4" style={{ marginTop: '1.5rem' }}>
                    {ANALYSES.map((a, i) => (
                        <AnalysisCard key={a.id} analysis={a} delay={i * 0.1} onClick={() => navigate('/analysis', { state: { method: a.endpoint } })} />
                    ))}
                </div>
            </section>
        </div>
    );
}

export { ANALYSES };
