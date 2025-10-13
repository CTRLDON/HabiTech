import os
from flask import Flask, render_template, abort
import time

# --- NECESSARY IMPORTS UNCOMMENTED FOR REAL DATA PROCESSING ---
import earthaccess
import xarray as xr
import numpy as np
# Added pandas as it is needed for the time coordinate assignment logic
import pandas as pd

# Initialize Flask App
app = Flask(__name__, template_folder='templates')

HIGH_RISK_THRESHOLD = 1.6e-9


def fetch_california_data():
    """
    Fetches and processes NASA Earth Observation data for a region in California.
    
    It attempts to use the 'earthaccess' library first. If that fails (due to 
    missing credentials or libraries), it falls back to providing mock data.
    """
    
    # --- Data Acquisition Logic (Real-World Implementation: OMI NO2) ---
    try:
        # 1. AUTHENTICATION (Crucial step for NASA Data)
        # You MUST run 'earthaccess.login()' once in your environment to save credentials
        # earthaccess.login()
        
        # 2. DEFINE THE AREA OF INTEREST (e.g., a bounding box for the LA area)
        # Define the region of interest (California bounding box used in processing)
        earthaccess.login(strategy="environment")
        lon_min, lat_min = -124.48, 32.53
        lon_max, lat_max = -114.13, 42.01
        BBOX = (lon_min, lat_min, lon_max, lat_max) # Defined as (west, south, east, north)
        
        START_DATE = "2025-09-01"
        END_DATE = "2025-10-01"
        
        # 3. QUERY FOR A DATASET (Updated to OMI Tropospheric NO2)
        # Concept ID for OMI-Aura_L3-OMNO2d (Daily Level 3 NO2)
        search_results = earthaccess.search_data(
            short_name="OMNO2d",
            temporal=(START_DATE, END_DATE),
            bounding_box=BBOX
        )

        print(len(search_results))
        
        # 4. DOWNLOAD THE DATA FILES
        # This will download the HE5 files to your current working directory.
        import glob
        files = glob.glob("tempo_data/OMI-Aura_L3.*he5")
        if not files:
            earthaccess.download(search_results , "tempo_data")
        files = glob.glob("tempo_data/OMI-Aura_L3*.he5")
        print(len(files))
        
        
        # files = [
        #     "C://Users//k2005//OneDrive//Documents//Python//nasa//tempo_data//OMI-Aura_L3-OMNO2d_2025m0101_v003-2025m0104t055810.he5" ,
        #     "C://Users\k2005\OneDrive\Documents//Python//nasa//tempo_data//OMI-Aura_L3-OMNO2d_2025m0102_v003-2025m0104t074359.he5" ,
        #     "C://Users\k2005\OneDrive\Documents//Python//nasa//tempo_data//OMI-Aura_L3-OMNO2d_2025m0103_v003-2025m0107t131052.he5"
        # ]
        
        # Fallback if no files were found for the query
        if not files:
            raise FileNotFoundError("Earthaccess ran, but no files were downloaded for the given query.")

        
        # 5. PROCESS THE HE5 FILES (The core of your NO2 processing)
        print(f"Processing {len(files)} downloaded HE5 files...")

        # --- Define Pre-processing Function (from user's code) ---
        def preprocess_omi_l3(ds):
            """
            Standardizes the OMI L3 Dataset for concatenation by renaming dimensions 
            and adding a placeholder time dimension, as the raw HE5 group output lacks them.
            """
            # Rename generic dimensions (720x1440 grid) to lat/lon
            ds = ds.rename_dims({'phony_dim_0': 'lat', 'phony_dim_1': 'lon'})

            # Drop the 'Weight' variable if it exists
            if 'Weight' in ds:
                ds = ds.drop_vars('Weight')

            # Add a time dimension of size 1, required for concatenation
            ds = ds.expand_dims(time=1)
            return ds

        # --- Open and Concatenate Files (from user's code) ---
        # Note: We use the dynamic 'files' list returned by earthaccess.download
        ds_combined = xr.open_mfdataset(
            files,
            engine="netcdf4",
            # Specify the internal group containing the data fields
            group="HDFEOS/GRIDS/ColumnAmountNO2/Data Fields",
            preprocess=preprocess_omi_l3,
            combine="nested",
            concat_dim="time",
            parallel=True
        )

        # OMI L3 Global Grid (0.25 degree resolution)
        lat = np.linspace(-89.875, 89.875, 720) 
        lon = np.linspace(-179.875, 179.875, 1440)

        # Assign the spatial coordinates
        ds_combined = ds_combined.assign_coords(lat=lat, lon=lon)

        # Skip assigning specific dates, as xarray should infer time dimension 
        # from the metadata or the order of files, which is sufficient for averaging.
        
        # --- Calculate Average NO2 for California Region (from user's code) ---
        # Select the data for the California region using .sel()
        ca_data = ds_combined.sel(
            lon=slice(lon_min, lon_max), 
            lat=slice(lat_min, lat_max)
        )

        # Calculate the overall average for the entire period across space (lat, lon) and time
        # Use .compute() to force Dask to load and calculate the result
        overall_mean_no2 = ca_data['ColumnAmountNO2Trop'].mean(dim=['lat', 'lon', 'time']).compute().item()
        
        # Format the NO2 value for display (Scientific notation)
        formatted_no2 = f"{overall_mean_no2:.2e}" 

        print(f"Successfully retrieved and calculated Average NO2: {formatted_no2} moles/cm^2")
        
