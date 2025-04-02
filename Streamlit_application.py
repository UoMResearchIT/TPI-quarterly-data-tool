import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time 
import re
import math

def quarter_to_numeric(q): # Converts "1997 Q3" → 1997.5
    year, qtr = q.split(" ")
    return int(year) + (int(qtr[1]) - 1) / 4  

def numeric_to_quarter(n): # Converts 1997.5 → "1997 Q3"
    year = int(n)
    qtr = int((n - year) * 4) + 1
    return f"{year} Q{qtr}"

@st.cache_data
def data_format(data, QorY, time_period, data_option, country_options, visType = '2D line graph', quarterly_selection =False, industry_selection = ['Total']):
    # Filter for time selection
    if QorY == "Quarterly":
        # Convert the time periods to numeric
        time_period = list(time_period)
        time_period[0] = quarter_to_numeric(time_period[0])
        time_period[1] = quarter_to_numeric(time_period[1])
        long_data = pd.read_csv('out/Long_Dataset.csv')
        if visType == 'QoQ': # remove - check is correct
            time_period[0] -= 0.25
        elif visType == 'YoY':
            time_period[0] -= 1
        data = long_data.query(
        f"Quarter >= {time_period[0]} and Quarter <= {time_period[1]} and Country in {country_options} and Variable == '{data_option}' and Industry in {industry_selection}")
    elif QorY == "Yearly":
        data = data[(data["Year"] >= time_period[0]) & (data["Year"] <= time_period[1])]
    
    # Data processing for bar graphs
    if visType == 'QoQ' or visType == 'YoY':
        qoq_data = data.copy()
        if visType == 'QoQ':
            # Calculate QoQ Growth (Change from the previous quarter)
            qoq_data["QoQ Growth (%)"] = qoq_data.groupby("Country")["Value"].pct_change().mul(100).round(2)

        if visType == 'YoY':
            # Filtering to show only selected quarters in yoy selection
            quarter_map = {1: 0, 2: 0.25, 3: 0.5, 4: 0.75}
            qoq_data["decimal_part"] = qoq_data["Quarter"] % 1
            qoq_data = qoq_data[qoq_data["decimal_part"].isin([quarter_map[quarterly_selection]])]
            qoq_data.drop("decimal_part", axis=1, inplace=True)
            qoq_data["YoY Growth (%)"] = qoq_data.groupby("Country")["Value"].pct_change().mul(100).round(2)
        data = qoq_data
    data['Quarter'] = data['Quarter'].apply(numeric_to_quarter)
    return data

@st.cache_data
def multi_data_format(data, industry):
    plot_data = data.query(f"Industry == '{industry}'")
    return plot_data

def make_fig(data, visType, data_option, show_dip_lines, second_plot):
    if visType == 'QoQ':
        fig = px.bar(data, x="Quarter", y="QoQ Growth (%)", color="Country",
                barmode="group", title="QoQ Growth Across Countries")
    elif visType == 'YoY':
        fig = px.bar(data, x="Quarter", y="YoY Growth (%)", color="Country",
             barmode="group", title="YoY Growth Across Countries")
    elif visType == '3D line graph':
        # Extract years from quarters
        data['Year'] = data['Quarter'].apply(lambda x: int(x.split()[0]))
        
        # Create the line plot
        fig = px.line_3d(data, x="Country", y="Year", z="Value", color='Country')

        # Customise layout with explicit axis labels
        fig.update_layout(
            title='3D Line Graph',
            scene=dict(camera=dict(eye=dict(x=1.7, y=1.7, z=1.7))),  # Move camera further away
            width=1000,
            height=500
        )
        fig.update_traces(line=dict(width=5))
    
    elif visType == '2D line graph':
        fig = px.line(data, 
                x="Quarter", 
                y="Value", 
                color="Country",
                title="Quarter on quarter Comparison (2020 = 100)",
                labels={"value": f"{data_option}", "variable": "Countries"})
        if show_dip_lines:
            highlighted_quarters = ["2007 Q4", "2009 Q2", "2019 Q4", "2021 Q1"]  # Quarters highlighted with verticle lines
            for quarter in highlighted_quarters:
                fig.add_vline(x=quarter, line_dash="dash", line_color="red")
    if second_plot:
        return fig.data
    else:
        return fig

