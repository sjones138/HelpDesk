# QueueIQ — AI Ticket Intelligence

Django REST Framework + Vue 3/TypeScript + scikit-learn. Cyberpunk-themed research dashboard based on `Final_All_in_One_Project_Revised.ipynb`.

## Requirements
Python 3.11 or 3.12, Node.js 20.19+ or 22.12+, npm, internet access for first dataset download.

## 1. Backend setup (from repository root)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m ml.train_export
python manage.py migrate
python manage.py test
python manage.py runserver
```

Windows PowerShell activation: `.venv\Scripts\Activate.ps1`.

The training step downloads the Hugging Face dataset, reproduces the notebook's cleaning/split/cross-validation, and writes `backend/artifacts/model.joblib` and `metrics.json`. It can take several minutes and needs memory. The model and metrics are intentionally not bundled; do not load untrusted joblib files.

## 2. Frontend setup (second terminal)

```bash
cd frontend
npm install
npm run dev
```

Open http://127.0.0.1:5173. Vite proxies `/api` to Django at http://127.0.0.1:8000.

## 3. Production build

```bash
cd frontend
npm run build
```

This is a **local development starter**, not a production deployment configuration. Before public deployment: disable Django DEBUG, set a secret key and allowed hosts, use HTTPS and PostgreSQL, enforce authentication/permissions for feedback and metrics as needed, apply stricter rate limiting, avoid storing raw ticket text without a privacy policy, and configure secure static hosting and CORS. The error explorer displays dataset excerpts and should be access-controlled if the dataset contains sensitive material. Do not expose Django's development server publicly.

## API
- `GET /api/health/`
- `POST /api/classify/` JSON `{ "ticket_text": "VPN login fails" }`
- `GET /api/metrics/`
- `GET /api/models/`
- `POST /api/feedback/` JSON `{ "ticket_text": "...", "predicted_queue": "IT Support", "corrected_queue": "Technical Support" }`

## Research integrity
The script selects the model by CV Macro-F1, not by test-set performance. It evaluates once on the untouched held-out test split. Feature contributions are positive signed linear SVM TF-IDF contributions, not confidence percentages or causal explanations. Human review is recommended because performance is limited.
