# =============================================================================
# SHIELD - SME Health Indicator and Evaluator for Loan Decision
# app.py - Main Streamlit Application
# =============================================================================

import io
import streamlit as st
import pandas as pd
import numpy as np
import joblib
import shap
import matplotlib
import matplotlib.pyplot as plt
import warnings

warnings.filterwarnings("ignore")

# =============================================================================
# PAGE CONFIGURATION
# Must be the first Streamlit call in the script.
# =============================================================================
st.set_page_config(
    page_title="SHIELD | SME Risk Evaluator",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =============================================================================
# GLOBAL CONSTANTS
# Exact feature names as they exist in the processed CSVs (with leading spaces).
# =============================================================================
FEATURE_NAMES = [
    ' ROA(C) before interest and depreciation before interest',
    ' ROA(A) before interest and % after tax',
    ' Continuous interest rate (after tax)',
    ' Net Value Per Share (B)',
    ' Net Value Per Share (A)',
    ' Net Value Per Share (C)',
    ' Persistent EPS in the Last Four Seasons',
    ' Per Share Net profit before tax',
    ' Interest Expense Ratio',
    ' Debt ratio %',
    ' Net worth/Assets',
    ' Borrowing dependency',
    ' Net profit before tax/Paid-in capital',
    ' Retained Earnings to Total Assets',
    ' Total income/Total expense',
    ' Net Income to Total Assets',
    " Net Income to Stockholder's Equity",
    ' Liability to Equity',
    ' Interest Coverage Ratio (Interest expense to EBIT)',
    ' Equity to Liability',
]

# Human-readable display labels for the input form (same order as FEATURE_NAMES)
FEATURE_LABELS = [
    "ROA(C) — Before Interest & Depreciation Before Interest",
    "ROA(A) — Before Interest & % After Tax",
    "Continuous Interest Rate (After Tax)",
    "Net Value Per Share (B)",
    "Net Value Per Share (A)",
    "Net Value Per Share (C)",
    "Persistent EPS in the Last Four Seasons",
    "Per Share Net Profit Before Tax",
    "Interest Expense Ratio",
    "Debt Ratio %",
    "Net Worth / Assets",
    "Borrowing Dependency",
    "Net Profit Before Tax / Paid-in Capital",
    "Retained Earnings to Total Assets",
    "Total Income / Total Expense",
    "Net Income to Total Assets",
    "Net Income to Stockholder's Equity",
    "Liability to Equity",
    "Interest Coverage Ratio (Interest Expense to EBIT)",
    "Equity to Liability",
]

# Median defaults extracted from df_cleaned_original.csv
MEDIAN_DEFAULTS = {
    ' ROA(C) before interest and depreciation before interest':  0.4724507510,
    ' ROA(A) before interest and % after tax':                   0.5320553249,
    ' Continuous interest rate (after tax)':                     0.7815367064,
    ' Net Value Per Share (B)':                                  0.1732333235,
    ' Net Value Per Share (A)':                                  0.1732333235,
    ' Net Value Per Share (C)':                                  0.1734018794,
    ' Persistent EPS in the Last Four Seasons':                  0.2115911884,
    ' Per Share Net profit before tax':                          0.1689343463,
    ' Interest Expense Ratio':                                   0.6306122519,
    ' Debt ratio %':                                             0.1561205497,
    ' Net worth/Assets':                                         0.8438794503,
    ' Borrowing dependency':                                     0.3774359165,
    ' Net profit before tax/Paid-in capital':                    0.1679541179,
    ' Retained Earnings to Total Assets':                        0.9291504440,
    ' Total income/Total expense':                               0.0022130871,
    ' Net Income to Total Assets':                               0.7934734606,
    " Net Income to Stockholder's Equity":                       0.8399382414,
    ' Liability to Equity':                                      0.2819822002,
    ' Interest Coverage Ratio (Interest expense to EBIT)':       0.5651583958,
    ' Equity to Liability':                                      0.0232401213,
}

# =============================================================================
# TEST PROFILES
# Profile A: lowest P(default) among true Class 0 in X_test → 0.007%
# Profile B: highest P(default) among true Class 1 in X_test → 99.8%
# =============================================================================
PROFILE_A_HEALTHY = {
    ' ROA(C) before interest and depreciation before interest':  0.5101990755,
    ' ROA(A) before interest and % after tax':                   0.5645483124,
    ' Continuous interest rate (after tax)':                     0.7811546026,
    ' Net Value Per Share (B)':                                  0.1943670407,
    ' Net Value Per Share (A)':                                  0.1942756119,
    ' Net Value Per Share (C)':                                  0.1943248059,
    ' Persistent EPS in the Last Four Seasons':                  0.2327743732,
    ' Per Share Net profit before tax':                          0.1884357433,
    ' Interest Expense Ratio':                                   0.6313819785,
    ' Debt ratio %':                                             0.1106172146,
    ' Net worth/Assets':                                         0.8893827854,
    ' Borrowing dependency':                                     0.3739696103,
    ' Net profit before tax/Paid-in capital':                    0.1863039832,
    ' Retained Earnings to Total Assets':                        0.9361581868,
    ' Total income/Total expense':                               0.0024427588,
    ' Net Income to Total Assets':                               0.8111407213,
    " Net Income to Stockholder's Equity":                       0.8409864856,
    ' Liability to Equity':                                      0.2797485083,
    ' Interest Coverage Ratio (Interest expense to EBIT)':       0.5657041165,
    ' Equity to Liability':                                      0.0488247804,
}

PROFILE_B_DISTRESSED = {
    ' ROA(C) before interest and depreciation before interest':  0.4183976458,
    ' ROA(A) before interest and % after tax':                   0.4657591781,
    ' Continuous interest rate (after tax)':                     0.7811561521,
    ' Net Value Per Share (B)':                                  0.1633479032,
    ' Net Value Per Share (A)':                                  0.1628020119,
    ' Net Value Per Share (C)':                                  0.1630462265,
    ' Persistent EPS in the Last Four Seasons':                  0.1923470309,
    ' Per Share Net profit before tax':                          0.1519647785,
    ' Interest Expense Ratio':                                   0.6306522965,
    ' Debt ratio %':                                             0.1788368463,
    ' Net worth/Assets':                                         0.8211631537,
    ' Borrowing dependency':                                     0.3844244754,
    ' Net profit before tax/Paid-in capital':                    0.1519429839,
    ' Retained Earnings to Total Assets':                        0.9067963727,
    ' Total income/Total expense':                               0.0021013057,
    ' Net Income to Total Assets':                               0.7413578792,
    " Net Income to Stockholder's Equity":                       0.8342608756,
    ' Liability to Equity':                                      0.2865768249,
    ' Interest Coverage Ratio (Interest expense to EBIT)':       0.5643454621,
    ' Equity to Liability':                                      0.0227042267,
}

# Maps dropdown label → values dict (None = manual, use MEDIAN_DEFAULTS)
PROFILES = {
    "✏️  Manual Input":                         None,
    "🟢  Profile A: Healthy SME (Low Risk)":    PROFILE_A_HEALTHY,
    "🔴  Profile B: Distressed SME (High Risk)": PROFILE_B_DISTRESSED,
}

# =============================================================================
# CUSTOM CSS — Dark Theme
# =============================================================================
st.markdown("""
<style>
    /* ---- Base & Background ---- */
    .stApp {
        background-color: #0d1117;
        color: #e6edf3;
    }
    section[data-testid="stSidebar"] {
        background-color: #161b22;
    }

    /* ---- Header Banner ---- */
    .shield-header {
        background: linear-gradient(135deg, #1a1f35 0%, #0d1117 60%, #1a1f35 100%);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 28px 36px;
        margin-bottom: 28px;
        text-align: center;
    }
    .shield-header h1 {
        font-size: 2.6rem;
        font-weight: 800;
        background: linear-gradient(90deg, #58a6ff, #a371f7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    .shield-header p {
        color: #8b949e;
        font-size: 1.0rem;
        margin-top: 6px;
    }

    /* ---- Section Cards ---- */
    .card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 20px 24px;
        margin-bottom: 16px;
    }
    .card-title {
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: #8b949e;
        margin-bottom: 14px;
    }

    /* ---- Risk Score Display ---- */
    .risk-score-value {
        font-size: 5rem;
        font-weight: 900;
        line-height: 1;
        text-align: center;
    }
    .risk-label {
        font-size: 1.2rem;
        font-weight: 700;
        text-align: center;
        border-radius: 8px;
        padding: 8px 16px;
        margin-top: 12px;
        display: inline-block;
        width: 100%;
    }
    .label-high {
        background-color: rgba(248, 81, 73, 0.15);
        color: #f85149;
        border: 1px solid #f85149;
    }
    .label-low {
        background-color: rgba(63, 185, 80, 0.15);
        color: #3fb950;
        border: 1px solid #3fb950;
    }
    .score-high { color: #f85149; }
    .score-low  { color: #3fb950; }

    /* ---- Progress Bar ---- */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #3fb950, #f0c000, #f85149);
    }

    /* ---- Streamlit Overrides ---- */
    div[data-testid="stNumberInput"] label,
    div[data-testid="stTextInput"] label {
        color: #c9d1d9 !important;
        font-size: 0.82rem !important;
    }
    .stButton > button {
        background: linear-gradient(135deg, #238636, #2ea043);
        color: #ffffff;
        border: none;
        border-radius: 8px;
        font-size: 1rem;
        font-weight: 700;
        padding: 14px 28px;
        width: 100%;
        transition: opacity 0.2s;
        letter-spacing: 0.05em;
    }
    .stButton > button:hover {
        opacity: 0.85;
    }
    /* Download / secondary button style */
    .stDownloadButton > button {
        background: transparent;
        color: #58a6ff;
        border: 1px solid #30363d;
        border-radius: 8px;
        font-size: 0.85rem;
        font-weight: 600;
        padding: 8px 16px;
        width: 100%;
        transition: border-color 0.2s, color 0.2s;
    }
    .stDownloadButton > button:hover {
        border-color: #58a6ff;
        color: #a5d6ff;
    }
    h2, h3 {
        color: #e6edf3;
    }
    hr {
        border-color: #30363d;
    }
    .advisory-box {
        background-color: #0d1117;
        border-left: 3px solid #a371f7;
        border-radius: 0 8px 8px 0;
        padding: 14px 18px;
        margin-bottom: 10px;
        font-size: 0.88rem;
        color: #c9d1d9;
        line-height: 1.6;
    }
    .advisory-title {
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: #a371f7;
        margin-bottom: 6px;
    }
    /* File uploader dark styling */
    [data-testid="stFileUploader"] {
        background-color: #161b22;
        border: 1px dashed #30363d;
        border-radius: 8px;
        padding: 4px;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: #58a6ff;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# CACHED RESOURCE LOADERS
# =============================================================================

@st.cache_resource(show_spinner="Loading SHIELD model...")
def load_model():
    return joblib.load("model/xgb_shield_model.joblib")


@st.cache_resource(show_spinner="Initialising SHAP explainer...")
def load_shap_explainer(_model):
    return shap.TreeExplainer(_model, feature_perturbation="tree_path_dependent")


# =============================================================================
# CSV TEMPLATE GENERATOR
# =============================================================================

@st.cache_data
def build_csv_template() -> bytes:
    """Return a blank CSV template with all 20 feature columns as UTF-8 bytes."""
    template_df = pd.DataFrame(columns=FEATURE_NAMES)
    # Add one blank row so the user can see the column layout clearly
    template_df.loc[0] = ["" for _ in FEATURE_NAMES]
    return template_df.to_csv(index=False).encode("utf-8")


# =============================================================================
# SESSION STATE — write all 20 field values atomically
# =============================================================================

def _apply_values(values_dict: dict) -> None:
    """Push a feature→value dict into session_state for all 20 number inputs."""
    for feat in FEATURE_NAMES:
        st.session_state[f"input_{feat}"] = float(round(values_dict[feat], 6))


def _init_defaults() -> None:
    """Seed session_state with MEDIAN_DEFAULTS on first run only."""
    if "_shield_initialised" not in st.session_state:
        _apply_values(MEDIAN_DEFAULTS)
        st.session_state["_shield_initialised"] = True
        st.session_state["_last_profile"] = list(PROFILES.keys())[0]
        st.session_state["_last_upload_id"] = None
        st.session_state["_input_source"] = "manual"   # "manual" | "profile" | "upload"
        st.session_state["_auto_evaluate"] = False


# =============================================================================
# FILE UPLOAD PARSER
# =============================================================================

def parse_uploaded_file(uploaded_file) -> dict | None:
    """
    Read the first data row from a CSV or XLSX file.
    Returns a feature→value dict, or None on failure (error shown inline).
    """
    try:
        fname = uploaded_file.name.lower()
        if fname.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file, nrows=1)
        else:
            df = pd.read_csv(uploaded_file, nrows=1)
    except Exception as exc:
        st.error(f"Could not read file: {exc}")
        return None

    if df.empty:
        st.error("The uploaded file has no data rows.")
        return None

    # Check that all required columns are present
    missing = [f for f in FEATURE_NAMES if f not in df.columns]
    if missing:
        st.error(
            f"Missing {len(missing)} required column(s) in your file. "
            "Download the template to see the exact column headers needed."
        )
        with st.expander("Show missing columns"):
            st.code("\n".join(missing))
        return None

    row = df.iloc[0]
    try:
        values = {feat: float(row[feat]) for feat in FEATURE_NAMES}
    except (ValueError, TypeError) as exc:
        st.error(f"Non-numeric value found in uploaded data: {exc}")
        return None

    return values


# =============================================================================
# SHAP WATERFALL PLOT
# =============================================================================

def generate_shap_waterfall(explainer, input_df: pd.DataFrame):
    shap_values_obj = explainer(input_df.values)

    if shap_values_obj.values.ndim == 3:
        sv       = shap_values_obj.values[0, :, 1]
        base_val = shap_values_obj.base_values[0, 1]
    else:
        sv       = shap_values_obj.values[0]
        base_val = shap_values_obj.base_values[0]

    explanation = shap.Explanation(
        values=sv,
        base_values=base_val,
        data=input_df.values[0],
        feature_names=list(FEATURE_LABELS),
    )

    matplotlib.rcParams.update({
        "figure.facecolor": "#161b22",
        "axes.facecolor":   "#161b22",
        "axes.edgecolor":   "#30363d",
        "axes.labelcolor":  "#c9d1d9",
        "xtick.color":      "#8b949e",
        "ytick.color":      "#c9d1d9",
        "text.color":       "#c9d1d9",
        "grid.color":       "#21262d",
    })

    fig, _ = plt.subplots(figsize=(7, 6))
    shap.plots.waterfall(explanation, max_display=10, show=False)
    fig = plt.gcf()
    fig.patch.set_facecolor("#161b22")
    for ax_ in fig.get_axes():
        ax_.set_facecolor("#161b22")
    plt.tight_layout()

    return fig, sv, base_val


# =============================================================================
# ADVISORY REPORT
# =============================================================================

def generate_advisory_report(shap_values: np.ndarray, prob: float) -> str:
    pairs          = list(zip(FEATURE_LABELS, shap_values))
    risk_drivers   = sorted([(l, v) for l, v in pairs if v > 0], key=lambda x: x[1], reverse=True)
    health_factors = sorted([(l, v) for l, v in pairs if v < 0], key=lambda x: x[1])

    lines = []

    if prob >= 0.70:
        tone = "**Critical Risk Detected.** The model indicates a very high likelihood of financial distress."
    elif prob >= 0.50:
        tone = "**Elevated Risk Detected.** The SME exhibits several financial vulnerabilities."
    elif prob >= 0.30:
        tone = "**Moderate Risk.** The SME shows some concerning signals but maintains core financial health."
    else:
        tone = "**Low Risk.** The SME appears financially healthy with strong fundamental indicators."

    lines.append(tone)
    lines.append("")

    if risk_drivers:
        lines.append("**Key Risk Drivers (pushing probability of default higher):**")
        for label, val in risk_drivers[:3]:
            lines.append(f"- **{label}** contributed +{val:.4f} to the risk score, indicating weakness in this area.")
        lines.append("")

    if health_factors:
        lines.append("**Protective Factors (pushing probability of default lower):**")
        for label, val in health_factors[:3]:
            lines.append(f"- **{label}** contributed {val:.4f}, acting as a financial buffer.")
        lines.append("")

    lines.append("**Recommendation:**")
    if prob >= 0.50:
        lines.append(
            "Loan approval should be approached with caution. A detailed due-diligence review of "
            "the flagged risk drivers is strongly advised. Consider requesting collateral or "
            "imposing covenant-based conditions before disbursement."
        )
    else:
        lines.append(
            "The financial profile supports a favourable loan consideration. Standard monitoring "
            "of the identified risk drivers is recommended throughout the loan tenure."
        )

    return "\n".join(lines)


# =============================================================================
# MAIN APPLICATION
# =============================================================================

def main():
    model    = load_model()
    explainer = load_shap_explainer(model)

    # Seed defaults once
    _init_defaults()

    # ---- Header ----
    st.markdown("""
    <div class="shield-header">
        <h1>🛡️ SHIELD</h1>
        <p>SME Health Indicator and Evaluator for Loan Decision &nbsp;|&nbsp; Powered by Random Forest + SHAP Explainability</p>
    </div>
    """, unsafe_allow_html=True)

    col_input, col_result, col_xai = st.columns([1.1, 0.9, 1.1], gap="large")

    # =========================================================================
    # LEFT COLUMN — Input Controls
    # =========================================================================
    with col_input:
        st.markdown('<div class="card-title">📋 Company Financial Inputs</div>', unsafe_allow_html=True)

        # -----------------------------------------------------------------
        # 1. PROFILE SELECTOR
        # -----------------------------------------------------------------
        selected_profile = st.selectbox(
            label="Select SME Test Profile",
            options=list(PROFILES.keys()),
            index=0,
            help="Choose a preset to auto-fill all fields, or keep Manual Input.",
            key="profile_selector",
        )

        # When the profile selection changes, write values and rerun
        if st.session_state.get("_last_profile") != selected_profile:
            st.session_state["_last_profile"] = selected_profile
            profile_values = PROFILES[selected_profile]
            source_values  = profile_values if profile_values is not None else MEDIAN_DEFAULTS
            _apply_values(source_values)
            st.session_state["_input_source"]   = "manual" if profile_values is None else "profile"
            st.session_state["_auto_evaluate"]  = profile_values is not None
            st.rerun()

        # -----------------------------------------------------------------
        # 2. FILE UPLOADER + TEMPLATE DOWNLOAD
        # -----------------------------------------------------------------
        st.markdown(
            '<div style="font-size:0.78rem; font-weight:600; letter-spacing:0.08em; '
            'text-transform:uppercase; color:#8b949e; margin-top:12px; margin-bottom:6px;">'
            '📂 Upload SME Data File</div>',
            unsafe_allow_html=True,
        )

        # Template download — sits above the uploader as a helper action
        st.download_button(
            label="⬇️  Download CSV Template",
            data=build_csv_template(),
            file_name="SHIELD_input_template.csv",
            mime="text/csv",
            help="Download a blank CSV with all 20 required column headers.",
            use_container_width=True,
        )

        uploaded_file = st.file_uploader(
            label="Upload a filled CSV or XLSX file",
            type=["csv", "xlsx"],
            accept_multiple_files=False,
            help="First data row will be used to auto-populate the 20 input fields below.",
            label_visibility="collapsed",
        )

        # When a new file is uploaded, parse it and inject into session_state
        upload_id = id(uploaded_file) if uploaded_file is not None else None
        if upload_id is not None and upload_id != st.session_state.get("_last_upload_id"):
            st.session_state["_last_upload_id"] = upload_id
            parsed = parse_uploaded_file(uploaded_file)
            if parsed is not None:
                _apply_values(parsed)
                st.session_state["_input_source"]  = "upload"
                st.session_state["_auto_evaluate"] = True
                # Reset profile selector back to Manual so it doesn't conflict
                st.session_state["profile_selector"] = list(PROFILES.keys())[0]
                st.session_state["_last_profile"]    = list(PROFILES.keys())[0]
                st.rerun()

        # -----------------------------------------------------------------
        # Source badge
        # -----------------------------------------------------------------
        source = st.session_state.get("_input_source", "manual")
        if source == "upload":
            st.markdown(
                '<div style="font-size:0.80rem; color:#58a6ff; background:rgba(88,166,255,0.07); '
                'border-radius:6px; padding:6px 10px; margin:6px 0;">'
                '📂 File uploaded — fields populated from first data row.</div>',
                unsafe_allow_html=True,
            )
        elif source == "profile":
            badge_color = "#3fb950" if "Healthy" in selected_profile else "#f85149"
            st.markdown(
                f'<div style="font-size:0.80rem; color:{badge_color}; '
                f'background:rgba(255,255,255,0.04); border-radius:6px; padding:6px 10px; margin:6px 0;">'
                f'✔ Preset loaded — you can still edit any field below.</div>',
                unsafe_allow_html=True,
            )
        else:
            st.caption("Enter the 20 key accounting metrics for the SME. Defaults are industry medians.")

        st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)

        # -----------------------------------------------------------------
        # 3. NUMBER INPUTS — driven entirely by session_state
        #    No value= argument here; session_state keys are the single
        #    source of truth for every field.
        # -----------------------------------------------------------------
        for feat, label in zip(FEATURE_NAMES, FEATURE_LABELS):
            st.number_input(
                label=label,
                format="%.6f",
                step=0.0001,
                key=f"input_{feat}",
            )

        # -----------------------------------------------------------------
        # 4. EVALUATE BUTTON
        # -----------------------------------------------------------------
        evaluate_clicked = st.button("⚡ Evaluate Risk", use_container_width=True)

    # =========================================================================
    # Decide whether to render results
    # auto_evaluate is set True after a profile/upload load so results appear
    # immediately without the user having to click the button.
    # =========================================================================
    should_evaluate = evaluate_clicked or st.session_state.get("_auto_evaluate", False)

    # Reset the auto-evaluate flag so it only fires once per load
    if st.session_state.get("_auto_evaluate"):
        st.session_state["_auto_evaluate"] = False

    if should_evaluate:
        # Collect current field values from session_state
        input_values = {feat: st.session_state[f"input_{feat}"] for feat in FEATURE_NAMES}
        input_df     = pd.DataFrame([input_values])[FEATURE_NAMES]

        prob_bankrupt = float(model.predict_proba(input_df)[0][1])
        is_high_risk  = prob_bankrupt >= 0.50

        with st.spinner("Computing SHAP explanations..."):
            shap_fig, shap_vals, base_val = generate_shap_waterfall(explainer, input_df)

        advisory_text = generate_advisory_report(shap_vals, prob_bankrupt)

        # =================================================================
        # MIDDLE COLUMN — Risk Assessment
        # =================================================================
        with col_result:
            st.markdown('<div class="card-title">🎯 Risk Assessment</div>', unsafe_allow_html=True)

            score_class = "score-high" if is_high_risk else "score-low"
            label_class = "label-high" if is_high_risk else "label-low"
            label_text  = "⚠️ Financially Distressed — HIGH RISK" if is_high_risk else "✅ Financially Healthy — LOW RISK"
            emoji        = "🔴" if is_high_risk else "🟢"

            st.markdown(f"""
            <div style="text-align:center; padding: 20px 0;">
                <div style="font-size:0.85rem; color:#8b949e; letter-spacing:0.1em;
                            text-transform:uppercase; margin-bottom:8px;">
                    Probability of Default
                </div>
                <div class="risk-score-value {score_class}">
                    {emoji} {prob_bankrupt:.1%}
                </div>
                <div class="risk-label {label_class}">
                    {label_text}
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("**Risk Gauge**")
            st.progress(prob_bankrupt)
            st.caption(
                f"SHAP base value: {base_val:.4f}"
            )

            st.divider()

            st.markdown("**Model Confidence Breakdown**")
            prob_healthy = 1 - prob_bankrupt
            c1, c2 = st.columns(2)
            with c1:
                st.metric("🟢 Healthy",    f"{prob_healthy:.1%}")
            with c2:
                st.metric("🔴 Distressed", f"{prob_bankrupt:.1%}")

            st.divider()

            st.markdown("**Input Snapshot (Top 5 by Risk Impact)**")
            top5_idx = np.argsort(np.abs(shap_vals))[::-1][:5]
            st.dataframe(
                pd.DataFrame({
                    "Metric": [FEATURE_LABELS[i] for i in top5_idx],
                    "Value":  [round(float(input_df.iloc[0, i]), 4) for i in top5_idx],
                }),
                use_container_width=True,
                hide_index=True,
            )

        # =================================================================
        # RIGHT COLUMN — SHAP + Advisory
        # =================================================================
        with col_xai:
            st.markdown('<div class="card-title">🔍 Explainability & Advisory</div>', unsafe_allow_html=True)

            st.markdown("**SHAP Feature Contributions (Top 10)**")
            st.caption("Red bars push toward default; blue bars push toward health.")
            st.pyplot(shap_fig, use_container_width=True)
            plt.close(shap_fig)

            st.divider()

            st.markdown("**📄 AI Advisory Report**")
            for line in advisory_text.split("\n"):
                if line.strip():
                    st.markdown(
                        f'<div class="advisory-box">{line}</div>',
                        unsafe_allow_html=True,
                    )

    else:
        # ---- Idle placeholders ----
        with col_result:
            st.markdown('<div class="card-title">🎯 Risk Assessment</div>', unsafe_allow_html=True)
            st.markdown("""
            <div style="text-align:center; padding:60px 20px; color:#8b949e;">
                <div style="font-size:3rem;">🛡️</div>
                <div style="margin-top:12px; font-size:1rem;">
                    Fill in the financial metrics on the left<br>
                    and click <strong>Evaluate Risk</strong> to begin.
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_xai:
            st.markdown('<div class="card-title">🔍 Explainability & Advisory</div>', unsafe_allow_html=True)
            st.markdown("""
            <div style="text-align:center; padding:60px 20px; color:#8b949e;">
                <div style="font-size:3rem;">📊</div>
                <div style="margin-top:12px; font-size:1rem;">
                    SHAP explanations and the advisory report<br>
                    will appear here after evaluation.
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ---- Footer ----
    st.markdown("---")
    st.markdown(
        "<div style='text-align:center; color:#484f58; font-size:0.78rem;'>"
        "SHIELD · Final Year Project · Random Forest + SHAP · For academic use only"
        "</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
