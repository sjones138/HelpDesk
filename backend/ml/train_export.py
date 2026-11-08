"""Reproduce the notebook's data cleaning, model selection and held-out evaluation."""
import json
from pathlib import Path
import joblib
import pandas as pd
from datasets import load_dataset
from sklearn.model_selection import train_test_split,StratifiedKFold,cross_validate
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
def main():
 print('Loading public dataset (first run requires internet)...',flush=True)
 raw=load_dataset('Tobi-Bueck/customer-support-tickets')['train'].to_pandas()
 english=raw[raw['language']=='en'].copy()
 english['ticket_text']=(english['subject'].fillna('').astype(str).str.strip()+' '+english['body'].fillna('').astype(str).str.strip()).str.strip()
 selected=english[english['queue'].isin(LABELS) & (english['ticket_text'].str.len()>0)].copy()
 counts=selected.groupby('ticket_text')['queue'].nunique()
 conflicts=set(counts[counts>1].index)
 df=selected[~selected['ticket_text'].isin(conflicts)].drop_duplicates(subset=['ticket_text']).reset_index(drop=True)
 X_train,X_test,y_train,y_test=train_test_split(df['ticket_text'],df['queue'],test_size=.20,random_state=2026,stratify=df['queue'])
 models={'Dummy Baseline':make_pipeline(DummyClassifier(strategy='most_frequent')),'Naive Bayes':make_pipeline(MultinomialNB()),'Logistic Regression':make_pipeline(LogisticRegression(max_iter=1000,random_state=42)),'Linear SVM':make_pipeline(LinearSVC(random_state=42))}
 cv=StratifiedKFold(n_splits=5,shuffle=True,random_state=42)
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
 errors=[{'ticket_text':str(text)[:1200],'true_queue':str(actual),'predicted_queue':str(guess)} for text,actual,guess in zip(X_test,y_test,pred) if actual!=guess]
 data={'selected_model':winner,'dataset':'Tobi-Bueck/customer-support-tickets','dataset_rows':int(len(df)),'train_rows':int(len(X_train)),'test_rows':int(len(X_test)),'labels':LABELS,'cv_results':rows,'test_metrics':{'accuracy':float(accuracy_score(y_test,pred)),'macro_precision':float(precision_score(y_test,pred,average='macro',zero_division=0)),'macro_recall':float(recall_score(y_test,pred,average='macro',zero_division=0)),'macro_f1':float(f1_score(y_test,pred,average='macro',zero_division=0)),'weighted_f1':float(f1_score(y_test,pred,average='weighted',zero_division=0))},'per_class':classification_report(y_test,pred,labels=LABELS,output_dict=True,zero_division=0),'confusion_matrix':confusion_matrix(y_test,pred,labels=LABELS).tolist(),'errors':errors}
 OUT.mkdir(parents=True,exist_ok=True)
 joblib.dump(model,OUT/'model.joblib')
 (OUT/'metrics.json').write_text(json.dumps(data,indent=2))
 print('Saved artifacts. Test metrics:',data['test_metrics'])
if __name__=='__main__':main()
