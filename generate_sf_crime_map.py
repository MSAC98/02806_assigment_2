import pandas as pd
import folium

df = pd.read_csv('sf_crime_2003_2025.csv.gz')

# Finding latitude and longitude columns
def find_lat_lon_columns(df):
    lat_candidates = [col for col in df.columns if 'lat' in col.lower()]
    lon_candidates = [col for col in df.columns if 'lon' in col.lower() or 'lng' in col.lower() or 'long' in col.lower()]
    if lat_candidates and lon_candidates:
        return lat_candidates[0], lon_candidates[0]
    raise ValueError('Latitude/Longitude columns not found.')

lat_col, lon_col = find_lat_lon_columns(df)

# Replace comma with period for decimal conversion
df[lat_col] = df[lat_col].astype(str).str.replace(',', '.', regex=False)
df[lon_col] = df[lon_col].astype(str).str.replace(',', '.', regex=False)

# Drop rows with missing or invalid coordinates
df = df[pd.to_numeric(df[lat_col], errors='coerce').notnull() & pd.to_numeric(df[lon_col], errors='coerce').notnull()]
df[lat_col] = df[lat_col].astype(float)
df[lon_col] = df[lon_col].astype(float)

# Remove any of the remaining NaNs
valid_coords = df[[lat_col, lon_col]].dropna()
if valid_coords.empty:
    raise ValueError('No valid coordinates found in the data.')

# Center map on San Francisco
sf_center = [valid_coords[lat_col].mean(), valid_coords[lon_col].mean()]
crime_map = folium.Map(location=sf_center, zoom_start=12)

# Add points (set to mac 1000 for performance)
for _, row in valid_coords.sample(n=min(1000, len(valid_coords)), random_state=1).iterrows():
    folium.CircleMarker(
        location=[row[lat_col], row[lon_col]],
        radius=2,
        color='red',
        fill=True,
        fill_opacity=0.5
    ).add_to(crime_map)

crime_map.save('plots/sf_crime_map.html')
print('Map saved to plots/sf_crime_map.html')
