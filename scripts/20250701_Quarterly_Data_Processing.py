import pandas as pd
import numpy as np
import plotly.express as px

pd.set_option('future.no_silent_downcasting', True)

# Import all Quarterly US productivity data since Q1 1997 (consistent with ONS data)
US_data = pd.read_excel('../src/US Labour Productivity.xlsx', sheet_name='Quarterly', usecols='A,C,D, GW:LC', skiprows=2)
US_data = US_data.loc[US_data['Sector'] == 'Nonfarm business sector']
US_data = US_data.loc[US_data['Units'] == 'Index (2017=100)']

# Reformat data
US_data.replace("N.A.", np.nan, inplace=True)
US_data = US_data.melt(id_vars=["Sector", "Measure", "Units"], var_name="Quarter", value_name="Value")
US_data = US_data.pivot_table(index=["Quarter"], columns="Measure", values="Value").reset_index()
US_data = US_data[["Quarter", "Hours worked", "Real value-added output", "Output per worker"]]
US_data = US_data.rename(columns={"Hours worked": "US hours worked", "Real value-added output": "US real value-added output", "Output per worker": "US OPW"})
# For some reason the US data is stored as objects so you have to convert them to be stored as floats to display the data in plotly
US_data["US OPW"] = pd.to_numeric(US_data["US OPW"], errors="coerce")
US_data["US hours worked"] = pd.to_numeric(US_data["US hours worked"], errors="coerce")
US_data["US real value-added output"] = pd.to_numeric(US_data["US real value-added output"], errors="coerce")

ONS_GVA = pd.read_excel('../src/ONS Reweighted productivity.xlsx', sheet_name='Table_1', usecols='A,B', skiprows=6, header=None, names=["Quarter", "ONS GVA"])
# New LFS weighting data:
ONS_OPH = pd.read_excel('../src/ONS Reweighted productivity.xlsx', sheet_name='Table_2', usecols='A,C', skiprows=6, header=None, names=["Quarter", "ONS OPH"])
ONS_OPW = pd.read_excel('../src/ONS Reweighted productivity.xlsx', sheet_name='Table_3', usecols='A,C', skiprows=6, header=None, names=["Quarter", "ONS OPW"])
ONS_OPJ = pd.read_excel('../src/ONS Reweighted productivity.xlsx', sheet_name='Table_4', usecols='A,C', skiprows=6, header=None, names=["Quarter", "ONS OPJ"])
ONS_Data = ONS_GVA.merge(ONS_OPH, on=["Quarter"])
ONS_Data = ONS_Data.merge(ONS_OPW, on=["Quarter"])
ONS_Data = ONS_Data.merge(ONS_OPJ, on=["Quarter"])
Dataset = ONS_Data.merge(US_data, on=["Quarter"])

EU_Data = pd.read_csv('../src/EU OPH OPW.csv')
EU_Data = EU_Data.rename(columns={"TIME_PERIOD": "Quarter"})
EU_Data["Quarter"] = EU_Data["Quarter"].str.replace("-", " ", regex=False)
EU_Data = EU_Data[["na_item", "Quarter", "geo", "OBS_VALUE"]]
EU_OPH = EU_Data.loc[EU_Data['na_item'] == 'Real labour productivity per hour worked']
EU_OPW = EU_Data.loc[EU_Data['na_item'] == 'Real labour productivity per person']

def EU_format(data, indicator):
    formatted_data = pd.DataFrame()
    for region in data["geo"].unique():
        tmp = data.loc[data['geo'] == region]
        tmp = tmp.rename(columns = {"OBS_VALUE": f"{region} {indicator}"})
        tmp = tmp.drop(["na_item", "geo"], axis=1)
        if formatted_data.empty:
            formatted_data = tmp
        else:
            formatted_data = formatted_data.merge(tmp, on=["Quarter"], how="outer")
    return formatted_data

print(EU_format(EU_OPH, "OPH"))
EU_OPH = EU_format(EU_OPH, "OPH")
EU_OPW = EU_format(EU_OPW, "OPW")
Dataset = Dataset.merge(EU_OPH, on=["Quarter"])
Dataset = Dataset.merge(EU_OPW, on=["Quarter"])
print(Dataset)

Dataset.to_csv("../out/Dataset.csv", index=False)

Dataset["Year"] = Dataset["Quarter"].str.extract(r"(\d{4})").astype(int)  # Extracts the 4-digit year
Dataset["Quarter_Num"] = Dataset["Quarter"].str.extract(r"Q(\d)").astype(int)  # Extracts the quarter number

Dataset["Quarter"] = pd.to_datetime(Dataset["Year"].astype(str) + "-" + (Dataset["Quarter_Num"] * 3 - 2).astype(str) + "-01")

print(Dataset.dtypes)
fig = px.line(Dataset, x="Quarter", y=["ONS OPW", "US OPW", "Germany OPW"], title="Time Series Comparison")
fig.show()