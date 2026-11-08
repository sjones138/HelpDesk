from django.test import TestCase
from unittest.mock import patch
class ApiTests(TestCase):
 def test_health(self):self.assertEqual(self.client.get('/api/health/').status_code,200)
 def test_empty_ticket(self):self.assertEqual(self.client.post('/api/classify/',{'ticket_text':' '}).status_code,400)
 @patch('api.views.predict',return_value={'queue':'IT Support','contributions':[]})
 def test_classification(self,mock_predict):
  response=self.client.post('/api/classify/',{'ticket_text':'VPN login fails'})
  self.assertEqual(response.status_code,200)
  self.assertEqual(response.json()['queue'],'IT Support')
