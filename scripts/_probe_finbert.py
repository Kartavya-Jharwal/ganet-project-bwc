"""Quick probe of FinBERT on known test sentences."""
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
model.eval()

id2label = {k: v.lower() for k, v in model.config.id2label.items()}
print("id2label:", id2label)

tests = [
    # canonical positives from FinBERT paper/readme
    "Operating profit rose to EUR 13.1 mn from EUR 8.7 mn in the year-earlier period",
    "The quarterly results beat analyst expectations, revenue up 30 percent year over year",
    "Earnings per share surpassed consensus estimates significantly",
    # neutral
    "The company did not comment on future plans",
    # negative
    "Profit attributable to parents decreased to EUR 30.5 mn from EUR 42.9 mn",
    "Revenue fell sharply as demand collapsed and margins compressed",
    "Company issues profit warning amid declining sales and layoffs",
]

inputs = tokenizer(tests, padding=True, truncation=True, max_length=128, return_tensors="pt")
with torch.no_grad():
    probs = torch.softmax(model(**inputs).logits, dim=-1)

for text, p in zip(tests, probs, strict=False):
    p_list = p.tolist()
    argmax = p.argmax().item()
    label = id2label[argmax]
    pos_idx = next(k for k, v in id2label.items() if v == "positive")
    neg_idx = next(k for k, v in id2label.items() if v == "negative")
    score = p_list[pos_idx] - p_list[neg_idx]
    print(f"{label:8s} score={score:+.4f}  probs={[round(x,3) for x in p_list]}  '{text[:60]}'")
