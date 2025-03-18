import pandas as pd
import numpy as np
import sqlite3

# Testing using SQL
df_long = pd.read_csv("../out/Long_Dataset.csv")

# Debug Step 1: Examine the dataframe
print("Original data sample:")
print(df_long.head())
print("\nData types:")
print(df_long.dtypes)
print("\nUnique Quarter values:")
print(df_long['Quarter'].unique())

# Create a clean, normalized database structure
conn = sqlite3.connect("../out/Quarterly_dataset.db")
cursor_obj = conn.cursor()
cursor_obj.execute("DROP TABLE IF EXISTS Quarters")
cursor_obj.execute("DROP TABLE IF EXISTS Countries")
cursor_obj.execute("DROP TABLE IF EXISTS Variables")
cursor_obj.execute("DROP TABLE IF EXISTS EconomicData")

# Create tables with explicit data types
quarters = """CREATE TABLE Quarters (
    QuarterID INTEGER PRIMARY KEY,
    Quarter TEXT UNIQUE
); """

countries = """CREATE TABLE Countries (
    CountryID INTEGER PRIMARY KEY,
    Country TEXT UNIQUE
);"""

variables = """CREATE TABLE Variables (
    VariableID INTEGER PRIMARY KEY,
    Variable TEXT UNIQUE
);"""

economic_data = """CREATE TABLE EconomicData (
    ID INTEGER PRIMARY KEY,
    QuarterID INTEGER,
    CountryID INTEGER,
    VariableID INTEGER,
    Value REAL,
    FOREIGN KEY (QuarterID) REFERENCES Quarters(QuarterID),
    FOREIGN KEY (CountryID) REFERENCES Countries(CountryID),
    FOREIGN KEY (VariableID) REFERENCES Variables(VariableID)
);"""

cursor_obj.execute(quarters)
cursor_obj.execute(countries)
cursor_obj.execute(variables)
cursor_obj.execute(economic_data)

# Debug Step 2: Create a copy of the dataframe and convert all joining columns to strings
df_working = df_long.copy()
print("\nConverting all joining columns to strings...")
df_working['Quarter'] = df_working['Quarter'].astype(str)
df_working['Country'] = df_working['Country'].astype(str)
df_working['Variable'] = df_working['Variable'].astype(str)

# Debug Step 3: Manually populate the tables
print("\nInserting unique values into lookup tables...")

# Quarters table
unique_quarters = df_working['Quarter'].unique().tolist()
for i, quarter in enumerate(unique_quarters, 1):
    cursor_obj.execute("INSERT INTO Quarters (QuarterID, Quarter) VALUES (?, ?)", (i, quarter))

# Countries table
unique_countries = df_working['Country'].unique().tolist()
for i, country in enumerate(unique_countries, 1):
    cursor_obj.execute("INSERT INTO Countries (CountryID, Country) VALUES (?, ?)", (i, country))

# Variables table
unique_variables = df_working['Variable'].unique().tolist()
for i, variable in enumerate(unique_variables, 1):
    cursor_obj.execute("INSERT INTO Variables (VariableID, Variable) VALUES (?, ?)", (i, variable))

conn.commit()

# Debug Step 4: Create dictionaries for mapping values to IDs
quarters_dict = {q: i for i, q in enumerate(unique_quarters, 1)}
countries_dict = {c: i for i, c in enumerate(unique_countries, 1)}
variables_dict = {v: i for i, v in enumerate(unique_variables, 1)}

print("\nCreated mapping dictionaries:")
print(f"Quarters: {len(quarters_dict)} unique values")
print(f"Countries: {len(countries_dict)} unique values")
print(f"Variables: {len(variables_dict)} unique values")

# Debug Step 5: Insert Economic Data using dictionaries instead of joins
print("\nInserting economic data...")
records = []
for i, row in df_working.iterrows():
    quarter_id = quarters_dict[row['Quarter']]
    country_id = countries_dict[row['Country']]
    variable_id = variables_dict[row['Variable']]
    value = row['Value']
    records.append((i+1, quarter_id, country_id, variable_id, value))

cursor_obj.executemany("""
INSERT INTO EconomicData (ID, QuarterID, CountryID, VariableID, Value) 
VALUES (?, ?, ?, ?, ?)
""", records)

conn.commit()

# Debug Step 6: Verify the contents with explicit queries
print("\nVerifying database contents...")

# Count records in each table
quarters_count = pd.read_sql("SELECT COUNT(*) FROM Quarters", conn).iloc[0, 0]
countries_count = pd.read_sql("SELECT COUNT(*) FROM Countries", conn).iloc[0, 0]
variables_count = pd.read_sql("SELECT COUNT(*) FROM Variables", conn).iloc[0, 0]
econ_data_count = pd.read_sql("SELECT COUNT(*) FROM EconomicData", conn).iloc[0, 0]

print(f"Quarters: {quarters_count} records")
print(f"Countries: {countries_count} records")
print(f"Variables: {variables_count} records")
print(f"Economic data: {econ_data_count} records")

# Verify with a sample join
print("\nSample data with proper joins:")
sample_query = """
SELECT q.Quarter, c.Country, v.Variable, e.Value
FROM EconomicData e
JOIN Quarters q ON e.QuarterID = q.QuarterID
JOIN Countries c ON e.CountryID = c.CountryID
JOIN Variables v ON e.VariableID = v.VariableID
LIMIT 10
"""

try:
    sample_data = pd.read_sql(sample_query, conn)
    print(sample_data)
    
    # Verify original row count matches the normalized data
    print(f"\nOriginal dataframe: {len(df_long)} rows")
    print(f"Normalized data: {econ_data_count} rows")
    if len(df_long) == econ_data_count:
        print("✓ Row counts match!")
    else:
        print("⚠ Row counts don't match!")
except Exception as e:
    print(f"Error in sample query: {e}")
conn.close()
