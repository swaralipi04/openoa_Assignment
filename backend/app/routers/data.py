"""Data management router — upload, list, delete, and load example datasets."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.models.schemas import (
    DatasetListResponse,
    UploadResponse,
    DatasetInfo,
)
from app.services import data_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/data", tags=["Data"])


@router.post("/upload", response_model=UploadResponse)
async def upload_data(
    scada: Optional[UploadFile] = File(None, description="SCADA turbine data CSV"),
    meter: Optional[UploadFile] = File(None, description="Revenue meter data CSV"),
    tower: Optional[UploadFile] = File(None, description="Met tower data CSV"),
    status: Optional[UploadFile] = File(None, description="Turbine status data CSV"),
    curtail: Optional[UploadFile] = File(None, description="Curtailment data CSV"),
    asset: Optional[UploadFile] = File(None, description="Asset metadata CSV"),
    reanalysis: Optional[UploadFile] = File(None, description="Reanalysis data CSV"),
):
    """
    Upload wind plant data as CSV files.

    At minimum, SCADA data is typically required. Additional data categories
    unlock more analysis methods.
    """
    files = {}
    for name, f in [
        ("scada", scada),
        ("meter", meter),
        ("tower", tower),
        ("status", status),
        ("curtail", curtail),
        ("asset", asset),
        ("reanalysis", reanalysis),
    ]:
        if f is not None and f.filename:
            files[name] = f

    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded. Please provide at least one CSV file.")

    try:
        dataset_id, summary = await data_service.parse_uploaded_files(files)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    categories = {
        k: DatasetInfo(
            rows=v["rows"],
            columns=v["columns"],
            date_range=v.get("date_range"),
        )
        for k, v in summary.items()
    }

    return UploadResponse(
        dataset_id=dataset_id,
        message=f"Successfully uploaded {len(files)} data file(s)",
        categories=categories,
    )


@router.post("/example", response_model=UploadResponse)
async def load_example_data():
    """
    Load the built-in La Haute Borne example wind farm dataset.

    This 4-turbine French wind farm dataset includes SCADA, meter,
    curtailment, and asset data, along with reanalysis products.
    """
    try:
        dataset_id, summary = data_service.load_example_data()
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ImportError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load example data: {str(e)}")

    categories = {
        k: DatasetInfo(
            rows=v["rows"],
            columns=v["columns"],
            date_range=v.get("date_range"),
        )
        for k, v in summary.items()
    }

    return UploadResponse(
        dataset_id=dataset_id,
        message="Successfully loaded La Haute Borne example dataset",
        categories=categories,
    )


@router.get("/list", response_model=DatasetListResponse)
async def list_datasets():
    """List all currently loaded datasets."""
    datasets = data_service.list_datasets()
    return DatasetListResponse(datasets=datasets)


@router.get("/{dataset_id}/summary")
async def get_dataset_summary(dataset_id: str):
    """Get a summary of a loaded dataset."""
    ds = data_service.get_dataset(dataset_id)
    if ds is None:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found")

    summary = {}
    raw = ds.get("raw", {})
    for category, df in raw.items():
        if df is None:
            continue
        if isinstance(df, dict):
            # Handle reanalysis dict of DataFrames
            for sub_name, sub_df in df.items():
                from app.utils.helpers import get_dataframe_summary
                s = get_dataframe_summary(sub_df, f"reanalysis_{sub_name}")
                if s:
                    summary[f"reanalysis_{sub_name}"] = s
        else:
            from app.utils.helpers import get_dataframe_summary
            s = get_dataframe_summary(df, category)
            if s:
                summary[category] = s

    has_plant_data = ds.get("plant") is not None

    return {
        "dataset_id": dataset_id,
        "has_plant_data": has_plant_data,
        "categories": summary,
    }


@router.delete("/{dataset_id}")
async def delete_dataset(dataset_id: str):
    """Delete a loaded dataset to free memory."""
    if data_service.delete_dataset(dataset_id):
        return {"message": f"Dataset '{dataset_id}' deleted"}
    raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found")
