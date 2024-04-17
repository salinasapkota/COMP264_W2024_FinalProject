import boto3

class ComprehendService:
    def __init__(self):
        self.client = boto3.client('comprehend')

    def detect_entities(self, text):
        # Detect entities in the text using Amazon Comprehend
        response = self.client.detect_entities(Text=text, LanguageCode='en')

        # Extract entity labels
        labels = []
        for entity in response['Entities']:
            labels.append(entity['Text'])

        return labels
