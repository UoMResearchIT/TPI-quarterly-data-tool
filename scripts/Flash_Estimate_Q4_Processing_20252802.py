# Script made for making visualisation for different datasets

import pandas as pd
import plotly_express as px
# import sys
# sys.path.append("../") # So I can import functions from the streamlit script, makes the bargraphs black and white though?
# from Streamlit_application import quarter_to_numeric, numeric_to_quarter

def quarter_to_numeric(q):
    year, qtr = q.split(" ")
    return int(year) + (int(qtr[1]) - 1) / 4  # Converts "1997 Q3" → 1997.5

def numeric_to_quarter(n):
    year = int(n)
    qtr = int((n - year) * 4) + 1
    return f"{year} Q{qtr}"

def line_graph(data, year):
        base = data.loc[data["Quarter"] == f"{year} Q1", ["GVA", "Hours Worked", "OPH"]].iloc[0].to_numpy()
        cols = ["GVA", "Hours Worked", "OPH"]
        data[cols] = (data[cols] / base) * 100

        data["quarter_numeric"] = data["Quarter"].apply(quarter_to_numeric)
        data = data[(data["quarter_numeric"] >= year) & (data["quarter_numeric"] <= 2024.75)]
        data = data.drop(["quarter_numeric"], axis=1)

        fig = px.line(
        data, 
        x="Quarter", 
        y=data.columns.drop("Quarter").tolist(), 
        title=f"Quarter on quarter Comparison ({year} = 100)",
        labels={"value": "Flash Estimate", "variable": "Productivity Flash Estimates"})
        return fig

def qoq(data):
        data = data[['Quarter', 'OPH']]
        data["quarter_numeric"] = data["Quarter"].apply(quarter_to_numeric)
        data = data[(data["quarter_numeric"] >= 2022 - 0.25) & (data["quarter_numeric"] <= 2024.75)]
        data = data.drop('quarter_numeric', axis=1)
        data = data.melt(id_vars = "Quarter", var_name = "Measure")
        data["QoQ Growth (%)"] = data.groupby("Measure")["value"].pct_change().mul(100).round(2)

        data = data.dropna()
        fig = px.bar(data, x="Quarter", y="QoQ Growth (%)", color="Measure",
                barmode="group", title="Q1 2022 - Q4 2024 QoQ Growth")
        fig.update_layout(showlegend=False)
        return fig

def yoy(data):
        data = data[['Quarter', 'OPH']]
        data["Quarter"] = data["Quarter"].apply(quarter_to_numeric)
        data = data[(data["Quarter"] >= 2020.75 - 1) & (data["Quarter"] <= 2024.75)]
        data = data.melt(id_vars = "Quarter", var_name = "Measure")
        quarter_map = {1: 0, 2: 0.25, 3: 0.5, 4: 0.75}
        data['decimal_part'] = data['Quarter'] % 1
        data = data[data['decimal_part'].isin([quarter_map[4]])]
        data.drop('decimal_part', axis=1, inplace=True)
        data["YoY Growth (%)"] = data.groupby("Measure")["value"].pct_change().mul(100).round(2)
        data["Quarter"] = data["Quarter"].apply(numeric_to_quarter)

        data = data.dropna()
        fig = px.bar(data, x="Quarter", y="YoY Growth (%)", color="Measure",
                barmode="group", title="Q4 YOY Growth")
        fig.update_layout(showlegend=False)
        return fig

Flash_Estimate = pd.read_csv('../src/Flash_Estimate_Q4.csv', skiprows=7, usecols=[0,1,2,3], names=["Quarter", "GVA", "Hours Worked", "OPH"])
# Change from Q4 1997 to 1997 Q4
Flash_Estimate["Quarter"] = Flash_Estimate["Quarter"].str.replace(r"(Q\d) (\d{4})", r"\2 \1", regex=True)

fig = line_graph(Flash_Estimate, 2007)
# fig = qoq(Flash_Estimate)
# fig = yoy(Flash_Estimate)

fig.update_layout(template="plotly_white")

fig.show()