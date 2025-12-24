# Codeforces Problem Recommendation System

A Python-based recommendation system that suggests Codeforces problems tailored to a user’s skill level by analyzing past submissions, ratings, and problem difficulty. The goal is to enable focused practice and steady performance improvement.

## Features
- Personalized problem recommendations
- Difficulty and rating-based filtering
- Helps identify and improve weak areas
- Lightweight and easy to run locally

## Tech Stack
- Python  
- Pandas, NumPy  
- Basic Machine Learning / Data Analysis  
- Flask (backend)

## Project Structure


cf_problem_recommender/
├── backend/
│ ├── app.py
│ ├── model.py
│ ├── hasher_submissions_dedup.csv
│ └── requirements.txt
├── requirements.txt
└── README.md

## How to Run
```bash
pip install -r requirements.txt
python backend/app.py
Future Improvements

User login and profile tracking

Advanced ML models for better recommendations

Web-based frontend dashboard

Author

Pankaj Kumar Sharma
