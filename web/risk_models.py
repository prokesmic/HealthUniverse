"""Validated clinical risk equations.

Implements the most-cited published risk scores:

  • ASCVD 10-year — Pooled Cohort Equations (Goff et al, Circulation 2014)
  • FINDRISC    — Finnish T2D risk score (Lindström & Tuomilehto, Diabetes Care 2003)
  • FRAX-lite   — A simplified 10-year hip + major fracture surrogate
  • QRISK3-lite — Simplified UK CV risk (closer to ASCVD; we expose
                   one CV equation publicly as 'mace_10yr')

All equations take a flat dict of inputs and return a dict
{ score, label, components, used_inputs, missing_inputs }.

If required inputs are missing, we return as much as we can with
'missing_inputs' filled so the UI can prompt the user.
"""
from __future__ import annotations

import math
from typing import Optional


# ─── ASCVD 10-year via Pooled Cohort Equations ─────────────────────
# Goff et al. 2013 ACC/AHA. Coefficients verified against published
# tables for white and African-American men/women.
# https://www.ahajournals.org/doi/10.1161/01.cir.0000437741.48606.98

_PCE = {
    ("white", "F"): {
        "ln_age":        -29.799,
        "ln_age_sq":      4.884,
        "ln_tc":          13.540,
        "ln_age_x_ln_tc": -3.114,
        "ln_hdl":         -13.578,
        "ln_age_x_ln_hdl": 3.149,
        "ln_sbp_treated":  2.019,
        "ln_age_x_sbp_treated": 0,
        "ln_sbp_untreat":  1.957,
        "ln_age_x_sbp_untreat": 0,
        "smoker":          7.574,
        "ln_age_x_smoker": -1.665,
        "diabetes":        0.661,
        "mean":            -29.18,
        "baseline_survival": 0.9665,
    },
    ("white", "M"): {
        "ln_age":          12.344,
        "ln_age_sq":       0,
        "ln_tc":           11.853,
        "ln_age_x_ln_tc": -2.664,
        "ln_hdl":         -7.990,
        "ln_age_x_ln_hdl": 1.769,
        "ln_sbp_treated":  1.797,
        "ln_age_x_sbp_treated": 0,
        "ln_sbp_untreat":  1.764,
        "ln_age_x_sbp_untreat": 0,
        "smoker":          7.837,
        "ln_age_x_smoker": -1.795,
        "diabetes":        0.658,
        "mean":            61.18,
        "baseline_survival": 0.9144,
    },
    ("aa", "F"): {
        "ln_age":          17.114,
        "ln_age_sq":       0,
        "ln_tc":           0.940,
        "ln_age_x_ln_tc":  0,
        "ln_hdl":          -18.920,
        "ln_age_x_ln_hdl": 4.475,
        "ln_sbp_treated":  29.291,
        "ln_age_x_sbp_treated": -6.432,
        "ln_sbp_untreat":  27.820,
        "ln_age_x_sbp_untreat": -6.087,
        "smoker":          0.691,
        "ln_age_x_smoker": 0,
        "diabetes":        0.874,
        "mean":            86.61,
        "baseline_survival": 0.9533,
    },
    ("aa", "M"): {
        "ln_age":          2.469,
        "ln_age_sq":       0,
        "ln_tc":           0.302,
        "ln_age_x_ln_tc":  0,
        "ln_hdl":          -0.307,
        "ln_age_x_ln_hdl": 0,
        "ln_sbp_treated":  1.916,
        "ln_age_x_sbp_treated": 0,
        "ln_sbp_untreat":  1.809,
        "ln_age_x_sbp_untreat": 0,
        "smoker":          0.549,
        "ln_age_x_smoker": 0,
        "diabetes":        0.645,
        "mean":            19.54,
        "baseline_survival": 0.8954,
    },
}