def create_quarterly_fig(data, show_legend, data_option, show_dip_lines, visType, second_plot, second_data):
    data = data.dropna()
    industries = data["Industry"].unique()
    if len(industries) > 1:  # If multiple industries are selected for GVA
        cols = 2
        rows = math.ceil(len(industries) / cols) # Rounds to nearest integer to calculate amount of rows
        fig = make_subplots(rows=rows, cols=cols, subplot_titles=industries)
        for i, industry in enumerate(industries):
            row = (i // cols) + 1  # Determine row position
            col = (i % cols) + 1  # Determine column position
            figs = px.line(multi_data_format(data, industry), 
                x="Quarter", 
                y="Value", 
                color="Country",
                title="Quarter on quarter Comparison (2020 = 100)",
                labels={"value": f"{data_option}", "variable": "Countries", "industry": f"{industry}"})
            for trace in figs.data:
                trace.showlegend = i == 0  # Show legend only for first subplot
                fig.add_trace(trace, row=row, col=col)
            fig.update_layout(showlegend=show_legend,
                        legend=dict(
                        title="Countries",
                        orientation="v",
                        yanchor="middle", y=0.5,
                        xanchor="left", x=1.02,
                        bgcolor="rgba(255,255,255,0.7)",
                        font=dict(size=12),
                    ),
                    height=300 * rows)
    elif second_plot:
        # x = "scene" - remove - sort this out
        # fig=make_subplots(rows=1, cols=2, specs=[[{"type": f"{x}"}, {"type": f"{x}"}]])
        fig=make_subplots(rows=1, cols=2)
        for trace in make_fig(data, visType, data_option, show_dip_lines, second_plot):
            fig.add_trace(trace, row=1, col=1)
        for trace in make_fig(second_data, visType, data_option, show_dip_lines, second_plot):
            fig.add_trace(trace, row=1, col=2)
    else:
        fig = make_fig(data, visType, data_option, show_dip_lines, second_plot)
    fig.update_layout(showlegend=show_legend)
    return fig

def create_yearly_fig(data, show_legend, second_plot, second_data):
    fig = px.line(data, 
              x="Year", 
              y=data.columns.drop("Year").tolist(), 
              title="GDP per Hour Worked Over Time (2015=100)")
    fig.update_layout(showlegend=show_legend)
    return fig

def update_selection(option):
    if st.session_state.selected == option:  # If clicked again, deselect
        st.session_state.selected = None
    else:
        st.session_state.selected = option


def visualisation_selection(quarterly_data, yearly_data, key):
    st.sidebar.divider()
    st.sidebar.subheader("Select data to plot")
    QorY = st.sidebar.radio(
        label="Select data to plot",
        options=["Quarterly", "Yearly"],
        captions=[
            "Quarterly labour productivity",
            "Yearly labour productivity",
        ],
        key=f'QorY_{key}'
    )
    if QorY == "Quarterly":
        st.session_state.show_quarter_slider_two = True
    elif QorY == "Yearly":
        st.session_state.show_yearly_slider_two = True
    
    # Quarter time series selection
    quarterly_option = None
    quarter = None
    industry_selection = None
    if st.session_state.show_quarter_slider_two:
        quarters = quarterly_data["Quarter"].unique()
        quarters = [numeric_to_quarter(x) for x in quarters]
        quarter = st.sidebar.select_slider(label = "Quarterly slider", options = quarters, value=(quarters[0], quarters[-1]), label_visibility="collapsed", key=f'Q_Slider_{key}')
        quarterly_options = ["OPH", "OPW", "GVA", "GDP per hour (TPI calculation)"]
        quarterly_option = st.sidebar.selectbox(label= "Select data", options=quarterly_options, key=f'Q_Option_{key}')
        industry_selection = ['Total']
        if quarterly_option == "GVA":
            industry_options = quarterly_data['Industry'].unique()
            industry_options = industry_options[~pd.isna(industry_options)] 
            industry_selection = st.sidebar.multiselect(label="Select industry selection", options=industry_options, default=['Total'], key=f'Industry_Selection_{key}')

    # Year time series selection
    yearly_option = None
    year = None
    if st.session_state.show_yearly_slider_two:
        year = st.sidebar.slider(label="Yearly slider!", min_value=yearly_data["Year"].iat[0], max_value=max(yearly_data["Year"]), value=[yearly_data["Year"].iat[0], max(yearly_data["Year"])], label_visibility="collapsed", key='Y_Slider_Two')
        if year[0] == year[1]:
            year = [year[0], year[0] + 1] if year[0] < max(yearly_data["Year"]) else [year[0] - 1, year[0]]
        yearly_option = yearly_options = ["GDP per hour worked"]
        st.sidebar.selectbox(label= "Select data", options=yearly_options, key='Y_Option')

    quarterly_selection = None
    if QorY == "Quarterly":
        # Only allow the user to select countries which are available for the data selected
        regex_escaped_options = re.escape(quarterly_option)
        matching_columns = quarterly_data.columns[quarterly_data.columns.str.contains(regex_escaped_options, case=False)]
        # Extract country names by removing the option part
        countries = quarterly_data['Country'].unique()
        # countries = [col.replace(quarterly_option, "").strip() for col in matching_columns]
        countries = sorted(countries, key=lambda x: (x not in ["UK", "US", "Euro Area", "European Union"], x))
        default_options = ["UK", "US", "Germany", "France", "Italy", "Spain"]
        country_selection = st.sidebar.multiselect(label = "Select countries to display", options = countries, default=default_options, key=f'country_selection_{key}')

        # Only show data options below if quarterly format is selected
        st.sidebar.write("Select data view options")
        st.sidebar.write("Line graph")
        st.sidebar.checkbox("2D line graph", 
        value=(st.session_state.selected == "2D line graph"), 
        on_change=lambda opt="2D line graph": update_selection(opt), key=f'2d_line_graph{key}')

        st.sidebar.checkbox("3D line graph", 
        value=(st.session_state.selected == "3D line graph"), 
        on_change=lambda opt="3D line graph": update_selection(opt), key=f'3d_line_graph{key}')

        st.sidebar.write("Bar graph")
        st.sidebar.checkbox("Quarter on quarter", 
        value=(st.session_state.selected == "Quarter on quarter"), 
        on_change=lambda opt="Quarter on quarter": update_selection(opt), key=f'qoq_graph{key}')

        st.sidebar.checkbox("Year on year", 
        value=(st.session_state.selected == "Year on year"), 
        on_change=lambda opt="Year on year": update_selection(opt), key=f'yoy_graph{key}')
        if st.session_state.selected == "Year on year":
            quarterly_selection = st.sidebar.selectbox(label= "Specific quarter comparison", options=[1, 2, 3, 4], key=f'quarterly_selection_{key}')

    elif QorY == "Yearly":
        # Only allow the user to select countries which are available for the data selected
        regex_escaped_options = re.escape("GDP per hour worked")
        matching_columns = yearly_data.columns[yearly_data.columns.str.contains(regex_escaped_options, case=False)]

        # Extract country names by removing the option part
        countries = [col.replace("GDP per hour worked", "").strip() for col in matching_columns]

        # Sort into alphabetical order, but with the European average options at the top
        countries = sorted(countries, key=lambda x: (x not in ["UK", "Euro Area", "European Union"], x))
        default_options = ["US", "UK", "Germany", "France", "Italy", "Spain"]
        country_selection = st.sidebar.multiselect(label = "Select countries to display", options = countries, default=default_options, key=f'country_selection_{key}')

    visType = '2D line graph'
    if st.session_state.selected == "Quarter on quarter":
        visType = 'QoQ'
    elif st.session_state.selected == "Year on year":
        visType = 'YoY'
    elif st.session_state.selected == '2D line graph':
        visType = '2D line graph'
    elif st.session_state.selected == '3D line graph':
        visType = '3D line graph'
    elif st.session_state.selected == '2D scatter':
        visType = '2D scatter'
    elif st.session_state.selected == '3D scatter':
        visType = '3D scatter'

    return QorY, quarter, quarterly_option, industry_selection, yearly_option, year, quarterly_selection, country_selection, visType

@st.cache_data
def load_data():
    t0 = time.time()
    yearly_data = pd.read_csv("out/OPH_Processed.csv")
    # quarterly_data = pd.read_csv("out/Dataset.csv")
    quarterly_data = pd.read_csv("out/Long_Dataset.csv")

    print("Runtime loading data: " + str(int((time.time() - t0)*1000)) + " miliseconds")
    return quarterly_data, yearly_data

def main():
    t0 = time.time()

    # Set session state variables
    st.session_state.show_quarter_slider = False
    st.session_state.show_yearly_slider = False
    st.session_state.show_quarter_slider_two = False
    st.session_state.show_yearly_slider_two = False

    if "selected" not in st.session_state:
        st.session_state.selected = "2D line graph"

    st.set_page_config(layout="wide")

    # Load datasets
    quarterly_data, yearly_data = load_data()

    # Page formatting
    st.sidebar.html('<a href="https://lab.productivity.ac.uk" alt="The Productivity Lab"></a>')
    st.logo("static/logo.png", link="https://lab.productivity.ac.uk/", icon_image=None)

    # First plot
    key = 1
    QorY, quarter, quarterly_option, industry_selection, yearly_option, year, quarterly_selection, country_selection, visType = visualisation_selection(quarterly_data, yearly_data, key)

    second_plot = False
    # Second plot options
    if len(industry_selection) == 1:
        st.sidebar.divider()
        second_plot = st.sidebar.toggle(label='Show a second plot side by side')
        if second_plot:
            key = 2
            QorY_two, quarter_two, quarterly_option_two, industry_selection_two, yearly_option_two, year_two, quarterly_selection_two, country_selection_two, visType_two = visualisation_selection(quarterly_data, yearly_data, key)

    #Figure formatting tools
    st.sidebar.divider()
    st.sidebar.subheader("Configure layout")
    show_legend = st.sidebar.toggle(label="Show legend", value=True)
    show_dip_lines = st.sidebar.toggle(label="Show verticle lines for before and after major dips in productivity (2008 recession and covid-19)", value=False)
    # showtrend = st.sidebar.toggle(label="Show trendline", value=False)
    # showlabel = st.sidebar.toggle(label="Show labels", value=False)

    # Export functionality
    if st.sidebar.button("Export Selected Data"):
        @st.cache_data
        def convert_df(df):
            return df.to_csv().encode('utf-8')
        
        csv = convert_df(data_format(quarterly_data, QorY, quarter, quarterly_option, country_selection, visType, quarterly_selection, industry_selection))
        st.sidebar.download_button(
            label="Download data as CSV",
            data=csv,
            file_name='productivity_data.csv',
            mime='text/csv',
        )
    
    #Define main content
    st.header("TPI Quarterly data tool for US, UK and European labour productivity")
    with st.expander(label="**About this tool**", expanded=False):
        st.markdown(
            """
            ## TPI Quarterly Data Tool
            ###### Developed by the [TPI Productivity Lab](https://lab.productivity.ac.uk/), this tool allows for the quick creation of graphs of quarterly and yearly productivity data on a national scale.
            ###### US Quarterly total economy data represents most of the US economy but leaves out certain sectors - read the sources and methods document that accompanies this tool for more information

            ### Customisation Options
            #### Data options
            - **Quarterly or Yearly selection**: Allows for the option of data to be shown as either quarterly or yearly
            - **Select time period**: change the time period selected
            - **Select data**: choose the productivity measure to be visualised
            - **Choose countries**: choose the countries selected from a large list containing many European countries, as well as the US
            #### Quarterly data specific options
            ##### Quarterly line graph
            - Plots all selected data as a line graph
            - GVA provides data options for multiple sectors:
            - if only sector is selected, a single line graph will be displayed
            - if multiple are selected, multiple plots will be displayed side by side
            - More information about the sectoral options is shown in the sources and methods and document
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
    # show_dip_lines = True  # remove
    if QorY == "Quarterly":
        quarterly_data = data_format(quarterly_data, QorY, quarter, quarterly_option, country_selection, visType, quarterly_selection, industry_selection)
        quarterly_data_two = None
        if second_plot:
            quarterly_data_two = data_format(quarterly_data, QorY_two, quarter_two, quarterly_option_two, country_selection_two, visType_two, quarterly_selection_two, industry_selection_two)
        fig = create_quarterly_fig(quarterly_data, show_legend, quarterly_option, show_dip_lines, visType, second_plot, quarterly_data_two)
    else:
        yearly_data = data_format(yearly_data, QorY, year, yearly_option, country_selection)
        yearly_data_two = None
        if second_plot:
            yearly_data_two = data_format(yearly_data, QorY_two, year_two, yearly_option_two, country_selection_two)
        fig = create_yearly_fig(yearly_data, show_legend, second_plot, yearly_data_two)
    
    # Display the figure
    if fig:
        # Save session state variables and load figure
        with st.spinner("Loading visualisation"):
            st.session_state.fig = fig
            figure.plotly_chart(st.session_state.fig, use_container_width=True,                 
                    config = {
                        'toImageButtonOptions': {
                            'filename': 'Downloaded_file',
                            'scale': 2
                        }
                    })
    
if __name__ == "__main__":
    main()
