import streamlit as st
import pandas as pd
import plotly.express as px

# ==========================
# Page configuration
# ==========================
st.set_page_config(
    page_title="Health Facility Dashboard",
    page_icon="🏥",
    layout="wide"
)

# Sidebar top-left icon
st.sidebar.image(r"Uganda Flag.jpg", width=200)
st.sidebar.title("Dashboard")
page = st.sidebar.radio("Go to", ["Overview", "Report", "Performance Metrics", "Geo Visualizer", "Feedback"])

# ==========================
# Load cleaned health data
# ==========================
DATA_PATH = (r"cleaned_health_data.xls")
df = pd.read_csv(DATA_PATH)

# ==========================
# Overview Page
# ==========================
if page == "Overview":
    st.title("Health Facility Dashboard - Overview")

    # Metric cards
    col1, col2, col3, col4 = st.columns(4)
    col1.markdown("**Country**\nUganda")
    col2.markdown("**District**\nKasese")
    col3.markdown("**Sub-counties**\n157")
    col4.markdown("**Health Facilities**\n158")

    st.subheader("Subcounty Health Facility Summary")
    subcounty_list = sorted(df['subcountydivision'].dropna().unique())
    selected_subcounties = st.multiselect("Select Subcounties", subcounty_list)

    if selected_subcounties:
        filtered_df = df[df['subcountydivision'].isin(selected_subcounties)]
        total_facilities = filtered_df['health_facility'].nunique()
    else:
        total_facilities = 0

    st.markdown(
        f"<div style='text-align:center; margin-top:20px;'><h2>Total Health Facilities</h2><h1 style='color:#2E86C1;'>{total_facilities}</h1></div>",
        unsafe_allow_html=True
    )

    # AGYW Population
    authorities = df['authority'].dropna().unique()
    selected_authority = st.selectbox("Select Authority", authorities)
    filtered_subcounties = df[df['authority'] == selected_authority]['subcountydivision'].dropna().unique()
    selected_subcounties = st.multiselect("Select Subcounty(s)", filtered_subcounties)

    if selected_subcounties:
        result_df = (
            df[df['subcountydivision'].isin(selected_subcounties)]
            .loc[:, ['subcountydivision', 'agyw_population']]
            .drop_duplicates(subset='subcountydivision')
            .reset_index(drop=True)
        )
        result_df['agyw_population'] = result_df['agyw_population'].astype(int)
        st.markdown("<h3 style='text-align:center;'>AGYW Population</h3>", unsafe_allow_html=True)
        st.dataframe(
            result_df.style.set_table_styles([{'selector': 'th, td', 'props': [('text-align', 'center')]}])
        )

# ==========================
# Report Page
# ==========================
if page == "Report":
    st.subheader("Report Dashboard")
    st.sidebar.subheader("Report Filters")

    selected_subcounty = st.sidebar.selectbox("Select Subcounty", sorted(df['subcountydivision'].dropna().unique()))
    facilities = df[df['subcountydivision'] == selected_subcounty]['health_facility'].dropna().unique()
    selected_facility = st.sidebar.selectbox("Select Health Facility", facilities)
    selected_year = st.sidebar.selectbox("Select Year", sorted(df['year'].dropna().unique()))
    selected_month = st.sidebar.selectbox("Select Month", sorted(df['month'].dropna().unique()))

    if st.sidebar.button("Generate Report"):
        filtered_df = df[
            (df['subcountydivision'] == selected_subcounty) &
            (df['health_facility'] == selected_facility) &
            (df['year'] == selected_year) &
            (df['month'] == selected_month)
        ]

        display_columns = [
            'anc1_total', 'anc4_total', 'maternal_deaths_total', 'newborn_deaths_07_days', 'deliveries_total',
            'preterms_births_in_the_unit__total', 'births_in_the_unit__live_births__25_kg',
            'fp_im_total', 'fp_pa_total', 'fp_implant3_total', 'fp_implant5_total',
            'fp_iudt_total', 'fp_iudh_total'
        ]

        if not filtered_df.empty:
            st.subheader("Health Facility Data")
            st.dataframe(filtered_df[display_columns].reset_index(drop=True))

            csv = filtered_df[display_columns].to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Data as CSV",
                data=csv,
                file_name=f"{selected_facility}_analytics_{selected_year}_{selected_month}.csv",
                mime='text/csv'
            )

            # Cascade chart
            total_deliveries = int(filtered_df['deliveries_total'].sum())
            maternal_deaths = int(filtered_df['maternal_deaths_total'].sum())
            preterm_births = int(filtered_df['preterms_births_in_the_unit__total'].sum())
            low_birth_weight = int(filtered_df['births_in_the_unit__live_births__25_kg'].sum())
            newborn_deaths = int(filtered_df['newborn_deaths_07_days'].sum())

            cascade_df = pd.DataFrame({
                "Indicator": ["Total Deliveries", "Maternal Deaths", "Preterm Births", "Births < 2.5kg", "Newborn Deaths"],
                "Count": [total_deliveries, maternal_deaths, preterm_births, low_birth_weight, newborn_deaths]
            })

            fig = px.bar(cascade_df, x="Indicator", y="Count", text="Count", title="Cascade of Birth Outcomes")
            fig.update_traces(texttemplate='%{text}', textposition='outside')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No data available for the selected filters.")

