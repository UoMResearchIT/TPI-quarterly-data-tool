import pandas as pd
from Quarterly_Data_Processing_20250701 import EU_format
import numpy as np

# Process UK GDP data
UK_GDP = pd.read_csv("../src/UK GDP at market prices.csv")
# Use regex to only keep rows containing quarterly data
UK_GDP = UK_GDP[UK_GDP['Title'].str.match(r'^\d{4} Q\d$')]
UK_GDP.columns = ["Quarter", "UK GDP"]

EU_GDP = pd.read_csv("../src/EU GDP at market prices.csv")
EU_GDP = EU_GDP[["TIME_PERIOD", "geo", "OBS_VALUE"]]
EU_GDP = EU_GDP.rename(columns={"TIME_PERIOD": "Quarter"})
EU_GDP["Quarter"] = EU_GDP["Quarter"].str.replace("-", " ", regex=False)
EU_GDP = EU_format(EU_GDP, "GDP")

US_GDP = pd.read_excel("../src/US GDP at market prices.xlsx", skiprows=207, usecols="E,F", names=["Quarter", "US GDP USD"])
# Regex to format quarters correctly
US_GDP["Quarter"] = US_GDP["Quarter"].str.replace(r"(\d{4})Q(\d)", r"\1 Q\2", regex=True)
# Convert to millions so consistent with EU and UK
US_GDP["US GDP USD"] = US_GDP["US GDP USD"] * 1000

GDP = UK_GDP.merge(US_GDP, on=["Quarter"], how="left")
GDP = GDP.merge(EU_GDP[["Quarter", "Germany GDP"]], on=["Quarter"])
GDP = GDP.merge(EU_GDP[["Quarter", "France GDP"]], on=["Quarter"])
GDP = GDP.merge(EU_GDP[["Quarter", "Spain GDP"]], on=["Quarter"])
GDP = GDP.merge(EU_GDP[["Quarter", "Italy GDP"]], on=["Quarter"])

PPP = pd.read_csv("../src/OECD PPP.csv")
PPP = PPP[["TIME_PERIOD", "Country", "OBS_VALUE"]]
PPP = PPP.rename(columns={"TIME_PERIOD": "Quarter", "Country": "geo"})
PPP = PPP.sort_values(by="Quarter", ascending=True)
PPP = EU_format(PPP, "PPP")
PPP = PPP.rename(columns={"Quarter": "Year"})

GDP["Year"] = GDP["Quarter"].str.extract(r"(\d{4})").astype(int)
GDP = GDP.merge(PPP, on="Year")
GDP["UK GDP"] = pd.to_numeric(GDP["UK GDP"], errors="coerce")
GDP["UK GDP USD"] = round(GDP["UK GDP"] * GDP["United Kingdom PPP"], 2)
GDP["Germany GDP USD"] = round(GDP["Germany GDP"] * GDP["Germany PPP"], 2)
GDP["France GDP USD"] = round(GDP["France GDP"] * GDP["France PPP"], 2)
GDP["Spain GDP USD"] = round(GDP["Spain GDP"] * GDP["Spain PPP"], 2)
GDP["Italy GDP USD"] = round(GDP["Italy GDP"] * GDP["Italy PPP"], 2)
GDP_USD = GDP[["Quarter", "UK GDP USD", "US GDP USD", "Germany GDP USD", "France GDP USD", "Spain GDP USD", "Italy GDP USD"]]

# Hours worked!
# UK data is already quarterly, hours per week - so need to times by 13 to get quarterly
# US data is quarterly, in billions of hours
# EU data is quarterly, in thousands of hours worked

EU_Hours = pd.read_csv("../src/EU Hours worked.csv")
EU_Hours = EU_Hours[["TIME_PERIOD", "geo", "OBS_VALUE"]]
EU_Hours = EU_Hours.rename(columns={"TIME_PERIOD": "Quarter"})
EU_Hours = EU_format(EU_Hours, "hours worked").dropna()
for column in EU_Hours.columns:
    if column != "Quarter":
        EU_Hours[column] = EU_Hours[column] / 10**6

UK_Hours = pd.read_excel("../src/ONS GVA and hours worked.xlsx", sheet_name="Table_18", usecols="A,B", skiprows=6, names=["Quarter", "Value"])
UK_Hours["Hours worked"] = UK_Hours["Value"] *13/(10**9)

# Import data and format correctly
US_Hours = pd.read_excel("../src/US hours worked.xlsx", skiprows=2, nrows=1)
US_Hours = US_Hours.drop(["Sector", "Basis", "Component", "Units"], axis=1)
US_Hours = US_Hours.set_index(US_Hours.columns[0]).T
US_Hours.columns.name = None
US_Hours = US_Hours  # Rename the first column
US_Hours = (
    US_Hours.reset_index()
    .rename(columns={"index": "Quarter"})
    .replace("N.A.", np.nan)
    .dropna())
# For some reason US data is always stored as an object, so you have to convert to numeric
US_Hours["Hours worked"] = pd.to_numeric(US_Hours["Hours worked"], errors='coerce')

GDPPH = GDP_USD.copy()
GDPPH["US GDP per hour"] = GDPPH["US GDP USD"] / US_Hours["Hours worked"]
GDPPH["UK GDP per hour"] = GDPPH["UK GDP USD"] / UK_Hours["Hours worked"]
GDPPH["Germany GDP per hour"] = GDPPH["Germany GDP USD"] / EU_Hours["Germany hours worked"]
GDPPH["France GDP per hour"] = GDPPH["France GDP USD"] / EU_Hours["France hours worked"]
GDPPH["Spain GDP per hour"] = GDPPH["Spain GDP USD"] / EU_Hours["Spain hours worked"]
GDPPH["Italy GDP per hour"] = GDPPH["Italy GDP USD"] / EU_Hours["Italy hours worked"]
GDPPH = GDPPH.dropna().drop(["US GDP USD", "UK GDP USD", "Germany GDP USD", "France GDP USD"], axis=1).round(2)

dataset = pd.read_csv("../out/Dataset.csv")
dataset = dataset.merge(GDPPH, on="Quarter", how="left")
dataset.to_csv("../out/Dataset.csv", index=False)
