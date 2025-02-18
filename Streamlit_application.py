import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time 
import re

def quarter_to_numeric(q):
    year, qtr = q.split(" ")
    return int(year) + (int(qtr[1]) - 1) / 4  # Converts "1997 Q3" → 1997.5

def numeric_to_quarter(n):
    year = int(n)
    qtr = int((n - year) * 4) + 1
    return f"{year} Q{qtr}"


def data_format(data, QorY, time_period, data_option, country_options, qoq= False, yoy= False):
    print("search", data.columns)
    print("search", data_option)
    if QorY == "Quarterly":
        # Convert the quaters to numeric
        data["quarter_numeric"] = data["Quarter"].apply(quarter_to_numeric)
        # Convert the time periods to numeric
        time_period = list(time_period)
        time_period[0] = quarter_to_numeric(time_period[0])
        time_period[1] = quarter_to_numeric(time_period[1])
        # Filter out period requested
        data = data[(data["quarter_numeric"] >= time_period[0]) & (data["quarter_numeric"] <= time_period[1])]
        regex_escaped_options = escaped_option = re.escape(data_option)
        data = data[['Quarter', *data.loc[:, data.columns[data.columns.str.contains(regex_escaped_options, case=False)]]]]
    elif QorY == "Yearly":
        data = data[(data["Year"] >= time_period[0]) & (data["Year"] <= time_period[1])]
    countries_data = pd.DataFrame()
    # data = data.reset_index()
    for country in country_options:
        country_data = data.loc[:, data.columns.str.contains(country, case=False)]
        countries_data = countries_data + country_data if not countries_data.empty else country_data
    data = data[[data.columns[0], *countries_data]].dropna()

    if qoq or yoy:
        qoq_data = data.copy()
        qoq_data = qoq_data.rename(columns=lambda x: x.split()[0])
        qoq_data = qoq_data.melt(id_vars = "Quarter", var_name = "Country")
        qoq_data = qoq_data.sort_values(['Country', 'Quarter']).reset_index(drop=True)
        if qoq:
            # Calculate QoQ Growth (GDP change from the previous quarter)
            qoq_data['QoQ Growth (%)'] = qoq_data.groupby('Country')['value'].pct_change().mul(100).round(2)
        if yoy:
            # Calculate YoY Growth (GDP change from the same quarter last year)
            qoq_data['YoY Growth (%)'] = qoq_data.groupby('Country')['value'].pct_change(4).mul(100).round(2)
        # print("Here", qoq_data)
        # qoq_data.to_csv("out/qoq_data.csv", index = False)
        # qoq_data = qoq_data.melt(id_vars=['Quarter', 'Country'], 
        #              value_vars=['QoQ Growth (%)', 'YoY Growth (%)'], 
        #              var_name='Metric', 
        #              value_name='Growth Rate')
        data = qoq_data
    print(data)
    return data

def create_quarterly_fig(data, qoq, yoy, show_legend):
    if qoq:
        fig = px.bar(data, x='Quarter', y="QoQ Growth (%)", color='Country',
             barmode='group', title="QoQ vs YoY Growth Across Countries")
    elif yoy:
        fig = px.bar(data, x='Quarter', y="YoY Growth (%)", color='Country',
             barmode='group', title="QoQ vs YoY Growth Across Countries")
    else:
        fig = px.line(data, 
                x="Quarter", 
                y=data.columns.drop('Quarter').tolist(), 
                title="Time Series Comparison")
    fig.update_layout(showlegend=show_legend)
    return fig

def create_yearly_fig(data, show_legend):
    fig = px.line(data, 
              x="Year", 
              y=data.columns.drop('Year').tolist(), 
              markers=True,
              title="GDP per Hour Worked (2015=100) Over Time")

    # fig.add_shape(
    #     go.layout.Shape(
    #         type="line",
    #         x0=2015, x1=2015,  # Vertical line at 2015
    #         y0=data["GDP per Hour Worked"].min(), 
    #         y1=data["GDP per Hour Worked"].max(),
    #         line=dict(color="gray", width=2, dash="dash"),
    #     )
    # )

    # Add annotation for 2015 Base Year
    # fig.add_annotation(
    #     x=2015, 
    #     y=data["GDP per Hour Worked"].max(),
    #     text="2015 = 100 (Base Year)",
    #     showarrow=False,
    #     font=dict(size=12, color="gray"),
    #     xshift=10
    # )
    fig.update_layout(showlegend=show_legend)
    return fig


