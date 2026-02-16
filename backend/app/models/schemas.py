"""Pydantic models for API request/response schemas."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


# ──────────────────────────────────────────────
# Data endpoints
# ──────────────────────────────────────────────


class DatasetInfo(BaseModel):
    """Summary information for a single data category."""

    rows: int
    columns: list[str]
    date_range: Optional[list[str]] = None  # [start, end] ISO strings


class UploadResponse(BaseModel):
    """Returned after a successful data upload or example load."""

    dataset_id: str
    message: str
    categories: dict[str, DatasetInfo]


class DatasetListItem(BaseModel):
    dataset_id: str
    categories: list[str]


class DatasetListResponse(BaseModel):
    datasets: list[DatasetListItem]


class ValidationResult(BaseModel):
    category: str
    valid: bool
    messages: list[str] = []


class ValidationResponse(BaseModel):
    dataset_id: str
    overall_valid: bool
    results: list[ValidationResult]


# ──────────────────────────────────────────────
# Analysis endpoints
# ──────────────────────────────────────────────


class AnalysisRequest(BaseModel):
    """Base request for all analysis endpoints."""

    dataset_id: str


class AEPRequest(AnalysisRequest):
    """Parameters for MonteCarloAEP analysis."""

    num_sim: int = Field(default=10, ge=1, le=20000, description="Number of Monte Carlo simulations")
    time_resolution: str = Field(default="MS", description="Time resolution: 'MS', 'ME', 'D', or 'h'")
    reg_model: str = Field(default="lin", description="Regression model: 'lin', 'gam', 'gbm', 'etr'")
    reg_temperature: bool = Field(default=False, description="Include temperature as regression input")
    reg_wind_direction: bool = Field(default=False, description="Include wind direction as regression input")
    uncertainty_meter: float = Field(default=0.005, description="Revenue meter uncertainty")
    uncertainty_losses: float = Field(default=0.05, description="Long-term losses uncertainty")
    outlier_detection: bool = Field(default=False, description="Perform outlier detection")


class ElectricalLossesRequest(AnalysisRequest):
    """Parameters for ElectricalLosses analysis."""

    num_sim: int = Field(default=10, ge=1, le=20000, description="Number of Monte Carlo simulations")
    uncertainty_meter: float = Field(default=0.005, description="Revenue meter uncertainty")
    uncertainty_scada: float = Field(default=0.005, description="SCADA data uncertainty")


class TurbineEnergyRequest(AnalysisRequest):
    """Parameters for TurbineLongTermGrossEnergy analysis."""

    num_sim: int = Field(default=10, ge=1, le=20000, description="Number of Monte Carlo simulations")
    uncertainty_scada: float = Field(default=0.005, description="SCADA data uncertainty")


class WakeLossesRequest(AnalysisRequest):
    """Parameters for WakeLosses analysis."""

    num_sim: int = Field(default=10, ge=1, le=100, description="Number of Monte Carlo simulations")
    wind_direction_col: str = Field(default="WMET_HorWdDir", description="Wind direction column name in SCADA")
    wind_direction_data_type: str = Field(default="scada", description="Data source: 'scada' or 'tower'")
    wd_bin_width: float = Field(default=5.0, ge=1.0, le=30.0, description="Wind direction bin width in degrees")


# ──────────────────────────────────────────────
# Analysis results
# ──────────────────────────────────────────────


class AEPResult(BaseModel):
    dataset_id: str
    analysis: str = "MonteCarloAEP"
    aep_gwh: float = Field(description="Estimated long-term AEP in GWh")
    aep_uncertainty_pct: float = Field(description="AEP uncertainty as percentage")
    avail_pct: float = Field(default=0.0, description="Mean availability percentage")
    curtail_pct: float = Field(default=0.0, description="Mean curtailment percentage")
    num_sim: int
    time_resolution: str
    aep_distribution: list[float] = Field(default_factory=list, description="AEP distribution from MC sims")
    plot_base64: Optional[str] = Field(default=None, description="Base64-encoded results plot")


class ElectricalLossesResult(BaseModel):
    dataset_id: str
    analysis: str = "ElectricalLosses"
    mean_losses_pct: float = Field(description="Mean electrical losses as percentage")
    median_losses_pct: float = Field(description="Median electrical losses as percentage")
    std_losses_pct: float = Field(description="Std dev of losses as percentage")
    num_sim: int
    losses_distribution: list[float] = Field(default_factory=list)
    plot_base64: Optional[str] = None


class TurbineEnergyResult(BaseModel):
    dataset_id: str
    analysis: str = "TurbineLongTermGrossEnergy"
    tie_gwh: float = Field(description="Turbine ideal energy in GWh")
    tie_uncertainty_pct: float = Field(description="TIE uncertainty as percentage")
    num_sim: int
    turbine_results: dict[str, Any] = Field(default_factory=dict, description="Per-turbine results")
    plot_base64: Optional[str] = None


class WakeLossesResult(BaseModel):
    dataset_id: str
    analysis: str = "WakeLosses"
    mean_wake_losses_pct: float = Field(description="Mean plant-level wake losses (%)")
    std_wake_losses_pct: float = Field(description="Std dev of wake losses (%)")
    num_sim: int
    turbine_wake_losses: dict[str, float] = Field(default_factory=dict, description="Per-turbine wake losses")
    plot_base64: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standardized error response."""

    error: str
    detail: str
    analysis: Optional[str] = None
