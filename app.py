app.py
import streamlit as st

st.set_page_config(page_title="Dialysis App", layout="centered")

st.title("คำนวณรายได้ศูนย์ฟอกไต")

with st.form("calc"):
    patients = st.number_input("จำนวนคนไข้", 0)

    st.subheader("จำนวนพยาบาลในรอบ")
    c1, c2 = st.columns(2)

    with c1:
        rn4 = st.number_input("RN4", 0)
        rn2 = st.number_input("RN2", 0)
        pn1 = st.number_input("PN1", 0)

    with c2:
        rn3 = st.number_input("RN3", 0)
        rn1 = st.number_input("RN1", 0)

    submit = st.form_submit_button("คำนวณ")

if submit:
    revenue = patients * 2500  # สูตรตัวอย่าง
    st.success(f"รายได้ประมาณ {revenue:,} บาท")
