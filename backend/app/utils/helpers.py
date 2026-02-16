"""Utility helpers for the OpenOA API."""

from __future__ import annotations

import io
import base64

import matplotlib

matplotlib.use("Agg")  # Non-interactive backend for server use
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def encode_figure_to_base64(fig: plt.Figure) -> str:
    """Render a matplotlib Figure to a base64-encoded PNG string."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return encoded


def dataframe_to_json_safe(df: pd.DataFrame) -> dict:
    """Convert a DataFrame (possibly with DatetimeIndex) to a JSON-safe dict."""
    df_copy = df.copy()
    if isinstance(df_copy.index, pd.DatetimeIndex):
        df_copy.index = df_copy.index.strftime("%Y-%m-%dT%H:%M:%S")
    # Convert numpy types to native Python
    result = {}
    for col in df_copy.columns:
        values = df_copy[col].tolist()
        result[col] = [
            float(v) if isinstance(v, (np.floating, float)) and not np.isnan(v)
            else (None if isinstance(v, float) and np.isnan(v) else v)
            for v in values
        ]
    result["index"] = df_copy.index.tolist()
    return result


def safe_float(value) -> float:
    """Convert a numpy/pandas scalar to a plain Python float."""
    if value is None:
        return 0.0
    try:
        f = float(value)
        return f if not np.isnan(f) else 0.0
    except (TypeError, ValueError):
        return 0.0


def get_dataframe_summary(df: pd.DataFrame | None, name: str) -> dict | None:
    """Return a compact summary of a DataFrame."""
    if df is None or (hasattr(df, "empty") and df.empty):
        return None
    info = {
        "rows": len(df),
        "columns": list(df.columns),
    }
    if isinstance(df.index, pd.DatetimeIndex) and len(df) > 0:
        info["date_range"] = [
            df.index.min().isoformat(),
            df.index.max().isoformat(),
        ]
    return info
