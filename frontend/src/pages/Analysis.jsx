import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { loadExampleData, runAnalysis } from '../api';
import ResultsPanel from '../components/ResultsPanel';
import { ANALYSES } from './Dashboard';
import './Analysis.css';

const METHOD_PARAMS = {
    aep: [
        { name: 'num_sim', label: 'Monte Carlo Simulations', type: 'number', default: 10, min: 1, max: 20000 },
        { name: 'time_resolution', label: 'Time Resolution', type: 'select', default: 'MS', options: ['MS', 'ME', 'W', 'D'] },
        { name: 'reg_model', label: 'Regression Model', type: 'select', default: 'lin', options: ['lin', 'gbm', 'etr'] },
    ],
    'electrical-losses': [
        { name: 'num_sim', label: 'Monte Carlo Simulations', type: 'number', default: 10, min: 1, max: 20000 },
        { name: 'uncertainty_meter', label: 'Meter Uncertainty', type: 'number', default: 0.005, step: 0.001 },
        { name: 'uncertainty_scada', label: 'SCADA Uncertainty', type: 'number', default: 0.005, step: 0.001 },
    ],
    'turbine-energy': [
        { name: 'num_sim', label: 'Monte Carlo Simulations', type: 'number', default: 10, min: 1, max: 20000 },
        { name: 'uncertainty_scada', label: 'SCADA Uncertainty', type: 'number', default: 0.005, step: 0.001 },
    ],
    'wake-losses': [
        { name: 'num_sim', label: 'Monte Carlo Simulations', type: 'number', default: 10, min: 1, max: 100 },
        { name: 'wd_bin_width', label: 'Wind Direction Bin Width (°)', type: 'number', default: 5.0, min: 1, max: 30 },
    ],
};

