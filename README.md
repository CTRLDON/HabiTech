HabiTech: Smarter Cities from Orbit
Project Overview
HabiTech is a web application prototype built using Flask and integrated with NASA Earth Observation data. It demonstrates a solution for climate and urban planning challenges by processing satellite data (specifically NO2 pollution data from the OMI instrument) and delivering actionable, AI-generated policy recommendations via a professional dashboard.

The application has two main routes:

Home Page (/): A responsive consulting website interface.

California Dashboard (/california-model): The data analysis and reporting dashboard.

🚀 Setup and Installation Guide for the Judge
To run and test the application, please follow these steps.

Prerequisites
You must have Python 3.8+ installed on your system.

1. File Structure
Ensure the files are organized in the following standard Flask structure:

HabiTech/
├── app.py
└── templates/
    ├── index.html
    └── california_data.html
└── README.md

2. Create and Activate Virtual Environment (Recommended)
Navigate to the project root directory (HabiTech/) and set up a dedicated virtual environment:

# Create the virtual environment
python -m venv venv

# Activate the environment (Linux/macOS)
source venv/bin/activate

# Activate the environment (Windows - Command Prompt/PowerShell)
# venv\Scripts\activate

3. Install Dependencies
With the virtual environment active, install the required Python libraries:

# Install Flask, NASA Earthdata clients, and data processing libraries
pip install Flask earthaccess xarray netCDF4 numpy pandas

4. NASA Earthdata Authentication (Crucial Step)
The application attempts to fetch real-time data using the earthaccess library, which requires NASA Earthdata Login (URS) credentials.

Open a separate Python interpreter or script:

python
>>> import earthaccess
>>> earthaccess.login()


Follow the prompts in the terminal to enter your Earthdata Login Username and Password. The library will save a token, allowing app.py to access and download the satellite files without further interruption.

Note to Judge: If authentication is skipped or fails, the application will automatically catch the error and display Simulated Mock Data on the dashboard. This ensures the frontend and dashboard features remain testable.

⚙️ How to Run the Application
Navigate back to the project root (HabiTech/).

Run the Flask application:

python app.py


The console will display the running URL (typically http://127.0.0.1:5000/). Open this link in your web browser.

✅ Testing the Data Dashboard
From the Home Page (/), scroll down to the "Case Study: California Resilience Initiative" section.

Click the button: "View Live Satellite Data & Full Report".

This will navigate to the /california-model route, triggering the following backend process defined in app.py:

Real Data Success Path (Preferred): If Earthdata login was successful, the app will query OMI NO2 data for California, download the HE5 files, use xarray to process, slice, and calculate the average NO2 concentration, and display the result on the dashboard.

Mock Data Fallback Path: If any part of the data fetching/processing fails, the app will serve the dashboard with mock data, clearly labeled as (Simulated) in the analysis date.

💡 Code Contribution and AI Integration Breakdown
This project was developed rapidly using a hybrid approach combining human expertise with advanced AI assistance:

Component

AI Generation Tool

Team Contribution / Refactoring

Frontend UI (index.html, california_data.html)

Google Gemini (100% initial generation)

Minimal refinement of Tailwind classes and Flask templating (url_for, {{ data.metric }}) for integration.

Flask Application (app.py)

Google Gemini (50% initial generation)

Major Refactoring. The team integrated and rigorously tested the complex geospatial data pipeline, including: setting up the earthaccess search, defining the preprocess_omi_l3 function, correctly implementing xarray.open_mfdataset with the HDF group, coordinate assignment (numpy.linspace), and the final mean calculation.

Data Processing Logic (NO2 Calculation)

Google Gemini (Initial conceptual structure)

Heavy Refinement. The team ensured coordinate slicing (.sel), dimension averaging, and scientific notation formatting were correct and robustly handled errors with the mock data fallback.

Project Concept & Business Model

Team-driven

Defined by the team for the hackathon.

This blend allowed us to prototype the professional frontend quickly and focus our team effort on the technically challenging data integration and processing required for a real-world Earth Observation application.