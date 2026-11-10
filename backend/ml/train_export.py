# pyright: reportMissingImports=false
"""Reproduce the notebook's data cleaning, model selection and held-out evaluation."""
import json
from pathlib import Path
import joblib
import pandas as pd
from datasets import load_dataset
from sklearn.model_selection import (
    train_test_split,
    StratifiedKFold,
    cross_validate,
    GridSearchCV,
)
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.dummy import DummyClassifier
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.metrics import accuracy_score,precision_score,recall_score,f1_score,classification_report,confusion_matrix
LABELS=['Customer Service','Technical Support','IT Support','Product Support']
OUT=Path(__file__).resolve().parent.parent/'artifacts'
def make_pipeline(classifier):
 return Pipeline([('tfidf',TfidfVectorizer(lowercase=True,stop_words='english',max_features=10000,ngram_range=(1,2),min_df=2)),('classifier',classifier)])

def tune_svm(X_train, y_train, cv):
 """
 Tune Linear SVM using training data only.
 Optimize macro-F1 to give all support queues equal importance.
 """
 pipeline = make_pipeline(
  LinearSVC(random_state=42)
 )

 param_grid = {
  "classifier__C": [0.1, 1.0, 5.0, 10.0],
  "classifier__class_weight": [None, "balanced"],
  "tfidf__ngram_range": [(1, 1), (1, 2)],
  "tfidf__min_df": [2, 3],
 }

 search = GridSearchCV(
  estimator=pipeline,
  param_grid=param_grid,
  scoring="f1_macro",
  cv=cv,
  n_jobs=-1,
  refit=True,
 )

 print("Tuning Linear SVM...", flush=True)
 search.fit(X_train, y_train)

 print("Best parameters:", search.best_params_)
 print("Best CV macro-F1:", search.best_score_)

 return search

