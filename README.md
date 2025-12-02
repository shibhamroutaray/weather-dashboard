# Weather Analytics Dashboard

This is a simple Streamlit web application that shows real-time weather data for any city.  
It uses the OpenWeatherMap API to display current conditions and a 5-day forecast.
You can view the live deployed app here:

**Live App:** https://weather-dashboard-alces.streamlit.app/

---

The dashboard includes:

- Current temperature, humidity, description, and weather icon  
- Temperature, humidity, wind speed, and precipitation probability charts  
- 5-day forecast table  
- Automatic refresh every 60 seconds  
- City comparison mode (view two cities on the same charts)  
- Map showing selected city (or both cities in comparison mode)

This project was created for learning purposes.

---

## Features

- View real-time weather information
- Compare two cities side-by-side
- Interactive Plotly line charts
- Clean table with 2-decimal formatting
- Map visualization with coordinates
- Supports °C and °F
- Updated every minute automatically

---

## How to Run Locally

### 1. Install the required packages

```
pip install -r requirements.txt

```

### 2. Create a `.env` file and add your OpenWeatherMap API key

```
OPENWEATHER_API_KEY=your_key_here

```

### 3. Run the app with Streamlit

```
streamlit run weather_dashboard.py

```

---

## Deployment

The project is deployed using Streamlit Cloud.  
Secrets (API key) are stored using the Streamlit Secrets Manager.

---

## Project Structure

```

└── weather_dashboard.py      # Main app
└── requirements.txt          # Dependencies
└── .streamlit/
      └── config.toml        # Theme settings

```
---

## Requirements

- Python 3.8 or higher  
- Streamlit  
- pandas  
- requests  
- plotly  
- python-dotenv  

These are all listed in `requirements.txt`.

---

## Notes

- Do not upload your `.env` file or share your API key.
- The free version of the OpenWeatherMap API may occasionally return slow results.
- The precipitation probability is based on POP values from the API (0–100%).

---

## License

This project is for learning and personal use.
