# import os
# import replicate
# import json
# import logging
# import requests
# from dotenv import dotenv_values
# from typing import Dict, Text, List
# from rasa_sdk import Tracker
# from rasa_sdk.events import EventType
# from rasa_sdk.executor import CollectingDispatcher
# from rasa_sdk import Action


# env_vars = dotenv_values('.env')
# print('env file found')

# print(os.getcwd())
# os.environ['REPLICATE_API_TOKEN'] = env_vars['REPLICATE_API_TOKEN']
# #os.environ['REPLICATE_API_TOKEN'] = 'your_replicate_api_token'

# class FallBackAction(Action):
#     def name(self) -> Text:
#         return "action_fallback"

#     def run(
#         self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
#     ) -> List[EventType]:
#         latest_user_message = tracker.latest_message.get("text", "")
#         conversations = self._get_conversation_history(tracker)

#         # Call LLaMA 7B API if there's a user message
#         if latest_user_message:
#             response = self._call_llama_api(latest_user_message, tracker)  # Pass tracker here
#             dispatcher.utter_message(text=response)
#         return []

#     def _get_conversation_history(self, tracker: Tracker) -> str:
#         history = ""
#         for event in tracker.events:
#             if event.get("event") == "user":
#                 history += "User: " + str(event.get("text", "")) + "\n\n"
#             elif event.get("event") == "bot":
#                 history += "Assistant: " + str(event.get("text", "")) + "\n\n"
#         return history    
    
#     def _call_llama_api(self, user_message: str, tracker: Tracker) -> str:
#             # Initialize the conversation string
#             string_dialogue = "Eres un útil 'Assistant'. No respondes como un 'User' ni finges ser un 'User'. Solo contestas como un 'Assistant'."

#             # Append conversation history to the string
#             for event in tracker.events:
#                 if event.get("event") == "user":
#                     string_dialogue += "User: " + event.get("text", "") + "\n\n"
#                 elif event.get("event") == "bot":
#                     string_dialogue += "Assistant: " + event.get("text", "") + "\n\n"

#             # Define LLaMA model and parameters
#             #llama_model = 'a16z-infra/llama13b-v2-chat:df7690f1994d94e96ad9d568eac121aecf50684a0b0963b25a41cc40061269e5'
#             llama_model = 'a16z-infra/llama7b-v2-chat:4f0a4744c7295c024a1de15e1a63c880d3da035fa1f49bfd344fe076074c8eea'
#             temperature = 0.1  # Adjust as needed
#             repetition_penalty = 1.0

#             # Call the LLaMA API
#             try:
#                 output = replicate.run(
#                     llama_model,
#                     input={
#                         "prompt": f"{string_dialogue} {user_message} Assistant: ",
#                         "temperature": temperature,
#                         "repetition_penalty": repetition_penalty
#                     }
#                 )
#                 return "".join(output)
#             except Exception as e:
#                 return f"An error occurred while processing your request: {e}"


# class FallbackWaitAction(Action):
#     def name(self) -> Text:
#         return "action_fallback_wait"

#     def run(
#         self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
#     ) -> List[EventType]:

#         dispatcher.utter_message(text='Conectando con Llama2-7B')

#         return []