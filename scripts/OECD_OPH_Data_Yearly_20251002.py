import pandas as pd

OPH = pd.read_csv("../src/OECD OPH.csv")
OPH = OPH[["TIME_PERIOD", "Country", "OBS_VALUE"]]
print(OPH)
OPH = OPH.pivot(index='TIME_PERIOD', columns='Country', values='OBS_VALUE').reset_index()
OPH = OPH.melt(id_vars="TIME_PERIOD", 
                  var_name="Country", 
                  value_name="Value")
OPH = OPH.rename(columns={"TIME_PERIOD": "Year"})
OPH["Country"] = OPH["Country"].replace("United Kingdom", "UK")
OPH["Country"] = OPH["Country"].replace("United States", "US")
OPH["Country"] = OPH["Country"].replace("Euro area (19 countries)", "Euro Area")
OPH["Country"] = OPH["Country"].replace("European Union – 27 countries (from 01/02/2020)", "European Union")
OPH["Country"] = OPH["Country"].replace("OECD - Total", "OECD Total")
OPH["Variable"] = "GDP per hour worked"
OPH.to_csv("../out/OPH_Processed.csv",index=False)