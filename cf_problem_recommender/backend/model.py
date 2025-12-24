# import requests
# import csv
# import time
# import pandas as pd
# from collections import defaultdict
# from sklearn.preprocessing import MultiLabelBinarizer
# from sklearn.model_selection import train_test_split
# from sklearn.ensemble import RandomForestClassifier

# def get_all_user_submissions(handle):
#     all_submissions = []
#     start = 1
#     batch_size = 1000

#     # print(f"Fetching submissions for user: {handle}")

#     while True:
#         url = "https://codeforces.com/api/user.status"
#         params = {'handle': handle, 'from': start, 'count': batch_size}
#         response = requests.get(url, params=params)
#         if response.status_code != 200:
#             print(f"Error: {response.status_code}")
#             break
#         data = response.json()
#         if data['status'] != 'OK':
#             print("API error:", data.get('comment'))
#             break

#         submissions = data['result']
#         if not submissions:
#             break

#         all_submissions.extend(submissions)
#         # print(f"Fetched {len(submissions)} submissions (Total: {len(all_submissions)})")

#         if len(submissions) < batch_size:
#             break
#         start += batch_size
#         time.sleep(0.2)

#     problems = []
#     for sub in all_submissions:
#         prob = sub['problem']
#         problem_info = {
#             'Submission ID': sub.get('id'),
#             'Problem Name': prob.get('name'),
#             'Contest ID': prob.get('contestId'),
#             'Index': prob.get('index'),
#             'Rating': prob.get('rating', 'N/A'),
#             'Tags': prob.get('tags', []),
#             'Verdict': sub.get('verdict', 'N/A'),
#             'Language': sub.get('programmingLanguage', 'N/A'),
#             'Time (ms)': sub.get('timeConsumedMillis', 'N/A')
#         }
#         problems.append(problem_info)

#     return problems
#     # return all_submissions
#     # with open(output_file, mode='w', newline='', encoding='utf-8') as f:
#     #     writer = csv.writer(f)
#     #     writer.writerow(['Submission ID', 'Problem Name', 'Contest ID', 'Index',
#     #                      'Rating', 'Tags', 'Verdict', 'Language', 'Time (ms)'])
#     #     for sub in all_submissions:
#     #         prob = sub['problem']
#     #         writer.writerow([
#     #             sub.get('id'),
#     #             prob.get('name'),
#     #             prob.get('contestId'),
#     #             prob.get('index'),
#     #             prob.get('rating', 'N/A'),
#     #             ", ".join(prob.get('tags', [])),
#     #             sub.get('verdict', 'N/A'),
#     #             sub.get('programmingLanguage', 'N/A'),
#     #             sub.get('timeConsumedMillis', 'N/A')
#     #         ])
#     # return output_file

#     # print(f"\n✅ Saved {len(all_submissions)} submissions to '{output_file}'.")

# # --- Start of main code ---
# # handle = "ecnerwala"
# # get_all_user_submissions(handle, output_file="hasher_submissions.csv")
# def get_user_rating(handle):
#     response = requests.get(f"https://codeforces.com/api/user.info?handles={handle}")
#     user_info = response.json()["result"][0]
#     user_rating = user_info.get("rating", 0)
#     return user_rating

# def get_problemset():
#     response = requests.get("https://codeforces.com/api/problemset.problems")
#     data = response.json()
#     if data['status'] != 'OK':
#         raise Exception("Failed to fetch problem")
#     problems = response.json()["result"]["problems"]
#     problems_df = pd.DataFrame(problems).dropna(subset=['rating'])
#     problems_df['tags'] = problems_df['tags'].apply(lambda x: x if isinstance(x, list) else [])
#     return problems_df




# def recommend_problems(handle):
#     submissions = get_all_user_submissions(handle)
#     user_rating = get_user_rating(handle)
#     problems_df = get_problemset()

#     df = pd.DataFrame(submissions)

#     # Ensure proper types
#     df['Tags'] = df['Tags'].apply(lambda x: x if isinstance(x, list) else [])
#     df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce').fillna(0).astype(int)
#     df['Time (ms)'] = pd.to_numeric(df['Time (ms)'], errors='coerce').fillna(0).astype(int)

