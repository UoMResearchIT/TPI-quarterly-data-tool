import pandas as pd
import numpy as np
from GDP_Data_Processing_20250602 import GDPPH_Calculation
import sqlite3

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
# US_data = pd.read_excel('../src/US Labour Productivity.xlsx', sheet_name='Quarterly', usecols='A,C,D, GW:LC', skiprows=2)
# US_data = US_data.loc[US_data['Sector'] == 'Nonfarm business sector']
# US_data = US_data.loc[US_data['Units'] == 'Index (2017=100)']

# # Reformat data
# US_data.replace("N.A.", np.nan, inplace=True)
# US_data = US_data.melt(id_vars=["Sector", "Measure", "Units"], var_name="Quarter", value_name="Value")
# US_data = US_data.pivot_table(index=["Quarter"], columns="Measure", values="Value").reset_index()
# US_data = US_data[["Quarter", "Real value-added output", "Output per worker"]]
# US_data = US_data.rename(columns={"Real value-added output": "US RVA", "Output per worker": "US OPW"})
# # For some reason the US data is stored as objects so you have to convert them to be stored as floats to display the data in plotly
# US_data["US OPW"] = pd.to_numeric(US_data["US OPW"], errors="coerce")
# US_data["US RVA"] = pd.to_numeric(US_data["US RVA"], errors="coerce")
# Dataset = ONS_Data.merge(US_data, on=["Quarter"])

# ONS_GVA = pd.read_excel('../src/ONS Reweighted productivity.xlsx', sheet_name='Table_1', usecols='A,B', skiprows=6, header=None, names=["Quarter", "GVA"])
# # New LFS weighting data:
# ONS_OPH = pd.read_excel('../src/ONS Reweighted productivity.xlsx', sheet_name='Table_2', usecols='A,C', skiprows=6, header=None, names=["Quarter", "OPH"])
# ONS_OPW = pd.read_excel('../src/ONS Reweighted productivity.xlsx', sheet_name='Table_3', usecols='A,C', skiprows=6, header=None, names=["Quarter", "OPW"])
# # ONS_OPJ = pd.read_excel('../src/ONS Reweighted productivity.xlsx', sheet_name='Table_4', usecols='A,C', skiprows=6, header=None, names=["Quarter", "OPJ"])
# ONS_Data = ONS_GVA.merge(ONS_OPH, on=["Quarter"])
# ONS_Data = ONS_Data.merge(ONS_OPW, on=["Quarter"])

# # Melt the DataFrame
# df_long = ONS_Data.melt(id_vars=["Quarter"], var_name="Variable", value_name="Value")

# # Add 'UK' column
# df_long["Country"] = "UK"

# # Reorder columns
# df_long = df_long[["Quarter", "Country", "Variable", "Value"]]
# print(df_long)

# Testing using SQL
# conn = sqlite3.connect("../out/Quarterly_dataset.db")
# df_long.to_sql("economic_data", conn, if_exists="replace", index=False)
# df_from_db = pd.read_sql("SELECT * FROM economic_data", conn)
# conn.close()
# print(df_from_db)


# # ONS_Data = ONS_Data.merge(ONS_OPJ, on=["Quarter"])

# ONS_Data["Year"] = ONS_Data["Quarter"].str[:4].astype(int)

# # Find the rebasing factor (Average of 2020 values)
# base_2020 = ONS_Data[ONS_Data["Year"] == 2020].iloc[:, 1:-1].mean()

# # Rebase all values so that 2020 = 100
# ONS_Data.iloc[:, 1:-1] = (ONS_Data.iloc[:, 1:-1] / base_2020) * 100
# ONS_Data = ONS_Data.drop("Year", axis=1)
# Dataset = ONS_Data

