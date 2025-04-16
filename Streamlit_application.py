import streamlit as st
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import re
import math

class data_options:
    def __init__(self, QorY, data_option, base_year, YoY_year):
        self.QorY= QorY
        self.data_option = data_option
        self.base_year = base_year
        self.YoY_year = YoY_year

def ordinal(n):
    return str(n)+("th" if 4<=n%100<=20 else {1:"st",2:"nd",3:"rd"}.get(n%10, "th"))

def quarter_to_numeric(q): # Converts "1997 Q3" → 1997.5    
    year, qtr = q.split(" ")
    return int(year) + (int(qtr[1]) - 1) / 4  

def numeric_to_quarter(n): # Converts 1997.5 → "1997 Q3"
    year = int(n)
    qtr = int((n - year) * 4) + 1
    return f"{year} Q{qtr}"

def rebase_chain_linked_quarters(df, new_base_year):
    df = df.copy()
    
    # Extract year from Quarter (e.g., 1997.25 -> 1997)
    df["Year"] = df["Quarter"].astype(int)

    def rebase_group(group):
        # Get the mean of the base year for this group
        base_year_values = group[group["Year"] == new_base_year]["Value"]
        if base_year_values.empty or base_year_values.mean() == 0:
            return group  # Skip group if base year is missing or zero
        base_mean = base_year_values.mean()
        group["Value"] = (group["Value"] / base_mean) * 100
        return group

    # Apply rebase per group
    df = df.groupby(["Country", "Industry", "Variable"], group_keys=False).apply(rebase_group)

    # Drop temporary year column
    df = df.drop(columns="Year")

    return df

# @st.cache_data
def data_format(data, QorY, time_period, data_option, country_options, show_years, visType = "2D line graph", quarterly_selection =False, industry_selection = ["Total"]):
    # Filter for time selection
    print("last", country_options)
    print(data)
    if QorY == "Quarterly":
        # Convert the time periods to numeric
        time_period = list(time_period)
        time_period[0] = quarter_to_numeric(time_period[0])
        time_period[1] = quarter_to_numeric(time_period[1])
        if visType == "QoQ": 
            time_period[0] -= 0.25
        elif visType == "YoY":
            time_period[0] -= 1
        data = data.query(
        f"Quarter >= {time_period[0]} and Quarter <= {time_period[1]} and Country in {country_options} and Variable == '{data_option.data_option}' and Industry in {industry_selection}")
    elif QorY == "Yearly":
        data = data.query(f"Year >= {time_period[0]} and Year <= {time_period[1]} and Country in {country_options}")
        return data
    
    # Data processing for bar graphs
    if visType == "QoQ" or visType == "YoY":
        qoq_data = data.copy()
        if visType == "QoQ":
            # Calculate QoQ Growth (Change from the previous quarter)
            qoq_data["QoQ Growth (%)"] = qoq_data.groupby("Country")["Value"].pct_change().mul(100).round(2)

        if visType == "YoY":
            # Filtering to show only selected quarters in yoy selection
            quarter_map = {1: 0, 2: 0.25, 3: 0.5, 4: 0.75}
            qoq_data["decimal_part"] = qoq_data["Quarter"] % 1
            qoq_data = qoq_data[qoq_data["decimal_part"].isin([quarter_map[quarterly_selection]])]
            qoq_data.drop("decimal_part", axis=1, inplace=True)
            qoq_data["YoY Growth (%)"] = qoq_data.groupby("Country")["Value"].pct_change().mul(100).round(2)
        data = qoq_data
    if data_option.base_year != 2020:
        data = rebase_chain_linked_quarters(data, data_option.base_year)
    if not show_years:
        data["Quarter"] = data["Quarter"].apply(numeric_to_quarter)
    return data

@st.cache_data
def multi_data_format(data, industry):
    plot_data = data.query(f"Industry == '{industry}'")
    return plot_data

