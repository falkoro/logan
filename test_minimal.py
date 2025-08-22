from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello from LoganGemma! Minimal Flask app is working!"

@app.route('/test')
def test():
    return "Test endpoint working!"

if __name__ == '__main__':
    print("Starting minimal Flask app...")
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        print(f"Error starting on port 5000: {e}")
        print("Trying port 8080...")
        try:
            app.run(host='0.0.0.0', port=8080, debug=True)
        except Exception as e2:
            print(f"Error starting on port 8080: {e2}")
            print("Trying port 3000...")
            app.run(host='0.0.0.0', port=3000, debug=True)
