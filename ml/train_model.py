import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import pickle

# =========================
# Load Dataset (spam.csv)
# =========================
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

X_train_tfidf = vectorizer.fit_transform(X_train)
model.fit(X_train_tfidf, y_train)

X_test_tfidf = vectorizer.transform(X_test)
pred = model.predict(X_test_tfidf)

print("Accuracy:", accuracy_score(y_test, pred))
df = pd.read_csv("spam.csv", encoding="latin-1")

# Keep only useful columns
df = df[['v1', 'v2']]
df.columns = ['label', 'message']

# Convert labels to numbers
df['label'] = df['label'].map({'ham': 0, 'spam': 1})

# Features and target
X = df['message']
y = df['label']

# =========================
# TF-IDF Vectorization
# =========================
vectorizer = TfidfVectorizer(
    stop_words="english",
    ngram_range=(1,2),   # learn phrases like "free prize"
    min_df=2             # ignore rare noise words
)
X_tfidf = vectorizer.fit_transform(X)

# =========================
# Train Naive Bayes Model
# =========================
model = MultinomialNB()
model.fit(X_tfidf, y)

print("✅ Model trained successfully!")

# =========================
# Save Model + Vectorizer
# =========================
pickle.dump(model, open("spam_model.pkl", "wb"))
pickle.dump(vectorizer, open("vectorizer.pkl", "wb"))

print("✅ Model saved as spam_model.pkl")