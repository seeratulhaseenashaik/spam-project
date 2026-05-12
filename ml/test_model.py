import pickle

try:
    model = pickle.load(open("spam_model.pkl", "rb"))
    print("Model loaded.")
    print("Type:", type(model))
    print("Has predict_proba:", hasattr(model, "predict_proba"))
except Exception as e:
    print("Error:", e)
