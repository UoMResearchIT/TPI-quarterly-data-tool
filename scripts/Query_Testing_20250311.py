import pandas as pd
import plotly_express as px
import plotly.graph_objects as go

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
    f"Quarter >= 2005.0 and Quarter <= 2024.25 and Country in ['UK', 'Germany', 'France', 'Italy', 'Spain'] and Variable == '{data_option}' and Industry == 'Total'"
)

filtered['Quarter'] = filtered['Quarter'].apply(numeric_to_quarter)
data = filtered.copy()
print(filtered)

data['Country_encoded'] = pd.Categorical(data['Country']).codes
data['Quarter_encoded'] = pd.Categorical(data['Quarter']).codes

fig = go.Figure(data=[go.Scatter3d(
    x=data['Country_encoded'],
    y=data['Quarter_encoded'],
    z=data['Value'],
    mode='markers',
    marker=dict(
        size=5,
        color=data['Value'],  # Color by z-axis value
        colorscale='Viridis',
        opacity=0.8,
        colorbar=dict(title='Value')
    ),
    text=[f"Country: {country}<br>Quarter: {quarter}<br>{'Value'}: {value}" 
            for country, quarter, value in zip(data['Country'], data['Quarter'], data['Value'])],
    hoverinfo='text'
)])

# fig = px.line(filtered, 
#               x='Quarter', 
#               y='Value', 
#               color='Country',
#               title='GVA Comparison: UK vs Germany (2005-2007)',
#               labels={'Value': 'GVA', 'Date': 'Quarter'},
#               markers=True)

# fig = px.line(
# filtered, 
# x="Quarter", 
# y=filtered.columns.drop("Quarter").tolist(), 
# title=f"Quarter on quarter Comparison",
# labels={"value": "Flash Estimate", "variable": "Productivity Flash Estimates"})

fig.show()