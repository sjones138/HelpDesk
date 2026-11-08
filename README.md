# HelpDesk — AI-Assisted Ticket Classification

A full-stack research demonstration that recommends a support queue for incoming help-desk tickets. Built with **Django REST Framework**, **Vue 3 + TypeScript**, and **scikit-learn** for an ICS 652 artificial intelligence and machine-learning project.

**The classifier recommends a queue; a human remains responsible for the routing decision.** The interface includes a live classifier, dataset explorer, model comparison, error analysis, and responsible-AI documentation.

> **Project scope:** Local development and academic demonstration, not a production-ready ticketing service.

## Technology stack

| Layer | Technology |
| --- | --- |
| Backend | Python 3.11/3.12, Django 5.2, Django REST Framework |
| Machine learning | scikit-learn, pandas, NumPy, Hugging Face `datasets`, joblib |
| Frontend | Vue 3, TypeScript, Vite, Axios, Apache ECharts |
| Local database | SQLite (feedback records) |

## Requirements

- Python **3.11 or 3.12**
- Node.js **20.19+ or 22.12+**, npm
- Internet access for the initial dataset download
- Sufficient memory and time to run cross-validation and export the model

## Quick start

Run these commands from the repository root. The first model-training run downloads the public dataset and may take several minutes.

### 1. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m ml.train_export
python manage.py migrate
python manage.py test
python manage.py runserver
```

On Windows PowerShell, activate the environment using `.venv\Scripts\Activate.ps1` instead.

Training creates the local artifacts `backend/artifacts/model.joblib` and `backend/artifacts/metrics.json`. These generated files are intentionally not committed. **Only load joblib artifacts you created or obtained from a trusted source**; loading an untrusted joblib file can execute arbitrary code.

Django serves the API at `http://127.0.0.1:8000/` by default.

### 2. Frontend

In a second terminal, from the repository root:

```bash
cd frontend
npm ci
npm run dev
```

Open **http://127.0.0.1:5173**. The Vite development server proxies `/api` requests to Django at `http://127.0.0.1:8000` (as configured in `frontend/vite.config.ts`).

### 3. Production build check

```bash
cd frontend
npm run build
```

The `build` script runs TypeScript validation and produces a Vite build in `frontend/dist/`. This does **not** by itself make the Django application production-ready.

## Application features

- **Live classifier:** Enter ticket text to receive a recommended support queue and model-derived term contributions.
- **Dataset Explorer:** Review preprocessing counts, queue distribution, and the stratified train/test split.
- **Model Laboratory:** Compare four models using cross-validation metrics.
- **Error Explorer:** Inspect the held-out confusion matrix and examples of incorrect predictions.
- **Responsible AI:** Review intended use, limitations, privacy concerns, and human oversight.
- **Feedback API:** Save a human-selected correction to the local database; feedback is **not automatically used to retrain** the classifier.

## Dataset and training methodology