export default function Analysis() {
    const location = useLocation();
    const [datasetId, setDatasetId] = useState(location.state?.datasetId || '');
    const [method, setMethod] = useState(location.state?.method || 'aep');
    const [params, setParams] = useState({});
    const [loading, setLoading] = useState(false);
    const [loadingData, setLoadingData] = useState(false);
    const [results, setResults] = useState(null);
    const [error, setError] = useState(null);
    const [elapsed, setElapsed] = useState(0);

    // Reset params when method changes
    useEffect(() => {
        const defaults = {};
        (METHOD_PARAMS[method] || []).forEach(p => {
            defaults[p.name] = p.default;
        });
        setParams(defaults);
        setResults(null);
        setError(null);
    }, [method]);

    // Timer during analysis
    useEffect(() => {
        let interval;
        if (loading) {
            setElapsed(0);
            interval = setInterval(() => setElapsed(prev => prev + 1), 1000);
        }
        return () => clearInterval(interval);
    }, [loading]);

    const handleLoadExample = async () => {
        setLoadingData(true);
        setError(null);
        try {
            const res = await loadExampleData();
            setDatasetId(res.data.dataset_id);
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to load example data');
        } finally {
            setLoadingData(false);
        }
    };

    const handleRun = async () => {
        if (!datasetId.trim()) {
            setError('Please load a dataset first');
            return;
        }

        setLoading(true);
        setResults(null);
        setError(null);

        try {
            const requestBody = { dataset_id: datasetId, ...params };
            const res = await runAnalysis(method, requestBody);
            setResults(res.data);
        } catch (err) {
            const detail = err.response?.data?.detail;
            setError(typeof detail === 'string' ? detail : JSON.stringify(detail) || 'Analysis failed');
        } finally {
            setLoading(false);
        }
    };

    const handleParamChange = (name, value, type) => {
        setParams(prev => ({
            ...prev,
            [name]: type === 'number' ? parseFloat(value) || 0 : value,
        }));
    };

    const currentAnalysis = ANALYSES.find(a => a.endpoint === method);
    const currentParams = METHOD_PARAMS[method] || [];

    return (
        <div className="analysis-page container">
            <div className="ap-header">
                <h1>Run Analysis</h1>
                <p>Configure parameters and run OpenOA analyses on your loaded dataset.</p>
            </div>

            <div className="ap-layout">
                {/* Sidebar */}
                <aside className="ap-sidebar">
                    {/* Dataset */}
                    <div className="glass-card ap-config-section">
                        <h4>Dataset</h4>
                        <div className="ap-dataset-input">
                            <input
                                className="input"
                                type="text"
                                placeholder="Dataset ID (e.g. example-2dbb)"
                                value={datasetId}
                                onChange={e => setDatasetId(e.target.value)}
                            />
                            <button className="btn btn-secondary btn-sm" onClick={handleLoadExample} disabled={loadingData}>
                                {loadingData ? <span className="spinner" /> : '⚡'} Load Example
                            </button>
                        </div>
                        {datasetId && <div className="badge badge-success" style={{ marginTop: '0.5rem' }}>● {datasetId}</div>}
                    </div>

                    {/* Method Selector */}
                    <div className="glass-card ap-config-section">
                        <h4>Analysis Method</h4>
                        <div className="ap-method-list">
                            {ANALYSES.map(a => (
                                <button
                                    key={a.endpoint}
                                    className={`ap-method-btn ${method === a.endpoint ? 'active' : ''}`}
                                    onClick={() => setMethod(a.endpoint)}
                                >
                                    <span className="ap-method-icon">{a.icon}</span>
                                    <span className="ap-method-name">{a.abbr}</span>
                                </button>
                            ))}
                        </div>
                        {currentAnalysis && (
                            <p className="ap-method-desc">{currentAnalysis.description}</p>
                        )}
                    </div>

                    {/* Parameters */}
                    <div className="glass-card ap-config-section">
                        <h4>Parameters</h4>
                        <div className="ap-params">
                            {currentParams.map(p => (
                                <div key={p.name} className="ap-param">
                                    <label>{p.label}</label>
                                    {p.type === 'select' ? (
                                        <select
                                            className="select"
                                            value={params[p.name] ?? p.default}
                                            onChange={e => handleParamChange(p.name, e.target.value, 'text')}
                                        >
                                            {p.options.map(opt => (
                                                <option key={opt} value={opt}>{opt}</option>
                                            ))}
                                        </select>
                                    ) : (
                                        <input
                                            className="input"
                                            type={p.type}
                                            value={params[p.name] ?? p.default}
                                            min={p.min}
                                            max={p.max}
                                            step={p.step}
                                            onChange={e => handleParamChange(p.name, e.target.value, p.type)}
                                        />
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Run Button */}
                    <button
                        className="btn btn-primary btn-lg ap-run-btn"
                        onClick={handleRun}
                        disabled={loading || !datasetId.trim()}
                    >
                        {loading ? (
                            <>
                                <span className="spinner" />
                                Running... ({elapsed}s)
                            </>
                        ) : (
                            <>🚀 Run {currentAnalysis?.abbr || 'Analysis'}</>
                        )}
                    </button>
                </aside>

                {/* Results Area */}
                <div className="ap-results">
                    {error && (
                        <div className="dm-status error animate-fade-in">
                            ❌ {error}
                        </div>
                    )}

                    {loading && (
                        <div className="ap-loading glass-card animate-fade-in">
                            <div className="spinner spinner-lg" />
                            <h3>Running {currentAnalysis?.title}...</h3>
                            <p>This may take 30–60 seconds for large datasets.</p>
                            <div className="ap-timer">{elapsed}s elapsed</div>
                        </div>
                    )}

                    {!loading && !results && !error && (
                        <div className="ap-empty glass-card">
                            <div className="ap-empty-icon">📊</div>
                            <h3>No Results Yet</h3>
                            <p>Select an analysis method, configure parameters, and click Run to see results here.</p>
                        </div>
                    )}

                    {results && <ResultsPanel method={method} results={results} />}
                </div>
            </div>
        </div>
    );
}
