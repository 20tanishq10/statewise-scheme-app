import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import zipfile
import os

# Unzip the shape files
with zipfile.ZipFile("india_ds.zip", 'r') as zip_ref:
    zip_ref.extractall("india_shapefile")

# Load shape file
gdf = gpd.read_file("india_shapefile/india_ds.shp")
gdf_states = gdf.dissolve(by="STATE")  # 'STATE' = column having state names

# Load schemes CSV
df = pd.read_csv("sample3.csv")

st.title("State-wise Scheme Benefits Explorer")

# Streamlit Form
with st.form(key='eligibility_form'):
    category_input = st.selectbox("Select Category", df['Category'].unique())
    gender_input = st.selectbox("Select Gender", ['Male', 'Female', 'Other'])
    income_input = st.slider("Select Annual Income (\u20b9)", 0, 500000, 100000)
    submit_button = st.form_submit_button(label='Submit')

if submit_button:
    # Filter based on form
    filtered_df = df[
        (df['Category'] == category_input) &
        ((df['Gender'] == gender_input) | (df['Gender'] == 'Any')) &
        (df['Max Annual Income'] >= income_input)
    ]

    if filtered_df.empty:
        st.warning("No schemes found for the selected inputs.")
    else:
        # Group total benefit per state
        df_total_benefit = filtered_df.groupby('State').agg({'Benefit': 'sum'}).reset_index()
        df_total_benefit.rename(columns={'Benefit': 'Total Benefit'}, inplace=True)

        # Create scheme summary per state
        df_scheme_summary = filtered_df.groupby('State').apply(
            lambda x: '<br>'.join(f"{row['Scheme Name']}: \u20b9{row['Benefit']:,}" for _, row in x.iterrows())
        ).reset_index(name='Scheme Details')

        # Merge both summaries
        df_state_summary = pd.merge(df_total_benefit, df_scheme_summary, on='State', how='left')

        # Merge with shapefile
        gdf_merged = gdf_states.merge(df_state_summary, how='left', left_on='STATE', right_on='State')
        gdf_merged['Total Benefit'] = gdf_merged['Total Benefit'].fillna(0)
        gdf_merged['Scheme Details'] = gdf_merged['Scheme Details'].fillna("No Schemes Available")

        # Prepare GeoJSON for Plotly
        gdf_merged_json = gdf_merged.__geo_interface__

        # Plot Choropleth Map
        fig = px.choropleth(
            gdf_merged,
            geojson=gdf_merged_json,
            locations=gdf_merged.index,
            color="Total Benefit",
            color_continuous_scale="Viridis",
            projection="mercator",
            hover_name="State",
            hover_data={
                "Scheme Details": True,
                "Total Benefit": ":,.0f"
            },
            width=1000,
            height=700
        )

        fig.update_geos(fitbounds="locations", visible=False)
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        st.plotly_chart(fig, use_container_width=True)

        # Show the filtered table below
        st.subheader("Schemes You Are Eligible For")
        st.dataframe(filtered_df[['Scheme Name', 'State', 'Benefit']].reset_index(drop=True))
