import streamlit as st
import pandas as pd
import plotly.express as px
import time 
import re
import numpy as np

def quarter_to_numeric(q):
    year, qtr = q.split(" ")
    return int(year) + (int(qtr[1]) - 1) / 4  # Converts "1997 Q3" → 1997.5

def numeric_to_quarter(n):
    year = int(n)
    qtr = int((n - year) * 4) + 1
    return f"{year} Q{qtr}"

@st.cache_data
def data_format(data, QorY, time_period, data_option, country_options, qoq= False, yoy= False, quarterly_selection =False, industry_selection = ['Total']):
    # Filter for time selection
    if QorY == "Quarterly":
        # Convert the time periods to numeric
        time_period = list(time_period)
        time_period[0] = quarter_to_numeric(time_period[0])
        time_period[1] = quarter_to_numeric(time_period[1])
        long_data = pd.read_csv('out/Long_Dataset.csv')
        if qoq: # remove - add error handling
            time_period[0] -= 0.25
        elif yoy:
            time_period[0] -= 1
        data = long_data.query(
        f"Quarter >= {time_period[0]} and Quarter <= {time_period[1]} and Country in {country_options} and Variable == '{data_option}' and Industry in {industry_selection}")
    elif QorY == "Yearly":
        data = data[(data["Year"] >= time_period[0]) & (data["Year"] <= time_period[1])]
    
    # Data processing for bar graphs
    if qoq or yoy:
        qoq_data = data.copy()
        # Split the country name from the data title
        qoq_data = qoq_data.rename(columns=lambda x: x.split()[0])
        # Reformat and sort data
        qoq_data = qoq_data.melt(id_vars = "Quarter", var_name = "Country")
        qoq_data = qoq_data.sort_values(["Country", "Quarter"]).reset_index(drop=True)
        if qoq:
            # Calculate QoQ Growth (Change from the previous quarter)
            qoq_data["QoQ Growth (%)"] = qoq_data.groupby("Country")["value"].pct_change().mul(100).round(2)

        if yoy:
            # Calculate YoY Growth (Change from the same quarter last year)
            qoq_data["Quarter"] = qoq_data["Quarter"].apply(quarter_to_numeric)
            # Filtering to show only selected quarters in yoy selection
            quarter_map = {1: 0, 2: 0.25, 3: 0.5, 4: 0.75}
            qoq_data["decimal_part"] = qoq_data["Quarter"] % 1
            qoq_data = qoq_data[qoq_data["decimal_part"].isin([quarter_map[quarterly_selection]])]
            qoq_data.drop("decimal_part", axis=1, inplace=True)
            qoq_data["YoY Growth (%)"] = qoq_data.groupby("Country")["value"].pct_change().mul(100).round(2)
            qoq_data["Quarter"] = qoq_data["Quarter"].apply(numeric_to_quarter)
        data = qoq_data
    return data

def create_quarterly_fig(data, qoq, yoy, show_legend, data_option):
    data = data.dropna()
    if qoq:
        fig = px.bar(data, x="Quarter", y="QoQ Growth (%)", color="Country",
             barmode="group", title="QoQ Growth Across Countries")
    elif yoy:
        fig = px.bar(data, x="Quarter", y="YoY Growth (%)", color="Country",
             barmode="group", title="YoY Growth Across Countries")
    else:
        fig = px.line(data, 
                x="Quarter", 
                y="Value", 
                color="Country",
                title="Quarter on quarter Comparison (2020 = 100)",
                labels={"value": f"{data_option}", "variable": "Countries"})
    fig.update_layout(showlegend=show_legend)
    return fig

def create_yearly_fig(data, show_legend):
    fig = px.line(data, 
              x="Year", 
              y=data.columns.drop("Year").tolist(), 
              title="GDP per Hour Worked Over Time (2015=100)")
    fig.update_layout(showlegend=show_legend)
    return fig