#     # Count wrong submissions
#     wrong_counts = df[df['Verdict'] == 'WRONG_ANSWER']['Problem Name'].value_counts().to_dict()
#     dedup_df = df.drop_duplicates(subset=['Problem Name']).copy()
#     dedup_df['Wrong_Submission_Count'] = dedup_df['Problem Name'].map(wrong_counts).fillna(0).astype(int)
#     submissions_df = dedup_df.copy()

#     # Encode tags
#     mlb = MultiLabelBinarizer()
#     tags_encoded = mlb.fit_transform(submissions_df['Tags'])
#     tags_encoded_df = pd.DataFrame(tags_encoded, columns=mlb.classes_, index=submissions_df.index)

#     # Prepare target variable
#     submissions_df['solved'] = (submissions_df['Verdict'] == 'OK').astype(int)

#     # Tag accuracy dictionary
#     tag_stats = defaultdict(lambda: {'solved': 0, 'attempted': 0})
#     for _, row in df.iterrows():
#         for tag in row['Tags']:
#             tag_stats[tag]['attempted'] += 1
#             if row['Verdict'] == 'OK':
#                 tag_stats[tag]['solved'] += 1

#     tag_accuracy = {
#         tag: stats['solved'] / stats['attempted'] if stats['attempted'] else 0.0
#         for tag, stats in tag_stats.items()
#     }

#     # Feature engineering
#     X = pd.concat([
#         pd.DataFrame({
#             'user_rating': [user_rating] * len(submissions_df),
#             'problem_rating': submissions_df['Rating']
#         }, index=submissions_df.index),
#         submissions_df[['Wrong_Submission_Count', 'Time (ms)']],
#         tags_encoded_df
#     ], axis=1)
#     X['relative_difficulty'] = X['problem_rating'] - X['user_rating']
#     y = submissions_df['solved']

#     # Train/test split and model
#     X_train, X_test, y_train, y_test = train_test_split(X, y, stratify=y, random_state=42)
#     model = RandomForestClassifier(n_estimators=200, max_depth=12, random_state=42)
#     model.fit(X_train, y_train)

#     # Predict on unattempted problems
#     attempted = set(zip(submissions_df['Contest ID'], submissions_df['Index']))
#     unattempted_problems = problems_df[
#         ~problems_df.apply(lambda row: (row['contestId'], row['index']) in attempted, axis=1)
#     ].dropna(subset=['rating'])

#     tags_for_unattempted = mlb.transform(unattempted_problems['tags'])
#     features_for_prediction = pd.concat([
#         pd.DataFrame({
#             'user_rating': [user_rating] * len(unattempted_problems),
#             'problem_rating': unattempted_problems['rating'].values
#         }, index=unattempted_problems.index),
#         pd.DataFrame(0, index=unattempted_problems.index, columns=['Wrong_Submission_Count', 'Time (ms)']),
#         pd.DataFrame(tags_for_unattempted, columns=mlb.classes_, index=unattempted_problems.index)
#     ], axis=1)
#     features_for_prediction['relative_difficulty'] = features_for_prediction['problem_rating'] - user_rating

#     pred_probs = model.predict_proba(features_for_prediction)[:, 1]
#     unattempted_problems['probability_of_success'] = pred_probs

#     # Adjust probabilities based on tag accuracy and difficulty
#     def adjust_probability(prob, tags, tag_accuracy, problem_rating, user_rating):
#         for tag in tags:
#             acc = tag_accuracy.get(tag, 0.5)
#             if acc < 0.3:
#                 prob *= 0.8
#             elif acc > 0.7:
#                 prob *= 1.1
#         if problem_rating < user_rating - 300:
#             prob *= 0.4
#         return min(prob, 1.0)

#     unattempted_problems['adjusted_prob'] = unattempted_problems.apply(
#         lambda row: adjust_probability(
#             row['probability_of_success'],
#             row['tags'],
#             tag_accuracy,
#             row['rating'],
#             user_rating
#         ), axis=1
#     )

#     # Exploration vs. Exploitation strategy
#     top_n = 10
#     exploit_size = int(top_n * 0.8)
#     explore_size = top_n - exploit_size

