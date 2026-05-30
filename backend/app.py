# coding: utf-8

from flask import Flask, request, jsonify

# Create Flask application instance
app = Flask(__name__)

@app.route('/')
def home():
    """Home route returning a welcome message."""
    return "Welcome to My Flask App!"

@app.route('/greet', methods=['GET'])
def greet():
    """
    Greet the user by name.
    Example: /greet?name=John
    """
    name = request.args.get('name', '').strip()

    # Input validation
    if not name:
        return jsonify({"error": "Missing 'name' parameter"}), 400
    if not name.isalpha():
        return jsonify({"error": "Name must contain only letters"}), 400

    return jsonify({"message": f"Hello, {name}!"})

@app.route('/add', methods=['POST'])
def add_numbers():
    """
    Add two numbers sent in JSON body.
    Example JSON: {"a": 5, "b": 3}
    """
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid JSON format"}), 400

    # Validate presence of keys
    if not all(k in data for k in ("a", "b")):
        return jsonify({"error": "JSON must contain 'a' and 'b'"}), 400

    # Validate numeric types
    try:
        a = float(data["a"])
        b = float(data["b"])
    except (ValueError, TypeError):
        return jsonify({"error": "'a' and 'b' must be numbers"}), 400

    return jsonify({"result": a + b})

# Run the app
if __name__ == '__main__':
    # Debug mode for development; remove debug=True in production
    app.run(debug=True)


