import math
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Dialysis Income", layout="centered")

# =========================
# Logic (ยกมาจากของเดิมแทบทั้งหมด)
# =========================
def solve_rn4_real(total_income, n4, n3, n2, n1, npn):
    """
    total_income = RN4*n4 + (RN4-100)*n3 + (RN4-250)*n2 + ((RN4+50)/2)*n1 + ((RN4-150)/2)*npn
    => total_income = A*RN4 + B
    """
    A = (n4 + n3 + n2) + 0.5*n1 + 0.5*npn
    B = (-100*n3) + (-250*n2) + (25*n1) + (-75*npn)
    if A == 0:
        return None
    return (total_income - B) / A

def rates_from_rn4_even(rn4_even):
    rn3 = rn4_even - 100
    rn2 = rn4_even - 250
    rn1 = (rn4_even + 50) // 2
    pn1_base = (rn4_even - 150) // 2
    return {"RN4": rn4_even, "RN3": rn3, "RN2": rn2, "RN1": rn1, "PN1_base": pn1_base}

def base_payout(rates, n4, n3, n2, n1, npn):
    return (
        rates["RN4"]*n4 +
        rates["RN3"]*n3 +
        rates["RN2"]*n2 +
        rates["RN1"]*n1 +
        rates["PN1_base"]*npn
    )

def pick_best_rn4_even(total_income, n4, n3, n2, n1, npn):
    rn4_real = solve_rn4_real(total_income, n4, n3, n2, n1, npn)
    if rn4_real is None:
        return None

    start = int(math.floor(rn4_real))
    if start % 2 != 0:
        start -= 1
    if start < 0:
        start = 0

    low = max(0, start - 500)
    high = start + 500

    best_detail = None
    best_gap = None

    for rn4_even in range(low, high + 1, 2):
        rates = rates_from_rn4_even(rn4_even)
        bp = base_payout(rates, n4, n3, n2, n1, npn)

        if bp > total_income:
            continue

        missing = total_income - bp

        if npn == 0:
            payout_final = bp
            gap = total_income - payout_final
            remainder_dropped = 0
            pn_final = None
        else:
            add_each = missing // npn
            remainder = missing % npn

            payout_final = bp + add_each*npn
            gap = total_income - payout_final
            remainder_dropped = remainder
            pn_final = rates["PN1_base"] + add_each

        if best_detail is None or gap < best_gap:
            best_gap = gap
            best_detail = {
                "rn4_even": rn4_even,
                "rates": rates,
                "base_payout": bp,
                "missing": missing,
                "payout_final": payout_final,
                "gap": gap,
                "pn_final": pn_final,
                "remainder_dropped": remainder_dropped
            }
            if best_gap == 0:
                break

    return best_detail

def build_result(patients, n4, n3, n2, n1, npn):
    # ---- Validation (เหมือนของเดิม)
    errors = []
    if patients is None or patients <= 0:
        errors.append("จำนวนคนไข้ต้อง > 0")
    for label, v in [("RN4", n4), ("RN3", n3), ("RN2", n2), ("RN1", n1), ("PN1", npn)]:
        if v is None or v < 0:
            errors.append(f"{label} ต้องเป็น 0 หรือจำนวนเต็มบวก")
    if (n4+n3+n2+n1+npn) == 0:
        errors.append("ต้องมีพนักงานอย่างน้อย 1 คน")

    if errors:
        return {"ok": False, "errors": errors}

    total_income = patients * 450
    detail = pick_best_rn4_even(total_income, n4, n3, n2, n1, npn)
    if detail is None:
        return {"ok": False, "errors": ["คำนวณไม่ได้ (ตัวหารเป็นศูนย์/จำนวนคนไม่เหมาะสม)"]}

    rates = detail["rates"]
    rn4_even = detail["rn4_even"]

    rn3_pay = rates["RN3"]
    rn2_pay = rates["RN2"]
    rn1_pay = rates["RN1"]
    pn_base = rates["PN1_base"]
    pn_pay = detail["pn_final"] if npn > 0 else None

    rows = []
    def add_row(role, count, pay_per_person):
        if count > 0:
            rows.append({
                "ตำแหน่ง": role,
                "จำนวนคน": int(count),
                "รายได้/คน (บาท)": int(pay_per_person),
                "รวม (บาท)": int(pay_per_person) * int(count)
            })

    add_row("RN4", n4, rn4_even)
    add_row("RN3", n3, rn3_pay)
    add_row("RN2", n2, rn2_pay)
    add_row("RN1", n1, rn1_pay)
    if npn > 0:
        add_row("PN1", npn, pn_pay)

    df = pd.DataFrame(rows)

    neg_roles = []
    if rn4_even < 0: neg_roles.append("RN4")
    if rn3_pay < 0: neg_roles.append("RN3")
    if rn2_pay < 0: neg_roles.append("RN2")
    if rn1_pay < 0: neg_roles.append("RN1")
    if npn > 0 and pn_pay is not None and pn_pay < 0: neg_roles.append("PN1")
    if npn == 0 and pn_base < 0: neg_roles.append("PN1_base(ไม่มีPNจริง)")

    return {
        "ok": True,
        "patients": patients,
        "total_income": total_income,
        "n4": n4, "n3": n3, "n2": n2, "n1": n1, "npn": npn,
        "rn4_even": rn4_even,
        "df": df,
        "payout_final": detail["payout_final"],
        "gap": detail["gap"],
        "missing": detail["missing"],
        "dropped": detail["remainder_dropped"],
        "neg_roles": neg_roles,
    }