#     top_problems = unattempted_problems.sort_values(by='adjusted_prob', ascending=False).head(exploit_size)

#     explore_range = (max(user_rating - 200, 1600), user_rating + 300)
#     medium_difficulty = unattempted_problems[
#         (unattempted_problems['rating'] >= explore_range[0]) &
#         (unattempted_problems['rating'] <= explore_range[1])
#     ]
#     explore_problems = medium_difficulty.sample(n=explore_size, random_state=42) if len(medium_difficulty) >= explore_size else medium_difficulty

#     final_recommendations = pd.concat([top_problems, explore_problems])

#     return final_recommendations[['name', 'contestId', 'index', 'rating', 'adjusted_prob','tags']]

import requests
import time
import pandas as pd
from collections import defaultdict
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

def get_all_user_submissions(handle):
    all_submissions = []
    start = 1
    batch_size = 1000

    while True:
        url = "https://codeforces.com/api/user.status"
        params = {'handle': handle, 'from': start, 'count': batch_size}
        response = requests.get(url, params=params)
        if response.status_code != 200:
            break
        data = response.json()
        if data['status'] != 'OK':
            break

        submissions = data['result']
        if not submissions:
            break

        all_submissions.extend(submissions)
        if len(submissions) < batch_size:
            break
        start += batch_size
        time.sleep(0.2)

    problems = []
    for sub in all_submissions:
        prob = sub['problem']
        problems.append({
            'Submission ID': sub.get('id'),
            'Problem Name': prob.get('name'),
            'Contest ID': prob.get('contestId'),
            'Index': prob.get('index'),
            'Rating': prob.get('rating', 'N/A'),
            'Tags': prob.get('tags', []),
            'Verdict': sub.get('verdict', 'N/A'),
            'Language': sub.get('programmingLanguage', 'N/A'),
            'Time (ms)': sub.get('timeConsumedMillis', 'N/A')
        })

    return problems

def get_user_rating(handle):
    response = requests.get(f"https://codeforces.com/api/user.info?handles={handle}")
    user_info = response.json()["result"][0]
    return user_info.get("rating", 0)

def get_problemset():
    response = requests.get("https://codeforces.com/api/problemset.problems")
    data = response.json()
    problems = data["result"]["problems"]
    problems_df = pd.DataFrame(problems).dropna(subset=['rating'])
    problems_df['tags'] = problems_df['tags'].apply(lambda x: x if isinstance(x, list) else [])
    return problems_df

