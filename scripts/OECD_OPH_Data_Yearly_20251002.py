import pandas as pd

# OPH = pd.read_csv("../src/OECD OPH Yearly.csv")
OPH = pd.read_csv("../src/OECD OPH Yearly 1970 onwards.csv")
OPH = OPH[["Country", "TIME_PERIOD", "OBS_VALUE"]]
OPH = OPH.pivot(index='Country', columns='TIME_PERIOD', values='OBS_VALUE').reset_index()
OPH = OPH.melt(id_vars=["Country"], var_name="Year", value_name="GDP per Hour Worked")
print(OPH)
OPH.to_csv("../out/OPH_Processed.csv",index=False)