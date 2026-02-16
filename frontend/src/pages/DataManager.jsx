import { useState, useRef } from 'react';
import { loadExampleData, uploadData, deleteDataset } from '../api';
import DatasetInfo from '../components/DatasetInfo';
import './DataManager.css';

const UPLOAD_FIELDS = [
    { name: 'scada', label: 'SCADA Data', desc: 'Turbine operational data (power, wind speed, etc.)', required: true },
    { name: 'meter', label: 'Revenue Meter', desc: 'Plant-level energy production from revenue meter' },
    { name: 'curtail', label: 'Curtailment', desc: 'Curtailment and availability records' },
    { name: 'asset', label: 'Asset Table', desc: 'Turbine specifications (lat, lon, rated power, hub height)' },
    { name: 'reanalysis', label: 'Reanalysis', desc: 'ERA5/MERRA2 weather data for long-term correction' },
];

export default function DataManager() {
    const [datasets, setDatasets] = useState([]);
    const [loading, setLoading] = useState(false);
    const [loadingUpload, setLoadingUpload] = useState(false);
    const [status, setStatus] = useState(null);
    const [files, setFiles] = useState({});
    const fileRefs = useRef({});

    const handleLoadExample = async () => {
        setLoading(true);
        setStatus(null);
        try {
            const res = await loadExampleData();
            setDatasets(prev => [res.data, ...prev]);
            setStatus({ type: 'success', message: `Loaded example dataset: ${res.data.dataset_id}` });
        } catch (err) {
            setStatus({ type: 'error', message: err.response?.data?.detail || 'Failed to load example data' });
        } finally {
            setLoading(false);
        }
    };

    const handleFileChange = (fieldName, file) => {
        setFiles(prev => ({ ...prev, [fieldName]: file }));
    };

    const handleUpload = async () => {
        if (!files.scada) {
            setStatus({ type: 'error', message: 'SCADA data is required for upload' });
            return;
        }

        setLoadingUpload(true);
        setStatus(null);
        try {
            const formData = new FormData();
            Object.entries(files).forEach(([key, file]) => {
                if (file) formData.append(key, file);
            });
            const res = await uploadData(formData);
            setDatasets(prev => [res.data, ...prev]);
            setStatus({ type: 'success', message: `Uploaded dataset: ${res.data.dataset_id}` });
            setFiles({});
        } catch (err) {
            setStatus({ type: 'error', message: err.response?.data?.detail || 'Upload failed' });
        } finally {
            setLoadingUpload(false);
        }
    };

    const handleDelete = async (datasetId) => {
        try {
            await deleteDataset(datasetId);
            setDatasets(prev => prev.filter(d => d.dataset_id !== datasetId));
            setStatus({ type: 'success', message: `Deleted dataset: ${datasetId}` });
        } catch (err) {
            setStatus({ type: 'error', message: err.response?.data?.detail || 'Delete failed' });
        }
    };

    return (
        <div className="data-manager container">
            <div className="dm-header">
                <div>
                    <h1>Data Manager</h1>
                    <p>Load example data or upload your own wind farm CSVs.</p>
                </div>
            </div>

            {status && (
                <div className={`dm-status ${status.type} animate-fade-in`}>
                    {status.type === 'success' ? '✅' : '❌'} {status.message}
                </div>
            )}

            {/* Quick Load */}
            <section className="dm-section">
                <h3>Quick Start</h3>
                <p className="section-desc">Load the La Haute Borne example dataset — a real French wind farm with 4 turbines, 2 years of SCADA data, and ERA5/MERRA2 reanalysis.</p>
                <button className="btn btn-primary" onClick={handleLoadExample} disabled={loading} style={{ marginTop: '1rem' }}>
                    {loading ? <><span className="spinner" /> Loading...</> : '⚡ Load Example Dataset'}
                </button>
            </section>

            {/* Upload */}
            <section className="dm-section">
                <h3>Upload Custom Data</h3>
                <p className="section-desc">Upload your own wind farm data as CSV files. At minimum, SCADA data is required.</p>

                <div className="upload-grid">
                    {UPLOAD_FIELDS.map(field => (
                        <div key={field.name} className="upload-field glass-card">
                            <div className="uf-header">
                                <span className="uf-label">{field.label}</span>
                                {field.required && <span className="badge badge-warning">Required</span>}
                            </div>
                            <p className="uf-desc">{field.desc}</p>
                            <div
                                className={`upload-zone ${files[field.name] ? 'has-file' : ''}`}
                                onClick={() => fileRefs.current[field.name]?.click()}
                            >
                                <input
                                    type="file"
                                    accept=".csv"
                                    ref={el => fileRefs.current[field.name] = el}
                                    onChange={e => handleFileChange(field.name, e.target.files[0])}
                                    style={{ display: 'none' }}
                                />
                                {files[field.name] ? (
                                    <div className="file-chosen">
                                        <span>📄 {files[field.name].name}</span>
                                        <span className="file-size">({(files[field.name].size / 1024).toFixed(0)} KB)</span>
                                    </div>
                                ) : (
                                    <span className="upload-placeholder">Click to choose CSV file</span>
                                )}
                            </div>
                        </div>
                    ))}
                </div>

                <button
                    className="btn btn-primary"
                    onClick={handleUpload}
                    disabled={loadingUpload || !files.scada}
                    style={{ marginTop: '1.5rem' }}
                >
                    {loadingUpload ? <><span className="spinner" /> Uploading...</> : '📤 Upload Data'}
                </button>
            </section>

            {/* Loaded Datasets */}
            {datasets.length > 0 && (
                <section className="dm-section">
                    <h3>Loaded Datasets ({datasets.length})</h3>
                    {datasets.map(ds => (
                        <DatasetInfo key={ds.dataset_id} dataset={ds} onDelete={handleDelete} />
                    ))}
                </section>
            )}
        </div>
    );
}
