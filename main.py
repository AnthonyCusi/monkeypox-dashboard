# Libraries
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import streamlit as st
import numpy as np
import altair as alt
from streamlit_option_menu import option_menu
from st_aggrid import GridOptionsBuilder, AgGrid
import geopandas
# from bs4 import BeautifulSoup
# import requests
# import urllib

# Modules
import data_loader
import charts


# -- CHANGES TO MAKE -- #
# check box to 'include suspected cases' which uses the 'Status' column in data


# ---------- Setting Up Webpage ---------- #
st.set_page_config(page_title = 'Monkeypox Dashboard', page_icon = ':bar_chart:', layout = 'wide')

# Hide hamburger menu
hide_st_style = """
            <style>
            footer {visibility: hidden;}
            </style>
            """
            #MainMenu {visibility: hidden;}
            #header {visibility: hidden;}

st.markdown(hide_st_style, unsafe_allow_html=True)

# Reduce padding above nav bar
st.write('<style>div.block-container{padding-top:1rem;}</style>', unsafe_allow_html=True)

# Navigation bar
selected = option_menu(None, ['Home', 'Maps', 'Sources'], 
    icons=['bar-chart-line', 'geo-alt', 'info-circle'], 
    menu_icon="cast", default_index=0, orientation="horizontal",
    styles = {'nav-link': {'--hover-color': '#8E6FF9'}}
)

    #  Add 'Resources' to first list and 'clipboard-check' to second list

# ---------- Loading Data ---------- #

# Initializing dataframes 
dataframes = data_loader.load_all()
full_df = dataframes[0]
cum_df = dataframes[1]
total_df = dataframes[2]

# Gets date data was last updated
date_df = dataframes[3]
last_updated = list(date_df.dt.strftime('%b %d, %Y').head())[0]

# Dataframe with countries and their current cases
country_counts = full_df['Country'].value_counts().to_frame()


# ---------- Sidebar ---------- #
# Logo
st.sidebar.image('content/Monkeypox_Dashboard.png')
st.sidebar.write('')
st.sidebar.write('')

# Filters
st.sidebar.header('Data Filters')
countries = st.sidebar.multiselect('Country Selection', 
    options = list(cum_df['Country'].unique()),
    default = ['United States', 'Germany', 'Spain', 'United Kingdom']
)


