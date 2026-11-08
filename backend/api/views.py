from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .services import predict,get_metrics
from .models import Feedback
LABELS=['Customer Service','Technical Support','IT Support','Product Support']
@api_view(['GET'])
def health(request):
 return Response({'status':'online'})
@api_view(['POST'])
def classify(request):
 text=request.data.get('ticket_text','')
 if not isinstance(text,str) or not 3<=len(text.strip())<=5000:
  return Response({'error':'ticket_text must contain 3–5000 characters'},status=400)
 try: return Response(predict(text.strip()))
 except FileNotFoundError as exc: return Response({'error':str(exc)},status=503)
@api_view(['GET'])
def metrics(request):
 try: return Response(get_metrics())
 except FileNotFoundError as exc: return Response({'error':str(exc)},status=503)
@api_view(['GET'])
def models(request):
 try:
  data=get_metrics();return Response({'selected_model':data['selected_model'],'cv_results':data['cv_results']})
 except FileNotFoundError as exc:return Response({'error':str(exc)},status=503)
@api_view(['POST'])
def feedback(request):
 text=request.data.get('ticket_text');pred=request.data.get('predicted_queue');corrected=request.data.get('corrected_queue')
 if not isinstance(text,str) or not 3<=len(text.strip())<=5000 or pred not in LABELS or corrected not in LABELS:
  return Response({'error':'Invalid ticket or queue label'},status=400)
 Feedback.objects.create(ticket_text=text.strip(),predicted_queue=pred,corrected_queue=corrected)
 return Response({'saved':True},status=201)
