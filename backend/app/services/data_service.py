"""Data service — handles file uploads, CSV parsing, and PlantData construction."""

from __future__ import annotations

import io
import uuid
import logging
import zipfile
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

# In-memory store: dataset_id -> {"plant": PlantData, "raw": {category: DataFrame}}
_datasets: dict[str, dict[str, Any]] = {}

# Directory to cache downloaded example data
_CACHE_DIR = Path(__file__).resolve().parent.parent.parent / ".data_cache"


def get_store() -> dict[str, dict[str, Any]]:
    return _datasets


def list_datasets() -> list[dict]:
    result = []
    for ds_id, ds in _datasets.items():
        cats = [k for k in ds.get("raw", {}).keys() if ds["raw"][k] is not None]
        result.append({"dataset_id": ds_id, "categories": cats})
    return result


def delete_dataset(dataset_id: str) -> bool:
    if dataset_id in _datasets:
        del _datasets[dataset_id]
        return True
    return False


def get_dataset(dataset_id: str) -> dict[str, Any] | None:
    return _datasets.get(dataset_id)


async def parse_uploaded_files(files: dict[str, Any]) -> tuple[str, dict]:
    """Parse uploaded CSV files into DataFrames and store them."""
    dataset_id = str(uuid.uuid4())[:8]
    raw = {}
    summary = {}

    for category, upload_file in files.items():
        if upload_file is None:
            continue
        try:
            content = await upload_file.read()
            df = pd.read_csv(io.BytesIO(content))
            raw[category] = df
            summary[category] = _make_summary(df)
            logger.info(f"Parsed {category}: {len(df)} rows, {len(df.columns)} columns")
        except Exception as e:
            logger.error(f"Failed to parse {category}: {e}")
            raise ValueError(f"Failed to parse '{category}' CSV: {str(e)}")

    _datasets[dataset_id] = {"plant": None, "raw": raw}
    return dataset_id, summary


# ─────────────────────────────────────────────────────────────
# Column mappings: Raw CSV columns → OpenOA internal names
# ─────────────────────────────────────────────────────────────

_SCADA_RENAME = {
    "Wind_turbine_name": "asset_id",
    "Date_time": "time",
    "P_avg": "WTUR_W",
    "Ws_avg": "WMET_HorWdSpd",
    "Wa_avg": "WMET_HorWdDir",
    "Va_avg": "WMET_HorWdDirRel",
    "Ot_avg": "WMET_EnvTmp",
    "Ya_avg": "WTUR_TurSt",
    "Ba_avg": "WROT_BlPthAngVal",
}

_METER_RENAME = {
    "time_utc": "time",
    "net_energy_kwh": "MMTR_SupWh",
}

_CURTAIL_RENAME = {
    "time_utc": "time",
    "curtailment_kwh": "IAVL_ExtPwrDnWh",
    "availability_kwh": "IAVL_DnWh",
}

_ASSET_RENAME = {
    "Wind_turbine_name": "asset_id",
    "Latitude": "latitude",
    "Longitude": "longitude",
    "Rated_power": "rated_power",
    "Hub_height_m": "hub_height",
    "Rotor_diameter_m": "rotor_diameter",
    "elevation_m": "elevation",
}

_ERA5_RENAME = {
    "datetime": "time",
    "ws_100m": "WMETR_HorWdSpd",
    "u_100": "WMETR_HorWdSpdU",
    "v_100": "WMETR_HorWdSpdV",
    "t_2m": "WMETR_EnvTmp",
    "dens_100m": "WMETR_AirDen",
    "surf_pres": "WMETR_EnvPres",
}

_MERRA2_RENAME = {
    "datetime": "time",
    "ws_50m": "WMETR_HorWdSpd",
    "u_50": "WMETR_HorWdSpdU",
    "v_50": "WMETR_HorWdSpdV",
    "temp_2m": "WMETR_EnvTmp",
    "dens_50m": "WMETR_AirDen",
    "surface_pressure": "WMETR_EnvPres",
}