# ---------- Home Page ---------- #
if selected == '"Home"' or selected == 'Home':

    # Page Header
    st.write('# Current Monkeypox (MPXV) Cases')
    st.write(f'Data last updated {last_updated}. (Updates Mon-Fri)')
    st.write('') 

    # Gets data for user-selected countries
    selection_df = cum_df[cum_df['Country'].isin(countries)]
   

    # Line chart
    nearest = alt.selection(type='single', nearest=True, on='mouseover',
                            fields=['Date'], empty='none')

    line_chart = alt.Chart(selection_df).mark_line(interpolate = 'basis').encode(
        x = alt.X('Date', axis = alt.Axis(title = 'Date', tickMinStep = 2)),
        y = 'Cumulative Cases',
        color = 'Country'
    )

    selectors = alt.Chart(selection_df).mark_point().encode(
        x = alt.X('Date', axis = alt.Axis(title = 'Date', tickMinStep = 2)),
        opacity=alt.value(0),
    ).add_selection(
        nearest
    )

    points = line_chart.mark_point().encode(
        opacity=alt.condition(nearest, alt.value(1), alt.value(0))
    )

    text = line_chart.mark_text(align='left', dx=5, dy=-5).encode(
        text=alt.condition(nearest, 'Cumulative Cases', alt.value(' '))
    )

    rules = alt.Chart(selection_df).mark_rule(color='gray').encode(
        x = alt.X('Date', axis = alt.Axis(title = 'Date', tickMinStep = 2))
    ).transform_filter(
        nearest
    )

    line_chart = alt.layer(
        line_chart, selectors, points, rules, text
    ).properties(
        width=600, height=300
    ).configure_axisX(labelAngle = 90).interactive()

    st.write('## Cumulative Cases by Country')
    st.write('Select countries to visualize on the left sidebar.')
    st.altair_chart(line_chart, use_container_width=True)

    country_counts_dict = country_counts['Country'].to_dict()
    if 'Democratic Republic Of The Congo' in country_counts_dict:
        country_counts_dict['Dem. Rep. Congo'] = country_counts_dict['Democratic Republic Of The Congo']
        country_counts_dict.pop('Democratic Republic Of The Congo')
    country_counts_dict = sorted(country_counts_dict.items(), key = lambda x: x[1], reverse = True)
    

    names, values = [], []
    for country, cases in country_counts_dict:
        names.append(country)
        values.append(cases)
        
    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)
    col5, col6 = st.columns(2)

    # Cumulative cases table
    with col1:
        st.write('## Cumulative Case Table')
        st.write('#### Select countries to directly compare:')
        merged = charts.get_daily_increases(cum_df, names, values)

        gb = GridOptionsBuilder.from_dataframe(merged)
        gb.configure_side_bar()
        gb.configure_selection('multiple', use_checkbox=True, groupSelectsChildren="Group checkbox select children") #Enable multi-row selection
        gridOptions = gb.build()

        grid_response = AgGrid(
            merged,
            gridOptions=gridOptions,
            data_return_mode='AS_INPUT', 
            update_mode='MODEL_CHANGED', 
            fit_columns_on_grid_load=False,
            theme='dark',
            enable_enterprise_modules=True,
            height=350, 
            width='100%',
            reload_data=True
        )

        selected = grid_response['selected_rows'] 
        selected_df = pd.DataFrame(selected) #Pass the selected rows to a new dataframe
        
    # Direct Comparison Table
    with col2: 
        if selected_df.shape[0] > 0:
            st.write('')
            st.write('')
            st.write('')
            st.write('')
            st.write('')
            st.write('#### Direct Comparison Table')
            gb2 = GridOptionsBuilder.from_dataframe(selected_df)
            gb2.configure_side_bar()
            grid2Options = gb2.build()
            grid2_response = AgGrid(
                selected_df,
                data_return_mode='AS_INPUT', 
                update_mode='MODEL_CHANGED', theme='dark', height=300
            )

    # Total global cases graph
    with col3: 
        st.write('## Total Cases Globally')
        global_case_graph = charts.global_case_graph(total_df)
        fig, ax, ax2 = global_case_graph[0], global_case_graph[1], global_case_graph[2]
        st.pyplot(fig)

    # Global cases pie chart
    with col4:
        st.write('## Breakdown of Global Cases')
        global_pie_chart = charts.global_pie_chart(names, values)
        fig, ax = global_pie_chart[0], global_pie_chart[1]
        st.pyplot(fig)

    # Gender distribution pie chart
    with col5:
        st.write('## Gender Distribution of Cases')
        gender_chart = charts.gender_chart(full_df)
        fig, ax = gender_chart[0], gender_chart[1]
        st.pyplot(fig)
    
    # Hospitalization bar chart
    with col6:
        st.write('## Hospitalization Rates')
        hosp_chart = charts.hospitalization_chart(full_df)
        fig, ax = hosp_chart[0], hosp_chart[1]
        st.pyplot(fig)
        
    st.write('Note: Gender and hospitalization data were not reported for all cases, \
        so the true distribution may vary slightly.')