# 6. RISK ASSESSMENT (NEW LOGIC)
        if overall_mean_no2 >= HIGH_RISK_THRESHOLD:
            risk_level = "HIGH RISK"
            risk_color_hex = "#DC2626" # Tailwind Red-600
            risk_interpretation = f"HIGH RISK: Concentration ({formatted_no2}) exceeds the threshold ({HIGH_RISK_THRESHOLD:.2e}), suggesting severe air quality stress from pollution."
        else:
            risk_level = "LOW/MODERATE RISK"
            risk_color_hex = "#059669" # Tailwind Green-600
            risk_interpretation = f"LOW/MODERATE RISK: Concentration ({formatted_no2}) is below the threshold, suggesting acceptable air quality for the period."

        
        # 7. RETURN REAL DATA STRUCTURE
        real_data = {
            "region_name": "Greater California Area (Live Earthdata)",
            "analysis_date": f"{time.strftime('%Y-%m-%d')} (Live)",
            "summary": f"Live AI analysis confirms **{risk_level}** air quality risk. Based on OMI data, the average Tropospheric NO2 in the BBOX is **{formatted_no2} moles/cm²**.",
            "metrics": [
                {
                    "name": "Average Tropospheric NO2", 
                    "value": formatted_no2, 
                    "unit": "moles/cm²", 
                    "interpretation": risk_interpretation
                },
                {"name": "Data Source", "value": "NASA OMI/Aura", "unit": "Satellite", "interpretation": "Analysis using actual satellite data for the specified period."},
            ],
            "recommendations": [
                "Implement dynamic traffic metering to reduce localized NO2 spikes.",
                "Promote public transport usage during peak NO2 hours.",
                "Review industrial emission standards in areas with peak NO2 readings."
            ],
            # --- FLAGS FOR UI CONTROL ---
            "is_live_data": True, 
            "risk_color_hex": risk_color_hex,
            "risk_level": risk_level
        }
        
        return real_data

    except Exception as e:
        # This block runs if real data fetching fails (e.g., credentials missing, files not found)
        print(f"Using mock data due to error: {e}")
        
        # --- Mock Data Fallback (Current Executable Code) ---
        mock_data = {
            "region_name": "Greater Los Angeles Area (Simulated)",
            "analysis_date": "2024-10-01 (Simulated)",
            "summary": "AI analysis highlights extreme Urban Heat Island effects and correlated pollution spikes near major transport hubs.",
            "metrics": [
                {"name": "Average Tropospheric NO2", "value": "5.50e+15", "unit": "moles/cm²", "interpretation": "Simulated high NO2 concentration reflecting heavy urban activity and traffic."},
                {"name": "Average Land Surface Temperature (LST)", "value": "95.2°F", "unit": "Fahrenheit", "interpretation": "High LST suggests severe Urban Heat Island effect, necessitating green infrastructure interventions."},
                {"name": "NDVI (Vegetation Index) Score", "value": "0.15", "unit": "Index (0-1)", "interpretation": "Extremely low score, indicating insufficient park coverage and tree canopy for heat mitigation."},
                {"name": "Precipitation Anomaly", "value": "-3.2 inches", "unit": "Inches (vs historical avg)", "interpretation": "Significant long-term drought conditions confirmed by NASA's GRACE-FO data, critical water management required."},
            ],
            "recommendations": [
                "Mandate reflective roofing materials across all new industrial development.",
                "Implement a 'Cool Pavement' pilot program in high-LST residential zones.",
                "Identify 50 acres for new urban agriculture and vertical farming projects to improve NDVI and air quality."
            ]
        }
        
        return mock_data

@app.route('/')
def home():
    """Renders the main HabiTech landing page."""
    return render_template('main.html')

@app.route('/california-model')
def california_model():
    """
    Renders the detailed California data page after fetching data.
    """
    try:
        # Fetch the data using the function, which handles real or mock retrieval
        data = fetch_california_data()
        
        # Render the template and pass the data dictionary to it
        return render_template('california_data.html', data=data)
    except Exception as e:
        # Simple error handling for the hackathon
        print(f"Fatal application error: {e}")
        # Use Flask's built-in 500 error page
        abort(500) 


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, port=port)


