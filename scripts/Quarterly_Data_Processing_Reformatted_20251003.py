import pandas as pd
import numpy as np
# from GDP_Data_Processing_20250602 import GDPPH_Calculation
import sqlite3

pd.set_option('future.no_silent_downcasting', True)
def quarter_to_numeric(q):
    if not isinstance(q, str) or "Q" not in q:
        print(f"Unexpected format: {q}")

    try:
        year, qtr = q.split(" ")
    except:
        # Remove trailing spaces
        q = q.strip()
        year, qtr = q.split(" ")
    return int(year) + (int(qtr[1]) - 1) / 4  # Converts "1997 Q3" → 1997.5

def numeric_to_quarter(n): # Converts 1997.5 → "1997 Q3"
    year = int(n)
    qtr = int((n - year) * 4) + 1
    return f"{year} Q{qtr}"

def EU_GVA_Process():
    EU_GVA = pd.read_csv('../src/EU GVA with industries.csv')
    EU_GVA["TIME_PERIOD"] = EU_GVA["TIME_PERIOD"].str.replace("-", " ", regex=False)
    EU_GVA = EU_GVA[["TIME_PERIOD", "geo", "nace_r2", "OBS_VALUE"]]
    EU_GVA = EU_GVA.rename(columns={"TIME_PERIOD": "Quarter", "geo": "Country", "nace_r2": "Industry", "OBS_VALUE": "Value"})
    EU_GVA["Variable"] = "GVA"
    EU_GVA["Industry"] = EU_GVA["Industry"].str.replace("Total - all NACE activities", "Total", regex=False)
    EU_GVA["Industry"] = EU_GVA["Industry"].str.replace("Wholesale and retail trade, transport, accommodation and food service activities", "Trade & Hospitality", regex=False)
    EU_GVA["Industry"] = EU_GVA["Industry"].str.replace("Financial and insurance activities", "Finance and insurance", regex=False)
    EU_GVA["Industry"] = EU_GVA["Industry"].str.replace("Real estate activities", "Real estate", regex=False)
    EU_GVA["Industry"] = EU_GVA["Industry"].str.replace("Professional, scientific and technical activities; administrative and support service activities", "Professional & Admin Services", regex=False)
    EU_GVA["Industry"] = EU_GVA["Industry"].str.replace("Public administration, defence, education, human health and social work activities", "Public Services", regex=False)
    EU_GVA["Industry"] = EU_GVA["Industry"].str.replace("Arts, entertainment and recreation; other service activities; activities of household and extra-territorial organizations and bodies", "Arts & Other Services", regex=False)
    EU_GVA["Country"] = EU_GVA["Country"].str.replace("Euro area (EA11-1999, EA12-2001, EA13-2007, EA15-2008, EA16-2009, EA17-2011, EA18-2014, EA19-2015, EA20-2023)", "Euro area", regex=False)
    EU_GVA["Country"] = EU_GVA["Country"].str.replace("European Union - 27 countries (from 2020)", "European Union", regex=False)
    return EU_GVA

def SIC_Code_Combine(dataset, letters):
    if len(letters) == 1:
        x = False
        combined = letters[0]
    else:
        x = True
        combined = "".join(letters)
    letter = letters[0]
    filtered_data = dataset.filter(like=f'Part of {letter}', axis=1).copy()
    if filtered_data.empty:
        filtered_data = dataset.filter(like=f'{letter}', axis=1)
    filtered_data.insert(0, 'Quarter', dataset['SIC 2007 section'])
    if x:
        for letter in letters[1:]:
            temp = dataset.filter(like=f'Part of {letter}', axis=1)
            if temp.empty:
                temp = dataset.filter(like=f'{letter}', axis=1)
            filtered_data = pd.concat([filtered_data, temp], axis=1, ignore_index=False)
    filtered_data.set_index("Quarter", inplace=True)
    filtered_data["Summed"] = filtered_data.sum(axis=1)
    ref_value = filtered_data.loc[filtered_data.index.str.startswith("2022"), "Summed"].mean()
    filtered_data[f"{combined}"] = (filtered_data["Summed"] / ref_value) * 100
    return filtered_data[[f"{combined}"]]

# Using the Flash estimate data instead
# ONS_OPH = pd.read_excel('../src/OPH May release.xlsx', sheet_name='Table_18', usecols='A,B', skiprows=110, names=["Quarter", "OPH"])
# ONS_OPW = pd.read_excel('../src/OPW May release.xlsx', sheet_name='Table_17', usecols='A,B', skiprows=7, names=["Quarter", "OPW"])
# ONS_Data = ONS_OPH.merge(ONS_OPW, on=["Quarter"])
# # Rebase to 2020
# ONS_Data["Year"] = ONS_Data["Quarter"].str[:4].astype(int)