# ==========================
# Performance Metrics
# ==========================
if page == "Performance Metrics":
    st.title("Adverse Pregnancy Outcomes Dashboard")

    # Load predicted data
    predicted_path = (r"predicted_data.csv")
    test_df = pd.read_csv(predicted_path)

    if 'year' not in test_df.columns:
        st.error("Column 'year' not found in CSV.")
        st.stop()

    selected_year = st.sidebar.selectbox("Select Year", sorted(test_df['year'].dropna().unique()))
    df_year = test_df[test_df['year'] == selected_year].copy()

    # Ensure numeric columns
    df_year['predicted_anc'] = df_year['predicted_anc'].fillna(0).round().astype(int)
    df_year['predicted_deliveries'] = df_year['predicted_deliveries'].fillna(0).round().astype(int)

    # Summary table
    required_cols = [
        'health_facility', 'predicted_preterm_adverse', 'predicted_lowbirthweight_adverse',
        'predicted_maternal_adverse', 'predicted_newborn_adverse', 'predicted_deliveries'
    ]
    missing_cols = [col for col in required_cols if col not in df_year.columns]
    if missing_cols:
        st.error(f"Missing columns in CSV: {missing_cols}")
        st.stop()

    summary_df = df_year.groupby('health_facility').agg({
        'predicted_preterm_adverse':'sum',
        'predicted_lowbirthweight_adverse':'sum',
        'predicted_newborn_adverse':'sum',
        'predicted_maternal_adverse':'sum',
        'predicted_deliveries':'sum'
    }).reset_index()

    summary_df.rename(columns={
        'predicted_preterm_adverse': 'Total Predicted Preterm Cases',
        'predicted_lowbirthweight_adverse': 'Total Predicted Low Birth Weight Cases',
        'predicted_newborn_adverse': 'Total Predicted New Birth Weight Cases',
        'predicted_maternal_adverse': 'Total Predicted Maternal Cases',
        'predicted_deliveries': 'Total Predicted Deliveries'
    }, inplace=True)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Facilities with Preterm Cases", summary_df['Total Predicted Preterm Cases'].gt(0).sum())
    col2.metric("Facilities with LBW Cases", summary_df['Total Predicted Low Birth Weight Cases'].gt(0).sum())
    col3.metric("Facilities with Neonatal Deaths", summary_df['Total Predicted New Birth Weight Cases'].gt(0).sum())
    col4.metric("Facilities with Maternal Deaths", summary_df['Total Predicted Maternal Cases'].gt(0).sum())
    col5.metric("Facilities with High Deliveries", summary_df['Total Predicted Deliveries'].gt(50).sum())

    st.markdown("### Facility-wise Predicted Adverse Events")
    st.dataframe(summary_df, use_container_width=True)

    st.download_button(
        label="📄 Download Summary (CSV)",
        data=summary_df.to_csv(index=False).encode('utf-8'),
        file_name=f"facility_adverse_summary_{selected_year}.csv",
        mime="text/csv"
    )

    # Month order
    month_order = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    if df_year['month'].dtype != 'object':
        df_year['month'] = df_year['month'].apply(lambda x: month_order[int(x)-1])

    # -------------------
    # Line graphs
    # -------------------
    # ANC1 line graph
    monthly_anc = df_year.groupby('month')['predicted_anc'].sum().reindex(month_order).fillna(0).astype(int).reset_index()
    st.subheader("📈 Total Predicted ANC1 per Month")
    fig1 = px.line(monthly_anc, x="month", y="predicted_anc", markers=True, text="predicted_anc")
    fig1.update_traces(textposition='top center')
    st.plotly_chart(fig1, use_container_width=True)

    # Deliveries line graph
    monthly_del = df_year.groupby('month')['predicted_deliveries'].sum().reindex(month_order).fillna(0).astype(int).reset_index()
    st.subheader("📈 Total Predicted Deliveries per Month")
    fig2 = px.line(monthly_del, x="month", y="predicted_deliveries", markers=True, text="predicted_deliveries")
    fig2.update_traces(textposition='top center')
    st.plotly_chart(fig2, use_container_width=True)

    # -------------------
    # ANC filter table
    # -------------------
    st.subheader("🏥 Filter Facilities by Predicted ANC1 Range")
    anc_range = st.selectbox("Choose ANC1 Range", ["Choose option", "0-49", "50-99", ">=100"], index=0)
    if anc_range != "Choose option":
        if anc_range == "0-49":
            filt = df_year[df_year['predicted_anc'] <= 49]
        elif anc_range == "50-99":
            filt = df_year[(df_year['predicted_anc'] >= 50) & (df_year['predicted_anc'] <= 99)]
        else:
            filt = df_year[df_year['predicted_anc'] >= 100]

        anc_table = filt.groupby(['health_facility','month'])['predicted_anc'].sum().reset_index()
        anc_table.columns = ['Health Facility','Month','Total Predicted ANC1']
        st.dataframe(anc_table, use_container_width=True)

    # -------------------
    # Deliveries filter table
    # -------------------
    st.subheader("🏥 Filter Facilities by Predicted Deliveries Range")
    del_range = st.selectbox("Choose Deliveries Range", ["Choose option", "0-49", "50-99", ">=100"], index=0)
    if del_range != "Choose option":
        if del_range == "0-49":
            filt_del = df_year[df_year['predicted_deliveries'] <= 49]
        elif del_range == "50-99":
            filt_del = df_year[(df_year['predicted_deliveries'] >= 50) & (df_year['predicted_deliveries'] <= 99)]
        else:
            filt_del = df_year[df_year['predicted_deliveries'] >= 100]

        del_table = filt_del.groupby(['health_facility','month'])['predicted_deliveries'].sum().reset_index()
        del_table.columns = ['Health Facility','Month','Total Predicted Deliveries']
        st.dataframe(del_table, use_container_width=True)