# =========================
# UI (Streamlit)
# =========================
st.markdown("### คำนวณรายได้ศูนย์ฟอกไต (จำนวนเต็ม + เติมส่วนขาดให้ PN แบบเท่าๆกัน)")

# ใช้ session_state เพื่อทำปุ่ม "ล้างค่า"
defaults = {"patients": 0, "rn4": 0, "rn3": 0, "rn2": 0, "rn1": 0, "pn1": 0}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

with st.form("calc_form"):
    patients = st.number_input("จำนวนคนไข้", min_value=0, step=1, key="patients")
    st.markdown("**จำนวนพยาบาล/ผู้ช่วยในรอบนั้น**")

    c1, c2 = st.columns(2)
    with c1:
        n4 = st.number_input("จำนวน RN4", min_value=0, step=1, key="rn4")
        n2 = st.number_input("จำนวน RN2", min_value=0, step=1, key="rn2")
        npn = st.number_input("จำนวน PN1", min_value=0, step=1, key="pn1")
    with c2:
        n3 = st.number_input("จำนวน RN3", min_value=0, step=1, key="rn3")
        n1 = st.number_input("จำนวน RN1", min_value=0, step=1, key="rn1")

    colA, colB = st.columns(2)
    submitted = colA.form_submit_button("คำนวณ")
    reset = colB.form_submit_button("ล้างค่า")

if reset:
    for k, v in defaults.items():
        st.session_state[k] = v
    st.rerun()

if submitted:
    result = build_result(patients, n4, n3, n2, n1, npn)

    if not result["ok"]:
        st.error("พบข้อผิดพลาด")
        for e in result["errors"]:
            st.write(f"- {e}")
    else:
        st.success("คำนวณสำเร็จ")

        st.write("#### สรุป")
        st.write(f"จำนวนคนไข้: {result['patients']}")
        st.write(f"รายได้รวม (คนไข้×450): {result['total_income']:,} บาท")
        st.write(f"จำนวนพนักงาน: RN4={result['n4']}, RN3={result['n3']}, RN2={result['n2']}, RN1={result['n1']}, PN1={result['npn']}")
        st.write(f"RN4 (เลือกเป็นเลขคู่เพื่อให้หาร 2 ลงตัว): {result['rn4_even']} บาท/คน")

        st.write("#### ตารางรายได้")
        st.dataframe(result["df"], use_container_width=True)

        st.write("#### ตรวจสอบยอดรวม")
        st.write(f"ยอดรวมที่จ่ายจริง (หลังปรับ PN เท่ากัน): {result['payout_final']:,} บาท")
        st.write(f"ส่วนต่างจากรายได้รวม (รายได้รวม - ยอดจ่ายจริง): {result['gap']:,} บาท")

        if result["npn"] > 0:
            if result["dropped"] > 0:
                st.info(f"หมายเหตุ: เงินส่วนที่ขาด {result['missing']:,} บาท หาร PN ไม่ลงตัว จึงทิ้งเศษ {result['dropped']} บาท เพื่อให้ PN เท่ากัน")
            else:
                st.info("หมายเหตุ: เติมเงินส่วนขาดให้ PN แล้วลงตัวพอดี")
        else:
            if result["missing"] > 0:
                st.warning(f"ไม่มี PN ให้เติมส่วนขาด {result['missing']:,} บาท")

        if result["neg_roles"]:
            st.warning("เตือน: มีรายได้ติดลบในตำแหน่ง: " + ", ".join(result["neg_roles"]) +
                       "\nแนะนำ: เพิ่มจำนวนคนไข้ หรือปรับจำนวนบุคลากร/สัดส่วนระดับ")