def main():
 print('Loading public dataset (first run requires internet)...',flush=True)

 raw = load_dataset(
  'Tobi-Bueck/customer-support-tickets'
 )['train'].to_pandas()

 # Stage 1: Keep English-language tickets
 english = raw[raw['language'] == 'en'].copy()

 # Stage 2: Combine subject and body
 english['ticket_text'] = (
         english['subject'].fillna('').astype(str).str.strip()
         + ' '
         + english['body'].fillna('').astype(str).str.strip()
 ).str.strip()

 # Stage 3: Keep the four supported queues
 queue_filtered = english[english['queue'].isin(LABELS)].copy()

 # Stage 4: Remove empty ticket texts
 selected = queue_filtered[
  queue_filtered['ticket_text'].str.len() > 0
  ].copy()

 # Stage 5: Identify texts with conflicting queue labels
 counts = selected.groupby('ticket_text')['queue'].nunique()
 conflicts = set(counts[counts > 1].index)

 without_conflicts = selected[
  ~selected['ticket_text'].isin(conflicts)
 ].copy()

 # Stage 6: Remove duplicate ticket texts
 df = without_conflicts.drop_duplicates(
  subset=['ticket_text']
 ).reset_index(drop=True)

 # Capture the cleaning audit
 dataset_audit = {
  'raw_rows': int(len(raw)),
  'english_rows': int(len(english)),
  'queue_filtered_rows': int(len(queue_filtered)),
  'empty_text_removed': int(
   len(queue_filtered) - len(selected)
  ),
  'conflicting_rows_removed': int(
   len(selected) - len(without_conflicts)
  ),
  'duplicate_rows_removed': int(
   len(without_conflicts) - len(df)
  ),
  'cleaned_rows': int(len(df)),
  'class_distribution': {
   label: int((df['queue'] == label).sum())
   for label in LABELS
  }
 }

 # Preserve the original notebook's stratified split
 X_train, X_test, y_train, y_test = train_test_split(
  df['ticket_text'],
  df['queue'],
  test_size=0.20,
  random_state=2026,
  stratify=df['queue']
 )

 dataset_audit['train_rows'] = int(len(X_train))
 dataset_audit['test_rows'] = int(len(X_test))
 dataset_audit['train_distribution'] = {
  label: int((y_train == label).sum())
  for label in LABELS
 }
 dataset_audit['test_distribution'] = {
  label: int((y_test == label).sum())
  for label in LABELS
 }

 print('Dataset audit:')
 print(json.dumps(dataset_audit, indent=2))

 models={'Dummy Baseline':make_pipeline(DummyClassifier(strategy='most_frequent')),'Naive Bayes':make_pipeline(MultinomialNB()),'Logistic Regression':make_pipeline(LogisticRegression(max_iter=1000,random_state=42)),'Linear SVM':make_pipeline(LinearSVC(random_state=42))}
 cv=StratifiedKFold(n_splits=5,shuffle=True,random_state=42)

 tuned_search = tune_svm(X_train, y_train, cv)

 rows=[]
 for name,model in models.items():
  print('Cross-validating:',name,flush=True)
  scores=cross_validate(model,X_train,y_train,cv=cv,scoring={'accuracy':'accuracy','macro_f1':'f1_macro','weighted_f1':'f1_weighted'},n_jobs=-1)
  row={'model':name}
  for metric in ('accuracy','macro_f1','weighted_f1'):
   row[metric]=float(scores['test_'+metric].mean());row[metric+'_std']=float(scores['test_'+metric].std())
  rows.append(row)
 rows.sort(key=lambda row:row['macro_f1'],reverse=True)
 winner=rows[0]['model'];model=models[winner]
 print('Training selected model:',winner,flush=True)
 model.fit(X_train,y_train);pred=model.predict(X_test)
 # Evaluate the tuned SVM on the same held-out test set.
 tuned_model = tuned_search.best_estimator_
 tuned_pred = tuned_model.predict(X_test)
 tuned_errors = [
  {
   'ticket_text': str(text)[:1200],
   'true_queue': str(actual),
   'predicted_queue': str(guess)
  }
  for text, actual, guess in zip(X_test, y_test, tuned_pred)
  if actual != guess
 ]

 tuned_test_metrics = {
  'accuracy': float(accuracy_score(y_test, tuned_pred)),
  'macro_precision': float(precision_score(
   y_test, tuned_pred, average='macro', zero_division=0
  )),
  'macro_recall': float(recall_score(
   y_test, tuned_pred, average='macro', zero_division=0
  )),
  'macro_f1': float(f1_score(
   y_test, tuned_pred, average='macro', zero_division=0
  )),
  'weighted_f1': float(f1_score(
   y_test, tuned_pred, average='weighted', zero_division=0
  )),
 }

 tuned_per_class = classification_report(
  y_test,
  tuned_pred,
  labels=LABELS,
  output_dict=True,
  zero_division=0
 )

 tuned_confusion_matrix = confusion_matrix(
  y_test,
  tuned_pred,
  labels=LABELS
 ).tolist()

 # Identify which predictions improved or regressed.
 comparison = {
  'both_correct': 0,
  'both_wrong': 0,
  'fixed_by_tuning': 0,
  'broken_by_tuning': 0,
 }

 for actual, original, tuned in zip(y_test, pred, tuned_pred):
  original_correct = original == actual
  tuned_correct = tuned == actual

  if original_correct and tuned_correct:
   comparison['both_correct'] += 1
  elif not original_correct and not tuned_correct:
   comparison['both_wrong'] += 1
  elif not original_correct and tuned_correct:
   comparison['fixed_by_tuning'] += 1
  else:
   comparison['broken_by_tuning'] += 1

 print('Tuned SVM test metrics:', tuned_test_metrics)
 print('Prediction comparison:', comparison)
 errors=[{'ticket_text':str(text)[:1200],'true_queue':str(actual),'predicted_queue':str(guess)} for text,actual,guess in zip(X_test,y_test,pred) if actual!=guess]

 data={
  'selected_model':winner,
  'dataset':'Tobi-Bueck/customer-support-tickets',
  'dataset_audit': dataset_audit,
  'dataset_rows':int(len(df)),
  'train_rows':int(len(X_train)),
  'test_rows':int(len(X_test)),
  'labels':LABELS,'cv_results':rows,
  'test_metrics':{'accuracy':float(accuracy_score(y_test,pred)),
                  'macro_precision':float(precision_score(y_test,pred,average='macro',zero_division=0)),
                  'macro_recall':float(recall_score(y_test,pred,average='macro',zero_division=0)),
                  'macro_f1':float(f1_score(y_test,pred,average='macro',zero_division=0)),
                  'weighted_f1':float(f1_score(y_test,pred,average='weighted',zero_division=0))
                  },
  'per_class':classification_report(y_test,pred,labels=LABELS,output_dict=True,zero_division=0),'confusion_matrix':confusion_matrix(y_test,pred,labels=LABELS).tolist(),'errors':errors}
 OUT.mkdir(parents=True, exist_ok=True)

 # Preserve the existing production model
 joblib.dump(model, OUT / 'model.joblib')

 # Export the optimized SVM separately
 joblib.dump(
  tuned_search.best_estimator_,
  OUT / 'model_tuned_svm.joblib'
 )

 # Record the tuned configuration and CV results
 data['tuned_svm'] = {
  'model': 'Tuned Linear SVM',

  'best_params': {
   key: list(value) if isinstance(value, tuple) else value
   for key, value in tuned_search.best_params_.items()
  },

  'best_cv_macro_f1': float(tuned_search.best_score_),

  'test_metrics': tuned_test_metrics,

  'per_class': tuned_per_class,

  'confusion_matrix': tuned_confusion_matrix,

  'errors': tuned_errors,

  'prediction_comparison': comparison,

  'note': (
   'Hyperparameters selected using training-set '
   'cross-validation. Test metrics calculated on '
   'the original held-out test set.'
  )
 }

 (OUT / 'metrics.json').write_text(
  json.dumps(data, indent=2)
 )
 joblib.dump(model,OUT/'model.joblib')
 (OUT/'metrics.json').write_text(json.dumps(data,indent=2))
 print('Saved artifacts. Test metrics:',data['test_metrics'])
if __name__=='__main__':main()
