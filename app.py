import streamlit as st
import pandas as pd

st.set_page_config(page_title="Dialysis Income", layout="centered")

st.title("โปรแกรมคำนวณค่าตอบแทนศูนย์ฟอกไต (ซ่อนแถวที่ไม่มีคน)")

# ---------- Inputs ----------
n_pts = st.number_input("จำนวนผู้ป่วย", min_value=0, step=1, value=0)

col1, col2 = st.columns(2)
with col1:
    n_rn4 = st.number_input("จำนวน RN4", min_value=0, step=1, value=0)
    n_rn3 = st.number_input("จำนวน RN3", min_value=0, step=1, value=0)
    n_rn2 = st.number_input("จำนวน RN2", min_value=0, step=1, value=0)
with col2:
    n_rn1 = st.number_input("จำนวน RN1", min_value=0, step=1, value=0)
    n_pn1 = st.number_input("จำนวน PN1", min_value=0, step=1, value=0)

btn = st.button("คำนวณรายได้")

# ---------- Calculation ----------
if btn:
    total_revenue = int(n_pts) * 450
    total_staff = int(n_rn4 + n_rn3 + n_rn2 + n_rn1 + n_pn1)

    if total_staff == 0:
        st.error("กรุณาระบุจำนวนบุคลากรอย่างน้อย 1 ท่าน")
        st.stop()

    coeff_x = (n_rn4 + n_rn3 + n_rn2) + (0.5 * n_rn1) + (0.5 * n_pn1)
    constant = (-100 * n_rn3) - (250 * n_rn2) + (25 * n_rn1) - (75 * n_pn1)

    if coeff_x == 0:
        st.error("ไม่สามารถคำนวณได้เนื่องจากไม่มีบุคลากรหลัก")
        st.stop()

    approx_x = (total_revenue - constant) / coeff_x

    base_rn4 = int(approx_x)
    if base_rn4 % 2 != 0:
        base_rn4 -= 1

    if base_rn4 < 0:
        st.warning(f"รายรับรวม ({total_revenue:,} บาท) ไม่เพียงพอสำหรับจ่ายตามสูตรขั้นต่ำ → ตั้ง RN4=0")
        base_rn4 = 0

    inc_rn4 = int(base_rn4)
    inc_rn3 = int(base_rn4 - 100)
    inc_rn2 = int(base_rn4 - 250)
    inc_rn1 = int((base_rn4 + 50) / 2)
    inc_pn1 = int((base_rn4 - 150) / 2)

    current_total = (inc_rn4 * n_rn4) + (inc_rn3 * n_rn3) + (inc_rn2 * n_rn2) + (inc_rn1 * n_rn1) + (inc_pn1 * n_pn1)
    remainder = total_revenue - int(current_total)

    note = ""
    final_remainder = remainder

    if n_pn1 > 0 and remainder > 0:
        top_up_per_pn = remainder // int(n_pn1)
        inc_pn1 += int(top_up_per_pn)
        used_for_topup = int(top_up_per_pn) * int(n_pn1)
        final_remainder = remainder - used_for_topup
        note = f"มีการนำเงินเหลือ {remainder:,} บาท เกลี่ยเพิ่มให้ PN คนละ {top_up_per_pn:,} บาท"
    elif n_pn1 == 0 and remainder > 0:
        note = f"มียอดเงินเหลือ {remainder:,} บาท แต่ไม่มี PN ให้เกลี่ย"

    final_total_payout = (inc_rn4 * n_rn4) + (inc_rn3 * n_rn3) + (inc_rn2 * n_rn2) + (inc_rn1 * n_rn1) + (inc_pn1 * n_pn1)

    st.divider()
    st.write(f"💰 รายรับรวมจากผู้ป่วย: **{total_revenue:,} บาท**")
    st.write(f"💸 จ่ายจริงรวม: **{int(final_total_payout):,} บาท**")
    st.write(f"🔹 เงินคงเหลือ (ปัดเศษ): **{int(final_remainder):,} บาท**")
    if note:
        st.info(note)
    st.divider()

    data = [
        ["RN4", int(n_rn4), inc_rn4, int(inc_rn4 * n_rn4)],
        ["RN3", int(n_rn3), inc_rn3, int(inc_rn3 * n_rn3)],
        ["RN2", int(n_rn2), inc_rn2, int(inc_rn2 * n_rn2)],
        ["RN1", int(n_rn1), inc_rn1, int(inc_rn1 * n_rn1)],
        ["PN1", int(n_pn1), inc_pn1, int(inc_pn1 * n_pn1)],
    ]

    df = pd.DataFrame(data, columns=["ระดับ", "จำนวนคน", "รายได้ต่อคน (บาท)", "รวมจ่าย (บาท)"])
    df_filtered = df[df["จำนวนคน"] > 0]

    if len(df_filtered) > 0:
        st.dataframe(df_filtered, hide_index=True, use_container_width=True)
    else:
        st.warning("ไม่พบข้อมูลบุคลากรในรอบนี้")
