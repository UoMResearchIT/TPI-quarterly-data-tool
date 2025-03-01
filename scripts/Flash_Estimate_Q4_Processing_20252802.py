import pandas as pd
import plotly_express as px

Flash_Estimate = pd.read_csv('../src/Flash_Estimate_Q4.csv', skiprows=7, usecols=[0,1,2,3], names=["Quarter", "GVA", "Hours Worked", "OPH"])
Flash_Estimate.columns = [
    f"ONS Flash Estimate {col}" if col not in ["Quarter"] else col
    for col in Flash_Estimate.columns]
Flash_Estimate["Quarter"] = Flash_Estimate["Quarter"].str.replace(r"(Q\d) (\d{4})", r"\2 \1", regex=True)
print(Flash_Estimate)


# fig = px.bar(Flash_Estimate, x="Quarter", y="QoQ Growth (%)", color="Country",
#         barmode="group", title="QoQ Growth Across Countries")

# fig = px.bar(Flash_Estimate, x="Quarter", y="YoY Growth (%)", color="Country",
#         barmode="group", title="YoY Growth Across Countries")

# fig = px.line(Flash_Estimate, 
#         x="Quarter", 
#         y=Flash_Estimate.columns.drop("Quarter").tolist(), 
#         title="Quarter on quarter Comparison (2020 = 100)",
#         labels={"value": "Flash Estimate", "variable": "Variable"})
# fig.update_layout(template="plotly_white")

fig.show()