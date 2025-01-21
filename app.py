from flask import Flask, render_template, request, jsonify
import pandas as pd
import os

app = Flask(__name__)

# Load dataset from CSV with error handling
try:
    # Ensure the correct path for deployment (Render's environment sets the working directory to your app folder)
    csv_path = os.path.join(os.path.dirname(__file__), 'sample_updated.csv')
    df = pd.read_csv(csv_path)
except FileNotFoundError:
    print("Error: CSV file not found. Please check the file path.")
    exit()

df = df.sort_values('gameNumber', ascending=False).reset_index(drop=True)
df['type'] = df['type'].str.lower()

# Function to find pattern probability
def find_pattern_probability(pattern):
    sizes = df['type'].tolist()
    pattern_occurrences = 0
    next_small_count = 0
    next_big_count = 0

    # Convert the pattern to lowercase 'small' or 'big'
    pattern = ['small' if p == 's' else 'big' for p in pattern]

    for i in range(len(sizes) - len(pattern)):
        if all(sizes[i + j] == pattern[j] for j in range(len(pattern))):
            pattern_occurrences += 1
            next_index = i + len(pattern)
            if next_index < len(sizes):
                next_value = sizes[next_index]
                if next_value == 'small':
                    next_small_count += 1
                elif next_value == 'big':
                    next_big_count += 1

    if pattern_occurrences > 0:
        small_probability = next_small_count / pattern_occurrences
        big_probability = next_big_count / pattern_occurrences
    else:
        small_probability = big_probability = 0

    return {
        'small_probability': small_probability,
        'big_probability': big_probability,
        'pattern_occurrences': pattern_occurrences
    }

# Analyze patterns for input
def analyze_patterns(input_pattern):
    results = {}
    for length in range(len(input_pattern), 1, -1):
        pattern = input_pattern[-length:]  # Consider sub-patterns
        result = find_pattern_probability(pattern)
        results[tuple(pattern)] = result
    return results

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    input_pattern = request.form['pattern'].lower().strip().split(',')
    analysis_results = analyze_patterns(input_pattern)
    
    table = []
    for pattern, result in analysis_results.items():
        sorted_pattern = pattern
        if result['pattern_occurrences'] > 0:
            small_prob = result['small_probability'] * 100
            big_prob = result['big_probability'] * 100
            diff = abs(small_prob - big_prob)
            
            # Apply color formatting based on probability difference
            if diff <= 2:
                small_prob_str = f"{small_prob:.2f} %"
                big_prob_str = f"{big_prob:.2f} %"
            elif small_prob > big_prob:
                small_prob_str = f"{small_prob:.2f} %"
                big_prob_str = f"{big_prob:.2f} %"
            else:
                small_prob_str = f"{small_prob:.2f} %"
                big_prob_str = f"{big_prob:.2f} %"
            
            row = [sorted_pattern, small_prob_str, big_prob_str, result['pattern_occurrences']]
        else:
            row = [sorted_pattern, "N/A", "N/A", "Pattern not found"]
        
        table.append(row)

    return jsonify(table)

if __name__ == '__main__':
    # Use 0.0.0.0 to ensure it works on Render's environment
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
