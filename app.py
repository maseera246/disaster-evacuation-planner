
from flask import Flask, render_template, jsonify, request
from routing import find_route_between_coordinates

app = Flask(__name__)


# Homepage
@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")


# A* route calculation API
@app.route("/api/route", methods=["POST"])
def get_route():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "error": "Invalid request. Please send JSON coordinates."
        }), 400

    try:
        start_lat = float(data["start_lat"])
        start_lon = float(data["start_lon"])
        end_lat = float(data["end_lat"])
        end_lon = float(data["end_lon"])

        # Validate geographic coordinate ranges
        if not (
            -90 <= start_lat <= 90
            and -180 <= start_lon <= 180
            and -90 <= end_lat <= 90
            and -180 <= end_lon <= 180
        ):
            raise ValueError("Coordinates are outside valid ranges.")

        # Calculate route using your existing A* algorithm
        result = find_route_between_coordinates(
            start_lat,
            start_lon,
            end_lat,
            end_lon
        )

        return jsonify({
            "success": True,
            "algorithm": "A* Search",
            "distance_m": round(result["distance"], 1),
            "distance_km": round(result["distance"] / 1000, 2),
            "route_coordinates": result["coordinates"],
            "node_count": len(result["route"]),
            "message": "Route calculated successfully."
        }), 200

    except (KeyError, TypeError, ValueError) as error:
        return jsonify({
            "success": False,
            "error": str(error) or "Please provide valid coordinates."
        }), 400

    except Exception:
        app.logger.exception("Route calculation failed")
        return jsonify({
            "success": False,
            "error": "Route calculation failed. Check the VS Code terminal."
        }), 500


# Handle unsupported HTTP methods with a JSON response
@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        "success": False,
        "error": "Method not allowed. Route calculations require POST to /api/route."
    }), 405


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
