import sqlite3
import sys
from datetime import datetime
from enum import Enum

from flask import Flask, jsonify, render_template, request, Response
from pprint import pprint
from flask_cors import CORS

APP = Flask(__name__)
CORS(APP)


# TODO grouping and cumulative doesn't work properly
class CoffeeGrouping:
    """
    Constructs SQL for data grouping and cumulative sum

    Returns tje SQL query as a string
    """

    @staticmethod
    def get_query(grouping: str, cumulative: bool) -> str:
        # Invalid grouping check
        if grouping not in set(item.value for item in CoffeeGrouping.Grouping):
            raise KeyError("Invalid grouping")

        # Converts string into enum
        grouping_enum = CoffeeGrouping.Grouping(grouping)

        # Adds a cumulative column if required
        return (
            (CoffeeGrouping._CUMULATIVE_SQL if cumulative else "")
            + CoffeeGrouping._QUERIES[grouping_enum]
            + (")" if cumulative else "")
        )

    class Grouping(Enum):
        """
        Valid ways of grouping the data
        """

        RAW = "raw"
        SECOND = "second"
        MINUTE = "minute"
        HOUR = "hour"
        DAY = "day"
        WEEK = "week"
        MONTH = "month"
        YEAR = "year"
        NAME = "name"

    """
    Component that does the cumulative sum

    High time complexity, maybe better to calculate the cumulative during insert?
    """
    _CUMULATIVE_SQL = "select *, sum(coffees) over (order by ts rows between unbounded preceding and current row) as cumulativeCoffees from ("

    """
    Queries for grouping
    """
    _QUERIES = {
        Grouping.RAW: "select timestamp as ts, coffees, name from coffees",
        Grouping.SECOND: "select strftime('%Y-%m-%dT%H:%M:%S', datetime(timestamp, 'unixepoch')) as ts, sum(coffees) as coffees from coffees group by ts",
        Grouping.MINUTE: "select strftime('%Y-%m-%dT%H:%M:00', datetime(timestamp, 'unixepoch')) as ts, sum(coffees) as coffees from coffees group by ts",
        Grouping.HOUR: "select strftime('%Y-%m-%dT%H:00:00', datetime(timestamp, 'unixepoch')) as ts, sum(coffees) as coffees from coffees group by ts",
        Grouping.DAY: "select strftime('%Y-%m-%d', datetime(timestamp, 'unixepoch')) as ts, sum(coffees) as coffees from coffees group by ts",
        Grouping.WEEK: "select strftime('%Y-W%W', datetime(timestamp, 'unixepoch')) as ts, sum(coffees) as coffees from coffees group by ts",
        Grouping.MONTH: "select strftime('%Y-%m-01', datetime(timestamp, 'unixepoch')) as ts, sum(coffees) as coffees from coffees group by ts",
        Grouping.YEAR: "select strftime('%Y-01-01', datetime(timestamp, 'unixepoch')) as ts, sum(coffees) as coffees from coffees group by ts",
        Grouping.NAME: "select name, sum(coffees) from coffees group by name",
    }


@APP.route("/test")
def test():
    """
    Test endpoints
    """

    print("hello")
    return jsonify({"hello": "world", "how are you": 12345})


@APP.route("/")
def hello():
    """
    Another test endpoint
    """

    return "Hello! This server is working"


@APP.route("/add_coffee", methods=["POST"])
def add_coffee():
    """
    Adds an entry to the database

    - Checks for negative number case
    - Checks for overflow case
    """

    coffees: int = request.form.get("coffees", type=int)
    # Negative coffee case
    if coffees <= 0:
        return Response("Amount of coffees must be positive", 400)

    try:
        with sqlite3.connect(DATABASE_NAME) as connection:
            pprint(request.form)
            unix_now = round(datetime.utcnow().timestamp())
            cursor = connection.cursor()
            cursor.execute(
                "insert into coffees (timestamp, name, coffees) values (?,?,?)",
                (unix_now, request.form.get("name", type=str), coffees),
            )

            connection.commit()
            print("Database entry added")

    except OverflowError:
        return Response("Number of coffees too large", 400)

    except RuntimeError:
        return Response("Internal error", 500)

    return Response("OK", 200)


@APP.route("/coffees", methods=["GET"])
def get_coffees():
    """
    Gets coffee data

    URL params
    - `grouping`:  see `CoffeeGrouping.Grouping` for valid strings
    - `cumulative`: `true` or `false` for whether a cumulative sum column is needed
    """
    try:
        # Gets the SQL query according request's args
        query = CoffeeGrouping.get_query(
            # Defaults to raw
            request.args.get("grouping", "raw", type=str),
            # Defaults to False (no cumulative column)
            str.lower(request.args.get("cumulative", "false", type=str)) == "true",
        )

    except KeyError:
        return Response("Invalid parameters", 400)

    with sqlite3.connect(DATABASE_NAME) as connection:
        pprint(f"Executing {query}")
        cursor = connection.cursor()
        cursor.execute(query)

        return jsonify(cursor.fetchall())


@APP.route("/index.html", methods=["GET"])
def form():
    """
    Deprecated form
    """

    return render_template("form.html")


if __name__ == "__main__":
    global DATABASE_NAME
    DATABASE_NAME = sys.argv[1]
    APP.debug = True
    APP.run(host="0.0.0.0")