# ---------- Maps Page ---------- #
if selected == '"Maps"' or selected == 'Maps':

    # Page Header
    st.write('# Current Monkeypox (MPXV) Cases')
    st.write(f'Data last updated {last_updated}.')
    st.write("") 

    # WORLD MAP
    map_df = geopandas.read_file('land_data/country_map/ne_50m_admin_0_countries.shp')
    map_df = map_df[['NAME', 'geometry']]
    st.set_option('deprecation.showPyplotGlobalUse', False)

    # Removing Antarctica from map
    map_df.drop([map_df.index[239]], inplace = True)
    
    # Fixing spelling differences between data sources
    map_df['NAME'] = np.where(map_df['NAME'] == 'United States of America', 'United States', map_df['NAME'])
    map_df['NAME'] = np.where(map_df['NAME'] == 'Bosnia and Herz.', 'Bosnia And Herzegovina', map_df['NAME'])
    map_df['NAME'] = np.where(map_df['NAME'] == 'Congo', 'Republic of Congo', map_df['NAME'])
    map_df['NAME'] = np.where(map_df['NAME'] == 'Dem. Rep. Congo', 'Democratic Republic Of The Congo', map_df['NAME'])
    map_df['NAME'] = np.where(map_df['NAME'] == 'Dominican Rep.', 'Dominican Republic', map_df['NAME'])
    map_df['NAME'] = np.where(map_df['NAME'] == 'Central African Rep.', 'Central African Republic', map_df['NAME'])
    map_df['NAME'] = np.where(map_df['NAME'] == 'Czechia', 'Czech Republic', map_df['NAME'])

    
    base = map_df['NAME'].unique()

    other = country_counts['Country'].to_dict()
    
    uk_current = other['England']
    uk_new = sum([other[country] for country in other if country in ('England', 'Scotland', 'Wales', 'Northern Ireland', 'Cayman Islands')])
    
    other = pd.DataFrame(list(other.items()), columns = ['Country', 'Cases'])
    other.loc[len(other.index)] = ['United Kingdom', uk_new]

    
    merged = map_df.merge(other, how = 'left', left_on = 'NAME',
        right_on = 'Country')
    merged['Cases'] = merged['Cases'].fillna(0)


    # Set range for choropleth values
    # change max to the current max cases
    min, max = 0, round(max(merged['Cases']), -3) 

    # create figure and axes for Matplotlib
    fig, ax = plt.subplots(1, figsize=(30, 10))
 
    # remove the axis
    ax.axis('off')

    ax.set_title('Total Monkeypox Cases per Country', fontdict={'fontsize': '25', 'fontweight' : '4'})


    # colorbar legend
    sm = plt.cm.ScalarMappable(cmap='Purples', norm=plt.Normalize(vmin=min, vmax=max))

    # empty array for data
    sm.set_array([])

    # Displaying colorball legend and map 
    fig.colorbar(sm, orientation="horizontal", fraction=0.036, pad=0.1, aspect = 40)

    merged.plot(column='Cases', cmap='Purples', linewidth=0.8, ax=ax, edgecolor='0.7')

    st.write('## Global Data')
    st.pyplot()
    st.write('')
    st.write('')


    # US MAP
    st.write('## U.S. Data')

    us_map_df = geopandas.read_file('land_data/us_map/cb_2018_us_state_5m.shp')
    us_map_df = us_map_df[['NAME', 'geometry']]
    
    state_cases = pd.read_csv('https://raw.githubusercontent.com/gridviz/monkeypox/main/data/processed/monkeypox_cases_states_cdc_latest.csv')
    state_cases = state_cases[['state', 'cases']]

    us_merged = us_map_df.merge(state_cases, how = 'left', left_on = 'NAME',
        right_on = 'state')
    
    us_merged.dropna(inplace = True)

    # Set range for choropleth values
    # change max to the current max cases
    min2, max2 = 0, round(us_merged['cases'].max(), -3)

    # create figure and axes for Matplotlib
    fig2, ax2 = plt.subplots(1, figsize=(30, 15))
 
    # remove the axis
    ax2.axis('off')

    ax2.set_title('Total Monkeypox Cases per State (Contiguous U.S.)', fontdict={'fontsize': '25', 'fontweight' : '4'})

    bounds = [-129, 25, -61, 50]


    xlim = ([bounds[0], bounds[2]])
    ylim = ([bounds[1],  bounds[3]])

    ax2.set_xlim(xlim)
    ax2.set_ylim(ylim)

    # colorbar legend
    sm2 = plt.cm.ScalarMappable(cmap='Purples', norm=plt.Normalize(vmin=min2, vmax=max2))

    # empty array for data
    sm2.set_array([])

    # Displaying colorball legend and map 
    fig2.colorbar(sm2, orientation="horizontal", fraction=0.036, pad=0.1, aspect = 40)

    # Labeling states
    manual_list = ['Louisiana', 'Mississippi', 'West Virginia', 'Virginia', 'District of Columbia', 'Delaware']
    us_merged.apply(lambda x: ax2.annotate(text = x.NAME + '\n' + str(int(x.cases)), xy = x['geometry'].centroid.coords[0], 
        ha = 'center', fontsize = 14) if x.NAME not in manual_list else '', axis = 1)
    
    # Manual label adjustents
    us_merged.apply(lambda x: ax2.annotate(text = x.NAME + '\n' + str(int(x.cases)), xy = (x['geometry'].centroid.coords[0][0], x['geometry'].centroid.coords[0][1] - 0.5), 
        ha = 'center', fontsize = 14) if x.NAME == 'Louisiana' else '', axis = 1)
    us_merged.apply(lambda x: ax2.annotate(text = x.NAME + '\n' + str(int(x.cases)), xy = (x['geometry'].centroid.coords[0][0], x['geometry'].centroid.coords[0][1] - 0.75), 
        ha = 'center', fontsize = 14) if x.NAME == 'Mississippi' else '', axis = 1)
    us_merged.apply(lambda x: ax2.annotate(text = x.NAME + '\n' + str(int(x.cases)), xy = (x['geometry'].centroid.coords[0][0], x['geometry'].centroid.coords[0][1] - 0.75), 
        ha = 'center', fontsize = 14) if x.NAME == 'West Virginia' else '', axis = 1)
    us_merged.apply(lambda x: ax2.annotate(text = x.NAME + '\n' + str(int(x.cases)), xy = (x['geometry'].centroid.coords[0][0], x['geometry'].centroid.coords[0][1] - 0.75), 
        ha = 'center', fontsize = 14) if x.NAME == 'Virginia' else '', axis = 1)
    us_merged.apply(lambda x: ax2.annotate(text = x.NAME + ': ' + str(int(x.cases)), xy = (x['geometry'].centroid.coords[0][0] + 10, x['geometry'].centroid.coords[0][1]), 
        ha = 'center', fontsize = 14) if x.NAME == 'District of Columbia' else '', axis = 1)
    us_merged.apply(lambda x: ax2.annotate(text = x.NAME + ': ' + str(int(x.cases)), xy = (x['geometry'].centroid.coords[0][0] + 8.2, x['geometry'].centroid.coords[0][1] - 1.4), 
        ha = 'center', fontsize = 14) if x.NAME == 'Delaware' else '', axis = 1)

    us_merged.plot(column='cases', cmap='Purples', linewidth=0.8, ax=ax2, edgecolor='0.7')

    st.pyplot()




   