@st.cache_data
def load_data():
    t0 = time.time()
    yearly_data = pd.read_csv('out/OPH_Processed.csv')
    quarterly_data = pd.read_csv('out/Dataset.csv')

    print("Runtime loading data: " + str(int((time.time() - t0)*1000)) + " miliseconds")
    return quarterly_data, yearly_data

@st.cache_data
def quarterly_process_data(data, start, end):

    t0 = time.time()
    print("Runtime data processing: " + str(int((time.time() - t0)*1000)) + " miliseconds")
    return

def main():
    t0 = time.time()

    def update_selection(option):
        if st.session_state.selected == option:  # If clicked again, deselect
            st.session_state.selected = None
        else:
            st.session_state.selected = option

    st.set_page_config(layout="wide")

    # Load datasets
    quarterly_data, yearly_data = load_data()

    # Page formatting
    st.sidebar.html("<a href='https://lab.productivity.ac.uk' alt='The Productivity Lab'></a>")
    st.logo("static/logo.png", link="https://lab.productivity.ac.uk/", icon_image=None)

    # Set session state variables
    st.session_state.show_quarter_slider = False
    st.session_state.show_yearly_slider = False

    if "selected" not in st.session_state:
        st.session_state.selected = "Line graph"

    #Data selection tools
    st.sidebar.divider()
    st.sidebar.subheader('Select data to plot')
    QorY = st.sidebar.radio(
        "Data as yearly or quarterly?",
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
        quarterly_options = ["GDP per hour (TPI calculation)", "OPH", "OPW", "GVA"]
        quarterly_option = st.sidebar.selectbox("Select data", options=quarterly_options)

    # Year time series selection
    if st.session_state.show_yearly_slider:
        year = st.sidebar.slider(label="Yearly slider!", min_value=yearly_data["Year"].iat[0], max_value=max(yearly_data["Year"]), value=[yearly_data["Year"].iat[0], max(yearly_data["Year"])], label_visibility="collapsed")
        if year[0] == year[1]:
            year = [year[0], year[0] + 1] if year[0] < max(yearly_data["Year"]) else [year[0] - 1, year[0]]
        yearly_option = yearly_options = ["GDP per hour worked"]
        st.sidebar.selectbox("Select data", options=yearly_options)

    # Country display selection
    country_options = ["US", "UK", "Germany", "France", "Italy", "Spain"]
    country_selection = st.sidebar.multiselect(label = "Select countries to display (where applicable)", options = country_options, default=country_options)

    if QorY == "Quarterly":
        st.sidebar.write("Select data view options")
        st.sidebar.write("Line graph")
        st.sidebar.checkbox("Line graph", 
                value=(st.session_state.selected == "Line graph"), 
                on_change=lambda opt="Line graph": update_selection(opt))

        st.sidebar.write("Bar graph")
        st.sidebar.checkbox("Quarter on quarter", 
                value=(st.session_state.selected == "Quarter on quarter"), 
                on_change=lambda opt="Quarter on quarter": update_selection(opt))
        st.sidebar.checkbox("Year on year", 
                value=(st.session_state.selected == "Year on year"), 
                on_change=lambda opt="Year on year": update_selection(opt))

    qoq = False
    yoy = False
    if st.session_state.selected == "Quarter on quarter":
        qoq = True
    elif st.session_state.selected == "Year on year":
        yoy = True

    #Figure formatting tools
    st.sidebar.divider()
    st.sidebar.subheader('Configure layout')
    show_legend = st.sidebar.toggle(label='Show legend', value=True)
    # showtrend = st.sidebar.toggle(label='Show trendline', value=False)
    # showlabel = st.sidebar.toggle(label='Show labels', value=False)
    
    #Define main content
    st.header('TPI Quarterly data tool for US, UK and European labour productivity')
    figure = st.empty() 
    if QorY == "Quarterly":
        quarterly_data = data_format(quarterly_data, QorY, quarter, quarterly_option, country_selection, qoq, yoy)
        fig = create_quarterly_fig(quarterly_data, qoq, yoy, show_legend)
    else:
        yearly_data = data_format(yearly_data, QorY, year, yearly_option, country_selection)
        fig = create_yearly_fig(yearly_data, show_legend)
    
    # Display the figure
    if fig:
        # Save session state variables and load figure
        with st.spinner('Loading visualisation'):
            st.session_state.fig = fig
            st.session_state.df = quarterly_data
            figure.plotly_chart(st.session_state.fig, use_container_width=True)
    
if __name__ == '__main__':
    main()
