from flask import Flask, render_template, request
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

# Load the dataset
data = pd.read_csv("filtered_recipes_cleaned.csv")

# Clean ingredients column (remove bullet points or special characters if necessary)
data['ingredients'] = data['ingredients'].str.replace('▢', '', regex=False)  # Clean ingredients
data_clean = data.dropna()  # Remove rows with missing ingredients

# Vectorize the ingredients using TF-IDF
vectorizer = TfidfVectorizer(stop_words='english')
X_ingredients = vectorizer.fit_transform(data_clean['clean_ingredients'])

# Function to recommend recipes based on input ingredients
def recommend_recipes(input_ingredients):
    # Transform the input ingredients into the same vectorized form
    input_vector = vectorizer.transform([input_ingredients])
    
    # Compute cosine similarity between the input and all recipes
    similarity_scores = cosine_similarity(input_vector, X_ingredients)
    
    # Get the top 5 most similar recipes based on cosine similarity
    similar_indices = similarity_scores.argsort()[0][-20:][::-1]
    recommendations = data_clean.iloc[similar_indices]
    
    # Check if the highest similarity score is above a certain threshold
    if similarity_scores[0][similar_indices[0]] < 0.1:  # Adjust threshold as needed
        return pd.DataFrame(columns=['title', 'clean_ingredients', 'image'])
    
    return recommendations[['title', 'clean_ingredients', 'image']]

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        ing = request.form['ing']
        
        # Check if input is valid
        if len(ing.strip()) < 3:
            return render_template(
                'index.html',
                recommendations=[],
                message="Please enter a valid ingredient list."
            )
        
        input_ingredients = ing  # User input ingredients
        recommendations = recommend_recipes(input_ingredients)  # Get recommended recipes
        
        if recommendations.empty:
            return render_template(
                'index.html',
                recommendations=[],
                message="No relevant recipes found for your search."
            )
        
        return render_template(
            'index.html',
            recommendations=recommendations.to_dict(orient='records')
        )
    return render_template('index.html', recommendations=[])


@app.route('/recipe/<title>')
def view_recipe(title):
    # Find the specific recipe by name
    recipe = data_clean[data_clean['title'] == title].to_dict(orient='records')
    
    if recipe:
        # Get the first matching recipe (in case of duplicates)
        recipe = recipe[0]
        return render_template('recipe_detail.html', recipe=recipe)
    else:
        # Handle case where recipe is not found
        return "Recipe not found", 404

if __name__ == "__main__":
    app.run(debug=True)