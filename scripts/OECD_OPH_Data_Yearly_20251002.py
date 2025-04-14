import pandas as pd

OPH = pd.read_csv("../src/OECD OPH Yearly 1970 onwards.csv")
OPH = OPH[["TIME_PERIOD", "Country", "OBS_VALUE"]]
# OPH = OPH.pivot(index='TIME_PERIOD', columns='Country', values='OBS_VALUE').reset_index()
OPH = OPH.rename(columns={"TIME_PERIOD": "Year", 
                          "OBS_VALUE": "Value"})
OPH["Country"] = OPH["Country"].replace("United Kingdom", "UK")
OPH["Country"] = OPH["Country"].replace("United States", "US")
OPH["Variable"] = "GDP per hour worked"
OPH.to_csv("../out/OPH_Processed.csv",index=False)