@st.cache_data
def load_data():
    t0 = time.time()
    yearly_data = pd.read_csv("out/OPH_Processed.csv")
    quarterly_data = pd.read_csv("out/Dataset.csv")
    Long_data = pd.read_csv("out/Long_Dataset.csv")

    print("Runtime loading data: " + str(int((time.time() - t0)*1000)) + " miliseconds")
    return quarterly_data, yearly_data, Long_data

def main():
    t0 = time.time()

    # Set session state variables
    st.session_state.show_quarter_slider = False
    st.session_state.show_yearly_slider = False

    if "selected" not in st.session_state:
        st.session_state.selected = "Line graph"

    def update_selection(option):
        if st.session_state.selected == option:  # If clicked again, deselect
            st.session_state.selected = None
        else:
            st.session_state.selected = option

    st.set_page_config(layout="wide")

    # Load datasets
    quarterly_data, yearly_data, long_data = load_data()

    # Page formatting
    st.sidebar.html('<a href="https://lab.productivity.ac.uk" alt="The Productivity Lab"></a>')
    st.logo("static/logo.png", link="https://lab.productivity.ac.uk/", icon_image=None)

    #Data selection tools in the sidebar section
    st.sidebar.divider()
    st.sidebar.subheader("Select data to plot")
    QorY = st.sidebar.radio(
        "",
        ["Quarterly", "Yearly"],
        captions=[
            "Quarterly labour productivity",
            "Yearly labour productivity",
        ],
    )
    
    if QorY == "Quarterly":
        st.session_state.show_quarter_slider = True
    elif QorY == "Yearly":
        st.session_state.show_yearly_slider = True

    # Quarter time series selection
    if st.session_state.show_quarter_slider:
        quarters = quarterly_data["Quarter"].tolist()
        quarter = st.sidebar.select_slider(label = "Quarterly slider", options = quarters, value=(quarters[0], quarters[-1]), label_visibility="collapsed")
        # if quarter[0] == quarter[1]:   # remove - need to update this for quarters
        #     quarter = [quarter[0], quarter[0] + 1] if quarter[0] < max(yearly_data["Year"]) else [quarter[0] - 1, quarter[0]]
        quarterly_options = ["OPH", "OPW", "GVA", "GDP per hour (TPI calculation)"]
        quarterly_option = st.sidebar.selectbox("Select data", options=quarterly_options)
        if quarterly_option == "GVA":
            industry_options = long_data['Industry'].unique()
            industry_options = industry_options[~pd.isna(industry_options)] 
            industry_selection = st.sidebar.multiselect(label="Select industry selection", options=industry_options, default=['Total'])
            print(industry_selection)

    # Year time series selection
    if st.session_state.show_yearly_slider:
        year = st.sidebar.slider(label="Yearly slider!", min_value=yearly_data["Year"].iat[0], max_value=max(yearly_data["Year"]), value=[yearly_data["Year"].iat[0], max(yearly_data["Year"])], label_visibility="collapsed")
        if year[0] == year[1]:
            year = [year[0], year[0] + 1] if year[0] < max(yearly_data["Year"]) else [year[0] - 1, year[0]]
        yearly_option = yearly_options = ["GDP per hour worked"]
        st.sidebar.selectbox("Select data", options=yearly_options)


    if QorY == "Quarterly":
        # Only allow the user to select countries which are available for the data selected
        regex_escaped_options = re.escape(quarterly_option)
        matching_columns = quarterly_data.columns[quarterly_data.columns.str.contains(regex_escaped_options, case=False)]
        # Extract country names by removing the option part
        countries = [col.replace(quarterly_option, "").strip() for col in matching_columns]
        countries = sorted(countries, key=lambda x: (x not in ["UK", "Euro Area", "European Union"], x))
        default_options = ["UK", "Germany", "France", "Italy", "Spain"]
        country_selection = st.sidebar.multiselect(label = "Select countries to display", options = countries, default=default_options)
        quarterly_selection = None

        # Only show data options below if quarterly format is selected
        st.sidebar.write("Select data view options")
        st.sidebar.write("Line graph")
        st.sidebar.checkbox("Quarter on quarter comparison", 
        value=(st.session_state.selected == "Line graph"), 
        on_change=lambda opt="Line graph": update_selection(opt))

        st.sidebar.write("Bar graph")
        st.sidebar.checkbox("Quarter on quarter", 
        value=(st.session_state.selected == "Quarter on quarter"), 
        on_change=lambda opt="Quarter on quarter": update_selection(opt))

        st.sidebar.checkbox("Year on year", 
        value=(st.session_state.selected == "Year on year"), 
        on_change=lambda opt="Year on year": update_selection(opt))
        if st.session_state.selected == "Year on year":
            quarterly_selection = st.sidebar.selectbox(label= "Specific quarter comparison", options=[1, 2, 3, 4])

    elif QorY == "Yearly":
        # Only allow the user to select countries which are available for the data selected
        regex_escaped_options = re.escape("GDP per hour worked")
        matching_columns = yearly_data.columns[yearly_data.columns.str.contains(regex_escaped_options, case=False)]

        # Extract country names by removing the option part
        countries = [col.replace("GDP per hour worked", "").strip() for col in matching_columns]

        # Sort into alphabetical order, but with the European average options at the top
        countries = sorted(countries, key=lambda x: (x not in ["UK", "Euro Area", "European Union"], x))
        default_options = ["US", "UK", "Germany", "France", "Italy", "Spain"]
        country_selection = st.sidebar.multiselect(label = "Select countries to display", options = countries, default=default_options)
        quarterly_selection = None

    qoq = False
    yoy = False
    if st.session_state.selected == "Quarter on quarter":
        qoq = True
    elif st.session_state.selected == "Year on year":
        yoy = True

    #Figure formatting tools
    st.sidebar.divider()
    st.sidebar.subheader("Configure layout")
    show_legend = st.sidebar.toggle(label="Show legend", value=True)
    # showtrend = st.sidebar.toggle(label="Show trendline", value=False)
    # showlabel = st.sidebar.toggle(label="Show labels", value=False)
    
    #Define main content
    st.header("TPI Quarterly data tool for US, UK and European labour productivity")
    with st.expander(label="**About this tool**", expanded=False):
        st.markdown(
            """
            ### Intro
            ###### Developed by the [TPI Productivity Lab](https://lab.productivity.ac.uk/), this tool allows for the quick creation of graphs of quarterly and yearly productivity data on a national scale.
            
            ### Customisation Options
            #### Data options
            - **Quarterly or Yearly selection**: Allows for the option of data to be shown as either quarterly or yearly
            - **Select time period**: change the time period selected
            - **Select data**: choose the productivity measure to be visualised
            - **Choose countries**: choose the countries selected from a large list containing many European countries, as well as the US
            #### Quarterly data specific options
            ##### Quarterly line graph
            - Plots all selected data as a line graph
            ##### QoQ bar graph
            - Plots all selected data as a bar graph showing Quarter on Quarter (QoQ) change as a percentage
            ##### YOY bar graph
            - Plots all selected data as a bar graph showing Year on Year (YoY) change as a percentage
            - Allows for selection of the specific quarter to be compared (if the 4th quarter is selected, it will show percentage change of the measure selected between the 4th quarters of the years selected)
            #### Formatting
            - **Show legend**: choose whether the legend is to be shown in the visualisation
            """
        )

    figure = st.empty() 
    if QorY == "Quarterly":
        quarterly_data = data_format(quarterly_data, QorY, quarter, quarterly_option, country_selection, qoq, yoy, quarterly_selection, industry_selection)
        fig = create_quarterly_fig(quarterly_data, qoq, yoy, show_legend, quarterly_option)
    else:
        yearly_data = data_format(yearly_data, QorY, year, yearly_option, country_selection)
        fig = create_yearly_fig(yearly_data, show_legend)
    
    # Display the figure
    if fig:
        # Save session state variables and load figure
        with st.spinner("Loading visualisation"):
            st.session_state.fig = fig
            st.session_state.df = quarterly_data
            figure.plotly_chart(st.session_state.fig, use_container_width=True)
    
if __name__ == "__main__":
    main()