# EU_OPH_OPW = pd.read_csv('../src/EU OPH OPW extended.csv')
# EU_OPH_OPW = EU_OPH_OPW.rename(columns={"TIME_PERIOD": "Quarter"})
# EU_OPH_OPW["Quarter"] = EU_OPH_OPW["Quarter"].str.replace("-", " ", regex=False)
# # EU_OPH_OPW = EU_OPH_OPW[["na_item", "Quarter", "geo", "OBS_VALUE"]]
# EU_OPH = EU_OPH_OPW.loc[EU_OPH_OPW['na_item'] == 'Real labour productivity per hour worked']
# EU_OPW = EU_OPH_OPW.loc[EU_OPH_OPW['na_item'] == 'Real labour productivity per person']
# EU_OPH = EU_OPH[["Quarter", "geo", "OBS_VALUE"]]
# EU_OPW = EU_OPW[["Quarter", "geo", "OBS_VALUE"]]

def process():
    EU_GVA = pd.read_csv('../src/EU GVA with industries.csv')
    EU_GVA["Quarter"] = EU_GVA["TIME_PERIOD"].str.replace("-", " ", regex=False)
    EU_GVA = EU_GVA[["TIME_PERIOD", "geo", "nace_r2", "OBS_VALUE"]]
    EU_GVA = EU_GVA.rename(columns={"TIME_PERIOD": "Quarter", "geo": "Country", "nace_r2": "Industry", "OBS_VALUE": "Value"})
    EU_GVA["Variable"] = "GVA"
    # EU_GVA = EU_GVA._append(df_long)
    return EU_GVA

UK_GVA_Bespoke = pd.read_excel('../src/ONS GVA and hours worked.xlsx', sheet_name='Table_15', header=4)
UK_GVA_Bespoke = UK_GVA_Bespoke.drop([0,1])
UK_GVA_Division = pd.read_excel('../src/ONS GVA and hours worked.xlsx', sheet_name='Table_23', header=4)
UK_GVA_Division = UK_GVA_Division.drop([0,1])

def SIC_Code_Combiner(dataset, letters):
    data = SIC_Code_Combine(dataset, letters[0])
    for letter in letters[1:]:
        temp = SIC_Code_Combine(dataset, letter)
        data = data.merge(temp, on='Quarter', how='left')
    return data

def SIC_Code_Combine(dataset, letter):
    filtered_data = dataset.filter(like=f'Part of {letter}', axis=1)
    filtered_data.insert(0, 'Quarter', dataset['SIC 2007 section'])
    filtered_data.set_index("Quarter", inplace=True)
    filtered_data["Summed"] = filtered_data.sum(axis=1)

    ref_value = filtered_data.loc[filtered_data.index.str.startswith("2022"), "Summed"].mean()
    filtered_data[f"{letter}"] = (filtered_data["Summed"] / ref_value) * 100
    return filtered_data[[f"{letter}"]]

print(SIC_Code_Combine(UK_GVA_Bespoke, 'C'))
print(SIC_Code_Combine(UK_GVA_Division, 'A'))
print(SIC_Code_Combine(UK_GVA_Division, 'F'))
print(SIC_Code_Combiner(UK_GVA_Division, ['G', 'H', 'I']))
# print(UK_GVA_Division)

# table 23

# EU_OPH = EU_format(EU_OPH, "OPH")
# EU_OPW = EU_format(EU_OPW, "OPW")
# EU_GVA = EU_format(EU_GVA, "GVA")
# Dataset = Dataset.merge(EU_OPH, on=["Quarter"])
# Dataset = Dataset.merge(EU_OPW, on=["Quarter"])
# Dataset = Dataset.merge(EU_GVA, on=["Quarter"])
# print(Dataset)
# print(Dataset.columns)

# Flash_Estimate = pd.read_csv('../src/Flash_Estimate_Q4.csv', skiprows=7, usecols=[0,1,3], names=["Quarter", "GVA", "OPH"])
# Flash_Estimate.columns = [
#     f"ONS Flash Estimate {col}" if col not in ["Quarter"] else col
#     for col in Flash_Estimate.columns]
# Flash_Estimate["Quarter"] = Flash_Estimate["Quarter"].str.replace(r"(Q\d) (\d{4})", r"\2 \1", regex=True)
# print(Flash_Estimate)
# Dataset = Dataset.merge(Flash_Estimate, on="Quarter", how="outer")

# GDPPH = GDPPH_Calculation()
# Dataset = Dataset.merge(GDPPH, on="Quarter", how="left")
# Dataset.to_csv("../out/Dataset.csv", index=False)
