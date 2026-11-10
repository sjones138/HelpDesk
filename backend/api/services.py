import json
from functools import lru_cache
from pathlib import Path
import joblib

ARTIFACTS=Path(__file__).resolve().parent.parent/'artifacts'

@lru_cache(maxsize=1)
def get_model():
 path=ARTIFACTS/'model.joblib'
 if not path.exists(): raise FileNotFoundError('Model missing: run python -m ml.train_export from backend/')
 return joblib.load(path) # only load trusted, locally generated artifacts

@lru_cache(maxsize=1)
def get_metrics():
 path=ARTIFACTS/'metrics.json'
 if not path.exists(): raise FileNotFoundError('Metrics missing: run python -m ml.train_export from backend/')
 return json.loads(path.read_text())

def predict(text):
 model=get_model()
 label=str(model.predict([text])[0]); result={'queue':label,'contributions':[]}
 classifier=model.named_steps['classifier']; vectorizer=model.named_steps['tfidf']
 if hasattr(classifier,'coef_'):
  x=vectorizer.transform([text]); classes=list(classifier.classes_); idx=classes.index(label)
  weights=classifier.coef_[idx]; contributions=x.multiply(weights).tocoo()
  terms=vectorizer.get_feature_names_out()
  ranked=sorted(((str(terms[c]),round(float(v),4)) for c,v in zip(contributions.col,contributions.data) if v>0),key=lambda t:t[1],reverse=True)
  result['contributions']=[{'term':term,'weight':weight} for term,weight in ranked[:8]]
 return result
