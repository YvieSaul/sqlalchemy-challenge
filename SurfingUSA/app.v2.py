# Import the dependencies.
import numpy as np
import sqlalchemy
import datetime as dt
from sqlalchemy.ext.automap import automap_base
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session

from flask import Flask, jsonify, request, render_template
from datetime import datetime, timedelta

#################################################
# Database S
database_path = r"C:\Users\skylo\sqlalchemy-challenge\SurfingUSA\Resources\hawaii.sqlite"
engine = create_engine(f"sqlite:///{database_path}")

#################################################


# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(autoload_with=engine)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)
#################################################
# Flask Setup
#################################################
app = Flask(__name__)


# List routes
@app.route("/")
def welcome():
    """List all available API routes"""
    return(
    f"Available Routes:<br/>"
        f"/api/v1.0/precipitation - Last year of precipitation data<br/>"
        f"/api/v1.0/stations - List of weather stations<br/>"
        f"/api/v1.0/tobs - Last year of temperature observation for most active station<br/>"
        f"/api/v1.0/start - Calculate temperature data from a start date<br/>"
        f"/api/v1.0/range - Calculate temperature data in a date range<br/>"    
    )

# query the last 12 months of precipitation data
@app.route("/api/v1.0/precipitation")
def precipitation():
    session = Session(engine)

    most_recent_date = session.query(func.max(Measurement.date)).scalar()
    one_year_ago = (datetime.strptime(most_recent_date, '%Y-%m-%d') - timedelta(days=365)).strftime('%Y-%m-%d')

    results = session.query(Measurement.date, Measurement.prcp).filter(
    Measurement.date >= one_year_ago).all()
    session.close()

    precipitation_data = [
         {"date": date, "prcp": prcp} for date, prcp in results
    ]
    
    return jsonify(precipitation_data)

# return a list of stations
@app.route("/api/v1.0/stations")
def stations():
    session = Session(engine)
    station_count = session.query(Measurement.station).distinct().all()
    session.close()

    station_data = [
        {"station name": station[0]} for station in station_count
    ]
    
    return jsonify(station_data)


@app.route("/api/v1.0/tobs")
def tobs():
    session = Session(engine)

       # Get most recent date
    most_recent_date = session.query(func.max(Measurement.date)).scalar()
    one_year_ago = (datetime.strptime(most_recent_date, '%Y-%m-%d') - timedelta(days=365)).strftime('%Y-%m-%d')
    
    # Get most active station from previous coding
    most_active_station = "USC00519281"
    
        
      
   # Query for 1 yr of temp observations at most active station
    tobs_measure = session.query(Measurement.date, Measurement.tobs).\
                    filter(Measurement.date >= one_year_ago).\
                    filter(Measurement.station == most_active_station).all()
    

    session.close()

    tobs_data = [
        {"date": date, "tobs": tobs} for date, tobs in tobs_measure
    ]
    
    return jsonify(tobs_data)

    
#################################################
# Flask Routes
#################################################

@app.route("/api/v1.0/start", methods=["GET", "POST"])
def start():
    if request.method == "GET":
        # Return the HTML form for entering the start date
        return """
            <!doctype html>
            <title>Enter Start Date</title>
            <h1>Enter a Start Date</h1>
            <form method="post">
                <label for="start">Start Date (YYYY-MM-DD):</label>
                <input type="date" id="start" name="start" required>
                <button type="submit">Submit</button>
            </form>
        """
    elif request.method == "POST":
        # Handle form submission and perform calculations
        start_date = request.form.get("start")  # Get the date from the form
        if start_date:
            try:
                # Convert the start_date string to a datetime object
                start_date = datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD."}), 400
            
            # Perform database query and calculations
            session = Session(engine)
            results = session.query(
                func.min(Measurement.tobs).label("min_temp"),
                func.max(Measurement.tobs).label("max_temp"),
                func.avg(Measurement.tobs).label("avg_temp")
            ).filter(Measurement.date >= start_date).all()

            session.close()

            min_temp, max_temp, avg_temp = results[0]
            start_calc = {
                "Start Date": start_date.strftime("%Y-%m-%d"),
                "Min Temperature": min_temp,
                "Max Temperature": max_temp,
                "Average Temperature": round(avg_temp, 2) if avg_temp else None,
            }
            return jsonify(start_calc)
        else:
            return jsonify({"error": "No start date provided."}), 400


@app.route("/api/v1.0/range", methods=["GET", "POST"])
def range():
    if request.method == "GET": 
     
        return """
            <!doctype html>
            <title>Enter Date Range</title>
            <h1>Enter a Date Range</h1>
            <form method="post">
                <label for="start">Start Date (YYYY-MM-DD):</label>
                <input type="date" id="start" name="start" required>
                <br><br>
                <label for="end">End Date (YYYY-MM-DD):</label>
                <input type="date" id="end" name="end" required>
                <br><br>
                <button type="submit">Submit</button>
            </form>
        """
    elif request.method == "POST":
        # Handle form submission and perform calculations
        start_date = request.form.get("start")  # Get the start date from the form
        end_date = request.form.get("end")  # Get the end date from the form

        # Validate and convert dates
        if start_date and end_date:
            try:
                start_date = datetime.strptime(start_date, "%Y-%m-%d")
                end_date = datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD."}), 400
            
            if start_date > end_date:
                return jsonify({"error": "Start date must be before or equal to end date."}), 400
            
            # Perform database query and calculations
            session = Session(engine)
            results = session.query(
                func.min(Measurement.tobs).label("min_temp"),
                func.max(Measurement.tobs).label("max_temp"),
                func.avg(Measurement.tobs).label("avg_temp")
            ).filter(Measurement.date >= start_date, Measurement.date <= end_date).all()
            session.close()

            min_temp, max_temp, avg_temp = results[0]
            date_range_calc = {
                "Start Date": start_date.strftime("%Y-%m-%d"),
                "End Date": end_date.strftime("%Y-%m-%d"),
                "Min Temperature": min_temp,
                "Max Temperature": max_temp,
                "Average Temperature": round(avg_temp, 2) if avg_temp else None,
            }
            return jsonify(date_range_calc)
        else:
            return jsonify({"error": "Both start and end dates are required."}), 400


if __name__ == "__main__":
    app.run(debug=True)


     