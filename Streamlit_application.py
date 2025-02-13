import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time 

def quarter_to_numeric(q):
    year, qtr = q.split(" ")
    return int(year) + (int(qtr[1]) - 1) / 4  # Converts "1997 Q3" → 1997.5

def numeric_to_quarter(n):
    year = int(n)
    qtr = int((n - year) * 4) + 1
    return f"{year} Q{qtr}"


def data_format(data, QorY, time_period, data_option):
    if QorY == "Quarterly":
        # Convert the quaters to numeric
        data["quarter_numeric"] = data["Quarter"].apply(quarter_to_numeric)
        # Convert the time periods to numeric
        time_period = list(time_period)
        time_period[0] = quarter_to_numeric(time_period[0])
        time_period[1] = quarter_to_numeric(time_period[1])
        # Filter out period requested
        data = data[(data["quarter_numeric"] >= time_period[0]) & (data["quarter_numeric"] <= time_period[1])]
        data = data[['Quarter', *data.columns[data.columns.str.contains(data_option, case=False)]]]
    elif QorY == "Yearly":
        data = data[(data["Year"] >= time_period[0]) & (data["Year"] <= time_period[1])]
        print(data)
    return data

def create_quarterly_fig(data):
    fig = px.line(data, 
              x="Quarter", 
              y=data.columns.drop('Quarter').tolist(), 
              title="Time Series Comparison")
    return fig

def create_yearly_fig(data):
    fig = px.line(data, 
              x="Year", 
              y="GDP per Hour Worked", 
              color="Country",
              markers=True,
              title="GDP per Hour Worked (2015=100) Over Time")

    fig.add_shape(
        go.layout.Shape(
            type="line",
            x0=2015, x1=2015,  # Vertical line at 2015
            y0=data["GDP per Hour Worked"].min(), 
            y1=data["GDP per Hour Worked"].max(),
            line=dict(color="gray", width=2, dash="dash"),
        )
    )

    # Add annotation for 2015 Base Year
    fig.add_annotation(
        x=2015, 
        y=data["GDP per Hour Worked"].max(),
        text="2015 = 100 (Base Year)",
        showarrow=False,
        font=dict(size=12, color="gray"),
        xshift=10
    )
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
    st.set_page_config(layout="wide")
    quarterly_data, yearly_data = load_data()
    t0 = time.time()

    st.sidebar.html("<a href='https://lab.productivity.ac.uk' alt='The Productivity Lab'></a>")
    st.logo("static/logo.png", link="https://lab.productivity.ac.uk/", icon_image=None)

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

    st.session_state.show_quarter_slider = False
    st.session_state.show_yearly_slider = False

    if QorY == "Quarterly":
        st.session_state.show_quarter_slider = True
    elif QorY == "Yearly":
        st.session_state.show_yearly_slider = True

    quarters = quarterly_data["Quarter"].tolist()
    if st.session_state.show_quarter_slider:
        quarter = st.sidebar.select_slider(label = "Quarterly slider", options = quarters, value=(quarters[0], quarters[-1]), label_visibility="collapsed")
        # if quarter[0] == quarter[1]:   # remove - need to update this for quarters
        #     quarter = [quarter[0], quarter[0] + 1] if quarter[0] < max(yearly_data["Year"]) else [quarter[0] - 1, quarter[0]]
        quarterly_options = ["OPH", "OPW", "GVA"]
        quarterly_option = st.sidebar.selectbox("Select data", options=quarterly_options)
    if st.session_state.show_yearly_slider:
        year = st.sidebar.slider(label="Yearly slider!", min_value=yearly_data["Year"].iat[0], max_value=max(yearly_data["Year"]), value=[yearly_data["Year"].iat[0], max(yearly_data["Year"])], label_visibility="collapsed")
        if year[0] == year[1]:
            year = [year[0], year[0] + 1] if year[0] < max(yearly_data["Year"]) else [year[0] - 1, year[0]]
        yearly_option = yearly_options = ["GDP per Hour worked"]
        st.sidebar.selectbox("Select data", options=yearly_options)

    #Figure formatting tools
    st.sidebar.divider()
    st.sidebar.subheader('Configure layout')
    size = st.sidebar.slider('Figure size', min_value=0.65, max_value = 2.0, value = 0.75)
    legend = st.sidebar.toggle(label='Show legend', value=True)
    showtrend = st.sidebar.toggle(label='Show trendline', value=False)
    showlabel = st.sidebar.toggle(label='Show labels', value=False)
    population = st.sidebar.toggle(label='Toggle population bubbles', value=False)
    
    
    #Define main content
    st.header('TPI Quarterly data tool for US, UK and European labour productivity')
    figure = st.empty() 
    print(QorY)
    if QorY == "Quarterly":
        quarterly_data = data_format(quarterly_data, QorY, quarter, quarterly_option)
        fig = create_quarterly_fig(quarterly_data)
    else:
        yearly_data = data_format(yearly_data, QorY, year, yearly_option)
        fig = create_yearly_fig(yearly_data)
    

    # Show the chart
    # fig.show()
    
    if fig:
        # Save session state variables and load figure
        st.session_state.fig = fig
        st.session_state.df = quarterly_data
        figure.plotly_chart(st.session_state.fig, use_container_width=True)
    
if __name__ == '__main__':
    main()
