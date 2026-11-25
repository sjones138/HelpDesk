from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Feedback
from .services import get_metrics, predict


LABELS = ["Customer Service", "Technical Support", "IT Support", "Product Support"]


@api_view(["GET"])
def health(request):
    return Response({"status": "online"})


@api_view(["POST"])
def classify(request):
    text = request.data.get("ticket_text", "")
    if not isinstance(text, str) or not 3 <= len(text.strip()) <= 5000:
        return Response(
            {"error": "ticket_text must contain 3–5000 characters"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        return Response(predict(text.strip()))
    except FileNotFoundError as exc:
        return Response(
            {"error": str(exc)},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


@api_view(["GET"])
def metrics(request):
    try:
        return Response(get_metrics())
    except FileNotFoundError as exc:
        return Response(
            {"error": str(exc)},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


@api_view(["GET"])
def models(request):
    try:
        data = get_metrics()
        return Response(
            {
                "selected_model": data["selected_model"],
                "cv_results": data["cv_results"],
            }
        )
    except FileNotFoundError as exc:
        return Response(
            {"error": str(exc)},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


@api_view(["POST"])
def feedback(request):
    text = request.data.get("ticket_text")
    predicted = request.data.get("predicted_queue")
    corrected = request.data.get("corrected_queue")

    if (
        not isinstance(text, str)
        or not 3 <= len(text.strip()) <= 5000
        or predicted not in LABELS
        or corrected not in LABELS
    ):
        return Response(
            {"error": "Invalid ticket or queue label"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    Feedback.objects.create(
        ticket_text=text.strip(),
        predicted_queue=predicted,
        corrected_queue=corrected,
    )
    return Response({"saved": True}, status=status.HTTP_201_CREATED)
