import streamlit as st
import pandas as pd

st.set_page_config(page_title="Dialysis Income", layout="centered")

# ----------------------------
# Helper: total cost from base_rn4
# ----------------------------
def get_total_cost(base_rn4, n_rn4, n_rn3, n_rn2, n_rn1, n_pn1):
    c_rn4 = base_rn4
    c_rn3 = base_rn4 - 100
    c_rn2 = base_rn4 - 250
    c_rn1 = int((base_rn4 + 50) / 2)
    c_pn1 = int((base_rn4 - 150) / 2)

    total = (
        (c_rn4 * n_rn4)
        + (c_rn3 * n_rn3)
        + (c_rn2 * n_rn2)
        + (c_rn1 * n_rn1)
        + (c_pn1 * n_pn1)
    )
    return total

# ----------------------------
# State
# ----------------------------
def init_state():
    defaults = {
        "patients": 0, "rn4": 0, "rn3": 0, "rn2": 0, "rn1": 0, "pn1": 0,
        "result": None
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def reset_all():
    st.session_state.patients = 0
    st.session_state.rn4 = 0
    st.session_state.rn3 = 0
    st.session_state.rn2 = 0
    st.session_state.rn1 = 0
    st.session_state.pn1 = 0
    st.session_state.result = None

init_state()

# ----------------------------
# UI
# ----------------------------
st.markdown("### 🏥 โปรแกรมคำนวณค่าตอบแทน (RN4 ลงท้ายด้วย 0 สูงสุด)")

st.session_state.patients = st.number_input(
    "จำนวนผู้ป่วย", min_value=0, step=1, value=int(st.session_state.patients)
)

c1, c2 = st.columns(2)
with c1:
    st.session_state.rn4 = st.number_input("จำนวน RN4", min_value=0, step=1, value=int(st.session_state.rn4))
    st.session_state.rn3 = st.number_input("จำนวน RN3", min_value=0, step=1, value=int(st.session_state.rn3))
    st.session_state.rn2 = st.number_input("จำนวน RN2", min_value=0, step=1, value=int(st.session_state.rn2))
with c2:
    st.session_state.rn1 = st.number_input("จำนวน RN1", min_value=0, step=1, value=int(st.session_state.rn1))
    st.session_state.pn1 = st.number_input("จำนวน PN1", min_value=0, step=1, value=int(st.session_state.pn1))

btn1, btn2 = st.columns(2)
calc_clicked = btn1.button("คำนวณรายได้", use_container_width=True)
reset_clicked = btn2.button("ล้างค่า", use_container_width=True)

if reset_clicked:
    reset_all()
    st.rerun()

# ----------------------------
# Calculation
# ----------------------------
def calculate():
    n_pts = int(st.session_state.patients)
    n_rn4 = int(st.session_state.rn4)
    n_rn3 = int(st.session_state.rn3)
    n_rn2 = int(st.session_state.rn2)
    n_rn1 = int(st.session_state.rn1)
    n_pn1 = int(st.session_state.pn1)

    total_revenue = n_pts * 450
    total_staff = n_rn4 + n_rn3 + n_rn2 + n_rn1 + n_pn1

    # Validation
    if total_staff == 0:
        return {"error": "❌ กรุณาระบุจำนวนบุคลากรอย่างน้อย 1 ท่าน"}
    if total_revenue == 0:
        return {"error": "⚠️ ยอดรายรับเป็น 0 (ไม่มีผู้ป่วย)"}

    # Estimate start RN4
    coeff = n_rn4 + n_rn3 + n_rn2 + (0.5 * n_rn1) + (0.5 * n_pn1)
    const = (-100 * n_rn3) - (250 * n_rn2) + (25 * n_rn1) - (75 * n_pn1)
    approx_x = 0 if coeff == 0 else (total_revenue - const) / coeff

    # round down to tens (ends with 0)
    start_rn4 = (int(approx_x) // 10) * 10
    if start_rn4 < 0:
        start_rn4 = 0

    # Find max RN4 (ends with 0) such that cost <= revenue
    curr_rn4 = start_rn4
    while True:
        cost = get_total_cost(curr_rn4, n_rn4, n_rn3, n_rn2, n_rn1, n_pn1)
        if cost <= total_revenue:
            final_rn4_base = curr_rn4
            break
        curr_rn4 -= 10
        if curr_rn4 < 0:
            final_rn4_base = 0
            break

    # Base pays
    inc_rn4 = final_rn4_base
    inc_rn3 = final_rn4_base - 100
    inc_rn2 = final_rn4_base - 250
    inc_rn1 = int((final_rn4_base + 50) / 2)
    inc_pn1 = int((final_rn4_base - 150) / 2)

    # remainder from base payout
    current_total_payout = get_total_cost(final_rn4_base, n_rn4, n_rn3, n_rn2, n_rn1, n_pn1)
    remainder = total_revenue - current_total_payout

    note = ""
    top_up = 0
    original_remainder = remainder

    if n_pn1 > 0 and remainder > 0:
        top_up = remainder // n_pn1
        inc_pn1 += top_up
        remainder = remainder - (top_up * n_pn1)
        note = f"RN4 ฐาน {final_rn4_base:,} บาท | เงินเหลือ {original_remainder:,} บาท แบ่งให้ PN เพิ่มคนละ {top_up:,} บาท"
    elif remainder > 0:
        note = f"RN4 ฐาน {final_rn4_base:,} บาท | เหลือเศษ {remainder:,} บาท ไม่มี PN ให้แบ่ง"

    final_payout = (
        (inc_rn4 * n_rn4)
        + (inc_rn3 * n_rn3)
        + (inc_rn2 * n_rn2)
        + (inc_rn1 * n_rn1)
        + (inc_pn1 * n_pn1)
    )

    df = pd.DataFrame(
        [
            ["RN4", n_rn4, inc_rn4, inc_rn4 * n_rn4],
            ["RN3", n_rn3, inc_rn3, inc_rn3 * n_rn3],
            ["RN2", n_rn2, inc_rn2, inc_rn2 * n_rn2],
            ["RN1", n_rn1, inc_rn1, inc_rn1 * n_rn1],
            ["PN1", n_pn1, inc_pn1, inc_pn1 * n_pn1],
        ],
        columns=["ระดับ", "จำนวนคน", "รายได้ต่อคน (บาท)", "รวมจ่าย (บาท)"],
    )
    df_filtered = df[df["จำนวนคน"] > 0].copy()

    return {
        "total_revenue": total_revenue,
        "final_payout": final_payout,
        "remainder": remainder,
        "note": note,
        "final_rn4_base": final_rn4_base,
        "df": df_filtered
    }

if calc_clicked:
    st.session_state.result = calculate()

# ----------------------------
# Output
# ----------------------------
res = st.session_state.result
if res:
    if "error" in res:
        st.error(res["error"])
    else:
        st.divider()
        st.write(f"💰 รายรับรวม (ผู้ป่วย {int(st.session_state.patients):,} คน × 450): **{res['total_revenue']:,} บาท**")
        st.write(f"💸 จ่ายจริงรวม: **{res['final_payout']:,} บาท**")
        st.write(f"🔹 คงเหลือยกยอด: **{res['remainder']:,} บาท**")
        if res.get("note"):
            st.info(res["note"])
        st.divider()

        if len(res["df"]) > 0:
            st.dataframe(res["df"], hide_index=True, use_container_width=True)
        else:
            st.warning("ไม่พบข้อมูลบุคลากร")
