import streamlit as st
import pandas as pd

st.set_page_config(page_title="Dialysis Income", layout="centered")

# ----------------------------
# Helpers
# ----------------------------
def reset_all():
    st.session_state.patients = 0
    st.session_state.rn4 = 0
    st.session_state.rn3 = 0
    st.session_state.rn2 = 0
    st.session_state.rn1 = 0
    st.session_state.pn1 = 0
    st.session_state.result = None  # ล้างผลลัพธ์ด้วย

def init_state():
    defaults = {
        "patients": 0, "rn4": 0, "rn3": 0, "rn2": 0, "rn1": 0, "pn1": 0,
        "result": None
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ----------------------------
# UI
# ----------------------------
st.markdown("## โปรแกรมคำนวณค่าตอบแทนศูนย์ฟอกไต (มีปุ่ม Reset)")

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

btn_col1, btn_col2 = st.columns(2)
calc_clicked = btn_col1.button("คำนวณรายได้", use_container_width=True)
reset_clicked = btn_col2.button("ล้างค่า", use_container_width=True)

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

    if total_staff == 0:
        return {"error": "❌ กรุณาระบุจำนวนบุคลากรอย่างน้อย 1 ท่าน"}

    coeff_x = n_rn4 + n_rn3 + n_rn2 + (0.5 * n_rn1) + (0.5 * n_pn1)
    constant = (-100 * n_rn3) - (250 * n_rn2) + (25 * n_rn1) - (75 * n_pn1)

    if coeff_x == 0:
        return {"error": "❌ ไม่สามารถคำนวณได้เนื่องจากไม่มีบุคลากรหลัก"}

    approx_x = (total_revenue - constant) / coeff_x

    base_rn4 = int(approx_x)
    if base_rn4 % 2 != 0:
        base_rn4 -= 1

    warn = None
    if base_rn4 < 0:
        warn = f"⚠️ รายรับรวม ({total_revenue:,} บาท) ไม่เพียงพอสำหรับจ่ายตามสูตรขั้นต่ำ → ตั้ง RN4=0"
        base_rn4 = 0

    inc_rn4 = base_rn4
    inc_rn3 = base_rn4 - 100
    inc_rn2 = base_rn4 - 250
    inc_rn1 = int((base_rn4 + 50) / 2)
    inc_pn1 = int((base_rn4 - 150) / 2)

    current_total = (inc_rn4 * n_rn4) + (inc_rn3 * n_rn3) + (inc_rn2 * n_rn2) + (inc_rn1 * n_rn1) + (inc_pn1 * n_pn1)
    remainder = total_revenue - current_total

    note = ""
    final_remainder = remainder

    if n_pn1 > 0 and remainder > 0:
        top_up_per_pn = remainder // n_pn1
        inc_pn1 += top_up_per_pn
        used_for_topup = top_up_per_pn * n_pn1
        final_remainder = remainder - used_for_topup
        note = f"มีการนำเงินเหลือ {remainder:,} บาท เกลี่ยเพิ่มให้ PN คนละ {top_up_per_pn:,} บาท"
    elif n_pn1 == 0 and remainder > 0:
        note = f"มียอดเงินเหลือ {remainder:,} บาท แต่ไม่มี PN ให้เกลี่ย"

    final_total_payout = (inc_rn4 * n_rn4) + (inc_rn3 * n_rn3) + (inc_rn2 * n_rn2) + (inc_rn1 * n_rn1) + (inc_pn1 * n_pn1)

    data = [
        ["RN4", n_rn4, inc_rn4, inc_rn4 * n_rn4],
        ["RN3", n_rn3, inc_rn3, inc_rn3 * n_rn3],
        ["RN2", n_rn2, inc_rn2, inc_rn2 * n_rn2],
        ["RN1", n_rn1, inc_rn1, inc_rn1 * n_rn1],
        ["PN1", n_pn1, inc_pn1, inc_pn1 * n_pn1],
    ]
    df = pd.DataFrame(data, columns=["ระดับ", "จำนวนคน", "รายได้ต่อคน (บาท)", "รวมจ่าย (บาท)"])
    df_filtered = df[df["จำนวนคน"] > 0].copy()

    return {
        "warn": warn,
        "total_revenue": total_revenue,
        "final_total_payout": final_total_payout,
        "final_remainder": final_remainder,
        "note": note,
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
        if res.get("warn"):
            st.warning(res["warn"])

        st.divider()
        st.write(f"💰 รายรับรวมจากผู้ป่วย: **{res['total_revenue']:,} บาท**")
        st.write(f"💸 จ่ายจริงรวม: **{res['final_total_payout']:,} บาท**")
        st.write(f"🔹 เงินคงเหลือ (ปัดเศษ): **{res['final_remainder']:,} บาท**")
        if res.get("note"):
            st.info(res["note"])
        st.divider()

        df_show = res["df"]
        if len(df_show) > 0:
            # แสดงเป็นตาราง (ซ่อน index)
            st.dataframe(df_show, hide_index=True, use_container_width=True)
        else:
            st.warning("ไม่พบข้อมูลบุคลากรในรอบนี้")