**Dataset:** [`Tobi-Bueck/customer-support-tickets`](https://huggingface.co/datasets/Tobi-Bueck/customer-support-tickets).

The export script `backend/ml/train_export.py`:

1. Loads the dataset and retains English-language records.
2. Concatenates subject and body into ticket text.
3. Retains four queues: **Customer Service**, **Technical Support**, **IT Support**, and **Product Support**.
4. Removes empty texts, texts with conflicting queue labels, and duplicate texts.
5. Creates a **stratified 80/20 train/test split**, with `random_state=2026`.
6. Compares four candidate classifiers with **five-fold stratified cross-validation** on the training set.
7. Selects the model by mean **macro-F1**, fits it on the full training split, and evaluates it on the untouched test split.
8. Exports the selected pipeline and metrics for the API and dashboard.

The text pipeline uses TF-IDF with lowercase conversion, English stop-word removal, up to 10,000 features, unigrams and bigrams, and `min_df=2`.

### Cross-validation results

The following values are from the previously exported experiment; rerunning training may yield different results if the upstream dataset or installed dependencies change.

| Model | Mean CV accuracy | Mean CV macro-F1 | Mean CV weighted-F1 |
| --- | ---: | ---: | ---: |
| Linear SVM | 0.5760 | **0.5509** | 0.5712 |
| Logistic Regression | 0.5309 | 0.4727 | 0.5086 |
| Naive Bayes | 0.4594 | 0.3503 | 0.4063 |
| Dummy baseline | 0.3876 | 0.1397 | 0.2166 |

**Selected model:** Linear SVM.

### Held-out test results

| Metric | Value |
| --- | ---: |
| Cleaned records | 17,691 |
| Training records | 14,152 |
| Test records | 3,539 |
| Test accuracy | 0.5869 |
| Test macro-F1 | 0.5632 |
| Test weighted-F1 | 0.5818 |

These test results are **not** cross-validation scores and were not used to select the model. The four queues have unequal performance, so overall accuracy should not be interpreted as uniformly reliable routing.

## API reference

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/api/health/` | Health status |
| POST | `/api/classify/` | Predict a queue for ticket text |
| GET | `/api/metrics/` | Retrieve exported evaluation metrics and dataset audit |
| GET | `/api/models/` | Retrieve selected model and CV comparison |
| POST | `/api/feedback/` | Save a human correction |

### Classify a ticket

```bash
curl -X POST http://127.0.0.1:8000/api/classify/ \
  -H 'Content-Type: application/json' \
  -d '{"ticket_text":"VPN login fails"}'
```

Successful responses contain a `queue` and a `contributions` array. The API requires `ticket_text` to be a string containing **3–5000 characters** after trimming. Invalid input returns HTTP **400**; a missing model artifact returns HTTP **503**.

### Submit feedback

```bash
curl -X POST http://127.0.0.1:8000/api/feedback/ \
  -H 'Content-Type: application/json' \
  -d '{"ticket_text":"VPN login fails","predicted_queue":"Technical Support","corrected_queue":"IT Support"}'
```

Both queue fields must match one of the four supported labels. Valid feedback returns HTTP **201** and `{ "saved": true }`.

## Tests and validation

From `backend`, with the virtual environment activated:

```bash
python manage.py check
python manage.py test api -v 2
python manage.py makemigrations --check --dry-run
```

The Django API tests use mocks for model inference and metrics retrieval. They validate HTTP behavior and feedback persistence but **do not replace the held-out machine-learning evaluation**.

From `frontend`:

```bash
npx vue-tsc --noEmit
npm run build
```

Vite may warn about a large JavaScript chunk; this is a performance warning rather than a failed build.

## Research integrity and responsible use

- **Decision support, not autonomous routing:** A person should confirm the recommended queue, particularly for ambiguous tickets.
- **No probability claim:** Linear SVM decision scores and signed TF-IDF term contributions are not calibrated confidence percentages or causal explanations.
- **Uneven class performance:** Examine per-class precision, recall, and confusion-matrix errors rather than relying only on accuracy.
- **Sensitive data:** Ticket text may include personal or confidential information. Do not enter real sensitive tickets into an unsecured demonstration or expose raw examples publicly without review.
- **Feedback handling:** The local feedback endpoint stores submitted ticket text and queue labels; it does not automatically update the model.
- **Dataset dependence:** Reported metrics reflect the selected dataset and preprocessing; performance on a different organization’s tickets is unknown.

## Deployment considerations

This repository is configured for **local development**. Before deploying publicly, at minimum:

- Set `DJANGO_DEBUG=0`, supply a strong `DJANGO_SECRET_KEY`, and configure `DJANGO_ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS`.
- Use HTTPS, a production WSGI/ASGI server, appropriate static hosting, and a production-grade database if needed.
- Require appropriate authentication and permissions for sensitive endpoints and data.
- Review throttling, logging, retention, and data minimization for ticket text and feedback.
- Review access to the metrics error explorer, which includes ticket excerpts.
- Never expose Django's `runserver` as a public production server.

## Repository structure

```text
HelpDesk/
├── README.md
├── backend/
│   ├── api/                 # REST endpoints, services, feedback model, tests
│   ├── artifacts/           # Locally generated model and metrics (not tracked)
│   ├── config/              # Django settings and URL configuration
│   ├── ml/train_export.py   # Dataset preparation, CV, evaluation, export
│   ├── manage.py
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── App.vue
    │   ├── DatasetExplorer.vue
    │   ├── EvaluationExplorer.vue
    │   ├── ResponsibleAI.vue
    │   └── api.ts
    ├── package.json
    └── package-lock.json
```

## Academic project note

Developed as an ICS 652 machine-learning project. The application demonstrates a reproducible classical text-classification workflow, transparent comparison against baselines, analysis of errors, and human-centered use of predictions.
