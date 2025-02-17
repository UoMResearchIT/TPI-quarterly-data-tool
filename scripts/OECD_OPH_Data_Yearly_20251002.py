import pandas as pd

OPH = pd.read_csv("../src/OECD OPH Yearly 1970 onwards.csv")
OPH = OPH[["TIME_PERIOD", "Country", "OBS_VALUE"]]
OPH = OPH.pivot(index='TIME_PERIOD', columns='Country', values='OBS_VALUE').reset_index()
OPH = OPH.rename(columns={"TIME_PERIOD": "Year", 
                          "Germany":"Germany GDP per hour worked",
                          "France": "France GDP per hour worked",
                          "Spain": "Spain GDP per hour worked",
                          "Italy": "Italy GDP per hour worked",
                          "United Kingdom": "UK GDP per hour worked",
                          "United States": "US GDP per hour worked"})
OPH.to_csv("../out/OPH_Processed.csv",index=False)