def make_fig(data, visType, data_option, show_dip_lines, second_plot, second_data, show_legend):
    if second_plot:  # remove - could move colour code to quarterly fig function and put in as a parameter, so it is run less
        countries = list(set(data["Country"]).union(set(second_data["Country"]))) # All countries in both lists
        colour_palette = px.colors.qualitative.Set1  # Choose a Plotly color set
        country_colors = {country: colour_palette[i % len(colour_palette)] for i, country in enumerate(countries)}
    else: # Need this to account for if second plot isn"t selected
        countries = data["Country"]
        colour_palette = px.colors.qualitative.Set1  # Choose a Plotly color set
        country_colors = {country: colour_palette[i % len(colour_palette)] for i, country in enumerate(countries)}

    if visType == "QoQ":
        fig = px.bar(data, x="Quarter", y="QoQ Growth (%)", color="Country",
                barmode="group", title=f"Quarter on quarter comparison of {data_option.data_option} (chain linked values {data_option.base_year} = 100)")
    elif visType == "YoY":
        fig = px.bar(data, x="Quarter", y="YoY Growth (%)", color="Country",
             barmode="group", title=f"Year on year comparison of {data_option.data_option} for Q{data_option.YoY_year} of each year selected (chain linked values {data_option.base_year} = 100)")
        
    elif visType == "3D line graph":
        # Extract years from quarters
        data["Year"] = data["Quarter"].apply(lambda x: int(x.split()[0]))
        
        # Create the line plot
        fig = px.line_3d(data, x="Country", y="Year", z="Value", color="Country")

        # Customise layout with explicit axis labels
        fig.update_layout(
            title=f"{data_option.QorY} comparison of {data_option.data_option} ({data_option.base_year} = 100)",
            scene=dict(camera=dict(eye=dict(x=1.7, y=1.7, z=1.7)), 
                       zaxis_title=f"{data_option.data_option}"),  # Move camera further away
            width=1000,
            height=500
        )
        fig.update_traces(line=dict(width=5))

    elif visType == "2D line graph":
        fig = px.line(data, 
                x="Quarter", 
                y="Value", 
                color="Country",
                color_discrete_map=country_colors,
                title=f"{data_option.QorY} comparison of {data_option.data_option} ({data_option.base_year} = 100)",
                labels={"value": f"{data_option.data_option}", "variable": "Countries"})
        fig.update_layout(
            yaxis=dict(
                title=dict(
                    text=f"{data_option.data_option}"
                )
            ),
        )
        if show_dip_lines:
            print("Trumbone")
            highlighted_quarters = ["2007 Q4", "2009 Q2", "2019 Q4", "2021 Q1"]  # Quarters highlighted with verticle lines
            for quarter in highlighted_quarters:
                fig.add_vline(x=quarter, line_dash="dash", line_color="red")
    elif visType == "Dummy bar graph":
        fig = px.bar(data, x="Quarter", y="Value", color="Country", title="")

    if not show_legend:
        for trace in fig.data:
            trace.showlegend = False
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
            industry_data = multi_data_format(data, industry)
            figs = px.line(industry_data, 
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
        fig.update_layout(title=f"Gross Value Added by industry (2020 = 100)")  # remove
        # fig.update_xaxes(showticklabels=False)
    elif second_plot:
        if visType == "3D line graph":  # Has to be "scene" instead of "xy" for 3d plot
            fig=make_subplots(rows=1, cols=2, specs=[[{"type": "scene"}, {"type": "scene"}]])
        else:
            fig=make_subplots(rows=1, cols=2, specs=[[{"type": "xy"}, {"type": "xy"}]])

        # fig=make_subplots(rows=1, cols=2)
        for trace in make_fig(data, visType, data_option, show_dip_lines, second_plot, second_data, True):
            # trace.showlegend = False
            fig.add_trace(trace, row=1, col=1)
        for trace in make_fig(second_data, visType, data_option, show_dip_lines, second_plot, second_data, False):
            # trace.showlegend = False
            fig.add_trace(trace, row=1, col=2)
        
        if visType != "3D line graph":
            # Determine missing countries (ones in second plot but not first)
            missing_countries = list(set(second_data["Country"]) - set(data["Country"]))

            # Create a dummy dataframe with missing countries
            dummy_df = pd.DataFrame({
                "Quarter": ["1900 Q1"] * len(missing_countries),  # Some old date unlikely to be in range
                "Value": [0] * len(missing_countries),
                "Country": missing_countries
            })
            
            if visType == "QoQ" or visType == "YoY":  # If it is displaying a bar graph
                # Generate hidden traces for missing countries
                for trace in make_fig(dummy_df, "Dummy bar graph", data_option, show_dip_lines, second_plot, second_data, show_legend):
                    trace.visible = "legendonly"  # Hide from graph but keep in legend
                    fig.add_trace(trace, row=1, col=1)
            else:  # If it is displaying a 2d line graph
                countries = list(set(data["Country"]).union(set(second_data["Country"]))) # All countries in both lists
                colour_palette = px.colors.qualitative.Set1  # Choose a Plotly color set
                country_colors = {country: colour_palette[i % len(colour_palette)] for i, country in enumerate(countries)}
                for country in missing_countries:
                    trace = go.Scatter(
                        x=["1900 Q1"],  # Fake data
                        y=[0],
                        mode="lines",
                        name=country,
                        line=dict(color=country_colors.get(country, "#000000")),
                        visible="legendonly",
                        showlegend=True
                    )
                    fig.add_trace(trace, row=1, col=1)
                if show_dip_lines:
                    highlighted_quarters = ["2007 Q4", "2009 Q2", "2019 Q4", "2021 Q1"]
                    for quarter in highlighted_quarters:
                        fig.add_vline(x=quarter, line_dash="dash", line_color="red", row=1, col=1)
                        fig.add_vline(x=quarter, line_dash="dash", line_color="red", row=1, col=2)
    else:
        fig = make_fig(data, visType, data_option, show_dip_lines, second_plot, second_data, show_legend)
    if not second_plot:
        fig.update_layout(showlegend=show_legend)
    return fig

def create_yearly_fig(data, show_legend, second_plot, second_data):
    def yearly_line_graph(data, country_colours):
        return px.line(data, 
        x="Year", 
        y="Value", 
        color="Country",
        color_discrete_map=country_colours,
        title="GDP per Hour Worked Over Time (2015=100)").data
    if second_plot:
        countries = list(set(data["Country"]).union(set(second_data["Country"]))) # All countries in both lists
        colour_palette = px.colors.qualitative.Set1  # Choose a Plotly color set
        country_colours = {country: colour_palette[i % len(colour_palette)] for i, country in enumerate(countries)}
            
        fig=make_subplots(rows=1, cols=2)
        for trace in yearly_line_graph(data, country_colours):
            fig.add_trace(trace, row=1, col=1)
        for trace in yearly_line_graph(second_data, country_colours):
            trace.showlegend = False
            fig.add_trace(trace, row=1, col=2)
    
        # Determine missing countries (ones in second plot but not first)
        missing_countries = list(set(second_data["Country"]) - set(data["Country"]))
        for country in missing_countries:
            trace = go.Scatter(
                x=["1900 Q1"],  # Fake data
                y=[0],
                mode="lines",
                name=country,
                line=dict(color=country_colours.get(country, "#000000")),
                visible="legendonly",
                showlegend=True
            )
            fig.add_trace(trace, row=1, col=1)
    else:
        fig = px.line(data, 
        x="Year", 
        y="Value", 
        color="Country",
        title="GDP per Hour Worked Over Time (2015=100)")
        fig.update_layout(showlegend=show_legend)
    return fig

def update_selection(option):
    if st.session_state.selected == option:  # If clicked again, deselect
        st.session_state.selected = None
    else:
        st.session_state.selected = option


def visualisation_selection(quarterly_data, yearly_data, key, lock_quarterly):
    st.sidebar.divider()
    st.sidebar.subheader("Select data to plot")
    if lock_quarterly:
        QorY = st.sidebar.radio(
            label="Select data to plot",
            options=["Yearly"],
            captions=[
                "Yearly labour productivity",
            ],
            key=f"QorY_{key}"
            )
    else:
        QorY = st.sidebar.radio(
            label="Select data to plot",
            options=["Quarterly", "Yearly"],
            captions=[
                "Quarterly labour productivity",
                "Yearly labour productivity",
            ],
            key=f"QorY_{key}"
        )
    if QorY == "Quarterly":
        st.session_state.show_quarter_slider_two = True
    elif QorY == "Yearly":
        st.session_state.show_yearly_slider_two = True
    
    # Quarter time series selection
    quarterly_option = None
    quarter = None
    industry_selection = ["Total"]
    if st.session_state.show_quarter_slider_two:
        quarters = quarterly_data["Quarter"].unique()
        quarters = [numeric_to_quarter(x) for x in quarters]
        quarter = st.sidebar.select_slider(label = "Quarterly slider", options = quarters, value=(quarters[0], quarters[-1]), label_visibility="collapsed", key=f"Q_Slider_{key}")
        quarterly_options = ["Output Per Hour", "Output Per Worker", "Gross Value Added", "GDP per hour (TPI calculation)"]
        quarterly_option = st.sidebar.selectbox(label= "Select data", options=quarterly_options, key=f"Q_Option_{key}")
        industry_selection = ["Total"]
        if quarterly_option == "Gross Value Added":
            industry_options = quarterly_data["Industry"].unique()
            industry_options = industry_options[~pd.isna(industry_options)] 
            industry_selection = st.sidebar.multiselect(label="Select industry selection", options=industry_options, default=["Total"], key=f"Industry_Selection_{key}")

    # Year time series selection
    yearly_option = None
    year = None
    if st.session_state.show_yearly_slider_two:
        year = st.sidebar.slider(label="Yearly slider!", min_value=yearly_data["Year"].iat[0], max_value=max(yearly_data["Year"]), value=[yearly_data["Year"].iat[0], max(yearly_data["Year"])], label_visibility="collapsed", key=f"Y_Slider_{key}")
        if year[0] == year[1]:
            year = [year[0], year[0] + 1] if year[0] < max(yearly_data["Year"]) else [year[0] - 1, year[0]]
        yearly_option = yearly_options = ["GDP per hour worked"]
        st.sidebar.selectbox(label= "Select data", options=yearly_options, key=f"Y_Option_{key}")

    quarterly_selection = None
    if QorY == "Quarterly":
        # Only allow the user to select countries which are available for the data selected
        regex_escaped_options = re.escape(quarterly_option)
        # Extract country names by removing the option part
        countries = quarterly_data["Country"].unique()
        # countries = [col.replace(quarterly_option, "").strip() for col in matching_columns]
        countries = sorted(countries, key=lambda x: (x not in ["UK", "US", "Euro Area", "European Union"], x))
        default_options = ["UK", "US", "Germany", "France", "Italy", "Spain"]
        country_selection = st.sidebar.multiselect(label = "Select countries to display", options = countries, default=default_options, key=f"country_selection_{key}")

        # Only show data options below if quarterly format is selected
        st.sidebar.write("Select data view options")
        st.sidebar.write("Line graph")
        st.sidebar.checkbox("2D line graph", 
        value=(st.session_state.selected == "2D line graph"), 
        on_change=lambda opt="2D line graph": update_selection(opt), key=f"2d_line_graph{key}")

        st.sidebar.checkbox("3D line graph", 
        value=(st.session_state.selected == "3D line graph"), 
        on_change=lambda opt="3D line graph": update_selection(opt), key=f"3d_line_graph{key}")

        st.sidebar.write("Bar graph")
        st.sidebar.checkbox("Quarter on quarter", 
        value=(st.session_state.selected == "Quarter on quarter"), 
        on_change=lambda opt="Quarter on quarter": update_selection(opt), key=f"qoq_graph{key}")

        st.sidebar.checkbox("Year on year", 
        value=(st.session_state.selected == "Year on year"), 
        on_change=lambda opt="Year on year": update_selection(opt), key=f"yoy_graph{key}")
        if st.session_state.selected == "Year on year":
            quarterly_selection = st.sidebar.selectbox(label= "Specific quarter comparison", options=[1, 2, 3, 4], key=f"quarterly_selection_{key}")

    elif QorY == "Yearly":
        # Only allow the user to select countries which are available for the data selected
        regex_escaped_options = re.escape("GDP per hour worked")
        matching_columns = yearly_data.columns[yearly_data.columns.str.contains(regex_escaped_options, case=False)]

        # Extract country names by removing the option part
        countries= yearly_data["Country"].unique()

        default_options = ["US", "UK", "Germany", "France", "Italy", "Spain"]
        country_selection = st.sidebar.multiselect(label = "Select countries to display", options = countries, default=default_options, key=f"country_selection_{key}")

    visType = "2D line graph"
    if st.session_state.selected == "Quarter on quarter":
        visType = "QoQ"
    elif st.session_state.selected == "Year on year":
        visType = "YoY"
    elif st.session_state.selected == "2D line graph":
        visType = "2D line graph"
    elif st.session_state.selected == "3D line graph":
        visType = "3D line graph"
    elif st.session_state.selected == "2D scatter":
        visType = "2D scatter"
    elif st.session_state.selected == "3D scatter":
        visType = "3D scatter"
    if QorY == "Quarterly":
        data_option = quarterly_option
    elif QorY == "Yearly":
        data_option = yearly_option
    
    # Base year selecter 
    base_year_options = list(range(1997, 2025))
    base_year = st.sidebar.selectbox(label="Change the base year? (default set to 2020)", options=base_year_options, index=base_year_options.index(2020), key=f"base_year_{key}")
    return QorY, quarter, data_option, industry_selection, year, quarterly_selection, country_selection, visType, base_year

@st.cache_data
def load_data():
    yearly_data = pd.read_csv("out/OPH_Processed.csv")
    quarterly_data = pd.read_csv("out/Long_Dataset.csv")
    return quarterly_data, yearly_data

def initialise_app():
    # Set session state variables
    st.session_state.show_quarter_slider = False
    st.session_state.show_yearly_slider = False
    st.session_state.show_quarter_slider_two = False
    st.session_state.show_yearly_slider_two = False
    if "selected" not in st.session_state:
        st.session_state.selected = "2D line graph"

    # Set page configuration
    st.set_page_config(layout="wide")
    # Page formatting
    st.sidebar.html("<a href='https://lab.productivity.ac.uk' alt='The Productivity Lab'></a>")
    st.logo("static/logo.png", link="https://lab.productivity.ac.uk/", icon_image=None)

def export_data_button(data):
    # Export functionality
    if st.sidebar.button("Export Selected Data"):
        @st.cache_data
        def convert_df(df):
            return df.to_csv(index=False).encode("utf-8")
        
        csv = convert_df(data)
        st.sidebar.download_button(
            label="Download data as CSV",
            data=csv,
            file_name="productivity_data.csv",
            mime="text/csv",
        )

def create_refresh_button():
    if st.sidebar.button("Reset To Default Settings"):
        # Use JavaScript to refresh the entire page
        js_code = """
        <script>
            window.parent.location.reload();
        </script>
        """
        st.components.v1.html(js_code, height=0, width=0)

def main_code():

    # Load datasets
    quarterly_data, yearly_data = load_data()

    # First plot
    key = 1
    QorY, quarter, data_option, industry_selection, year, quarterly_selection, country_selection, visType, base_year = visualisation_selection(quarterly_data, yearly_data, key, False)
    plot_one_data_option = data_options(QorY, data_option, base_year, quarterly_selection)
    if QorY == "Quarterly":
        data = quarterly_data
    elif QorY == "Yearly":
        data = yearly_data

    second_plot = False
    # Second plot options
    if len(industry_selection) == 1:
        st.sidebar.divider()
        second_plot = st.sidebar.toggle(label="Show a second plot side by side")
        if second_plot:
            key = 2  # Need a key for duplicated streamlit components (the sidebar options)
            if QorY == "Yearly":
                lock_quarterly = True
            else:
                lock_quarterly = False
            QorY_two, quarter_two, data_option_two, industry_selection_two, year_two, quarterly_selection_two, country_selection_two, visType_two, base_year_two = visualisation_selection(quarterly_data, yearly_data, key, lock_quarterly)
            plot_two_data_option = data_options(QorY_two, data_option_two, base_year_two, quarterly_selection_two)

    #Figure formatting tools
    st.sidebar.divider()
    st.sidebar.subheader("Configure layout")
    show_legend = st.sidebar.toggle(label="Show legend", value=True)
    if visType == "2D line graph":
        show_dip_lines = st.sidebar.toggle(label="Show verticle lines for before and after major dips in productivity (2008 recession and covid-19)", value=False)
    else:
        show_dip_lines = False
    if not show_dip_lines:
        show_years = st.sidebar.toggle(label="Show years instead of quarters", value=False)
    else:
        show_years = False
    
    # Load main content (not in sidebars)
    st.header("TPI Quarterly data tool for US, UK and European labour productivity")


    figure = st.empty()
    if QorY == "Quarterly":
        formatted_data = data_format(data, QorY, quarter, plot_one_data_option, country_selection, show_years, visType, quarterly_selection, industry_selection)
        formatted_data_two = None
        if second_plot:
            formatted_data_two = data_format(data, QorY_two, quarter_two, plot_two_data_option, country_selection_two, show_years, visType_two, quarterly_selection_two, industry_selection_two)
        fig = create_quarterly_fig(formatted_data, show_legend, plot_one_data_option, show_dip_lines, visType, second_plot, formatted_data_two)
        if second_plot:
            fig.update_layout(title=f"{plot_one_data_option.data_option} against {plot_two_data_option.data_option}")  # remove - change this
    else:
        formatted_data = data_format(data, QorY, year, plot_one_data_option, country_selection, show_years)
        formatted_data_two = None
        if second_plot:
            formatted_data_two = data_format(data, QorY_two, year_two, plot_two_data_option, country_selection_two)
        fig = create_yearly_fig(formatted_data, show_legend, second_plot, formatted_data_two) # remove, need to add data_option
    
    # Provides a button to download data
    export_data_button(data)
    create_refresh_button()

    # Display the figure
    if fig:
        # Save session state variables and load figure
        with st.spinner("Loading visualisation"):
            st.session_state.fig = fig
            figure.plotly_chart(st.session_state.fig, use_container_width=True,                 
                    config = {
                        "toImageButtonOptions": {
                            "filename": "Downloaded_file",
                            "scale": 2
                        }
                    })

def main():
    # Initialise app
    initialise_app()

    tab1, tab2 = st.tabs(["Quarterly Data Tool", "About this tool"])
    with tab1:
        main_code()
    with tab2:
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


if __name__ == "__main__":
    main()