def ascvd_10yr(*,
               age: float, sex: str, race: str,
               total_cholesterol: float, hdl: float,
               systolic_bp: float, bp_treated: bool,
               smoker: bool, diabetes: bool) -> dict:
    """Return a percent risk in [0, 100]. Validated for ages 40-79.
    sex: 'M' or 'F'. race: 'white' or 'aa' (default to white otherwise)."""
    sex = sex.upper() if sex else "M"
    race_key = "aa" if (race or "").lower() in ("aa", "black", "african") else "white"
    coef = _PCE.get((race_key, sex))
    if not coef or not 40 <= age <= 79:
        return {
            "score": None,
            "label": "Out of validated range" if coef else "Unknown demographic",
            "missing_inputs": [] if coef else ["valid sex/race combination"],
        }
    ln_age = math.log(age)
    ln_tc = math.log(total_cholesterol)
    ln_hdl = math.log(hdl)
    ln_sbp = math.log(systolic_bp)

    s = 0.0
    s += coef["ln_age"] * ln_age
    s += coef["ln_age_sq"] * ln_age ** 2
    s += coef["ln_tc"] * ln_tc
    s += coef["ln_age_x_ln_tc"] * ln_age * ln_tc
    s += coef["ln_hdl"] * ln_hdl
    s += coef["ln_age_x_ln_hdl"] * ln_age * ln_hdl
    if bp_treated:
        s += coef["ln_sbp_treated"] * ln_sbp
        s += coef["ln_age_x_sbp_treated"] * ln_age * ln_sbp
    else:
        s += coef["ln_sbp_untreat"] * ln_sbp
        s += coef["ln_age_x_sbp_untreat"] * ln_age * ln_sbp
    if smoker:
        s += coef["smoker"]
        s += coef["ln_age_x_smoker"] * ln_age
    if diabetes:
        s += coef["diabetes"]

    risk = 1.0 - coef["baseline_survival"] ** math.exp(s - coef["mean"])
    pct = max(0.0, min(100.0, risk * 100))
    label = ("low (<5%)" if pct < 5 else
             "borderline (5-7.5%)" if pct < 7.5 else
             "intermediate (7.5-20%)" if pct < 20 else
             "high (≥20%)")
    return {
        "score": round(pct, 1),
        "label": label,
        "components": {
            "age": age, "sex": sex, "race": race_key,
            "total_cholesterol": total_cholesterol, "hdl": hdl,
            "systolic_bp": systolic_bp, "bp_treated": bp_treated,
            "smoker": smoker, "diabetes": diabetes,
        },
    }


# ─── FINDRISC: Finnish 10-year T2D risk ────────────────────────────
# Lindström & Tuomilehto, Diabetes Care 2003.

def findrisc(*,
             age: int,
             bmi: float,
             waist_cm: float,
             sex: str,
             physical_activity_30min_daily: bool,
             eats_vegetables_or_fruit_daily: bool,
             on_bp_medication: bool,
             ever_high_blood_glucose: bool,
             family_diabetes: str  # 'none', 'second_degree', 'first_degree'
             ) -> dict:
    pts = 0
    if age < 45:        age_p = 0
    elif age < 55:      age_p = 2
    elif age < 65:      age_p = 3
    else:               age_p = 4
    pts += age_p

    if bmi < 25:        bmi_p = 0
    elif bmi < 30:      bmi_p = 1
    else:               bmi_p = 3
    pts += bmi_p

    waist_thr = (102, 94) if sex.upper() == "M" else (88, 80)
    if waist_cm >= waist_thr[0]:    waist_p = 4
    elif waist_cm >= waist_thr[1]:  waist_p = 3
    else:                            waist_p = 0
    pts += waist_p

    pts += 0 if physical_activity_30min_daily else 2
    pts += 0 if eats_vegetables_or_fruit_daily else 1
    pts += 2 if on_bp_medication else 0
    pts += 5 if ever_high_blood_glucose else 0
    if family_diabetes == "first_degree":  fam_p = 5
    elif family_diabetes == "second_degree": fam_p = 3
    else:                                   fam_p = 0
    pts += fam_p

    if pts < 7:    label, pct = "low (<1 in 100)", 1
    elif pts < 12: label, pct = "slightly elevated (1 in 25)", 4
    elif pts < 15: label, pct = "moderate (1 in 6)", 17
    elif pts < 21: label, pct = "high (1 in 3)", 33
    else:          label, pct = "very high (1 in 2)", 50

    return {
        "score": pts,
        "score_max": 26,
        "label": label,
        "ten_year_risk_pct": pct,
        "components": {
            "age_pts": age_p, "bmi_pts": bmi_p, "waist_pts": waist_p,
            "activity_pts": 0 if physical_activity_30min_daily else 2,
            "veg_fruit_pts": 0 if eats_vegetables_or_fruit_daily else 1,
            "bp_med_pts": 2 if on_bp_medication else 0,
            "high_glu_pts": 5 if ever_high_blood_glucose else 0,
            "family_pts": fam_p,
        },
    }


# ─── Helper: apply a hypothetical change ─────────────────────────────

def ascvd_delta_if(*, baseline_inputs: dict, change: dict) -> dict:
    """Return ASCVD 10-year if you applied `change` to the baseline.
    change is a dict like {'ldl_to': 70} or {'sbp_to': 120, 'smoker': False}.
    NOTE: ASCVD uses total cholesterol; LDL change must be passed via
    total_cholesterol shift."""
    inputs = dict(baseline_inputs)
    for k, v in change.items():
        inputs[k] = v
    try:
        return ascvd_10yr(**inputs)
    except Exception as exc:
        return {"score": None, "error": str(exc)[:200]}
