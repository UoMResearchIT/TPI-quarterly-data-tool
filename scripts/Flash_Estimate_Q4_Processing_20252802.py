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

Flash_Estimate = pd.read_csv('../src/Flash_Estimate_Q4.csv', skiprows=7, usecols=[0,1,2,3], names=["Quarter", "GVA", "Hours Worked", "OPH"])
# Flash_Estimate.columns = [
#     f"ONS Flash Estimate {col}" if col not in ["Quarter"] else col
#     for col in Flash_Estimate.columns]
Flash_Estimate["Quarter"] = Flash_Estimate["Quarter"].str.replace(r"(Q\d) (\d{4})", r"\2 \1", regex=True)
print(Flash_Estimate)

Flash_Estimate = Flash_Estimate[['Quarter', 'OPH']]
Flash_Estimate["quarter_numeric"] = Flash_Estimate["Quarter"].apply(quarter_to_numeric)
Flash_Estimate = Flash_Estimate[(Flash_Estimate["quarter_numeric"] >= 2022 - 0.25) & (Flash_Estimate["quarter_numeric"] <= 2024.75)]
Flash_Estimate = Flash_Estimate.drop('quarter_numeric', axis=1)
Flash_Estimate = Flash_Estimate.melt(id_vars = "Quarter", var_name = "Measure")
print(Flash_Estimate)
Flash_Estimate["QoQ Growth (%)"] = Flash_Estimate.groupby("Measure")["value"].pct_change().mul(100).round(2)


Flash_Estimate = Flash_Estimate.dropna()
fig = px.bar(Flash_Estimate, x="Quarter", y="QoQ Growth (%)", color="Measure",
        barmode="group", title="Q1 2022 - Q4 2024 QoQ Growth")
fig.update_layout(showlegend=False)

# Flash_Estimate = Flash_Estimate[['Quarter', 'OPH']]
# Flash_Estimate["Quarter"] = Flash_Estimate["Quarter"].apply(quarter_to_numeric)
# Flash_Estimate = Flash_Estimate[(Flash_Estimate["Quarter"] >= 2020.75 - 1) & (Flash_Estimate["Quarter"] <= 2024.75)]
# # Flash_Estimate = Flash_Estimate.drop('quarter_numeric', axis=1)
# Flash_Estimate = Flash_Estimate.melt(id_vars = "Quarter", var_name = "Measure")
# # Flash_Estimate["QoQ Growth (%)"] = Flash_Estimate.groupby("Measure")["value"].pct_change().mul(100).round(2)
# print(Flash_Estimate)
# quarter_map = {1: 0, 2: 0.25, 3: 0.5, 4: 0.75}
# Flash_Estimate['decimal_part'] = Flash_Estimate['Quarter'] % 1
# print(Flash_Estimate)
# Flash_Estimate = Flash_Estimate[Flash_Estimate['decimal_part'].isin([quarter_map[4]])]
# Flash_Estimate.drop('decimal_part', axis=1, inplace=True)
# Flash_Estimate["YoY Growth (%)"] = Flash_Estimate.groupby("Measure")["value"].pct_change().mul(100).round(2)
# Flash_Estimate["Quarter"] = Flash_Estimate["Quarter"].apply(numeric_to_quarter)
# print(Flash_Estimate)

# Flash_Estimate = Flash_Estimate.dropna()
# fig = px.bar(Flash_Estimate, x="Quarter", y="YoY Growth (%)", color="Measure",
#         barmode="group", title="Q4 YOY Growth")
# fig.update_layout(showlegend=False)
# fig = px.line(Flash_Estimate, 
#         x="Quarter", 
#         y=Flash_Estimate.columns.drop("Quarter").tolist(), 
#         title="Quarter on quarter Comparison (1997 = 100)",
#         labels={"value": "Flash Estimate", "variable": "Productivity Flash Estimates"})
fig.update_layout(template="plotly_white")

fig.show()