# # Find the rebasing factor (Average of 2020 values)
# base_2020 = ONS_Data[ONS_Data["Year"] == 2020].iloc[:, 1:-1].mean()

# # Rebase all values so that 2020 = 100
# ONS_Data.iloc[:, 1:-1] = (ONS_Data.iloc[:, 1:-1] / base_2020) * 100
# ONS_Data = ONS_Data.drop("Year", axis=1)

# # Reformat dataframe
# ONS_Data = ONS_Data.melt(id_vars=["Quarter"], var_name="Variable", value_name="Value")
# ONS_Data["Country"] = "UK"
# ONS_Data = ONS_Data[["Quarter", "Country", "Variable", "Value"]]

EU_OPH_OPW = pd.read_csv('../src/EU OPH OPW.csv')
EU_OPH_OPW = EU_OPH_OPW.rename(columns={"TIME_PERIOD": "Quarter", "na_item": "Variable", "geo": "Country", "OBS_VALUE": "Value"})
EU_OPH_OPW["Quarter"] = EU_OPH_OPW["Quarter"].str.replace("-", " ", regex=False)
EU_OPH_OPW = EU_OPH_OPW[["Quarter", "Variable", "Country", "Value"]]
EU_OPH_OPW["Variable"] = EU_OPH_OPW["Variable"].replace({"Real labour productivity per hour worked": "OPH", "Real labour productivity per person": "OPW"}) 
EU_OPH_OPW["Country"] = EU_OPH_OPW["Country"].str.replace("Euro area (EA11-1999, EA12-2001, EA13-2007, EA15-2008, EA16-2009, EA17-2011, EA18-2014, EA19-2015, EA20-2023)", "Euro area", regex=False)
EU_OPH_OPW["Country"] = EU_OPH_OPW["Country"].str.replace("European Union - 27 countries (from 2020)", "European Union", regex=False)

Dataset = EU_GVA_Process()
# Dataset = pd.concat([Dataset, ONS_Data])
Dataset = pd.concat([Dataset, EU_OPH_OPW])

UK_GVA_Division = pd.read_excel('../src/ONS GVA May 2025 release.xlsx', sheet_name='Table_23', header=4)
UK_GVA_Division = UK_GVA_Division.drop([0,1])
SIC_Codes = ['A', 'C', 'F', ['G', 'H', 'I'], 'J', 'K', 'L', ['M', 'N'], ['O', 'P', 'Q'], ['B', 'C', 'D', 'E']]
SIC_Codes_Dict = {'A to T': 'Total', 'A': 'Agriculture, forestry and fishing', 'C': 'Manufacturing', 'F': 'Construction', 'GHI': 'Trade & Hospitality', 'J': 'Information and communication', 'K': 'Finance and insurance', 'L': 'Real estate', 'MN': 'Professional & Admin Services', 'OPQ': 'Public Services', 'BCDE': 'Industry (except construction)'}
SIC_Code_Data = UK_GVA_Division.filter(like='A to T', axis=1)
SIC_Code_Data.insert(0, 'Quarter', UK_GVA_Division['SIC 2007 section'])
for code in SIC_Codes:
    temp = SIC_Code_Combine(UK_GVA_Division, code)
    SIC_Code_Data = SIC_Code_Data.merge(temp, on='Quarter', how='left')
SIC_Code_Data = SIC_Code_Data.rename(columns=SIC_Codes_Dict)
SIC_Code_Data["Year"] = SIC_Code_Data["Quarter"].str[:4].astype(int)

# Find the rebasing factor (Average of 2020 values)
base_2020 = SIC_Code_Data[SIC_Code_Data["Year"] == 2020].iloc[:, 1:-1].mean()

# Rebase all values so that 2020 = 100
SIC_Code_Data.iloc[:, 1:-1] = (SIC_Code_Data.iloc[:, 1:-1] / base_2020) * 100
SIC_Code_Data = SIC_Code_Data.drop("Year", axis=1)

# Format for long form data
SIC_Code_Data = SIC_Code_Data.melt(id_vars=["Quarter"], var_name="Industry", value_name="Value").dropna()
SIC_Code_Data["Country"] = "UK"
SIC_Code_Data["Variable"] = "GVA"
Dataset = pd.concat([Dataset, SIC_Code_Data])

# Import all Quarterly US productivity data since Q1 1997 (consistent with ONS data)
US_data = pd.read_excel('../src/US Labour Productivity.xlsx', sheet_name='Quarterly', usecols='A,C,D, GW:LE', skiprows=2) # Need to change LE every data release, this is silly
US_data = US_data.loc[US_data['Sector'] == 'Business sector']  # Most representative of total economy
US_data = US_data.loc[US_data['Units'] == 'Index (2017=100)']

