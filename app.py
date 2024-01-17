# Import the dependencies.
import numpy as np
import flask

import sqlalchemy

from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
import datetime as dt

from flask import Flask, jsonify


#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(autoload_with=engine)

# Save references to each table
Station = Base.classes.station
Measurement = Base.classes.measurement


#################################################
# Flask Setup
#################################################
app = Flask(__name__)


#################################################
# Flask Routes
#################################################


# Route for the home page (index)
@app.route("/")
def index():
    """List all available api routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"Enter START Date YYYY-MM-DD:<br/>"
        f"/api/v1.0/temp/<start><br/>"
        f"Enter START and END Date YYYY-MM-DD:<br/>"
        f"/api/v1.0/temp/<start>/<end>"
    )


# Route for precipitation scores ranging from the last date in the data set and one year before that
@app.route("/api/v1.0/precipitation")
def precipitation():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    # Calculate the date one year before the last date in data set.
    one_yr_ago = dt.date(2017, 8, 23) - dt.timedelta(days=365)
    one_yr_ago

    # Perform a query to retrieve the date and precipitation scores
    results = (
        session.query(Measurement.date, Measurement.prcp)
        .filter(Measurement.date >= one_yr_ago)
        .all()
    )

    session.close

    # Convert query results into a dictionary
    prcp_data = {date: prcp for date, prcp in results}

    return jsonify(prcp_data)


# Route for list of all station names
@app.route("/api/v1.0/stations")
def stations():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    # Perform a query to retrieve all station names
    results = session.query(Measurement.station).group_by(Measurement.station).all()

    session.close

    all_stations = [result.station for result in results]

    return jsonify(all_stations)


# Route for temperature observations for the most active station
@app.route("/api/v1.0/tobs")
def tobs():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    # Perform a query to find the amount of times each station appears in the database
    station_counts = (
        session.query(Measurement.station, func.count(Measurement.id).label("count"))
        .group_by(Measurement.station)
        .order_by(func.count(Measurement.id).desc())
        .all()
    )

    # Create a variable for the most active station
    most_active_station = station_counts[0][0]

    # Calculate the date one year from the last date in data set.
    one_yr_ago = dt.date(2017, 8, 23) - dt.timedelta(days=365)

    # Perform a query for the dates and temp observations of most active station for previous year of data
    results = (
        session.query(Measurement.date, Measurement.tobs)
        .filter(Measurement.date >= one_yr_ago)
        .filter(Measurement.station == most_active_station)
        .all()
    )

    session.close

    # Convert results into a list of dictionaries
    temps = [{"date": date, "tobs": tobs} for date, tobs in results]

    return jsonify(temps)


# Route for temperature statistics for a specified start or start-end range
@app.route("/api/v1.0/temp/<start>")
@app.route("/api/v1.0/temp/<start>/<end>")
def temperature_stats(start, end=None):
    # Create our session (link) from Python to the DB
    session = Session(engine)

    # If an end date is provided, calculate stats for the date range
    if end:
        results = (
            session.query(
                func.min(Measurement.tobs).label("TMIN"),
                func.avg(Measurement.tobs).label("TAVG"),
                func.max(Measurement.tobs).label("TMAX"),
            )
            .filter(Measurement.date >= start)
            .filter(Measurement.date <= end)
            .all()
        )
    else:
        # If only a start date is provided, calculate statistics from the start date and forward
        results = (
            session.query(
                func.min(Measurement.tobs).label("TMIN"),
                func.avg(Measurement.tobs).label("TAVG"),
                func.max(Measurement.tobs).label("TMAX"),
            )
            .filter(Measurement.date >= start)
            .all()
        )

    session.close()

    # Convert the query results into a dictionary
    temp_stats_dict = {
        "TMIN": results[0][0],
        "TAVG": results[0][1],
        "TMAX": results[0][2],
    }

    # Return JSON representation of the temperature statistics
    return jsonify(temp_stats_dict)


# Run the app
if __name__ == "__main__":
    app.run(debug=True)
