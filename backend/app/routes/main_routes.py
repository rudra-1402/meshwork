from flask import Blueprint, jsonify

main_routes = Blueprint("main_routes", __name__)

@main_routes.route("/", strict_slashes=False)
def landing():
    return jsonify({
        "success": True,
        "message": "MeshWork API root",
        "docs": "/api/health"
    }), 200
