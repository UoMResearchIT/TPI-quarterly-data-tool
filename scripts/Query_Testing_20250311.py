import pandas as pd

Long_Dataset = pd.read_csv('../out/Long_Dataset.csv')
Short_Dataset = pd.read_csv('../out/Dataset.csv')
# Long_Dataset = Long_Dataset.set_index(["Quarter", "Country", "Variable", "Industry"]).sort_index()
# x = Long_Dataset.loc[(["2005 Q1", "2010 Q3"], ["UK", "Germany"], "GVA", ["Manufacturing", "Trade & Hospitality"])]
# df_reset = Long_Dataset.reset_index()

filtered = Long_Dataset.query(
    "Country in ['UK', 'Germany', 'Poland'] and Variable == 'GVA' and Industry in ['Manufacturing', 'Trade & Hospitality']"
)

print(filtered)