def _find_file(directory: Path, *patterns: str) -> Path | None:
    for pattern in patterns:
        matches = list(directory.glob(pattern))
        if matches:
            return matches[0]
    return None


def _drop_unnamed(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop(columns=[c for c in df.columns if "Unnamed" in c], errors="ignore")


def load_example_data() -> tuple[str, dict]:
    """
    Load the La Haute Borne example dataset with correct column mappings.

    IMPORTANT: OpenOA PlantData expects 'time' as a regular column (NOT the index).
    """
    try:
        from openoa.plant import PlantData
        from openoa.schema import PlantMetaData
    except ImportError as e:
        raise ImportError(f"OpenOA is not installed: {e}")

    _ensure_example_data()
    dataset_id = "example-" + str(uuid.uuid4())[:4]

    try:
        raw = {}
        summary = {}

        # ── SCADA ──
        f = _find_file(_CACHE_DIR, "la-haute-borne-data*.csv")
        if f:
            df = pd.read_csv(f)
            df = df.rename(columns=_SCADA_RENAME)
            df["time"] = pd.to_datetime(df["time"], utc=True)
            # Remove duplicate (time, asset_id) rows — required for analyses that pivot
            df = df.drop_duplicates(subset=["time", "asset_id"], keep="first")
            raw["scada"] = df
            summary["scada"] = _make_summary(df)
            logger.info(f"Loaded SCADA: {len(df)} rows")

        # ── Meter ──
        f = _find_file(_CACHE_DIR, "plant_data.csv")
        if f:
            df = pd.read_csv(f)
            # Meter data
            meter_df = df.rename(columns=_METER_RENAME)
            meter_df["time"] = pd.to_datetime(meter_df["time"], utc=True)
            raw["meter"] = meter_df
            summary["meter"] = _make_summary(meter_df)
            logger.info(f"Loaded meter: {len(meter_df)} rows")

            # Curtailment data (from same file)
            curtail_df = df.rename(columns=_CURTAIL_RENAME)
            curtail_df["time"] = pd.to_datetime(curtail_df["time"], utc=True)
            # Keep only the curtailment columns
            curtail_cols = ["time", "IAVL_ExtPwrDnWh", "IAVL_DnWh"]
            curtail_df = curtail_df[[c for c in curtail_cols if c in curtail_df.columns]]
            raw["curtail"] = curtail_df
            summary["curtail"] = _make_summary(curtail_df)
            logger.info(f"Loaded curtailment: {len(curtail_df)} rows")

        # ── Asset ──
        f = _find_file(_CACHE_DIR, "*asset*.csv")
        if f:
            df = pd.read_csv(f)
            df = df.rename(columns=_ASSET_RENAME)
            # OpenOA requires a 'type' column to identify turbines
            if "type" not in df.columns:
                df["type"] = "turbine"
            raw["asset"] = df
            summary["asset"] = _make_summary(df)
            logger.info(f"Loaded asset: {len(df)} rows")

        # ── Reanalysis ──
        reanalysis = {}

        f = _find_file(_CACHE_DIR, "*era5*.csv")
        if f:
            df = _drop_unnamed(pd.read_csv(f).rename(columns=_ERA5_RENAME))
            df["time"] = pd.to_datetime(df["time"], utc=True)
            reanalysis["era5"] = df
            summary["reanalysis_era5"] = _make_summary(df)
            logger.info(f"Loaded ERA5: {len(df)} rows")

        f = _find_file(_CACHE_DIR, "*merra2*.csv")
        if f:
            df = _drop_unnamed(pd.read_csv(f).rename(columns=_MERRA2_RENAME))
            df["time"] = pd.to_datetime(df["time"], utc=True)
            reanalysis["merra2"] = df
            summary["reanalysis_merra2"] = _make_summary(df)
            logger.info(f"Loaded MERRA2: {len(df)} rows")

        if reanalysis:
            raw["reanalysis"] = reanalysis

        # ── Build PlantMetaData with reanalysis definitions ──
        meta = PlantMetaData.from_dict({
            "latitude": 48.4523,
            "longitude": 5.5872,
            "capacity": 8.2,
            "reanalysis": {k: {} for k in reanalysis},
        })

        # ── Create PlantData ──
        try:
            plant = PlantData(
                metadata=meta,
                scada=raw.get("scada"),
                meter=raw.get("meter"),
                curtail=raw.get("curtail"),
                asset=raw.get("asset"),
                reanalysis=raw.get("reanalysis"),
                analysis_type=None,
            )
            _datasets[dataset_id] = {"plant": plant, "raw": raw}
            logger.info(f"PlantData created successfully: {dataset_id}")
        except Exception as e:
            logger.warning(f"Could not create PlantData: {e}")
            _datasets[dataset_id] = {"plant": None, "raw": raw}

    except Exception as e:
        logger.error(f"Error loading example data: {e}", exc_info=True)
        raise RuntimeError(f"Failed to load example data: {str(e)}")

    return dataset_id, summary


def _ensure_example_data():
    """Make sure CSV example files exist in .data_cache/."""
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    csvs = list(_CACHE_DIR.glob("*.csv"))
    if len(csvs) >= 3:
        return

    zip_path = _CACHE_DIR / "la_haute_borne.zip"
    if zip_path.exists():
        logger.info(f"Extracting {zip_path}...")
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(_CACHE_DIR)
        for sub in _CACHE_DIR.iterdir():
            if sub.is_dir() and sub.name != "__MACOSX":
                for f in sub.rglob("*.csv"):
                    dest = _CACHE_DIR / f.name
                    if not dest.exists():
                        f.rename(dest)
        return

    raise FileNotFoundError(
        f"Example data not found. Place CSV files in: {_CACHE_DIR}"
    )


def _make_summary(df: pd.DataFrame) -> dict:
    info = {"rows": len(df), "columns": list(df.columns)}
    if "time" in df.columns:
        try:
            ts = pd.to_datetime(df["time"])
            info["date_range"] = [ts.min().isoformat(), ts.max().isoformat()]
        except Exception:
            pass
    elif isinstance(df.index, pd.DatetimeIndex) and len(df) > 0:
        info["date_range"] = [df.index.min().isoformat(), df.index.max().isoformat()]
    return info


def get_or_create_plant_data(dataset_id: str, analysis_type: str | None = None):
    """Get the PlantData for a dataset, creating it if necessary."""
    ds = _datasets.get(dataset_id)
    if ds is None:
        raise KeyError(f"Dataset '{dataset_id}' not found")

    if ds["plant"] is not None:
        return ds["plant"]

    try:
        from openoa.plant import PlantData
        from openoa.schema import PlantMetaData

        raw = ds["raw"]

        # Build metadata
        reanalysis_keys = {}
        if "reanalysis" in raw and isinstance(raw["reanalysis"], dict):
            reanalysis_keys = {k: {} for k in raw["reanalysis"]}

        meta = PlantMetaData.from_dict({
            "latitude": 0.0,
            "longitude": 0.0,
            "capacity": 1.0,
            "reanalysis": reanalysis_keys,
        })

        plant = PlantData(
            metadata=meta,
            scada=raw.get("scada"),
            meter=raw.get("meter"),
            tower=raw.get("tower"),
            status=raw.get("status"),
            curtail=raw.get("curtail"),
            asset=raw.get("asset"),
            reanalysis=raw.get("reanalysis"),
            analysis_type=analysis_type,
        )
        ds["plant"] = plant
        return plant
    except Exception as e:
        raise RuntimeError(f"Cannot create PlantData: {str(e)}")