def recommend_problems(handle):
    submissions = get_all_user_submissions(handle)
    user_rating = get_user_rating(handle)
    problems_df = get_problemset()

    df = pd.DataFrame(submissions)
    df['Tags'] = df['Tags'].apply(lambda x: x if isinstance(x, list) else [])
    df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce').fillna(0).astype(int)
    df['Time (ms)'] = pd.to_numeric(df['Time (ms)'], errors='coerce').fillna(0).astype(int)

    wrong_counts = df[df['Verdict'] == 'WRONG_ANSWER']['Problem Name'].value_counts().to_dict()
    dedup_df = df.drop_duplicates(subset=['Problem Name']).copy()
    dedup_df['Wrong_Submission_Count'] = dedup_df['Problem Name'].map(wrong_counts).fillna(0).astype(int)
    submissions_df = dedup_df.copy()

    mlb = MultiLabelBinarizer()
    tags_encoded = mlb.fit_transform(submissions_df['Tags'])
    tags_encoded_df = pd.DataFrame(tags_encoded, columns=mlb.classes_, index=submissions_df.index)

    submissions_df['solved'] = (submissions_df['Verdict'] == 'OK').astype(int)

    tag_stats = defaultdict(lambda: {'solved': 0, 'attempted': 0})
    for _, row in df.iterrows():
        for tag in row['Tags']:
            tag_stats[tag]['attempted'] += 1
            if row['Verdict'] == 'OK':
                tag_stats[tag]['solved'] += 1

    tag_accuracy = {
        tag: stats['solved'] / stats['attempted'] if stats['attempted'] else 0.0
        for tag, stats in tag_stats.items()
    }

    X = pd.concat([
        pd.DataFrame({'user_rating': [user_rating] * len(submissions_df), 'problem_rating': submissions_df['Rating']}),
        submissions_df[['Wrong_Submission_Count', 'Time (ms)']],
        tags_encoded_df
    ], axis=1)
    X['relative_difficulty'] = X['problem_rating'] - X['user_rating']
    y = submissions_df['solved']

    X_train, X_test, y_train, y_test = train_test_split(X, y, stratify=y, random_state=42)
    model = RandomForestClassifier(n_estimators=200, max_depth=12, random_state=42)
    model.fit(X_train, y_train)

    attempted = set(zip(submissions_df['Contest ID'], submissions_df['Index']))
    unattempted_problems = problems_df[
        ~problems_df.apply(lambda row: (row['contestId'], row['index']) in attempted, axis=1)
    ].dropna(subset=['rating'])

    tags_for_unattempted = mlb.transform(unattempted_problems['tags'])
    features_for_prediction = pd.concat([
        pd.DataFrame({'user_rating': [user_rating] * len(unattempted_problems),
                      'problem_rating': unattempted_problems['rating'].values}, index=unattempted_problems.index),
        pd.DataFrame(0, index=unattempted_problems.index, columns=['Wrong_Submission_Count', 'Time (ms)']),
        pd.DataFrame(tags_for_unattempted, columns=mlb.classes_, index=unattempted_problems.index)
    ], axis=1)
    features_for_prediction['relative_difficulty'] = features_for_prediction['problem_rating'] - user_rating

    pred_probs = model.predict_proba(features_for_prediction)[:, 1]
    unattempted_problems['probability_of_success'] = pred_probs

    def adjust_probability(prob, tags, tag_accuracy, problem_rating, user_rating):
        for tag in tags:
            acc = tag_accuracy.get(tag, 0.5)
            if acc < 0.3:
                prob *= 0.8
            elif acc > 0.7:
                prob *= 1.1
        if problem_rating < user_rating - 300:
            prob *= 0.4
        return min(prob, 1.0)

    unattempted_problems['adjusted_prob'] = unattempted_problems.apply(
        lambda row: adjust_probability(row['probability_of_success'], row['tags'], tag_accuracy, row['rating'], user_rating),
        axis=1
    )

    top_n = 10
    exploit_size = int(top_n * 0.8)
    explore_size = top_n - exploit_size

    top_problems = unattempted_problems.sort_values(by='adjusted_prob', ascending=False).head(exploit_size)

    explore_range = (max(user_rating - 200, 1600), user_rating + 300)
    medium_difficulty = unattempted_problems[
        (unattempted_problems['rating'] >= explore_range[0]) & (unattempted_problems['rating'] <= explore_range[1])
    ]
    explore_problems = medium_difficulty.sample(n=explore_size, random_state=42) if len(medium_difficulty) >= explore_size else medium_difficulty

    final_recommendations = pd.concat([top_problems, explore_problems])

    # --- ✅ Unified recommendations dictionary ---
    recommendations = {}

    # 1️⃣ Add 'all' key for overall recommendations
    recommendations['all'] = []
    for _, row in final_recommendations.iterrows():
        recommendations['all'].append({
            'name': row['name'],
            'contestId': row['contestId'],
            'index': row['index'],
            'rating': row['rating'],
            'adjusted_prob': row['adjusted_prob'],
            'tags': row['tags']
        })

    # 2️⃣ Add per-tag recommendations
    for tag in mlb.classes_:
        problems_with_tag = unattempted_problems[unattempted_problems['tags'].apply(lambda tags: tag in tags)]
        if not problems_with_tag.empty:
            top_problems_with_tag = problems_with_tag.sort_values(by='adjusted_prob', ascending=False).head(10)
            problem_list = []
            for _, row in top_problems_with_tag.iterrows():
                problem_list.append({
                    'name': row['name'],
                    'contestId': row['contestId'],
                    'index': row['index'],
                    'rating': row['rating'],
                    'adjusted_prob': row['adjusted_prob'],
                    'tags': row['tags']
                })
            recommendations[tag] = problem_list

    return recommendations
