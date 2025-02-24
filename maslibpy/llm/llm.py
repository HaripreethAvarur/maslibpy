import os
import logging
from typing import  List, Dict, Union
from litellm import completion
from maslibpy.messages.user import UserMessage
from maslibpy.messages.assistant import AIMessage
from maslibpy.llm.constants import MODELS,PROVIDERS,ENV_VARS
logging.basicConfig(level=logging.INFO)
os.environ['LITELLM_LOG'] = 'DEBUG'
class LLM():
    """
    Represents a Language Learning Model (LLM) interface to interact with various providers and models.

    This class supports initialization with a provider and model name, validates configurations,
    and allows invoking the model with input messages to generate responses.
    """
    def __init__(
            self, 
            provider: str = "together",
            model_name: str = "together_ai/mistralai/Mixtral-8x7B-Instruct-v0.1"):
        """
        Initialize the LLM instance with a provider and model name.

        Parameters:
        - provider (str): The name of the LLM provider. Default is "together".
        - model_name (str): The name of the model from the provider. 
          Default is "together_ai/mistralai/Mixtral-8x7B-Instruct-v0.1".

        Attributes:
        - provider (str): The selected provider for the LLM.
        - model_name (str): The selected model for the LLM.
        - api_key (str or None): The API key retrieved from environment variables for authentication.

        This method also validates the provider and model configurations.
        """
        self.provider = provider
        self.model_name = model_name
        self.api_key = None
        self.validate_provider()

    def validate_provider(self):
        """
        Validate the provider and model configuration.

        Checks:
        1. Ensures the provider is supported.
        2. Ensures the model is available for the given provider.
        3. Ensures the required API key is set as an environment variable.

        Raises:
        - ValueError: If the provider or model is unsupported.
        - EnvironmentError: If the required API key is missing.

        Logs errors and prompts the user to address configuration issues.
        """
        if self.provider not in PROVIDERS:
            logging.error(f"Unsupported provider: {self.provider}. Supported providers are: {PROVIDERS}")
            raise ValueError(f"Unsupported provider. Supported providers: {PROVIDERS}")
        
        if self.model_name not in MODELS[self.provider]:
            logging.error(f"Unsupported model: {self.model_name}. Supported models for {self.provider}: {MODELS[self.provider]}")
            raise ValueError(
                f"Unsupported model: {self.model_name} for provider: {self.provider}. "
                f"Available models for {self.provider}: {MODELS[self.provider]}"
            )
        
        env_key = ENV_VARS[self.provider]["key_name"]
        if not os.environ.get(env_key):
            logging.error(f"Missing environment variable: {env_key}")

            raise EnvironmentError(ENV_VARS[self.provider]["prompt"])
        
        self.api_key = os.environ.get(env_key)
        logging.info(f"API key validated for provider {self.provider}")

    def invoke(self, messages: Union[str, List[Dict[str, str]]]) -> str:
        """
        Invoke the LLM with the provided messages to generate a response.

        Parameters:
        - messages (Union[str, List[Dict[str, str]]]): 
          The input messages for the LLM. This can be:
          - A string representing a single user message.
          - A list of dictionaries, where each dictionary represents a message with attributes like `role` and `content`.

        Returns:
        - str: The content of the response generated by the LLM.

        Raises:
        - ValueError: If the input messages are neither a string nor a list of dictionaries.
        - Exception: If an error occurs during model invocation.

        Logs errors and handles exceptions gracefully during invocation.
        """
        if isinstance(messages, str):
            human_msg=UserMessage(role="user",content=messages)
            formatted_messages= [{"role": human_msg.role, "content": human_msg.content}]
        elif isinstance(messages, list) and all(isinstance(msg, dict) for msg in messages):
            formatted_messages = messages
        else:
            logging.error("Input must be a string or a list of dictionaries for messages.")
            raise ValueError("Input must be a string or a list of dictionaries for messages.")
        try:
            response = completion(model=self.model_name, messages=formatted_messages,stream=False)
            res= response["choices"][0]["message"]["content"]
            AIMessage(content=res)
            return res
        except Exception as e:
            logging.error(f"Error invoking the model: {e}")
            raise e
