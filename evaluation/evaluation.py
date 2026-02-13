import pandas as pd
from sklearn.metrics import accuracy_score
from app.agent import run_agent

df = pd.read_csv("data/kaggle_tickets.csv").head(50)

true_labels = []
pred_labels = []

for _, row in df.iterrows():
    result = run_agent(row["ticket_text"])
    pred_labels.append(result["category"])
    true_labels.append(row["category"])

print("Classification Accuracy:", accuracy_score(true_labels, pred_labels))
