
# 3-point mDI_woI Calculator

This Streamlit app calculates mDI_woI3p using OGTT glucose values at 0, 60, and 120 minutes.

## Required files

- app.py
- model_core.py
- requirements.txt

## Local launch

```bash
cd DIwoI_3point_calculator
pip install -r requirements.txt
streamlit run app.py
```

## Input columns for batch mode

- CaseID
- G0
- G60
- G120

## Output

- mDI_woI3p_raw
- mDI_woI3p_x10^-4_mL_per_mU_per_min
- sigma_3p
- si_3p
- WRSS_3p
- RSQ_3p
- AIC_3p
