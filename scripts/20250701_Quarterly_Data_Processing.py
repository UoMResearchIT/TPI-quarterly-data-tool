import pandas as pd
import numpy as np

pd.set_option('future.no_silent_downcasting', True)

# Import all Quarterly US productivity data since Q1 1997 (consistent with ONS data)
US_data = pd.read_excel('../src/US Labour Productivity.xlsx', sheet_name='Quarterly', usecols='A,C,D, GW:LC', skiprows=2)
US_data = US_data.loc[US_data['Sector'] == 'Nonfarm business sector']
US_data = US_data.loc[US_data['Units'] == 'Index (2017=100)']

US_data.replace("N.A.", np.nan, inplace=True)
US_data = US_data.melt(id_vars=["Sector", "Measure", "Units"], var_name="Quarter", value_name="Value")
US_data = US_data.pivot_table(index=["Quarter"], columns="Measure", values="Value").reset_index()
US_data = US_data[["Quarter", "Hours worked", "Real value-added output", "Output per worker"]]
US_data = US_data.rename(columns={"Hours worked": "US hours worked", "Real value-added output": "US real value-added output", "Output per worker": "US OPW"})
print(US_data)

ONS_GVA = pd.read_excel('../src/ONS Reweighted productivity.xlsx', sheet_name='Table_1', usecols='A,B', skiprows=7, header=None, names=["Quarter", "ONS GVA"])
# New LFS weighting data
ONS_OPH = pd.read_excel('../src/ONS Reweighted productivity.xlsx', sheet_name='Table_2', usecols='A,C', skiprows=7, header=None, names=["Quarter", "ONS OPH"])
ONS_OPW = pd.read_excel('../src/ONS Reweighted productivity.xlsx', sheet_name='Table_3', usecols='A,C', skiprows=7, header=None, names=["Quarter", "ONS OPW"])
ONS_OPJ = pd.read_excel('../src/ONS Reweighted productivity.xlsx', sheet_name='Table_4', usecols='A,C', skiprows=7, header=None, names=["Quarter", "ONS OPJ"])
ONS_Data = ONS_GVA.merge(ONS_OPH, on=["Quarter"])
ONS_Data = ONS_Data.merge(ONS_OPW, on=["Quarter"])
ONS_Data = ONS_Data.merge(ONS_OPJ, on=["Quarter"])
Dataset = ONS_Data.merge(US_data, on=["Quarter"])

print(Dataset)