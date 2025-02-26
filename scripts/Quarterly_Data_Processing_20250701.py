import pandas as pd
import numpy as np
import plotly.express as px

pd.set_option('future.no_silent_downcasting', True)


def EU_format(data, indicator):
    formatted_data = pd.DataFrame()
    for region in data["geo"].unique():
        tmp = data.loc[data['geo'] == region]
        if "Euro area" in region:
            tmp = tmp.rename(columns = {"OBS_VALUE": f"Euro Area {indicator}"})
        if "European Union" in region:
            tmp = tmp.rename(columns = {"OBS_VALUE": f"European Union {indicator}"})
        else:
            tmp = tmp.rename(columns = {"OBS_VALUE": f"{region} {indicator}"})
        tmp = tmp.drop(["geo"], axis=1)
        if formatted_data.empty:
            formatted_data = tmp
        else:
            formatted_data = formatted_data.merge(tmp, on=["Quarter"], how="outer")
    return formatted_data

# Import all Quarterly US productivity data since Q1 1997 (consistent with ONS data)
# Need to change cause this is only one specific industry
US_data = pd.read_excel('../src/US Labour Productivity.xlsx', sheet_name='Quarterly', usecols='A,C,D, GW:LC', skiprows=2)
US_data = US_data.loc[US_data['Sector'] == 'Nonfarm business sector']
US_data = US_data.loc[US_data['Units'] == 'Index (2017=100)']

# Reformat data
US_data.replace("N.A.", np.nan, inplace=True)
US_data = US_data.melt(id_vars=["Sector", "Measure", "Units"], var_name="Quarter", value_name="Value")
US_data = US_data.pivot_table(index=["Quarter"], columns="Measure", values="Value").reset_index()
US_data = US_data[["Quarter", "Real value-added output", "Output per worker"]]
US_data = US_data.rename(columns={"Real value-added output": "US RVA", "Output per worker": "US OPW"})
# For some reason the US data is stored as objects so you have to convert them to be stored as floats to display the data in plotly
US_data["US OPW"] = pd.to_numeric(US_data["US OPW"], errors="coerce")
US_data["US RVA"] = pd.to_numeric(US_data["US RVA"], errors="coerce")

ONS_GVA = pd.read_excel('../src/ONS Reweighted productivity.xlsx', sheet_name='Table_1', usecols='A,B', skiprows=6, header=None, names=["Quarter", "UK GVA"])
# New LFS weighting data:
ONS_OPH = pd.read_excel('../src/ONS Reweighted productivity.xlsx', sheet_name='Table_2', usecols='A,C', skiprows=6, header=None, names=["Quarter", "UK OPH"])
ONS_OPW = pd.read_excel('../src/ONS Reweighted productivity.xlsx', sheet_name='Table_3', usecols='A,C', skiprows=6, header=None, names=["Quarter", "UK OPW"])
ONS_OPJ = pd.read_excel('../src/ONS Reweighted productivity.xlsx', sheet_name='Table_4', usecols='A,C', skiprows=6, header=None, names=["Quarter", "UK OPJ"])
ONS_Data = ONS_GVA.merge(ONS_OPH, on=["Quarter"])
ONS_Data = ONS_Data.merge(ONS_OPW, on=["Quarter"])
ONS_Data = ONS_Data.merge(ONS_OPJ, on=["Quarter"])
# A_2020 = ONS_Data.loc[ONS_Data['Quarter'] == "2020 Q1"]  # Index value in 2020
# B_2022 = ONS_Data.loc[ONS_Data['Quarter'] == "2022 Q1"]  # Index value in 2022
# print(ONS_Data)
# print(A_2020)
# print(B_2022)
# Convert 'Quarter' to datetime for easier filtering
# print("here", ONS_Data.to_string())
ONS_Data["Year"] = ONS_Data["Quarter"].str[:4].astype(int)

# Find the rebasing factor (Average of 2020 values)
base_2020 = ONS_Data[ONS_Data["Year"] == 2020].iloc[:, 1:-1].mean()

# Rebase all values so that 2020 = 100
ONS_Data.iloc[:, 1:-1] = (ONS_Data.iloc[:, 1:-1] / base_2020) * 100
ONS_Data = ONS_Data.drop("Year", axis=1)
Dataset = ONS_Data.merge(US_data, on=["Quarter"])

EU_OPH_OPW = pd.read_csv('../src/EU OPH OPW extended.csv')
EU_OPH_OPW = EU_OPH_OPW.rename(columns={"TIME_PERIOD": "Quarter"})
EU_OPH_OPW["Quarter"] = EU_OPH_OPW["Quarter"].str.replace("-", " ", regex=False)
# EU_OPH_OPW = EU_OPH_OPW[["na_item", "Quarter", "geo", "OBS_VALUE"]]
EU_OPH = EU_OPH_OPW.loc[EU_OPH_OPW['na_item'] == 'Real labour productivity per hour worked']
EU_OPW = EU_OPH_OPW.loc[EU_OPH_OPW['na_item'] == 'Real labour productivity per person']
EU_OPH = EU_OPH[["Quarter", "geo", "OBS_VALUE"]]
EU_OPW = EU_OPW[["Quarter", "geo", "OBS_VALUE"]]

EU_GVA = pd.read_csv('../src/EU GVA extended.csv')
EU_GVA = EU_GVA.rename(columns={"TIME_PERIOD": "Quarter"})
EU_GVA["Quarter"] = EU_GVA["Quarter"].str.replace("-", " ", regex=False)
EU_GVA = EU_GVA[["Quarter", "geo", "OBS_VALUE"]]
print(EU_GVA)
print(EU_GVA.columns)

EU_OPH = EU_format(EU_OPH, "OPH")
EU_OPW = EU_format(EU_OPW, "OPW")
EU_GVA = EU_format(EU_GVA, "GVA")
Dataset = Dataset.merge(EU_OPH, on=["Quarter"])
Dataset = Dataset.merge(EU_OPW, on=["Quarter"])
Dataset = Dataset.merge(EU_GVA, on=["Quarter"])

Dataset.to_csv("../out/Dataset.csv", index=False)

# Reformating quarters to datatime so can be used by Plotly - remove?
# Dataset["Year"] = Dataset["Quarter"].str.extract(r"(\d{4})").astype(int)  # Extracts the 4-digit year
# Dataset["Quarter_Num"] = Dataset["Quarter"].str.extract(r"Q(\d)").astype(int)  # Extracts the quarter number
# Dataset["Quarter"] = pd.to_datetime(Dataset["Year"].astype(str) + "-" + (Dataset["Quarter_Num"] * 3 - 2).astype(str) + "-01")

