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
grades = [
    "الأول الابتدائي",
    "الثاني الابتدائي",
    "الثالث الابتدائي",
    "الرابع الابتدائي",
    "الخامس الابتدائي",
    "السادس الابتدائي",
]
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

st.info(
    "يمكن أن تكون عناوين الأعمدة بأي اسم (عربي أو إنجليزي)، "
    "وسيتم اختيار العمود الصحيح من داخل النظام.",
    icon="ℹ️",
)


def load_period_df(uploaded_file, period_name, key_prefix):
    """
    قراءة ملف الفترة (إكسل) مع السماح باختيار أعمدة:
    رقم الطالب - اسم الطالب - الصف - الفصل - الدرجة
    بدون الحاجة لتغيير ملف الإكسل نفسه.
    """
    if uploaded_file is None:
        return None

    try:
        df = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"خطأ في قراءة ملف {period_name}: {e}")
        return None

    st.markdown(f"### إعداد أعمدة ملف: {period_name}")
    st.write("أعمدة الملف:", list(df.columns))

    cols = df.columns.tolist()

    col1, col2, col3 = st.columns(3)
    with col1:
        id_col = st.selectbox(
            f"عمود **رقم الطالب** في {period_name}",
            cols,
            key=f"{key_prefix}_id",
        )
        grade_col = st.selectbox(
            f"عمود **الصف** في {period_name}",
            cols,
            key=f"{key_prefix}_grade",
        )
    with col2:
        name_col = st.selectbox(
            f"عمود **اسم الطالب** في {period_name}",
            cols,
            key=f"{key_prefix}_name",
        )
        section_col = st.selectbox(
            f"عمود **الفصل/الشعبة** في {period_name}",
            cols,
            key=f"{key_prefix}_section",
        )
    with col3:
        score_col = st.selectbox(
            f"عمود **الدرجة** في {period_name}",
            cols,
            key=f"{key_prefix}_score",
        )

    # نبني إطار بيانات قياسي بالأسماء التي يستخدمها بقية الكود
    df_std = pd.DataFrame(
        {
            "student_id": df[id_col],
            "student_name": df[name_col],
            "grade": df[grade_col],
            "section": df[section_col],
            "score": df[score_col],
        }
    )

    # تحويل الصف والفصل إلى أرقام إن لزم
    df_std["grade"] = pd.to_numeric(df_std["grade"], errors="coerce")
    df_std["section"] = pd.to_numeric(df_std["section"], errors="coerce")
    df_std["score"] = pd.to_numeric(df_std["score"], errors="coerce")

    # فلترة حسب الصف والفصل المختارين من الأعلى
    df_std = df_std[df_std["grade"] == grade_value]
    df_std = df_std[df_std["section"] == int(section)]

    # إضافة اسم الفترة
    df_std = df_std.copy()
    df_std["period"] = period_name

    return df_std


def merge_periods(dfs):
    """
    دمج بيانات الفترات على مستوى الطالب (رقم + اسم)
    لتكوين جدول واحد فيه درجات كل فترة.
    """
    main_df = None
    for period_name, df in dfs.items():
        if df is None or df.empty:
            continue
        df_period = df[["student_id", "student_name", "score"]].copy()
        df_period = df_period.rename(columns={"score": f"{period_name}"})
        if main_df is None:
            main_df = df_period
        else:
            main_df = pd.merge(
                main_df,
                df_period,
                on=["student_id", "student_name"],
                how="outer",
            )
    return main_df


# تحميل بيانات الفترات مع اختيار الأعمدة يدويًا من المستخدم
df_p1 = load_period_df(file_p1, "الفترة الأولى", "p1")
df_p2 = load_period_df(file_p2, "الفترة الثانية", "p2")
df_final = load_period_df(file_final, "نهاية الفصل", "pf")

dfs_dict = {
    "الفترة الأولى": df_p1,
    "الفترة الثانية": df_p2,
    "نهاية الفصل": df_final,
}

