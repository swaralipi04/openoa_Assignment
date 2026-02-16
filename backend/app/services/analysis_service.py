"""Analysis service — wrappers around OpenOA analysis classes (v3.2 API)."""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from app.utils.helpers import encode_figure_to_base64, safe_float

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# MonteCarloAEP
# ─────────────────────────────────────────────────────────────

def run_monte_carlo_aep(plant, params: dict[str, Any]) -> dict[str, Any]:
    """Run MonteCarloAEP analysis."""
    from openoa.analysis.aep import MonteCarloAEP

    logger.info(f"Running MonteCarloAEP with params: {params}")

    try:
        aep = MonteCarloAEP(
            plant=plant,
            reg_temperature=params.get("reg_temperature", False),
            reg_wind_direction=params.get("reg_wind_direction", False),
            uncertainty_meter=params.get("uncertainty_meter", 0.005),
            uncertainty_losses=params.get("uncertainty_losses", 0.05),
            outlier_detection=params.get("outlier_detection", False),
        )
        aep.run(
            num_sim=params.get("num_sim", 10),
            reg_model=params.get("reg_model", "lin"),
            time_resolution=params.get("time_resolution", "MS"),
            progress_bar=False,
        )

        # Extract results — v3.2: aep.results is a DataFrame
        aep_dist = []
        aep_mean = 0.0
        aep_std = 0.0

        if hasattr(aep, "results") and aep.results is not None:
            res = aep.results
            logger.info(f"AEP results type: {type(res)}, shape: {getattr(res, 'shape', 'N/A')}")
            logger.info(f"AEP results columns: {list(res.columns) if hasattr(res, 'columns') else 'N/A'}")
            if hasattr(res, "values"):
                vals = res.values.flatten()
                vals = vals[~np.isnan(vals)]
                if len(vals) > 0:
                    # Convert from Wh to GWh if values are very large
                    if np.mean(vals) > 1e6:
                        vals = vals / 1e9  # Wh → GWh
                    elif np.mean(vals) > 1e3:
                        vals = vals / 1e6  # kWh → GWh
                    aep_dist = [safe_float(v) for v in vals]
                    aep_mean = safe_float(np.mean(vals))
                    aep_std = safe_float(np.std(vals))

        uncertainty_pct = (aep_std / aep_mean * 100) if aep_mean != 0 else 0.0

        # Generate plot
        plot_b64 = None
        try:
            fig, ax = plt.subplots(1, 1, figsize=(8, 5))
            if aep_dist:
                ax.hist(aep_dist, bins=min(20, max(5, len(aep_dist))),
                        edgecolor="white", alpha=0.8, color="#2196F3")
                ax.axvline(aep_mean, color="#FF5722", linestyle="--", linewidth=2,
                           label=f"Mean: {aep_mean:.2f} GWh")
                ax.set_xlabel("AEP (GWh)", fontsize=12)
                ax.set_ylabel("Frequency", fontsize=12)
                ax.set_title("Monte Carlo AEP Distribution", fontsize=14, fontweight="bold")
                ax.legend(fontsize=11)
            fig.tight_layout()
            plot_b64 = encode_figure_to_base64(fig)
            plt.close(fig)
        except Exception as e:
            logger.warning(f"Failed to generate AEP plot: {e}")

        return {
            "aep_gwh": aep_mean,
            "aep_uncertainty_pct": safe_float(uncertainty_pct),
            "avail_pct": 0.0,
            "curtail_pct": 0.0,
            "num_sim": params.get("num_sim", 10),
            "time_resolution": params.get("time_resolution", "MS"),
            "aep_distribution": aep_dist,
            "plot_base64": plot_b64,
        }

    except Exception as e:
        logger.error(f"MonteCarloAEP analysis failed: {e}", exc_info=True)
        raise RuntimeError(f"MonteCarloAEP analysis failed: {str(e)}")


# ─────────────────────────────────────────────────────────────
# ElectricalLosses
# ─────────────────────────────────────────────────────────────

