import './DatasetInfo.css';

export default function DatasetInfo({ dataset, onDelete }) {
    if (!dataset) return null;

    const { dataset_id, categories, message } = dataset;

    return (
        <div className="dataset-info glass-card animate-fade-in">
            <div className="di-header">
                <div>
                    <div className="di-id-row">
                        <span className="di-id">{dataset_id}</span>
                        <span className="badge badge-success">● Loaded</span>
                    </div>
                    {message && <p className="di-message">{message}</p>}
                </div>
                {onDelete && (
                    <button className="btn btn-danger btn-sm" onClick={() => onDelete(dataset_id)}>
                        Delete
                    </button>
                )}
            </div>

            {categories && (
                <div className="di-categories">
                    {Object.entries(categories).map(([key, info]) => (
                        <div key={key} className="di-cat-chip">
                            <span className="di-cat-name">{key}</span>
                            <span className="di-cat-rows">{info.rows?.toLocaleString()} rows</span>
                            {info.date_range && (
                                <span className="di-cat-date">
                                    {info.date_range[0]?.slice(0, 10)} → {info.date_range[1]?.slice(0, 10)}
                                </span>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
