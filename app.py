import streamlit as st
import pandas as pd

# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="Income Tax Calculator | Old vs New Regime",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: #F8FAFC;
        border-radius: 10px;
        padding: 15px 20px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .winner-new {
        background: linear-gradient(135deg, #ECFDF5 0%, #D1FAE5 100%);
        border: 2px solid #10B981;
        border-radius: 12px;
        padding: 18px 24px;
        margin-bottom: 20px;
    }
    .winner-old {
        background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%);
        border: 2px solid #3B82F6;
        border-radius: 12px;
        padding: 18px 24px;
        margin-bottom: 20px;
    }
    .winner-tie {
        background: linear-gradient(135deg, #F3F4F6 0%, #E5E7EB 100%);
        border: 2px solid #6B7280;
        border-radius: 12px;
        padding: 18px 24px;
        margin-bottom: 20px;
    }
    .head-badge {
        display: inline-block;
        font-weight: 600;
        font-size: 0.85rem;
        padding: 3px 8px;
        border-radius: 6px;
        margin-right: 6px;
        background-color: #E0E7FF;
        color: #3730A3;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# Tax Calculation Engine
# ---------------------------------------------------------

def calculate_new_regime_tax(taxable_income):
    """
    Computes tax under the New Tax Regime (Section 115BAC)
    Applicable for FY 2024-25 / FY 2025-26 (Budget 2024 revised slabs):
      - Up to ₹3,00,000: Nil
      - ₹3,00,001 - ₹7,00,000: 5%
      - ₹7,00,001 - ₹10,00,000: 10%
      - ₹10,00,001 - ₹12,00,000: 15%
      - ₹12,00,001 - ₹15,00,000: 20%
      - Above ₹15,00,000: 30%
    Rebate u/s 87A: Full rebate if taxable income <= ₹7,00,000 (tax = 0).
    Marginal relief for income marginally above ₹7,00,000.
    """
    if taxable_income <= 0:
        return 0, 0, 0, 0, 0, []

    slabs = [
        ("₹0 - ₹3,00,000", 300000, 0.00),
        ("₹3,00,001 - ₹7,00,000", 400000, 0.05),
        ("₹7,00,001 - ₹10,00,000", 300000, 0.10),
        ("₹10,00,001 - ₹12,00,000", 200000, 0.15),
        ("₹12,00,001 - ₹15,00,000", 300000, 0.20),
        ("Above ₹15,00,000", float("inf"), 0.30)
    ]

    breakdown = []
    rem_income = taxable_income
    basic_tax = 0.0

    for label, span, rate in slabs:
        if rem_income <= 0:
            breakdown.append({"Slab": label, "Rate": f"{int(rate*100)}%", "Taxable Amount": 0.0, "Tax": 0.0})
            continue

        taxable_in_slab = min(rem_income, span)
        slab_tax = taxable_in_slab * rate
        basic_tax += slab_tax
        rem_income -= taxable_in_slab

        breakdown.append({
            "Slab": label,
            "Rate": f"{int(rate*100)}%",
            "Taxable Amount": taxable_in_slab,
            "Tax": slab_tax
        })

    # Section 87A Rebate & Marginal Relief (New Regime)
    rebate = 0.0
    if taxable_income <= 700000:
        rebate = basic_tax
        tax_after_rebate = 0.0
    else:
        # Marginal relief: Tax payable cannot exceed (Taxable Income - 7,00,000)
        excess_over_7l = taxable_income - 700000
        if basic_tax > excess_over_7l:
            marginal_relief = basic_tax - excess_over_7l
            rebate = marginal_relief
            tax_after_rebate = excess_over_7l
        else:
            tax_after_rebate = basic_tax

    # Surcharge (New Regime: Capped at 25%)
    surcharge = 0.0
    if taxable_income > 20000000:
        surcharge = tax_after_rebate * 0.25
    elif taxable_income > 10000000:
        surcharge = tax_after_rebate * 0.15
    elif taxable_income > 5000000:
        surcharge = tax_after_rebate * 0.10

    # Health & Education Cess @ 4%
    tax_plus_surcharge = tax_after_rebate + surcharge
    cess = tax_plus_surcharge * 0.04
    total_tax = tax_plus_surcharge + cess

    return basic_tax, rebate, surcharge, cess, total_tax, breakdown


def calculate_old_regime_tax(taxable_income, age_group="General (< 60 yrs)"):
    """
    Computes tax under Old Tax Regime with slabs based on age:
      - General (< 60 yrs): 2.5L Nil, 2.5-5L 5%, 5-10L 20%, >10L 30%
      - Senior Citizen (60-80 yrs): 3L Nil, 3-5L 5%, 5-10L 20%, >10L 30%
      - Super Senior (80+ yrs): 5L Nil, 5-10L 20%, >10L 30%
    Rebate u/s 87A: Full rebate up to ₹12,500 if taxable income <= ₹5,00,000.
    """
    if taxable_income <= 0:
        return 0, 0, 0, 0, 0, []

    if age_group == "Super Senior Citizen (80+ yrs)":
        slabs = [
            ("₹0 - ₹5,00,000", 500000, 0.00),
            ("₹5,00,001 - ₹10,00,000", 500000, 0.20),
            ("Above ₹10,00,000", float("inf"), 0.30)
        ]
    elif age_group == "Senior Citizen (60 - 80 yrs)":
        slabs = [
            ("₹0 - ₹3,00,000", 300000, 0.00),
            ("₹3,00,001 - ₹5,00,000", 200000, 0.05),
            ("₹5,00,001 - ₹10,00,000", 500000, 0.20),
            ("Above ₹10,00,000", float("inf"), 0.30)
        ]
    else:
        slabs = [
            ("₹0 - ₹2,50,000", 250000, 0.00),
            ("₹2,50,001 - ₹5,00,000", 250000, 0.05),
            ("₹5,00,001 - ₹10,00,000", 500000, 0.20),
            ("Above ₹10,00,000", float("inf"), 0.30)
        ]

    breakdown = []
    rem_income = taxable_income
    basic_tax = 0.0

    for label, span, rate in slabs:
        if rem_income <= 0:
            breakdown.append({"Slab": label, "Rate": f"{int(rate*100)}%", "Taxable Amount": 0.0, "Tax": 0.0})
            continue

        taxable_in_slab = min(rem_income, span)
        slab_tax = taxable_in_slab * rate
        basic_tax += slab_tax
        rem_income -= taxable_in_slab

        breakdown.append({
            "Slab": label,
            "Rate": f"{int(rate*100)}%",
            "Taxable Amount": taxable_in_slab,
            "Tax": slab_tax
        })

    # Section 87A Rebate (Old Regime: up to ₹12,500 if income <= ₹5,00,000)
    rebate = 0.0
    if taxable_income <= 500000:
        rebate = min(basic_tax, 12500.0)

    tax_after_rebate = max(0.0, basic_tax - rebate)

    # Surcharge (Old Regime)
    surcharge = 0.0
    if taxable_income > 50000000:
        surcharge = tax_after_rebate * 0.37
    elif taxable_income > 20000000:
        surcharge = tax_after_rebate * 0.25
    elif taxable_income > 10000000:
        surcharge = tax_after_rebate * 0.15
    elif taxable_income > 5000000:
        surcharge = tax_after_rebate * 0.10

    tax_plus_surcharge = tax_after_rebate + surcharge
    cess = tax_plus_surcharge * 0.04
    total_tax = tax_plus_surcharge + cess

    return basic_tax, rebate, surcharge, cess, total_tax, breakdown


# ---------------------------------------------------------
# UI Header & Sidebar Controls
# ---------------------------------------------------------

st.markdown('<div class="main-title">⚖️ Comprehensive Income Tax Calculator</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Detailed 5 Heads of Income Bifurcation & Side-by-Side Comparison: <b>New Tax Regime vs Old Tax Regime</b> (FY 2024-25 / AY 2025-26)</div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Taxpayer Profile")
    financial_year = st.selectbox(
        "Financial Year",
        ["FY 2024-25 (AY 2025-26) - Revised Budget 2024", "FY 2023-24 (AY 2024-25)"],
        index=0
    )
    
    age_category = st.radio(
        "Age Category (for Old Regime)",
        ["General (< 60 yrs)", "Senior Citizen (60 - 80 yrs)", "Super Senior Citizen (80+ yrs)"],
        index=0
    )
    
    st.info("ℹ️ **New Tax Regime** has identical slabs across all age groups, with standard deduction of **₹75,000** for salaried taxpayers.")

    st.markdown("---")
    st.caption("Developed for Indian Taxpayers & Professionals. Always verify with official income tax guidelines prior to e-filing.")


# ---------------------------------------------------------
# Tabbed Input Interface
# ---------------------------------------------------------

tab_heads, tab_deductions = st.tabs([
    "📂 Five Heads of Income Bifurcation",
    "🛡️ Chapter VI-A Deductions & Exemptions"
])

with tab_heads:
    st.markdown("### Enter Income across all 5 Heads")
    
    # -----------------------------------------------------
    # HEAD 1: Salary
    # -----------------------------------------------------
    with st.expander("💼 Head 1: Income from Salary", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            gross_salary = st.number_input(
                "Gross Annual Salary (₹)",
                min_value=0.0,
                value=1200000.0,
                step=25000.0,
                format="%.2f",
                help="Total salary including Basic, DA, HRA, bonuses, perks and other allowances."
            )
        with col2:
            exempt_allowances = st.number_input(
                "Exempt Allowances u/s 10 (HRA, LTA, etc.) (₹)",
                min_value=0.0,
                value=0.0,
                step=10000.0,
                format="%.2f",
                help="Allowances exempt under Old Regime only (e.g. HRA exemption u/s 10(13A), LTA u/s 10(5)). Not available in New Regime."
            )
        with col3:
            prof_tax = st.number_input(
                "Professional Tax Paid (₹)",
                min_value=0.0,
                max_value=2500.0,
                value=2500.0,
                step=500.0,
                format="%.2f",
                help="Professional tax paid up to ₹2,500/year (Deductible in Old Regime)."
            )

        # Standard Deduction logic
        # Budget 2024 increased New Regime standard deduction to ₹75,000 (FY 2024-25)
        new_regime_std_ded = min(gross_salary, 75000.0) if gross_salary > 0 else 0.0
        old_regime_std_ded = min(max(0.0, gross_salary - exempt_allowances), 50000.0) if gross_salary > 0 else 0.0

        st.caption(f"📌 **Standard Deduction applied automatically:** ₹{new_regime_std_ded:,.0f} in New Regime | ₹{old_regime_std_ded:,.0f} in Old Regime.")

    # -----------------------------------------------------
    # HEAD 2: House Property
    # -----------------------------------------------------
    with st.expander("🏠 Head 2: Income from House Property", expanded=False):
        hp_type = st.radio("Property Occupancy Type", ["Self-Occupied", "Let-Out Property"], horizontal=True)

        if hp_type == "Self-Occupied":
            self_hp_interest = st.number_input(
                "Interest on Housing Loan u/s 24(b) (₹)",
                min_value=0.0,
                value=0.0,
                step=10000.0,
                format="%.2f",
                help="Interest paid on loan for self-occupied home. Max ₹2,00,000 loss deductible in Old Regime. In New Regime, loss from self-occupied house cannot be set off."
            )
            rent_received = 0.0
            municipal_taxes = 0.0
            letout_hp_interest = 0.0
        else:
            col_hp1, col_hp2, col_hp3 = st.columns(3)
            with col_hp1:
                rent_received = st.number_input("Annual Gross Rent Received (₹)", min_value=0.0, value=240000.0, step=10000.0, format="%.2f")
            with col_hp2:
                municipal_taxes = st.number_input("Municipal Taxes Paid by Owner (₹)", min_value=0.0, value=10000.0, step=2000.0, format="%.2f")
            with col_hp3:
                letout_hp_interest = st.number_input("Interest on Borrowed Capital (₹)", min_value=0.0, value=100000.0, step=10000.0, format="%.2f")
            self_hp_interest = 0.0

    # -----------------------------------------------------
    # HEAD 3: Business or Profession (PGBP)
    # -----------------------------------------------------
    with st.expander("📈 Head 3: Profits and Gains of Business or Profession (PGBP)", expanded=False):
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            business_profit = st.number_input(
                "Net Profit / Professional Income (₹)",
                min_value=0.0,
                value=0.0,
                step=25000.0,
                format="%.2f",
                help="Net profit from business, consulting, freelancing, or professional services (after business expenses)."
            )
        with col_b2:
            presumptive = st.checkbox("Opted for Presumptive Taxation (Sec 44AD / 44ADA / 44AE)", value=False)
            if presumptive:
                st.caption("Ensure profit declared adheres to the minimum presumptive rate (6%/8% for 44AD or 50% for 44ADA).")

    # -----------------------------------------------------
    # HEAD 4: Capital Gains
    # -----------------------------------------------------
    with st.expander("📊 Head 4: Capital Gains", expanded=False):
        col_cg1, col_cg2 = st.columns(2)
        with col_cg1:
            stcg = st.number_input(
                "Short-Term Capital Gains (STCG) (₹)",
                min_value=0.0,
                value=0.0,
                step=10000.0,
                format="%.2f",
                help="Net Short-Term Capital Gains from equity, mutual funds, or other assets."
            )
        with col_cg2:
            ltcg = st.number_input(
                "Long-Term Capital Gains (LTCG) (₹)",
                min_value=0.0,
                value=0.0,
                step=10000.0,
                format="%.2f",
                help="Net Long-Term Capital Gains from sale of properties, stocks, or mutual funds."
            )

    # -----------------------------------------------------
    # HEAD 5: Other Sources
    # -----------------------------------------------------
    with st.expander("🏦 Head 5: Income from Other Sources (IFOS)", expanded=False):
        col_os1, col_os2, col_os3, col_os4 = st.columns(4)
        with col_os1:
            savings_interest = st.number_input(
                "Savings Bank Interest (₹)",
                min_value=0.0,
                value=15000.0,
                step=2000.0,
                format="%.2f",
                help="Eligible for deduction u/s 80TTA (up to ₹10,000) or 80TTB (up to ₹50,000 for Senior Citizens) in Old Regime."
            )
        with col_os2:
            fd_interest = st.number_input(
                "Fixed Deposit / Term Deposit Interest (₹)",
                min_value=0.0,
                value=0.0,
                step=5000.0,
                format="%.2f"
            )
        with col_os3:
            dividend_income = st.number_input(
                "Dividend Income (₹)",
                min_value=0.0,
                value=0.0,
                step=2000.0,
                format="%.2f"
            )
        with col_os4:
            other_misc_income = st.number_input(
                "Other Miscellaneous Income (₹)",
                min_value=0.0,
                value=0.0,
                step=5000.0,
                format="%.2f",
                help="Any gifts, prizes, commission, or casual income taxable under other sources."
            )


with tab_deductions:
    st.markdown("### Chapter VI-A Deductions & Exemptions")
    st.info("💡 Note: Most Chapter VI-A deductions are exclusive to the **Old Tax Regime**. Only **Section 80CCD(2)** (Employer NPS contribution) is eligible under **both** regimes.")

    col_d1, col_d2 = st.columns(2)
    with col_d1:
        sec_80c = st.number_input(
            "Section 80C (PPF, EPF, ELSS, LIC, Home Loan Principal, etc.) (₹)",
            min_value=0.0,
            max_value=150000.0,
            value=150000.0,
            step=10000.0,
            format="%.2f",
            help="Maximum deduction allowable is ₹1,50,000 under Old Regime only."
        )

        sec_80d_self = st.number_input(
            "Section 80D: Health Insurance for Self & Family (₹)",
            min_value=0.0,
            max_value=50000.0,
            value=25000.0,
            step=5000.0,
            format="%.2f",
            help="Max ₹25,000 (or ₹50,000 if senior citizen) under Old Regime."
        )

        sec_80d_parents = st.number_input(
            "Section 80D: Health Insurance for Parents (₹)",
            min_value=0.0,
            max_value=50000.0,
            value=25000.0,
            step=5000.0,
            format="%.2f",
            help="Max ₹25,000 (or ₹50,000 if parents are senior citizens) under Old Regime."
        )

        sec_80ccd1b = st.number_input(
            "Section 80CCD(1B): Self NPS Contribution (₹)",
            min_value=0.0,
            max_value=50000.0,
            value=50000.0,
            step=5000.0,
            format="%.2f",
            help="Additional deduction for NPS up to ₹50,000 (Old Regime only)."
        )

    with col_d2:
        sec_80ccd2 = st.number_input(
            "Section 80CCD(2): Employer Contribution to NPS (₹)",
            min_value=0.0,
            value=0.0,
            step=10000.0,
            format="%.2f",
            help="Allowed in BOTH Old and New Regimes! Up to 10% (14% for Central/State Govt) of Salary (Basic + DA)."
        )

        sec_80e = st.number_input(
            "Section 80E: Interest on Higher Education Loan (₹)",
            min_value=0.0,
            value=0.0,
            step=10000.0,
            format="%.2f",
            help="No upper limit for eligible interest paid for up to 8 years (Old Regime only)."
        )

        sec_80g = st.number_input(
            "Section 80G: Eligible Donations to Charitable Trusts (₹)",
            min_value=0.0,
            value=0.0,
            step=5000.0,
            format="%.2f",
            help="Qualifying donations (50% or 100% eligible) under Old Regime."
        )

        other_deductions = st.number_input(
            "Other Chapter VI-A Deductions (80GG, 80U, 80DDB, etc.) (₹)",
            min_value=0.0,
            value=0.0,
            step=5000.0,
            format="%.2f",
            help="Other deductions allowed under Old Regime."
        )


# ---------------------------------------------------------
# COMPUTATION LOGIC ACROSS BOTH REGIMES
# ---------------------------------------------------------

# 1. Salary Computation
# New Regime: Gross - Standard Deduction (₹75,000)
net_salary_new = max(0.0, gross_salary - new_regime_std_ded)

# Old Regime: Gross - Exempt Allowances - Professional Tax - Standard Deduction (₹50,000)
salary_after_exempt = max(0.0, gross_salary - exempt_allowances - prof_tax)
net_salary_old = max(0.0, salary_after_exempt - min(50000.0, salary_after_exempt))

# 2. House Property Computation
if hp_type == "Self-Occupied":
    # Old Regime: Max deduction of ₹2,00,000 as loss from house property
    hp_income_old = -min(200000.0, self_hp_interest)
    # New Regime: Loss from self-occupied house cannot be set off against other heads
    hp_income_new = 0.0
else:
    # Let-out property:
    # NAV = Rent - Municipal Taxes
    nav = max(0.0, rent_received - municipal_taxes)
    std_ded_hp = nav * 0.30
    hp_net = nav - std_ded_hp - letout_hp_interest
    
    # In Old regime, loss can be set off up to ₹2,00,000
    if hp_net < 0:
        hp_income_old = max(-200000.0, hp_net)
        hp_income_new = 0.0  # In new regime, loss cannot be set off against other heads
    else:
        hp_income_old = hp_net
        hp_income_new = hp_net

# 3. Business / Profession (PGBP)
pgbp_income_new = business_profit
pgbp_income_old = business_profit

# 4. Capital Gains
cg_income_new = stcg + ltcg
cg_income_old = stcg + ltcg

# 5. Other Sources
total_other_sources = savings_interest + fd_interest + dividend_income + other_misc_income
other_sources_new = total_other_sources
other_sources_old = total_other_sources

# Section 80TTA / 80TTB calculation for Old Regime:
if age_category == "General (< 60 yrs)":
    sec_80tta_ttb = min(savings_interest, 10000.0)
else:
    # 80TTB for Senior Citizens covers savings + FD interest up to ₹50,000
    sec_80tta_ttb = min(savings_interest + fd_interest, 50000.0)

# ---------------------------------------------------------
# Gross Total Income (GTI)
# ---------------------------------------------------------
gti_new = max(0.0, net_salary_new + hp_income_new + pgbp_income_new + cg_income_new + other_sources_new)
gti_old = max(0.0, net_salary_old + hp_income_old + pgbp_income_old + cg_income_old + other_sources_old)

# ---------------------------------------------------------
# Deductions Application
# ---------------------------------------------------------
# New Regime allows ONLY 80CCD(2)
total_deductions_new = sec_80ccd2

# Old Regime allows all Chapter VI-A deductions
total_deductions_old = (
    min(sec_80c, 150000.0)
    + sec_80d_self
    + sec_80d_parents
    + sec_80ccd1b
    + sec_80ccd2
    + sec_80tta_ttb
    + sec_80e
    + sec_80g
    + other_deductions
)

# Net Taxable Income (Rounded to nearest 10)
taxable_income_new = round(max(0.0, gti_new - total_deductions_new), -1)
taxable_income_old = round(max(0.0, gti_old - total_deductions_old), -1)

# ---------------------------------------------------------
# Tax Calculation Execution
# ---------------------------------------------------------
tax_new_basic, rebate_new, surcharge_new, cess_new, total_tax_new, breakdown_new = calculate_new_regime_tax(taxable_income_new)
tax_old_basic, rebate_old, surcharge_old, cess_old, total_tax_old, breakdown_old = calculate_old_regime_tax(taxable_income_old, age_category)

# Monthly taxes
monthly_tax_new = total_tax_new / 12
monthly_tax_old = total_tax_old / 12

# Effective tax rates
effective_rate_new = (total_tax_new / taxable_income_new * 100) if taxable_income_new > 0 else 0.0
effective_rate_old = (total_tax_old / taxable_income_old * 100) if taxable_income_old > 0 else 0.0

tax_diff = abs(total_tax_old - total_tax_new)


# ---------------------------------------------------------
# PRESENTATION / DASHBOARD
# ---------------------------------------------------------
st.markdown("---")
st.subheader("📊 Comparative Tax Result & Regime Recommendation")

# Highlight Banner for Regime Recommendation
if total_tax_new < total_tax_old:
    st.markdown(f"""
    <div class="winner-new">
        <h3 style="margin:0; color:#065F46;">🎉 Recommendation: NEW TAX REGIME is Beneficial!</h3>
        <p style="margin:5px 0 0 0; font-size:1.15rem; color:#047857;">
            You save <b>₹{tax_diff:,.2f}</b> per year (approx. <b>₹{tax_diff/12:,.2f}/month</b>) by opting for the New Tax Regime.
        </p>
    </div>
    """, unsafe_allow_html=True)
elif total_tax_old < total_tax_new:
    st.markdown(f"""
    <div class="winner-old">
        <h3 style="margin:0; color:#1E40AF;">🎉 Recommendation: OLD TAX REGIME is Beneficial!</h3>
        <p style="margin:5px 0 0 0; font-size:1.15rem; color:#1D4ED8;">
            You save <b>₹{tax_diff:,.2f}</b> per year (approx. <b>₹{tax_diff/12:,.2f}/month</b>) by staying with the Old Tax Regime due to high deductions/exemptions.
        </p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="winner-tie">
        <h3 style="margin:0; color:#374151;">⚖️ Both Tax Regimes Result in the Same Tax Liability</h3>
        <p style="margin:5px 0 0 0; font-size:1.1rem; color:#4B5563;">
            Total tax payable is identical under both regimes. The New Tax Regime may be preferable due to simpler compliance and no need to submit proof of investments.
        </p>
    </div>
    """, unsafe_allow_html=True)


# Key Metrics Side by Side
col_m1, col_m2, col_m3, col_m4 = st.columns(4)

with col_m1:
    st.metric(
        label="Tax Payable (New Regime)",
        value=f"₹{total_tax_new:,.0f}",
        delta=f"-₹{tax_diff:,.0f}" if total_tax_new < total_tax_old else None,
        delta_color="inverse"
    )
    st.caption(f"Monthly: ₹{monthly_tax_new:,.0f}")

with col_m2:
    st.metric(
        label="Tax Payable (Old Regime)",
        value=f"₹{total_tax_old:,.0f}",
        delta=f"-₹{tax_diff:,.0f}" if total_tax_old < total_tax_new else None,
        delta_color="inverse"
    )
    st.caption(f"Monthly: ₹{monthly_tax_old:,.0f}")

with col_m3:
    st.metric(
        label="Taxable Income (New)",
        value=f"₹{taxable_income_new:,.0f}",
        help="Gross Total Income minus Standard Deduction & 80CCD(2)"
    )
    st.caption(f"Effective Rate: {effective_rate_new:.2f}%")

with col_m4:
    st.metric(
        label="Taxable Income (Old)",
        value=f"₹{taxable_income_old:,.0f}",
        help="Gross Total Income minus all Chapter VI-A deductions and allowances"
    )
    st.caption(f"Effective Rate: {effective_rate_old:.2f}%")


# Detailed Comparison Table
st.markdown("#### 📋 Step-by-Step Bifurcation Comparison")

comparison_data = {
    "Heads & Calculation Step": [
        "1. Income from Salary (Net after Standard Deduction & Allowances)",
        "2. Income / (Loss) from House Property",
        "3. Profits & Gains of Business or Profession (PGBP)",
        "4. Capital Gains (STCG + LTCG)",
        "5. Income from Other Sources (Interest, Dividends, etc.)",
        "🔹 Gross Total Income (GTI)",
        "Less: Chapter VI-A Deductions",
        "🔹 Net Taxable Income",
        "Basic Slab Tax",
        "Less: Section 87A Rebate",
        "Add: Surcharge",
        "Add: Health & Education Cess (4%)",
        "⭐ Total Tax Payable",
        "Estimated Monthly Tax Outflow"
    ],
    "New Tax Regime (₹)": [
        f"₹{net_salary_new:,.2f}",
        f"₹{hp_income_new:,.2f}",
        f"₹{pgbp_income_new:,.2f}",
        f"₹{cg_income_new:,.2f}",
        f"₹{other_sources_new:,.2f}",
        f"₹{gti_new:,.2f}",
        f"₹{total_deductions_new:,.2f}",
        f"₹{taxable_income_new:,.2f}",
        f"₹{tax_new_basic:,.2f}",
        f"-₹{rebate_new:,.2f}",
        f"₹{surcharge_new:,.2f}",
        f"₹{cess_new:,.2f}",
        f"₹{total_tax_new:,.2f}",
        f"₹{monthly_tax_new:,.2f}"
    ],
    "Old Tax Regime (₹)": [
        f"₹{net_salary_old:,.2f}",
        f"₹{hp_income_old:,.2f}",
        f"₹{pgbp_income_old:,.2f}",
        f"₹{cg_income_old:,.2f}",
        f"₹{other_sources_old:,.2f}",
        f"₹{gti_old:,.2f}",
        f"₹{total_deductions_old:,.2f}",
        f"₹{taxable_income_old:,.2f}",
        f"₹{tax_old_basic:,.2f}",
        f"-₹{rebate_old:,.2f}",
        f"₹{surcharge_old:,.2f}",
        f"₹{cess_old:,.2f}",
        f"₹{total_tax_old:,.2f}",
        f"₹{monthly_tax_old:,.2f}"
    ]
}

comp_df = pd.DataFrame(comparison_data)
st.dataframe(comp_df, hide_index=True)


# Visual Chart Comparison
st.markdown("#### 📈 Visual Comparison")
chart_df = pd.DataFrame({
    "Regime": ["New Regime", "Old Regime"],
    "Net Taxable Income": [taxable_income_new, taxable_income_old],
    "Total Tax Payable": [total_tax_new, total_tax_old],
    "Deductions Claimed": [
        total_deductions_new + new_regime_std_ded,
        total_deductions_old + old_regime_std_ded + exempt_allowances + prof_tax
    ]
}).set_index("Regime")

st.bar_chart(chart_df[["Net Taxable Income", "Deductions Claimed", "Total Tax Payable"]])


# Slabs Breakdown Expanders
col_sl1, col_sl2 = st.columns(2)

with col_sl1:
    with st.expander("🔍 New Regime Slab-by-Slab Tax Breakdown", expanded=False):
        df_new_slabs = pd.DataFrame(breakdown_new)
        df_new_slabs["Taxable Amount"] = df_new_slabs["Taxable Amount"].apply(lambda x: f"₹{x:,.2f}")
        df_new_slabs["Tax"] = df_new_slabs["Tax"].apply(lambda x: f"₹{x:,.2f}")
        st.dataframe(df_new_slabs, hide_index=True)
        st.caption(f"Rebate u/s 87A: ₹{rebate_new:,.2f} | 4% Cess: ₹{cess_new:,.2f}")

with col_sl2:
    with st.expander("🔍 Old Regime Slab-by-Slab Tax Breakdown", expanded=False):
        df_old_slabs = pd.DataFrame(breakdown_old)
        df_old_slabs["Taxable Amount"] = df_old_slabs["Taxable Amount"].apply(lambda x: f"₹{x:,.2f}")
        df_old_slabs["Tax"] = df_old_slabs["Tax"].apply(lambda x: f"₹{x:,.2f}")
        st.dataframe(df_old_slabs, hide_index=True)
        st.caption(f"Rebate u/s 87A: ₹{rebate_old:,.2f} | 4% Cess: ₹{cess_old:,.2f}")


# ---------------------------------------------------------
# Educational Summary / Tax Notes
# ---------------------------------------------------------
with st.expander("ℹ️ Key Highlights & Rules under Budget 2024 / FY 2024-25"):
    st.markdown("""
    1. **Default Regime:** New Tax Regime is the default regime under Section 115BAC unless opted out.
    2. **Standard Deduction:** Increased to **₹75,000** for salaried employees and pensioners under the New Tax Regime (remains **₹50,000** under the Old Regime).
    3. **Tax-Free Thresholds:**
       - **New Regime:** Income up to **₹7,00,000** is completely tax-free after Section 87A rebate. For salaried employees claiming the ₹75,000 standard deduction, salary income up to **₹7,75,000** has zero tax liability!
       - **Old Regime:** Income up to **₹5,00,000** is tax-free after Section 87A rebate.
    4. **House Property Loss:** Under the New Regime, loss from self-occupied house property (housing loan interest) cannot be adjusted against salary or other heads of income.
    5. **Employer NPS (80CCD(2)):** Deductible up to 10% (14% for government employees) of Basic + DA in **both** Old and New regimes.
    """)

st.divider()
st.caption(
    "Disclaimer: This calculator is provided for estimation and informational purposes in accordance with the provisions of the Indian Income-tax Act, 1961. "
    "Actual tax liabilities may vary based on specific surcharge applicability, marginal reliefs, and individual assessment scenarios. "
    "Please consult a Chartered Accountant or Certified Tax Professional before filing your Income Tax Return (ITR)."
)