# Reformat data
US_data.replace("N.A.", np.nan, inplace=True)
US_data = US_data.melt(id_vars=["Sector", "Measure", "Units"], var_name="Quarter", value_name="Value")
US_data = US_data.pivot_table(index=["Quarter"], columns="Measure", values="Value").reset_index()
US_data = US_data[["Quarter", "Real value-added output", "Output per worker", "Labor productivity"]]

US_data["Year"] = US_data["Quarter"].str[:4].astype(int)

# Find the rebasing factor (Average of 2020 values)
base_2020 = US_data[US_data["Year"] == 2020].iloc[:, 1:-1].mean()

# Rebase all values so that 2020 = 100
US_data.iloc[:, 1:-1] = (US_data.iloc[:, 1:-1] / base_2020) * 100
US_data = US_data.drop("Year", axis=1)

US_data = US_data.rename(columns={"Real value-added output": "GVA", "Output per worker": "OPW", "Labor productivity": "OPH"})
# For some reason the US data is stored as objects so you have to convert them to be stored as floats to display the data in plotly
US_data = US_data.melt(id_vars=['Quarter'], var_name='Variable', value_name='Value')
US_data["Value"] = pd.to_numeric(US_data["Value"], errors="coerce")
US_data['Country'] = 'US'
US_data = US_data[['Quarter', 'Variable', 'Country', 'Value']] # doesnt matter what order !
Dataset = pd.concat([Dataset, US_data])

# Flash Estimate ONS Data
# OPH:
Flash_Estimate_OPH = pd.read_csv('../src/OPH Q1 Flash Estimate.csv', skiprows=7, usecols=[0,3], names=["Quarter", "Output Per Hour"])
Flash_Estimate_OPH["Quarter"] = Flash_Estimate_OPH["Quarter"].str.replace(r"(Q\d) (\d{4})", r"\2 \1", regex=True)

# Change to 2020 = 100
Flash_Estimate_OPH["Year"] = Flash_Estimate_OPH["Quarter"].str[:4].astype(int)
base_2020 = Flash_Estimate_OPH[Flash_Estimate_OPH["Year"] == 2020].iloc[:, 1:-1].mean()
Flash_Estimate_OPH.iloc[:, 1:-1] = (Flash_Estimate_OPH.iloc[:, 1:-1] / base_2020) * 100
Flash_Estimate_OPH = Flash_Estimate_OPH.drop("Year", axis=1)

# OPW:
Flash_Estimate_OPW = pd.read_csv('../src/OPW Q1 Flash Estimate.csv', skiprows=7, usecols=[0,3], names=["Quarter", "Output Per Worker"])
Flash_Estimate_OPW["Quarter"] = Flash_Estimate_OPW["Quarter"].str.replace(r"(Q\d) (\d{4})", r"\2 \1", regex=True)

# Change to 2020 = 100
Flash_Estimate_OPW["Year"] = Flash_Estimate_OPW["Quarter"].str[:4].astype(int)
base_2020 = Flash_Estimate_OPW[Flash_Estimate_OPW["Year"] == 2020].iloc[:, 1:-1].mean()
Flash_Estimate_OPW.iloc[:, 1:-1] = (Flash_Estimate_OPW.iloc[:, 1:-1] / base_2020) * 100
Flash_Estimate_OPW = Flash_Estimate_OPW.drop("Year", axis=1)

Flash_Estimate_Data = Flash_Estimate_OPH.merge(Flash_Estimate_OPW, on='Quarter')
Flash_Estimate_Data = Flash_Estimate_Data.melt(id_vars=["Quarter"], var_name="Variable", value_name="Value")
# Flash_Estimate_Data['Country'] = 'UK Flash Estimate'
Flash_Estimate_Data['Country'] = 'UK'
Flash_Estimate_Data['Industry'] = 'Total'
Dataset = pd.concat([Dataset, Flash_Estimate_Data])

# Replace all with full indicator titles
Dataset["Variable"] = Dataset['Variable'].replace('OPH', 'Output Per Hour')
Dataset["Variable"] = Dataset['Variable'].replace('OPW', 'Output Per Worker')
Dataset["Variable"] = Dataset['Variable'].replace('GVA', 'Gross Value Added')
Dataset["Quarter"] = Dataset["Quarter"].apply(quarter_to_numeric) 
Dataset["Industry"] = Dataset["Industry"].fillna("Total")
Dataset.to_csv("../out/Long_Dataset.csv", index=False)