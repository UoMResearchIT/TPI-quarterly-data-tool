import pandas as pd

# Data from 
# https://data-explorer.oecd.org/vis?tm=output%20per%20hour&pg=0&snb=8&df[ds]=dsDisseminateFinalDMZ&df[id]=DSD_PDB%40DF_PDB_GR&df[ag]=OECD.SDD.TPS&df[vs]=1.0&dq=FIN%2BDEU%2BIRL%2BITA%2BNLD%2BNOR%2BPOL%2BPRT%2BESP%2BSWE%2BGBR%2BUSA%2BEA20%2BEU27_2020%2BOECD%2BDNK%2BFRA.A.GDPHRS..IX....&pd=1995%2C2024&to[TIME_PERIOD]=false&vw=tb
# Base = 2020
OPH = pd.read_csv("../src/OECD OPH.csv")
OPH = OPH[["TIME_PERIOD", "Reference area", "OBS_VALUE"]].rename(columns={"Reference area": "Country"})
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