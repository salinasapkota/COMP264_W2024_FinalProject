import boto3

class ComprehendService:
    def __init__(self):
        self.client = boto3.client(service_name='comprehend')

    def detect_medical_entities(self, text):
        response = self.client.detect_entities(Text=text, LanguageCode='en')
        return response
