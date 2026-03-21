import streamlit as st
import pandas as pd

st.set_page_config(page_title="Salary Calculator", layout="centered")

st.title("💼 Salary Calculator")
st.markdown("### Enter details to calculate salary structure")

# -------------------------------
# Upload Excel
# -------------------------------
file = "salary_data.xlsx"

wages_df = pd.read_excel(file, sheet_name="wages", header=[0,1])
pt_df = pd.read_excel(file, sheet_name="pt")
lwf_df = pd.read_excel(file, sheet_name="lwf")

    # Fix columns
    wages_df.columns = [' '.join(col).strip() for col in wages_df.columns]
    wages_df.columns = wages_df.columns.str.strip()

    pt_df.columns = pt_df.columns.str.strip()
    lwf_df.columns = lwf_df.columns.str.strip()

    # Rename State column
    for col in wages_df.columns:
        if "State" in col or "Location" in col:
            wages_df.rename(columns={col: "State"}, inplace=True)

    # -------------------------------
    # Functions
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

    def get_pt(state, gross):
        df = pt_df[pt_df["State"].str.upper() == state.upper()]
        for _, r in df.iterrows():
            if r["From_Value"] <= gross <= r["To_Value"]:
                return 0 if pd.isna(r["PT"]) else float(r["PT"])
        return 0

    def get_lwf(state):
        df = lwf_df[lwf_df["State"].str.upper() == state.upper()]
        if df.empty or df.iloc[0]["Status"] != "Applicable":
            return (0,0)
        return float(df.iloc[0]["Employer Contribution"]), float(df.iloc[0]["Employee Contribution"])

    def calculate_salary(state, skill, nth):

        basic = get_min_wage(state, skill)

        hra = 0.05 * basic if state.upper() in ["MAHARASHTRA","WEST BENGAL"] else 0.40 * basic
        cca = 0
        bonus = 0 if basic > 21000 else 0.0833 * basic

        gross = nth

        for _ in range(50):

            pf_base = basic + cca

            emp_pf = 1800 if pf_base > 15000 else 0.12 * pf_base
            emp_esi = 0 if gross > 21000 else 0.0075 * gross
            pt = get_pt(state, gross)
            lwf_emp, lwf_emp_emp = get_lwf(state)

            total_ded = emp_pf + emp_esi + lwf_emp_emp + pt

            new_gross = nth + total_ded

            if abs(new_gross - gross) < 1:
                break

            gross = new_gross

        employer_pf = 1950 if pf_base > 15000 else 0.13 * pf_base
        employer_esi = 0 if gross > 21000 else 0.0325 * gross

        ctc = gross + employer_pf + employer_esi + lwf_emp

        return {
            "Basic": round(basic, 2),
            "HRA": round(hra, 2),
            "Bonus": round(bonus, 2),
            "Gross": round(gross, 2),
            "Employee PF": round(emp_pf, 2),
            "Employee ESI": round(emp_esi, 2),
            "PT": round(pt, 2),
            "CTC": round(ctc, 2),
            "Net Take Home": nth
        }

    # -------------------------------
    # UI Inputs
    # -------------------------------
    state = st.selectbox("Select State", wages_df["State"].dropna().unique())
    skill = st.selectbox("Select Skill Type", ["Unskilled","Semi Skilled","Skilled","Highly Skilled"])
    nth = st.number_input("Enter In-Hand Salary", min_value=0)

    if st.button("Calculate Salary"):

        result = calculate_salary(state, skill, nth)

        st.success("Calculation Done ✅")

        st.subheader("📊 Salary Breakdown")
        st.table(pd.DataFrame(result.items(), columns=["Component", "Amount"]))