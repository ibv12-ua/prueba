from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from random import choice
from typing import Any, Text, Dict, List
import re


# .............................................

class ActionSetUserName(Action):
    def name(self) -> str:
        return "action_set_user_name"
    
    def corregir_nombre(self, nombre: Text) -> Text:
        partes_nombre = nombre.split()  # Dividir el nombre en partes
        nombre_corregido = ' '.join(part.capitalize() if part.lower() not in ['de','la','las','del','los'] else part.lower() for part in partes_nombre)
        return nombre_corregido

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict) -> list:
            user_name = next(tracker.get_latest_entity_values("name"), None)
            current_name = tracker.get_slot("user_name")
            if user_name:
                user_name = self.corregir_nombre(user_name) 
                dispatcher.utter_message(text=f"Es un placer conocerte, {user_name}.")
                return [SlotSet("user_name", user_name)]
            elif current_name:
                current_name = self.corregir_nombre(current_name)
                dispatcher.utter_message(text=f"¡Hola de nuevo, {current_name}! ¿En qué puedo ayudarte hoy?")
                return []
            else:
                dispatcher.utter_message(text="¡Hola! ¿En qué puedo ayudarte hoy?")
                return []


def clean_response(response: str) -> str:
    """ Limpia el texto """
    response = re.sub(r'\s{2,}', ' ', response)  # Reemplaza dobles espacios por un solo espacio
    response = re.sub(r'\s([,.?])', r'\1', response)  # Elimina espacios antes de ",", ".", "?"
    response = re.sub(r',\.', '.', response)  # Reemplaza específicamente ",." por "."
    response = re.sub(r',,', ',', response)  

    return response

class ActionHandleFallback(Action):
    def name(self) -> str:
        return "action_handle_fallback"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict) -> list:
        user_name = tracker.get_slot("user_name")
        name_placeholder = user_name if user_name else ""
        responses = domain["responses"].get("utter_fallback", [])
        
        personalized_responses = [
            r["text"].replace("{name_placeholder}", name_placeholder).strip() for r in responses
        ]

        selected_response = choice(personalized_responses)
        selected_response = clean_response(selected_response)  

        dispatcher.utter_message(text=selected_response)
        return []

class ActionHandleOutOfScope(Action):
    def name(self) -> str:
        return "action_handle_out_of_scope"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict) -> list:
        user_name = tracker.get_slot("user_name")
        name_placeholder = user_name if user_name else ""
        responses = domain["responses"].get("utter_out_of_scope", [])
        
        personalized_responses = [
            r["text"].replace("{name_placeholder}", name_placeholder).strip() for r in responses
        ]

        selected_response = choice(personalized_responses)
        selected_response = clean_response(selected_response)  

        dispatcher.utter_message(text=selected_response)
        return []

# .............................................
# OLD NAME ACTION
# .............................................


# from typing import Any, Text, Dict, List

# from rasa_sdk import Action, Tracker
# from rasa_sdk.executor import CollectingDispatcher
# import pandas as pd
# # from .data import data

# class ActionNombre(Action):

#     def name(self) -> Text:
#         return "action_nombre"

#     def corregir_nombre(self, nombre: Text) -> Text:
#         partes_nombre = nombre.split()  # Dividir el nombre en partes
#         nombre_corregido = ' '.join(part.capitalize() if part.lower() not in ['de','la','las','del','los'] else part.lower() for part in partes_nombre)
#         return nombre_corregido
    
#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

#         nombre = tracker.slots.get("nombre")
#         print('nombre',nombre)

#         intent = tracker.latest_message["intent"].get("name")
#         print('intent',intent)

#         # sentiment = tracker.slots.get("sentiment")
#         # print('sentiment',sentiment)

#         if nombre:
#             nombre_corregido=self.corregir_nombre(nombre)
#             #msg = data.query(f"intent=='{intent}'&sentiment=='{sentiment}'&name=='yes'").reset_index()['reponse_text'][0].format(nombre=nombre_corregido)
#             msg = f"intent=='{intent}".reset_index()['reponse_text'][0].format(nombre=nombre_corregido)


#         else:
#             #msg = data.query(f"intent=='{intent}'&sentiment=='{sentiment}'&name=='no'").reset_index()['reponse_text'][0]
#             msg = f"intent=='{intent}".reset_index()['reponse_text'][0]


#         dispatcher.utter_message(text=msg)

#         return [] 