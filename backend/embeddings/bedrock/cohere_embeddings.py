import json

from embeddings.bedrock.client import BedrockClient
from botocore.exceptions import ClientError

from typing import Optional

import logging

import os
from dotenv import load_dotenv

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BedrockCohereEnglishEmbeddings(BedrockClient):
    """ A class to generate text embeddings using the Cohere Embed English model. """
    # References:
    # https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-embed.html
    # https://docs.cohere.com/reference/embed

    log: logging.Logger = logging.getLogger("BedrockCohereEnglishEmbeddings")

    def __init__(self, model_id: str, aws_access_key: Optional[str] = None, aws_secret_key: Optional[str] = None,
                 region_name: Optional[str] = "us-east-1", ) -> None:
        super().__init__(aws_access_key=aws_access_key, aws_secret_key=aws_secret_key, region_name=region_name)
        """
        Initialize the BedrockCohereEnglishEmbeddings class.
        
        Args:
            model_id (str): The model ID to use. Only accepts Cohere Embed English models.
            aws_access_key (str): The AWS access key.
            aws_secret_key (str): The AWS secret key.
            region_name (str): The AWS region name.
            bedrock_client (BedrockClient): The BedrockClient instance.

        """
        self.model_id = model_id
        self.bedrock_client = self._get_bedrock_client()

    def generate_text_embeddings(self, body):
        """
        Generate text embedding by using the Cohere Embed model.
        Args:
            body (str) : The request body to use.
        Returns:
            dict: The response from the model.
        """

        accept = '*/*'
        content_type = 'application/json'

        response = self.bedrock_client.invoke_model(
            body=body,
            modelId=self.model_id,
            accept=accept,
            contentType=content_type
        )

        return response

    def predict(self, text: str):
        """ Predict text embeddings based on the input text. 

        Args:
            text (str): The input text to generate embeddings for.

        Returns:
            list: The text embeddings generated by the model.
        """

        input_type = "search_document"
        embedding_types = ["float"]

        try:
            body = json.dumps({
                "texts": [text],
                "input_type": input_type,
                "embedding_types": embedding_types}
            )
            response = self.generate_text_embeddings(body=body)
            # Extract the response embeddings
            response_embeddings = json.loads(response.get('body').read())[
                "embeddings"]["float"][0]

            return response_embeddings
        except ClientError as err:
            message = err.response["Error"]["Message"]
            self.log.error("A client error occurred: %s", message)


# Example usage of the BedrockCohereEnglishEmbeddings class.
if __name__ == '__main__':

    # Note that if you are going to execute this script, you need to change the import statement to: 
    # from client import BedrockClient

    # If you are not going to use BedrockClient and its models, you might remove the packages boto3 and botocore. If so:
    # Open a Terminal and run the following commands:
    # 1. cd backend ---> (Make sure to be in the backend directory)
    # 2. poetry remove boto3 botocore ---> (This will remove the packages from the project)

    embedding_model = "cohere.embed-english-v3" # You can change this to any other Cohere English model
    aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    region_name = os.getenv("AWS_REGION")

    # Example usage of the BedrockCohereEnglishEmbeddings class.
    embeddings = BedrockCohereEnglishEmbeddings(
        model_id=embedding_model,
        region_name=region_name,
        aws_access_key=aws_access_key,
        aws_secret_key=aws_secret_key
    )

    print(type(embeddings))
    print(embeddings)
    print(embeddings.predict('Embed this text.'))
