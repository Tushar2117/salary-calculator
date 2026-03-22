import streamlit as st
import pandas as pd

st.set_page_config(page_title="Salary Calculator", layout="centered")

st.title("💼 Salary Calculator")
st.markdown("### Enter details to calculate salary structure")

# -------------------------------
# Load Excel
# -------------------------------
file = "salary_data.xlsx"

wages_df = pd.read_excel(file, sheet_name="wages", header=[0,1])
pt_df = pd.read_excel(file, sheet_name="pt")
lwf_df = pd.read_excel(file, sheet_name="lwf")

# -------------------------------
# CLEANING DATA
# -------------------------------

# Fix multi-header columns
wages_df.columns = [' '.join(col).strip() for col in wages_df.columns]
wages_df.columns = wages_df.columns.str.strip()

# Clean PT & LWF columns
pt_df.columns = pt_df.columns.str.strip()
lwf_df.columns = lwf_df.columns.str.strip()

# Fix wrong column name (Cateogry -> Gender)
pt_df.rename(columns={
    "Cateogry": "Gender",
    "category": "Gender"
}, inplace=True)

# Rename State column
for col in wages_df.columns:
    if "State" in col or "Location" in col:
        wages_df.rename(columns={col: "State"}, inplace=True)

# -------------------------------
# HELPER FUNCTIONS
# -------------------------------
def get_wage_column(skill_type):
    skill_type = skill_type.lower()

    for col in wages_df.columns:
        c = col.lower()

        if skill_type == "unskilled" and "unskilled" in c and "monthly" in c:
            return col
        elif skill_type == "semi skilled" and "semi" in c and "monthly" in c:
            return col
        elif skill_type == "skilled" and "skilled" in c and "semi" not in c and "monthly" in c:
            return col
        elif skill_type == "highly skilled" and "highly" in c and "monthly" in c:
            return col

def get_min_wage(state, skill):
    col = get_wage_column(skill)
    row = wages_df[wages_df["State"].str.upper() == state.upper()]
    return float(row.iloc[0][col])

# PT with Gender Logic
def get_pt(state, gross, gender):
    df = pt_df[pt_df["State"].str.upper() == state.upper()]

    for _, r in df.iterrows():
        if r["From_Value"] <= gross <= r["To_Value"]:

            if "Gender" in df.columns:
                category = str(r["Gender"]).lower()

                if category == "male" and gender.lower() != "male":
                    return 0
                elif category == "female" and gender.lower() != "female":
                    return 0

            return 0 if pd.isna(r["PT"]) else float(r["PT"])

    return 0

def get_lwf(state):
    df = lwf_df[lwf_df["State"].str.upper() == state.upper()]

    if df.empty or df.iloc[0]["Status"] != "Applicable":
        return (0, 0)

    return float(df.iloc[0]["Employer Contribution"]), float(df.iloc[0]["Employee Contribution"])

# -------------------------------
# MAIN CALCULATION
# -------------------------------
def calculate_salary(state, skill, nth, metro, insurance, gender):

    basic = get_min_wage(state, skill)

    # HRA Logic
    if state.upper() in ["MAHARASHTRA", "WEST BENGAL"]:
        hra = 0.05 * basic
    else:
        hra = 0.50 * basic if metro == "Metro" else 0.40 * basic

    bonus = 0 if basic > 21000 else 0.0833 * basic

    cca = 0
    gross = basic + hra + bonus

    # Adjust CCA dynamically
    for _ in range(100):

        pf_base = basic + cca

        emp_pf = 1800 if pf_base > 15000 else 0.12 * pf_base
        emp_esi = 0 if gross > 21000 else 0.0075 * gross
        pt = get_pt(state, gross, gender)
        lwf_er, lwf_ee = get_lwf(state)

        total_deduction = emp_pf + emp_esi + pt + lwf_ee

        required_gross = nth + total_deduction
        new_cca = required_gross - (basic + hra + bonus)

        if abs(new_cca - cca) < 1:
            cca = new_cca
            break

        cca = new_cca
        gross = basic + hra + cca + bonus

    # Final Calculations
    pf_base = basic + cca

    employer_pf = 1950 if pf_base > 15000 else 0.13 * pf_base
    employer_esi = 0 if gross > 21000 else 0.0325 * gross

    lwf_er, lwf_ee = get_lwf(state)

    total_contribution = employer_pf + employer_esi + lwf_er + insurance
    total_deduction = emp_pf + emp_esi + pt + lwf_ee

    ctc = gross + total_contribution

    return {
        # PART A
        "Basic": round(basic, 2),
        "HRA": round(hra, 2),
        "CCA": round(cca, 2),
        "Bonus": round(bonus, 2),
        "Gross": round(gross, 2),

        # PART B
        "Employer PF": round(employer_pf, 2),
        "Employer ESI": round(employer_esi, 2),
        "LWF Employer": round(lwf_er, 2),
        "Insurance": round(insurance, 2),
        "Total Contribution": round(total_contribution, 2),
        "CTC": round(ctc, 2),

        # PART C
        "Employee PF": round(emp_pf, 2),
        "Employee ESI": round(emp_esi, 2),
        "PT": round(pt, 2),
        "LWF Employee": round(lwf_ee, 2),
        "Total Deduction": round(total_deduction, 2),
        "Net Take Home": nth
    }

# -------------------------------
# UI INPUTS
# -------------------------------
state = st.selectbox("Select State", wages_df["State"].dropna().unique())

skill = st.selectbox("Select Skill Type",
                     ["Unskilled", "Semi Skilled", "Skilled", "Highly Skilled"])

metro = st.selectbox("Metro / Non-Metro", ["Metro", "Non-Metro"])

gender = st.selectbox("Select Gender", ["Male", "Female"])

nth = st.number_input("Enter In-Hand Salary", min_value=0)

insurance = st.number_input("Enter Insurance Amount", min_value=0)

# -------------------------------
# BUTTON
# -------------------------------
if st.button("Calculate Salary"):

    result = calculate_salary(state, skill, nth, metro, insurance, gender)

    st.success("Calculation Done ✅")

    st.subheader("📊 Salary Breakdown")

    df = pd.DataFrame(result.items(), columns=["Component", "Amount"])
    st.table(df)
