import pandas as pd
from Quarterly_Data_Processing_20250701 import EU_format

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

PPP = pd.read_csv("../src/OECD PPP.csv")
PPP = PPP[["TIME_PERIOD", "Country", "OBS_VALUE"]]
PPP = PPP.rename(columns={"TIME_PERIOD": "Quarter", "Country": "geo"})
PPP = PPP.sort_values(by="Quarter", ascending=True)
PPP = EU_format(PPP, "PPP")
PPP = PPP.rename(columns={"Quarter": "Year"})
print(PPP)

GDP["Year"] = GDP["Quarter"].str.extract(r"(\d{4})").astype(int)
GDP = GDP.merge(PPP, on="Year")
GDP["UK GDP"] = pd.to_numeric(GDP["UK GDP"], errors="coerce")
print(GDP.dtypes)
GDP["UK GDP USD"] = round(GDP["UK GDP"] * GDP["United Kingdom PPP"], 2)
GDP["Germany GDP USD"] = round(GDP["Germany GDP"] * GDP["Germany PPP"], 2)
GDP["France GDP USD"] = round(GDP["France GDP"] * GDP["France PPP"], 2)
print(GDP)
GDP_USD = GDP[["UK GDP USD", "US GDP USD", "Germany GDP USD", "France GDP USD"]]
print(GDP_USD)

# Hours worked!
# UK data is already quarterly, hours per week - so need to times by 13 to get quarterly
# US data is annually, so divide by 4 to get quarterly
# EU data is quarterly, in thousands of hours worked

