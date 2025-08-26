import streamlit as st
import pandas as pd
import plotly.graph_objects as go 
import plotly.express as px
from pathlib import Path

# ---------------------------------------------------------------------
# Page configuration
st.set_page_config(
    page_title='PrC Dashboard',
    page_icon=':earth_americas:',
    layout="wide"
)

st.title(":earth_americas: Data Analysis Dashboard")
st.write("Interactive dashboard to analyze sales and customer data.")

# ---------------------------------------------------------------------
# Load CSV / Excel data
@st.cache_data(ttl=3600)

def load_data():
    actuals_df = pd.read_csv("data/Actuals_data.csv")
    location_df = pd.read_excel("data/Location.xlsx")

    # Convert numeric columns
    actuals_df['Sales(€)'] = pd.to_numeric(actuals_df['Sales(€)'], errors='coerce')
    actuals_df['Customers'] = pd.to_numeric(actuals_df['Customers'], errors='coerce')

    # Convert Date
    actuals_df['Date'] = pd.to_datetime(actuals_df['Date'], dayfirst=True, errors='coerce')
    actuals_df['Year'] = actuals_df['Date'].dt.year
    actuals_df['Month'] = actuals_df['Date'].dt.month

    # Merge with location to get Country, City, Restaurant_Name
    merged_df = pd.merge(
        actuals_df,
        location_df[['Rest_Key', 'Country', 'City', 'Restaurant_Name']],
        on='Rest_Key',
        how='left'
    )

    return actuals_df, location_df, merged_df
actuals_df, location_df, merged_df = load_data()

# ---------------------------------------------------------------------
# Sidebar Filters
st.sidebar.header("Filters")

# Year range filter
min_year, max_year = int(merged_df['Year'].min()), int(merged_df['Year'].max())
selected_year_range = st.sidebar.slider(
    "Select Year Range:",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year)
)

# Country multiselect
countries = merged_df['Country'].dropna().unique()
selected_countries = st.sidebar.multiselect(
    "Select Country/Countries:",
    options=sorted(countries),
    default=sorted(countries)  # default selects all
)

# City multiselect
cities = merged_df['City'].dropna().unique()
selected_cities = st.sidebar.multiselect(
    "Select City/Cities:",
    options=sorted(cities),
    default=sorted(cities)  # default selects all
)

# Restaurant multiselect
restaurants = merged_df['Restaurant_Name'].dropna().unique()
selected_restaurants = st.sidebar.multiselect(
    "Select Restaurant(s):",
    options=sorted(restaurants),
    default=[]  # default none selected
)

# ---------------------------------------------------------------------
# Filtered data
filtered_df = merged_df[
    (merged_df['Year'] >= selected_year_range[0]) &
    (merged_df['Year'] <= selected_year_range[1])
]

if selected_countries:
    filtered_df = filtered_df[filtered_df['Country'].isin(selected_countries)]

if selected_cities:
    filtered_df = filtered_df[filtered_df['City'].isin(selected_cities)]

if selected_restaurants:
    filtered_df = filtered_df[filtered_df['Restaurant_Name'].isin(selected_restaurants)]

# Monthly Sales + Number of Restaurants

st.subheader("Monthly Sales and Number of Restaurants")

sales_by_month = filtered_df.groupby('Month')['Sales(€)'].sum()
restaurants_by_month = filtered_df.groupby('Month')['Rest_Key'].nunique()
month_names = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
st.subheader("Monthly Sales and Restaurant Count Table")

# Combine sales and restaurant counts into one DataFrame
monthly_summary = pd.DataFrame({
    'Month': [month_names[m-1] for m in sales_by_month.index],
    'Total Sales (€)': sales_by_month.values,
    'Number of Restaurants': restaurants_by_month.values
})

# Display in Streamlit
st.dataframe(monthly_summary)
fig_sales = go.Figure()
fig_sales.add_trace(go.Bar(
    x=[month_names[m-1] for m in sales_by_month.index],
    y=sales_by_month.values,
    name='Sales (€)',
    marker_color='blue',
    yaxis='y1'
))
fig_sales.add_trace(go.Scatter(
    x=[month_names[m-1] for m in restaurants_by_month.index],
    y=restaurants_by_month.values,
    name='Number of Restaurants',
    marker_color='orange',
    mode='lines+markers',
    yaxis='y2'
))
fig_sales.update_layout(
    title="Sales and Restaurant Count by Month",
    xaxis=dict(title='Month'),
    yaxis=dict(title=dict(text='Sales (€)', font=dict(color='blue')), tickfont=dict(color='blue')),
    yaxis2=dict(title=dict(text='Number of Restaurants', font=dict(color='orange')), tickfont=dict(color='orange'),
                overlaying='y', side='right'),
    legend=dict(x=0.1, y=1.1, orientation='h')
)
st.plotly_chart(fig_sales, use_container_width=True)

# ---------------------------------------------------------------------
# Total Customers per Restaurant
st.subheader("Total Customers per Restaurant")

customers_by_restaurant = filtered_df.groupby('Restaurant_Name')['Customers'].sum().reset_index()
customers_by_restaurant.columns = ['Restaurant Name', 'Total Customers']
customers_by_restaurant = customers_by_restaurant.sort_values(by='Total Customers', ascending=False)
st.dataframe(customers_by_restaurant)

# ---------------------------------------------------------------------
# Total Customers per Country
st.subheader("Total Customers per Country")

customers_by_country = filtered_df.groupby('Country')['Customers'].sum().reset_index()
customers_by_country.columns = ['Country', 'Total Customers']
customers_by_country = customers_by_country.sort_values(by='Total Customers', ascending=False)
st.dataframe(customers_by_country)

# ---------------------------------------------------------------------
# Pie Chart: Customer Distribution by Country
st.subheader("Customer Distribution by Country")

fig_pie = px.pie(
    customers_by_country,
    names='Country',
    values='Total Customers',
    title='Total Customers by Country',
    hole=0.3
)
fig_pie.update_traces(textposition='inside', textinfo='percent+label')
st.plotly_chart(fig_pie, use_container_width=True)
# st.subheader("Customer Distribution by Channel")
# sales_by_channel = filtered_df.groupby('Channel Description')['Sales(€)'].sum().reset_index()
# sales_by_channel.columns = ['Channel', 'Total Sales (€)']
# sales_by_channel = sales_by_channel.sort_values(by='Total Sales (€)', ascending=False)

# fig_channel_pie = px.pie(
#     sales_by_channel,
#     names='Channel',
#     values='Total Sales (€)',
#     title='Total Sales by Channel',
#     hole=0.3
# )
# fig_channel_pie.update_traces(textposition='inside', textinfo='percent+label')
# st.plotly_chart(fig_channel_pie, use_container_width=True)