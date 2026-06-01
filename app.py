
# =========================================================
# 3-point mDI_woI calculator
# G0, G60, G120 only
# Streamlit app
# =========================================================

import numpy as np
import pandas as pd
import streamlit as st

import model_core


APP_TITLE = "3-point mDI_woI Calculator"
APP_VERSION = "1.0"


def calculate_diwoi_3p(g0, g60, g120):
    """
    Calculate 3-point mDI_woI using glucose values at 0, 60, and 120 min.
    G30 and G90 are passed as missing values.
    """

    weights_G_3p = np.array([1, 1, 1, 1, 1], dtype=float)

    res = model_core.estimate_clamp_di_from_glucose(
        g0=float(g0),
        g30=np.nan,
        g60=float(g60),
        g90=np.nan,
        g120=float(g120),
        weights_G=weights_G_3p
    )

    fit = res["fit_res"]
    mdi_raw = res["mDI_woI"]

    # raw値が mL/mU/min の場合、
    # 「×10^-4 mL/mU/min」表記の数値は raw / 10^-4 = raw * 10000
    mdi_x10minus4 = mdi_raw * 1e4 if np.isfinite(mdi_raw) else np.nan

    return {
        "mDI_woI3p_raw": mdi_raw,
        "mDI_woI3p_x10^-4_mL_per_mU_per_min": mdi_x10minus4,
        "Clamp_DI_pred_linear": res["Clamp_DI_pred_linear"],
        "Clamp_DI_pred_loglog": res["Clamp_DI_pred_loglog"],
        "sigma_3p": fit["sigma"],
        "si_3p": fit["si"],
        "WRSS_3p": fit["WRSS"],
        "RSQ_3p": fit["RSQ"],
        "AIC_3p": fit["AIC"],
        "fit_status": res["fit_status"],
        "messages": " | ".join(res["messages"]) if res["messages"] else ""
    }


st.set_page_config(page_title=f"{APP_TITLE} v{APP_VERSION}", layout="wide")

st.title(APP_TITLE)
st.caption(f"Version {APP_VERSION}")

st.markdown(
    """
This calculator estimates **mDI_woI3p** from three OGTT glucose values:
**0, 60, and 120 min**.

The model internally treats 30-min and 90-min glucose values as missing.
"""
)

tab_single, tab_batch = st.tabs(["Single case", "Batch Excel/CSV"])


with tab_single:
    st.subheader("Single-case calculation")

    col1, col2, col3 = st.columns(3)

    with col1:
        g0 = st.number_input(
            "Glucose 0 min, G0 (mg/dL)",
            min_value=1.0, max_value=600.0, value=90.0, step=1.0
        )
    with col2:
        g60 = st.number_input(
            "Glucose 60 min, G60 (mg/dL)",
            min_value=1.0, max_value=600.0, value=160.0, step=1.0
        )
    with col3:
        g120 = st.number_input(
            "Glucose 120 min, G120 (mg/dL)",
            min_value=1.0, max_value=600.0, value=120.0, step=1.0
        )

    if st.button("Calculate mDI_woI3p"):
        try:
            out = calculate_diwoi_3p(g0, g60, g120)

            st.success("Calculation completed.")

            c1, c2 = st.columns(2)
            c1.metric("mDI_woI3p raw", f"{out['mDI_woI3p_raw']:.8g}")
            c2.metric(
                "mDI_woI3p (×10^-4 mL/mU/min)",
                f"{out['mDI_woI3p_x10^-4_mL_per_mU_per_min']:.4f}"
            )

            st.write("Detailed results")
            st.dataframe(pd.DataFrame([out]), use_container_width=True)

        except Exception as e:
            st.error(f"Calculation failed: {e}")


with tab_batch:
    st.subheader("Batch calculation from Excel or CSV")

    st.markdown(
        """
Required columns:

- `CaseID`
- `G0`
- `G60`
- `G120`
"""
    )

    uploaded_file = st.file_uploader(
        "Upload Excel or CSV file",
        type=["xlsx", "xls", "csv"]
    )

    if uploaded_file is not None:
        try:
            if uploaded_file.name.lower().endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

            st.write("Input preview")
            st.dataframe(df.head(), use_container_width=True)

            required_cols = ["CaseID", "G0", "G60", "G120"]
            missing_cols = [c for c in required_cols if c not in df.columns]

            if missing_cols:
                st.error(f"Missing required columns: {missing_cols}")
            else:
                if st.button("Run batch calculation"):
                    rows = []

                    progress = st.progress(0)
                    status_text = st.empty()

                    for i, row in df.iterrows():
                        case_id = row["CaseID"]
                        status_text.text(f"Calculating {i+1}/{len(df)}: {case_id}")

                        try:
                            out = calculate_diwoi_3p(row["G0"], row["G60"], row["G120"])
                            rows.append({
                                "CaseID": case_id,
                                "G0": row["G0"],
                                "G60": row["G60"],
                                "G120": row["G120"],
                                **out
                            })
                        except Exception as e:
                            rows.append({
                                "CaseID": case_id,
                                "G0": row.get("G0", np.nan),
                                "G60": row.get("G60", np.nan),
                                "G120": row.get("G120", np.nan),
                                "mDI_woI3p_raw": np.nan,
                                "mDI_woI3p_x10^-4_mL_per_mU_per_min": np.nan,
                                "Clamp_DI_pred_linear": np.nan,
                                "Clamp_DI_pred_loglog": np.nan,
                                "sigma_3p": np.nan,
                                "si_3p": np.nan,
                                "WRSS_3p": np.nan,
                                "RSQ_3p": np.nan,
                                "AIC_3p": np.nan,
                                "fit_status": "error",
                                "messages": str(e)
                            })

                        progress.progress((i + 1) / len(df))

                    result_df = pd.DataFrame(rows)

                    st.success("Batch calculation completed.")
                    st.dataframe(result_df, use_container_width=True)

                    csv = result_df.to_csv(index=False).encode("utf-8-sig")
                    st.download_button(
                        label="Download results as CSV",
                        data=csv,
                        file_name="DIwoI_3point_results.csv",
                        mime="text/csv"
                    )

        except Exception as e:
            st.error(f"File reading failed: {e}")


st.divider()

st.caption(
    "Note: mDI_woI3p raw is multiplied by 10,000 to display the value in units of ×10^-4 mL/mU/min."
)