if page == "Geo Visualizer":
    st.title("🗺️ Kasese Health Facilities Map")

    GEO_PATH = r"C:\Users\RAuma.ug\OneDrive - Population Services International\Desktop\Mine\UCU\Semester One\Object Oriented Programming\Exam\predicted_data.csv"
    geo_df = pd.read_csv(GEO_PATH)

    kasese_df = geo_df[geo_df['district'].str.upper() == "KASESE"].copy()
    if 'latitude' not in kasese_df.columns or 'longitude' not in kasese_df.columns:
        st.error("Latitude or Longitude columns not found.")
        st.stop()

    kasese_df = kasese_df.dropna(subset=['latitude', 'longitude'])

    indicator = st.selectbox(
        "Select Indicator to Display",
        options=[
            "predicted_anc",
            "predicted_deliveries",
            "predicted_maternal_adverse",
            "predicted_newborn_adverse",
            "predicted_lowbirthweight_adverse",
            "predicted_preterm_adverse"
        ]
    )

    kasese_df[indicator] = pd.to_numeric(kasese_df[indicator], errors='coerce').fillna(0)
    kasese_df['hover_info'] = kasese_df['health_facility'] + "<br>" + indicator + ": " + kasese_df[indicator].astype(int).astype(str)

    fig = px.scatter_mapbox(
        kasese_df,
        lat="latitude",
        lon="longitude",
        color=indicator,
        size=indicator,
        hover_name="hover_info",
        color_continuous_scale="YlOrRd",
        size_max=15,
        zoom=11,
        center={"lat": 0.1699, "lon": 30.0781},
        mapbox_style="carto-positron"
    )
    st.plotly_chart(fig, use_container_width=True)


# ==========================
# Feedback Page
# ==========================
if page == "Feedback":
    st.title("Share Your Feedback")
    feedback_message = st.text_area("Message *", placeholder="Please provide detailed feedback...")
    screenshot = st.file_uploader("Screenshot (Optional)", type=['png', 'jpg', 'jpeg', 'gif'])

    if st.button("Submit Feedback"):
        st.success("Thank you! Your feedback has been submitted.")
    st.info("Your feedback will be reviewed by our team.")