def run_electrical_losses(plant, params: dict[str, Any]) -> dict[str, Any]:
    """Run ElectricalLosses analysis."""
    from openoa.analysis.electrical_losses import ElectricalLosses

    logger.info(f"Running ElectricalLosses with params: {params}")

    try:
        el = ElectricalLosses(plant=plant)
        el.run(
            num_sim=params.get("num_sim", 10),
            uncertainty_meter=params.get("uncertainty_meter", 0.005),
            uncertainty_scada=params.get("uncertainty_scada", 0.005),
        )

        # v3.2 result: el.electrical_losses (array of fractional losses)
        losses_dist = []
        mean_loss = 0.0
        median_loss = 0.0
        std_loss = 0.0

        if hasattr(el, "electrical_losses") and el.electrical_losses is not None:
            losses_raw = el.electrical_losses
            logger.info(f"Electrical losses type: {type(losses_raw)}")
            if hasattr(losses_raw, "values"):
                losses_arr = losses_raw.values.flatten()
            else:
                losses_arr = np.array(losses_raw).flatten()
            losses_arr = losses_arr[~np.isnan(losses_arr)]
            logger.info(f"Electrical losses raw values: {losses_arr}")
            if len(losses_arr) > 0:
                losses_dist = [safe_float(v * 100) for v in losses_arr]
                mean_loss = safe_float(np.mean(losses_arr) * 100)
                median_loss = safe_float(np.median(losses_arr) * 100)
                std_loss = safe_float(np.std(losses_arr) * 100)
                logger.info(f"EL: mean={mean_loss:.4f}%, median={median_loss:.4f}%, std={std_loss:.4f}%")

        # Generate plot
        plot_b64 = None
        try:
            fig, ax = plt.subplots(1, 1, figsize=(8, 5))
            if losses_dist:
                n_bins = max(10, min(30, len(losses_dist) // 2))
                ax.hist(losses_dist, bins=n_bins,
                        edgecolor="white", alpha=0.8, color="#4CAF50",
                        density=True)
                ax.axvline(mean_loss, color="#FF5722", linestyle="--", linewidth=2,
                           label=f"Mean: {mean_loss:.2f}%")
                if std_loss > 0:
                    ax.axvline(mean_loss - std_loss, color="#2196F3", linestyle=":", linewidth=1.5,
                               label=f"±1σ: {std_loss:.2f}%")
                    ax.axvline(mean_loss + std_loss, color="#2196F3", linestyle=":", linewidth=1.5)
                ax.set_xlabel("Electrical Losses (%)", fontsize=12)
                ax.set_ylabel("Density", fontsize=12)
                ax.set_title("Electrical Losses Distribution", fontsize=14, fontweight="bold")
                ax.legend(fontsize=11)
            fig.tight_layout()
            plot_b64 = encode_figure_to_base64(fig)
            plt.close(fig)
        except Exception as e:
            logger.warning(f"Failed to generate electrical losses plot: {e}")

        return {
            "mean_losses_pct": mean_loss,
            "median_losses_pct": median_loss,
            "std_losses_pct": std_loss,
            "num_sim": params.get("num_sim", 10),
            "losses_distribution": losses_dist,
            "plot_base64": plot_b64,
        }

    except Exception as e:
        logger.error(f"ElectricalLosses analysis failed: {e}", exc_info=True)
        raise RuntimeError(f"ElectricalLosses analysis failed: {str(e)}")


# ─────────────────────────────────────────────────────────────
# TurbineLongTermGrossEnergy
# ─────────────────────────────────────────────────────────────

def run_turbine_long_term_energy(plant, params: dict[str, Any]) -> dict[str, Any]:
    """Run TurbineLongTermGrossEnergy analysis."""
    from openoa.analysis.turbine_long_term_gross_energy import TurbineLongTermGrossEnergy

    logger.info(f"Running TurbineLongTermGrossEnergy with params: {params}")

    try:
        tle = TurbineLongTermGrossEnergy(plant=plant)
        tle.run(
            num_sim=params.get("num_sim", 10),
            uncertainty_scada=params.get("uncertainty_scada", 0.005),
        )

        # v3.2 results:
        #   tle.plant_gross  — numpy.ndarray of per-sim plant-level gross energy (Wh)
        #   tle.turb_lt_gross — DataFrame of daily Wh per turbine (rows=days, cols=turbines)
        tie_gwh = 0.0
        tie_unc = 0.0
        turbine_results = {}

        # plant_gross is a numpy array, each element = one simulation's plant gross (Wh)
        if hasattr(tle, "plant_gross") and tle.plant_gross is not None:
            pg = np.array(tle.plant_gross).flatten()
            pg = pg[~np.isnan(pg)]
            logger.info(f"plant_gross: {len(pg)} sims, values (Wh): {pg}")
            if len(pg) > 0:
                pg_gwh = pg / 1e9  # Wh → GWh
                tie_gwh = safe_float(np.mean(pg_gwh))
                tie_unc = safe_float(np.std(pg_gwh) / np.mean(pg_gwh) * 100) if tie_gwh != 0 else 0.0
                logger.info(f"Plant gross: mean={tie_gwh:.4f} GWh, unc={tie_unc:.2f}%")

        # turb_lt_gross: DataFrame with daily gross energy per turbine (Wh)
        # Sum across days to get total long-term gross per turbine
        if hasattr(tle, "turb_lt_gross") and tle.turb_lt_gross is not None:
            tdf = tle.turb_lt_gross
            logger.info(f"turb_lt_gross: type={type(tdf)}, shape={getattr(tdf, 'shape', 'N/A')}")
            if hasattr(tdf, "columns") and len(tdf) > 0:
                for col in tdf.columns:
                    val_wh = tdf[col].sum()  # Total Wh for this turbine
                    val_gwh = val_wh / 1e9   # Convert to GWh
                    turbine_results[str(col)] = safe_float(val_gwh)
                logger.info(f"Per-turbine gross (GWh): {turbine_results}")

        # Generate plot
        plot_b64 = None
        try:
            fig, ax = plt.subplots(1, 1, figsize=(8, 5))
            if turbine_results:
                turbine_ids = list(turbine_results.keys())
                values = list(turbine_results.values())
                bars = ax.bar(turbine_ids, values, color="#9C27B0", alpha=0.8, edgecolor="white")
                ax.set_xlabel("Turbine", fontsize=12)
                ax.set_ylabel("Gross Energy (GWh)", fontsize=12)
                ax.set_title("Turbine Long-Term Gross Energy", fontsize=14, fontweight="bold")
                ax.tick_params(axis="x", rotation=45)
                # Add value labels on bars
                for bar, val in zip(bars, values):
                    ax.text(bar.get_x() + bar.get_width() / 2., bar.get_height(),
                            f"{val:.2f}", ha="center", va="bottom", fontsize=10)
            fig.tight_layout()
            plot_b64 = encode_figure_to_base64(fig)
            plt.close(fig)
        except Exception as e:
            logger.warning(f"Failed to generate TIE plot: {e}")

        return {
            "tie_gwh": tie_gwh,
            "tie_uncertainty_pct": tie_unc,
            "num_sim": params.get("num_sim", 10),
            "turbine_results": turbine_results,
            "plot_base64": plot_b64,
        }

    except Exception as e:
        logger.error(f"TurbineLongTermGrossEnergy analysis failed: {e}", exc_info=True)
        raise RuntimeError(f"TurbineLongTermGrossEnergy analysis failed: {str(e)}")


# ─────────────────────────────────────────────────────────────
# WakeLosses
# ─────────────────────────────────────────────────────────────

def run_wake_losses(plant, params: dict[str, Any]) -> dict[str, Any]:
    """Run WakeLosses analysis."""
    from openoa.analysis.wake_losses import WakeLosses

    logger.info(f"Running WakeLosses with params: {params}")

    try:
        wl = WakeLosses(
            plant=plant,
            wind_direction_col=params.get("wind_direction_col", "WMET_HorWdDir"),
            wind_direction_data_type=params.get("wind_direction_data_type", "scada"),
        )
        wl.run(
            num_sim=params.get("num_sim", 10),
            wd_bin_width=params.get("wd_bin_width", 5.0),
        )

        # v3.2 results:
        #   wl.wake_losses_lt_mean — float, plant-level long-term mean wake loss (fraction)
        #   wl.wake_losses_lt_std  — float, std dev
        #   wl.turbine_wake_losses_lt_mean — dict/Series, per-turbine long-term mean
        #   wl.wake_losses_por_mean — float, period-of-record mean
        mean_wake = 0.0
        std_wake = 0.0
        turbine_wakes = {}

        if hasattr(wl, "wake_losses_lt_mean") and wl.wake_losses_lt_mean is not None:
            mean_wake = safe_float(float(wl.wake_losses_lt_mean) * 100)
        elif hasattr(wl, "wake_losses_por_mean") and wl.wake_losses_por_mean is not None:
            mean_wake = safe_float(float(wl.wake_losses_por_mean) * 100)

        if hasattr(wl, "wake_losses_lt_std") and wl.wake_losses_lt_std is not None:
            std_wake = safe_float(float(wl.wake_losses_lt_std) * 100)
        elif hasattr(wl, "wake_losses_por_std") and wl.wake_losses_por_std is not None:
            std_wake = safe_float(float(wl.wake_losses_por_std) * 100)

        # Get turbine IDs for pairing with array results
        t_ids = []
        if hasattr(wl, "turbine_ids") and wl.turbine_ids is not None:
            t_ids = list(wl.turbine_ids)

        if hasattr(wl, "turbine_wake_losses_lt_mean") and wl.turbine_wake_losses_lt_mean is not None:
            twl = wl.turbine_wake_losses_lt_mean
            if hasattr(twl, "items"):
                # Series/dict
                for k, v in twl.items():
                    turbine_wakes[str(k)] = safe_float(float(v) * 100)
            else:
                # numpy array — pair with turbine_ids
                twl_arr = np.array(twl).flatten()
                ids = t_ids if len(t_ids) == len(twl_arr) else [f"T{i+1}" for i in range(len(twl_arr))]
                for tid, val in zip(ids, twl_arr):
                    turbine_wakes[str(tid)] = safe_float(float(val) * 100)
        elif hasattr(wl, "turbine_wake_losses_por_mean") and wl.turbine_wake_losses_por_mean is not None:
            twl = wl.turbine_wake_losses_por_mean
            if hasattr(twl, "items"):
                for k, v in twl.items():
                    turbine_wakes[str(k)] = safe_float(float(v) * 100)
            else:
                twl_arr = np.array(twl).flatten()
                ids = t_ids if len(t_ids) == len(twl_arr) else [f"T{i+1}" for i in range(len(twl_arr))]
                for tid, val in zip(ids, twl_arr):
                    turbine_wakes[str(tid)] = safe_float(float(val) * 100)

        logger.info(f"Wake losses: mean={mean_wake:.2f}%, std={std_wake:.2f}%, turbines={len(turbine_wakes)}")

        # Generate plot
        plot_b64 = None
        try:
            fig, ax = plt.subplots(1, 1, figsize=(8, 5))
            if turbine_wakes:
                turbine_ids = list(turbine_wakes.keys())
                values = list(turbine_wakes.values())
                bars = ax.bar(turbine_ids, values, color="#FF9800", alpha=0.8, edgecolor="white")
                ax.axhline(mean_wake, color="#F44336", linestyle="--", linewidth=2,
                           label=f"Plant mean: {mean_wake:.2f}%")
                ax.set_xlabel("Turbine", fontsize=12)
                ax.set_ylabel("Wake Losses (%)", fontsize=12)
                ax.set_title("Per-Turbine Wake Losses", fontsize=14, fontweight="bold")
                ax.tick_params(axis="x", rotation=45)
                ax.legend(fontsize=11)
                for bar, val in zip(bars, values):
                    ax.text(bar.get_x() + bar.get_width() / 2., bar.get_height(),
                            f"{val:.1f}%", ha="center", va="bottom", fontsize=10)
            fig.tight_layout()
            plot_b64 = encode_figure_to_base64(fig)
            plt.close(fig)
        except Exception as e:
            logger.warning(f"Failed to generate wake losses plot: {e}")

        return {
            "mean_wake_losses_pct": mean_wake,
            "std_wake_losses_pct": std_wake,
            "num_sim": params.get("num_sim", 10),
            "turbine_wake_losses": turbine_wakes,
            "plot_base64": plot_b64,
        }

    except Exception as e:
        logger.error(f"WakeLosses analysis failed: {e}", exc_info=True)
        raise RuntimeError(f"WakeLosses analysis failed: {str(e)}")
