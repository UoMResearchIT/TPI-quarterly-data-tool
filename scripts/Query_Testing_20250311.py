import pandas as pd

Long_Dataset = pd.read_csv('../out/Long_Dataset.csv')
Short_Dataset = pd.read_csv('../out/Dataset.csv')
# Long_Dataset = Long_Dataset.set_index(["Quarter", "Country", "Variable", "Industry"]).sort_index()
# x = Long_Dataset.loc[(["2005 Q1", "2010 Q3"], ["UK", "Germany"], "GVA", ["Manufacturing", "Trade & Hospitality"])]
# df_reset = Long_Dataset.reset_index()
print(Long_Dataset)
filtered = Long_Dataset.query(
    "Quarter >= 2005.0 and Quarter <= 2007.75 and Country in ['UK', 'Germany'] and Variable == 'GVA' and Industry in ['Manufacturing', 'Services']"
)
print(Long_Dataset['Industry'].unique())
print(filtered)