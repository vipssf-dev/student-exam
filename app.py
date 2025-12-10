import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# إعداد الصفحة
st.set_page_config(page_title="تحليل نتائج الطلاب في المواد المهارية", layout="wide")

st.title("📊 تحليل نتائج الطلاب في المواد المهارية")
st.write("الفصل الدراسي الأول / الثاني")

# القوائم المنسدلة
subjects = ["لغتي", "الرياضيات", "العلوم", "اللغة الإنجليزية"]
grades = ["الأول الابتدائي", "الثاني الابتدائي", "الثالث الابتدائي",
          "الرابع الابتدائي", "الخامس الابتدائي", "السادس الابتدائي"]
grade_map = {
    "الأول الابتدائي": 1,
    "الثاني الابتدائي": 2,
    "الثالث الابتدائي": 3,
    "الرابع الابتدائي": 4,
    "الخامس الابتدائي": 5,
    "السادس الابتدائي": 6,
}

sections = ["1", "2", "3", "4"]

col1, col2, col3 = st.columns(3)
with col1:
    subject = st.selectbox("اختر المادة", subjects)
with col2:
    grade_label = st.selectbox("اختر الصف", grades)
    grade_value = grade_map[grade_label]
with col3:
    section = st.selectbox("اختر الفصل (الشعبة)", sections)

st.markdown("---")

st.subheader("📁 رفع ملفات الإكسل للفترات")

col_p1, col_p2, col_p3 = st.columns(3)
with col_p1:
    file_p1 = st.file_uploader("الفترة الأولى", type=["xlsx", "xls"], key="p1")
with col_p2:
    file_p2 = st.file_uploader("الفترة الثانية", type=["xlsx", "xls"], key="p2")
with col_p3:
    file_final = st.file_uploader("نهاية الفصل الدراسي", type=["xlsx", "xls"], key="p3")

st.info("يجب أن تحتوي ملفات الإكسل على الأعمدة التالية: student_id, student_name, grade, section, score", icon="ℹ️")


def load_period_df(uploaded_file, period_name):
    if uploaded_file is None:
        return None
    try:
        df = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"خطأ في قراءة ملف {period_name}: {e}")
        return None

    required_cols = {"student_id", "student_name", "grade", "section", "score"}
    if not required_cols.issubset(df.columns):
        st.error(f"ملف {period_name} لا يحتوي على الأعمدة المطلوبة: {required_cols}")
        return None

    # فلترة حسب الصف والفصل
    df = df[df["grade"] == grade_value]
    df = df[df["section"] == int(section)]

    # إضافة اسم الفترة
    df = df.copy()
    df["period"] = period_name
    return df


df_p1 = load_period_df(file_p1, "الفترة الأولى")
df_p2 = load_period_df(file_p2, "الفترة الثانية")
df_final = load_period_df(file_final, "نهاية الفصل")


def merge_periods(dfs):
    # دمج الملفات على مستوى الطالب
    main_df = None
    for period_name, df in dfs.items():
        if df is None or df.empty:
            continue
        df_period = df[["student_id", "student_name", "score"]].copy()
        df_period = df_period.rename(columns={"score": f"{period_name}"})
        if main_df is None:
            main_df = df_period
        else:
            main_df = pd.merge(main_df, df_period, on=["student_id", "student_name"], how="outer")
    return main_df


dfs_dict = {
    "الفترة الأولى": df_p1,
    "الفترة الثانية": df_p2,
    "نهاية الفصل": df_final,
}

if any(df is not None and not df.empty for df in dfs_dict.values()):
    st.markdown("## 📈 الإحصائيات العامة")

    merged = merge_periods(dfs_dict)

    if merged is None or merged.empty:
        st.warning("لا توجد بيانات بعد تطبيق الفلترة على الصف/الفصل المحدد.")
    else:
        score_cols = [c for c in merged.columns if c in ["الفترة الأولى", "الفترة الثانية", "نهاية الفصل"]]
        merged["متوسط الطالب"] = merged[score_cols].mean(axis=1, skipna=True)

        def classify_student(row):
            base = row.get("نهاية الفصل", np.nan)
            if pd.isna(base):
                base = row["متوسط الطالب"]
            if pd.isna(base):
                return "بدون بيانات"
            if base < 50:
                return "ضعيف"
            elif base >= 90:
                return "متفوق"
            else:
                return "مستوى متوسط"

        merged["تصنيف"] = merged.apply(classify_student, axis=1)

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("عدد الطلاب", len(merged))
        with col_b:
            st.metric("عدد الطلاب الضعاف (< 50%)", int((merged["تصنيف"] == "ضعيف").sum()))
        with col_c:
            st.metric("عدد الطلاب المتفوقين (≥ 90%)", int((merged["تصنيف"] == "متفوق").sum()))

        st.markdown("### 🧾 جدول تفصيلي")
        st.dataframe(merged.style.format(precision=2), use_container_width=True)

        col_w, col_g = st.columns(2)
        with col_w:
            st.markdown("#### 👎 الطلاب الضعاف")
            st.dataframe(merged[merged["تصنيف"] == "ضعيف"], use_container_width=True)
        with col_g:
            st.markdown("#### 🌟 الطلاب المتفوقون")
            st.dataframe(merged[merged["تصنيف"] == "متفوق"], use_container_width=True)

        st.markdown("---")
        st.markdown("## 📊 مقارنة الفترات")

        if len(score_cols) >= 2:
            long_df = merged.melt(
                id_vars=["student_id", "student_name"],
                value_vars=score_cols,
                var_name="الفترة",
                value_name="الدرجة"
            )

            avg_by_period = long_df.groupby("الفترة")["الدرجة"].mean().reset_index()
            fig1 = px.bar(avg_by_period, x="الفترة", y="الدرجة",
                          title="متوسط درجات الصف في الفترات",
                          text="الدرجة", range_y=[0, 100])
            fig1.update_traces(textposition="outside")
            st.plotly_chart(fig1, use_container_width=True)

            st.markdown("### 🔍 تقدم طالب معين")
            student_names = merged["student_name"].tolist()
            selected_student = st.selectbox("اختر الطالب", student_names)
            stu_row = merged[merged["student_name"] == selected_student].iloc[0]
            stu_scores = {col: stu_row[col] for col in score_cols}

            stu_df = pd.DataFrame({
                "الفترة": list(stu_scores.keys()),
                "الدرجة": list(stu_scores.values())
            })

            fig2 = px.line(stu_df, x="الفترة", y="الدرجة", markers=True,
                           title=f"تقدم الطالب: {selected_student}",
                           range_y=[0, 100])
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("لإظهار مقارنة الفترات، يلزم رفع ملفين على الأقل.")
else:
    st.warning("الرجاء رفع ملف واحد على الأقل لعرض الإحصائيات.")

