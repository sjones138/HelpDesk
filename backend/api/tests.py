
from unittest.mock import patch

from django.test import TestCase

from .models import Feedback


class ApiTests(TestCase):
    """Tests for the HelpDesk REST API."""

    def test_health(self):
        response = self.client.get("/api/health/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "online")

    @patch("api.views.predict")
    def test_classification(self, mock_predict):
        mock_predict.return_value = {
            "queue": "IT Support",
            "contributions": [],
        }

        response = self.client.post(
            "/api/classify/",
            {"ticket_text": "VPN login fails"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["queue"], "IT Support")
        mock_predict.assert_called_once_with("VPN login fails")

    def test_empty_ticket(self):
        response = self.client.post(
            "/api/classify/",
            {"ticket_text": " "},
        )

        self.assertEqual(response.status_code, 400)

    def test_missing_ticket(self):
        response = self.client.post("/api/classify/", {})

        self.assertEqual(response.status_code, 400)

    def test_short_ticket(self):
        response = self.client.post(
            "/api/classify/",
            {"ticket_text": "ab"},
        )

        self.assertEqual(response.status_code, 400)

    def test_oversized_ticket(self):
        response = self.client.post(
            "/api/classify/",
            {"ticket_text": "x" * 5001},
        )

        self.assertEqual(response.status_code, 400)

    def test_non_string_ticket(self):
        response = self.client.post(
            "/api/classify/",
            {"ticket_text": 123},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)

    @patch("api.views.predict")
    def test_classification_model_unavailable(self, mock_predict):
        mock_predict.side_effect = FileNotFoundError(
            "Model artifact not found"
        )

        response = self.client.post(
            "/api/classify/",
            {"ticket_text": "VPN login fails"},
        )

        self.assertEqual(response.status_code, 503)
        self.assertIn("error", response.json())

    @patch("api.views.get_metrics")
    def test_metrics(self, mock_get_metrics):
        mock_get_metrics.return_value = {
            "selected_model": "Linear SVM",
            "test_metrics": {
                "accuracy": 0.5869,
                "macro_f1": 0.5632,
            },
        }

        response = self.client.get("/api/metrics/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["selected_model"],
            "Linear SVM",
        )
        self.assertIn("test_metrics", response.json())

    @patch("api.views.get_metrics")
    def test_metrics_unavailable(self, mock_get_metrics):
        mock_get_metrics.side_effect = FileNotFoundError(
            "Metrics artifact not found"
        )

        response = self.client.get("/api/metrics/")

        self.assertEqual(response.status_code, 503)
        self.assertIn("error", response.json())

    @patch("api.views.get_metrics")
    def test_models(self, mock_get_metrics):
        mock_get_metrics.return_value = {
            "selected_model": "Linear SVM",
            "cv_results": [
                {
                    "model": "Linear SVM",
                    "macro_f1": 0.5509,
                }
            ],
        }

        response = self.client.get("/api/models/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["selected_model"],
            "Linear SVM",
        )
        self.assertEqual(len(response.json()["cv_results"]), 1)

    @patch("api.views.get_metrics")
    def test_models_unavailable(self, mock_get_metrics):
        mock_get_metrics.side_effect = FileNotFoundError(
            "Metrics artifact not found"
        )

        response = self.client.get("/api/models/")

        self.assertEqual(response.status_code, 503)

    def test_feedback_submission(self):
        response = self.client.post(
            "/api/feedback/",
            {
                "ticket_text": "VPN login fails",
                "predicted_queue": "Technical Support",
                "corrected_queue": "IT Support",
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["saved"], True)
        self.assertEqual(Feedback.objects.count(), 1)

        saved_feedback = Feedback.objects.first()

        self.assertEqual(
            saved_feedback.predicted_queue,
            "Technical Support",
        )
        self.assertEqual(
            saved_feedback.corrected_queue,
            "IT Support",
        )

    def test_feedback_invalid_queue(self):
        response = self.client.post(
            "/api/feedback/",
            {
                "ticket_text": "VPN login fails",
                "predicted_queue": "Unknown Queue",
                "corrected_queue": "IT Support",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Feedback.objects.count(), 0)

    def test_feedback_missing_fields(self):
        response = self.client.post(
            "/api/feedback/",
            {"ticket_text": "VPN login fails"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Feedback.objects.count(), 0)

    def test_feedback_empty_ticket(self):
        response = self.client.post(
            "/api/feedback/",
            {
                "ticket_text": " ",
                "predicted_queue": "Technical Support",
                "corrected_queue": "IT Support",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Feedback.objects.count(), 0)

    def test_feedback_oversized_ticket(self):
        response = self.client.post(
            "/api/feedback/",
            {
                "ticket_text": "x" * 5001,
                "predicted_queue": "Technical Support",
                "corrected_queue": "IT Support",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Feedback.objects.count(), 0)
