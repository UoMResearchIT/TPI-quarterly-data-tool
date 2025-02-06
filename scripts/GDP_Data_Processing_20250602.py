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

US_GDP = pd.read_excel("../src/US GDP at market prices.xlsx", skiprows=207, usecols="E,F", names=["Quarter", "US GDP"])
US_GDP["Quarter"] = US_GDP["Quarter"].str.replace(r"(\d{4})Q(\d)", r"\1 Q\2", regex=True)
US_GDP["US GDP"] = US_GDP["US GDP"] * 1000
GDP = UK_GDP.merge(US_GDP, on=["Quarter"], how="left")
GDP = GDP.merge(EU_GDP[["Quarter", "Germany GDP"]], on=["Quarter"])
GDP = GDP.merge(EU_GDP[["Quarter", "France GDP"]], on=["Quarter"])
print(GDP)