# لو فيه أي ملف مرفوع وفيه بيانات بعد الفلترة
if any(df is not None and not df.empty for df in dfs_dict.values()):
    st.markdown("## 📈 الإحصائيات العامة")

    merged = merge_periods(dfs_dict)

    if merged is None or merged.empty:
        st.warning("لا توجد بيانات بعد تطبيق الفلترة على الصف/الفصل المحدد.")
    else:
        # أعمدة الدرجات للفترات
        score_cols = [
            c
            for c in merged.columns
            if c in ["الفترة الأولى", "الفترة الثانية", "نهاية الفصل"]
        ]

        # متوسط الطالب عبر الفترات المتاحة
        merged["متوسط الطالب"] = merged[score_cols].mean(axis=1, skipna=True)

        # تصنيف الطلاب
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

        # كروت إحصائية سريعة
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("عدد الطلاب في الصف/الفصل", len(merged))
        with col_b:
            st.metric(
                "عدد الطلاب الضعاف (< 50%)",
                int((merged["تصنيف"] == "ضعيف").sum()),
            )
        with col_c:
            st.metric(
                "عدد الطلاب المتفوقين (≥ 90%)",
                int((merged["تصنيف"] == "متفوق").sum()),
            )

        # جدول تفصيلي
        st.markdown("### 🧾 جدول تفصيلي للطلاب")
        st.dataframe(
            merged[
                ["student_id", "student_name"] + score_cols + ["متوسط الطالب", "تصنيف"]
            ].style.format(precision=2),
            use_container_width=True,
        )

        # الطلاب الضعاف والمتفوقون
        col_w, col_g = st.columns(2)
        with col_w:
            st.markdown("#### 👎 الطلاب الضعاف (< 50%)")
            weak_df = merged[merged["تصنيف"] == "ضعيف"]
            if weak_df.empty:
                st.write("لا يوجد طلاب ضعاف حسب المعايير الحالية.")
            else:
                st.dataframe(
                    weak_df[
                        ["student_id", "student_name"]
                        + score_cols
                        + ["متوسط الطالب"]
                    ],
                    use_container_width=True,
                )
        with col_g:
            st.markdown("#### 🌟 الطلاب المتفوقون (≥ 90%)")
            gifted_df = merged[merged["تصنيف"] == "متفوق"]
            if gifted_df.empty:
                st.write("لا يوجد طلاب متفوقون حسب المعايير الحالية.")
            else:
                st.dataframe(
                    gifted_df[
                        ["student_id", "student_name"]
                        + score_cols
                        + ["متوسط الطالب"]
                    ],
                    use_container_width=True,
                )

        st.markdown("---")
        st.markdown("## 📊 مقارنة الفترات (تقدّم الصف والطلاب)")

        if len(score_cols) >= 2:
            # تحويل البيانات لشكل طويل للرسم
            long_df = merged.melt(
                id_vars=["student_id", "student_name"],
                value_vars=score_cols,
                var_name="الفترة",
                value_name="الدرجة",
            )

            # متوسط الصف في كل فترة
            avg_by_period = long_df.groupby("الفترة")["الدرجة"].mean().reset_index()
            fig1 = px.bar(
                avg_by_period,
                x="الفترة",
                y="الدرجة",
                title=f"متوسط درجات الصف {grade_label} الفصل {section} في الفترات",
                text="الدرجة",
                range_y=[0, 100],
            )
            fig1.update_traces(textposition="outside")
            st.plotly_chart(fig1, use_container_width=True)

            # تقدّم طالب معيّن
            st.markdown("### 🔍 متابعة تقدم طالب معيّن عبر الفترات")
            student_names = merged["student_name"].dropna().tolist()
            if student_names:
                selected_student = st.selectbox("اختر الطالب", student_names)
                stu_row = merged[merged["student_name"] == selected_student].iloc[0]
                stu_scores = {col: stu_row[col] for col in score_cols}

                stu_df = pd.DataFrame(
                    {
                        "الفترة": list(stu_scores.keys()),
                        "الدرجة": list(stu_scores.values()),
                    }
                )

                fig2 = px.line(
                    stu_df,
                    x="الفترة",
                    y="الدرجة",
                    markers=True,
                    title=f"تقدم الطالب: {selected_student}",
                    range_y=[0, 100],
                )
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("لا يوجد طلاب لعرض تقدمهم.", icon="ℹ️")
        else:
            st.info(
                "لإظهار مقارنة الفترات والرسوم البيانية، ارفع ملفين على الأقل من الفترات الثلاث.",
                icon="ℹ️",
            )
else:
    st.warning("الرجاء رفع ملف واحد على الأقل لعرض الإحصائيات.", icon="⚠️")