# ---------- Sources Page ---------- #
if selected in ('"Sources"', 'Sources'):
    st.write('## Sources and Acknowledgments')
    st.write('The visualizations in this dashboard are made possible by public data provided by various sources.')
    st.write('')
    st.write('')
    st.write('Data on Monkeypox cases are provided by Global.health, and can be found at the following repository:')
    st.write(f'https://github.com/globaldothealth/monkeypox (Last accessed: {last_updated})')
    st.write('')
    st.write('Case counts by U.S. state is provided by the CDC:')
    st.write('https://www.cdc.gov/poxvirus/monkeypox/response/2022/us-map.html')
    st.write('')
    st.write('Geographic (GIS) data for map building is provided by Natural Earth at the following link:')
    st.write('http://www.naturalearthdata.com/downloads/50m-cultural-vectors/')
    st.write('')
    st.write('Geographic data for the US map is provided by the United States Census:')  
    st.write('https://www.census.gov/geographies/mapping-files/time-series/geo/carto-boundary-file.html')  
    st.write('')
    st.write('')
    st.write('')
    st.write('')
    st.write('All data is used with permission under a CC-BY-4.0 license.')
    st.write('')
    st.write('')
    st.write('')
    st.write('')
    st.write('')
    st.write('---------------------------------------------------------')
    st.write('Monkeypox Dashboard was created by Anthony Cusimano.')
    st.write('Contribute to the repository! https://github.com/AnthonyCusi/Monkeypox-Dashboard')
    st.write('')
    st.write('Thank you for visiting this page, and please stay safe!')


#st.sidebar.write("https://www.linkedin.com/in/anthonycusi/", color = 'gray')
st.sidebar.write('')
st.sidebar.write('')
st.sidebar.write('')
st.sidebar.write('')
st.sidebar.write('')
st.sidebar.write('')
st.sidebar.write('')
st.sidebar.write('')



# [theme]
# base="dark"
# primaryColor="#6C3EFF"
# backgroundColor="#0e0b16"
# textColor="#e7dfdd"
