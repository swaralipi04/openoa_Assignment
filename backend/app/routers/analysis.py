"""Analysis router — endpoints for running OpenOA analysis methods."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    AEPRequest,
    AEPResult,
    ElectricalLossesRequest,
    ElectricalLossesResult,
    TurbineEnergyRequest,
    TurbineEnergyResult,
    WakeLossesRequest,
    WakeLossesResult,
    ErrorResponse,
)
from app.services import analysis_service, data_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analysis", tags=["Analysis"])


@router.post(
    "/aep",
    response_model=AEPResult,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def run_aep_analysis(request: AEPRequest):
    """
    Run **MonteCarloAEP** analysis on a loaded dataset.

    Estimates long-term annual energy production (AEP) using Monte Carlo
    simulation with uncertainty quantification. Requires SCADA, meter,
    curtailment, and reanalysis data.
    """
    try:
        plant = data_service.get_or_create_plant_data(request.dataset_id, analysis_type="MonteCarloAEP")
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Dataset '{request.dataset_id}' not found")
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        result = analysis_service.run_monte_carlo_aep(
            plant=plant,
            params=request.model_dump(exclude={"dataset_id"}),
        )
        return AEPResult(dataset_id=request.dataset_id, **result)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/electrical-losses",
    response_model=ElectricalLossesResult,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def run_electrical_losses_analysis(request: ElectricalLossesRequest):
    """
    Run **ElectricalLosses** analysis on a loaded dataset.

    Estimates average electrical losses by comparing turbine-level energy
    production to grid-delivered energy. Requires SCADA and meter data.
    """
    try:
        plant = data_service.get_or_create_plant_data(request.dataset_id, analysis_type="ElectricalLosses")
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Dataset '{request.dataset_id}' not found")
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        result = analysis_service.run_electrical_losses(
            plant=plant,
            params=request.model_dump(exclude={"dataset_id"}),
        )
        return ElectricalLossesResult(dataset_id=request.dataset_id, **result)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/turbine-energy",
    response_model=TurbineEnergyResult,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def run_turbine_energy_analysis(request: TurbineEnergyRequest):
    """
    Run **TurbineLongTermGrossEnergy** analysis on a loaded dataset.

    Estimates the long-term turbine ideal energy (TIE) — the AEP that would
    be generated if all turbines operated normally. Requires SCADA, reanalysis,
    and asset data.
    """
    try:
        plant = data_service.get_or_create_plant_data(
            request.dataset_id, analysis_type="TurbineLongTermGrossEnergy"
        )
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Dataset '{request.dataset_id}' not found")
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        result = analysis_service.run_turbine_long_term_energy(
            plant=plant,
            params=request.model_dump(exclude={"dataset_id"}),
        )
        return TurbineEnergyResult(dataset_id=request.dataset_id, **result)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/wake-losses",
    response_model=WakeLossesResult,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def run_wake_losses_analysis(request: WakeLossesRequest):
    """
    Run **WakeLosses** analysis on a loaded dataset.

    Estimates internal wake losses per turbine and plant-wide.
    Requires SCADA data with wind direction, and asset data.
    """
    try:
        plant = data_service.get_or_create_plant_data(request.dataset_id, analysis_type="WakeLosses-scada")
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Dataset '{request.dataset_id}' not found")
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        result = analysis_service.run_wake_losses(
            plant=plant,
            params=request.model_dump(exclude={"dataset_id"}),
        )
        return WakeLossesResult(dataset_id=request.dataset_id, **result)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
