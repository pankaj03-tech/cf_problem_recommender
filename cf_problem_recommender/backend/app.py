from flask import Flask, request, jsonify
from flask_cors import CORS  # 👈 to allow React frontend to access the backend
from model import recommend_problems

app = Flask(__name__)
CORS(app)  # 👈 Enables CORS for all routes

@app.route('/')
def home():
    return "Codeforces Recommender Backend is Running"

@app.route('/recommend', methods=['POST'])
def recommend():
    data = request.get_json()
    handle = data.get('handle')

    if not handle:
        return jsonify({'error': 'Handle is required'}), 400

    try:
        recommendations_df = recommend_problems(handle)
        # recommendations = recommendations_df.to_dict(orient='records')
        return jsonify(recommendations_df)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
