import pandas as pd
import plotly_express as px

def numeric_to_quarter(n):
    year = int(n)
    qtr = int((n - year) * 4) + 1
    return f"{year} Q{qtr}"

Long_Dataset = pd.read_csv('../out/Long_Dataset.csv')
# Short_Dataset = pd.read_csv('../out/Dataset.csv')
# Long_Dataset = Long_Dataset.set_index(["Quarter", "Country", "Variable", "Industry"]).sort_index()
# x = Long_Dataset.loc[(["2005 Q1", "2010 Q3"], ["UK", "Germany"], "GVA", ["Manufacturing", "Trade & Hospitality"])]
# df_reset = Long_Dataset.reset_index()
data_option = "GVA"
print(Long_Dataset)
filtered = Long_Dataset.query(
    f"Quarter >= 2005.0 and Quarter <= 2007.75 and Country in ['UK', 'Germany'] and Variable == '{data_option}' and Industry == 'Total'"
)

filtered['Quarter'] = filtered['Quarter'].apply(numeric_to_quarter)
print(filtered)

fig = px.line(filtered, 
              x='Quarter', 
              y='Value', 
              color='Country',
              title='GVA Comparison: UK vs Germany (2005-2007)',
              labels={'Value': 'GVA', 'Date': 'Quarter'},
              markers=True)

# fig = px.line(
# filtered, 
# x="Quarter", 
# y=filtered.columns.drop("Quarter").tolist(), 
# title=f"Quarter on quarter Comparison",
# labels={"value": "Flash Estimate", "variable": "Productivity Flash Estimates"})

fig.show()