import os
from dotenv import load_dotenv
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FollowupAction, ActiveLoop
from typing import Text, List, Dict, Any

import requests

#-----------------------------------------
#  RESTART CONVERSATION AL DARLE A BIN
#-----------------------------------------

class ActionRestartConversation(Action):
    def name(self):
        return "action_restart_conversation"

    def run(self, dispatcher, tracker, domain):
        tipo_consulta = tracker.get_slot("tipo_consulta")
        tipo_consulta_v = tracker.get_slot("tipo_consulta_v")
        tipo_consulta_c = tracker.get_slot("tipo_consulta_c")
        tipo_consulta_cl = tracker.get_slot("tipo_consulta_cl")

        if tipo_consulta:

            return [
                ActiveLoop(None),
                SlotSet("requested_slot", None),
                SlotSet("tipo_consulta", None),
                SlotSet("destino_b", None),
                SlotSet("origen_pais_b", None),
                SlotSet("origen_ciudad_b", None),
                SlotSet("anno_b", None),
                SlotSet("date_filter", None),
                SlotSet("consulta", None),
                FollowupAction("action_listen")
            ]
        elif tipo_consulta_v:
            return [
                ActiveLoop(None),
                SlotSet("requested_slot", None),
                SlotSet("tipo_consulta_v", None),
                SlotSet("destino_v", None),
                SlotSet("origen_pais_v", None),
                SlotSet("origen_ciudad_v", None),
                SlotSet("date_filter_v", None),
                SlotSet("consulta_v", None),
                FollowupAction("action_listen")
            ]
        elif tipo_consulta_c:
            return [
                ActiveLoop(None),
                SlotSet("requested_slot", None),
                SlotSet("tipo_consulta_c", None),
                SlotSet("destino_c", None),
                SlotSet("origen_pais_c", None),
                SlotSet("anno_c", None),
                SlotSet("date_filter_c", None),
                SlotSet("rango_ventana", None),
                SlotSet("perfil", None),
                FollowupAction("action_listen")
            ]
        
        elif tipo_consulta_cl:
            return [
                ActiveLoop(None),
                SlotSet("requested_slot", None),
                SlotSet("tipo_consulta_cl", None),
                SlotSet("destino_cl", None),
                SlotSet("origen_pais_cl", None),
                SlotSet("origen_ciudad_cl", None),
                SlotSet("date_filter_cl", None),
                SlotSet("clima_cl", None),
                FollowupAction("action_listen")
            ]
        
#--------------------------------------
#  HANDLE USER CONFIRMATION (YES)
#--------------------------------------

class ActionHandleConfirmacion(Action):
    def name(self):
        return "action_handle_confirmacion"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        user_intent = tracker.latest_message["intent"].get("name")
        tipo_consulta = tracker.get_slot("tipo_consulta")
        tipo_consulta_v = tracker.get_slot("tipo_consulta_v")
        tipo_consulta_c = tracker.get_slot("tipo_consulta_c")
        tipo_consulta_cl = tracker.get_slot("tipo_consulta_cl")

        if user_intent == "confirmar_envio" and tipo_consulta:
            dispatcher.utter_message(text="🔄 Procesando consulta...")
            return [FollowupAction("action_query_snowflake_busquedas")]
        elif user_intent == "confirmar_envio" and tipo_consulta_v:
            dispatcher.utter_message(text="🔄 Procesando consulta...")
            return [FollowupAction("action_query_snowflake_ventana")]
        elif user_intent == "confirmar_envio" and tipo_consulta_c:
            dispatcher.utter_message(text="🔄 Procesando consulta...")
            return [FollowupAction("action_query_snowflake_cluster")]
        elif user_intent == "confirmar_envio" and tipo_consulta_cl:
            dispatcher.utter_message(text="🔄 Procesando consulta...")
            return [FollowupAction("action_query_snowflake_clima")]
        return []

#--------------------------------------
#  HANDLE USER DENIAL (NO)
#--------------------------------------

class ActionHandleDenial(Action):
    def name(self):
        return "action_handle_denial"

    def run(self, dispatcher, tracker, domain):
        user_intent = tracker.latest_message["intent"].get("name")
        tipo_consulta = tracker.get_slot("tipo_consulta")
        tipo_consulta_v = tracker.get_slot("tipo_consulta_v")
        tipo_consulta_c = tracker.get_slot("tipo_consulta_c")
        tipo_consulta_cl = tracker.get_slot("tipo_consulta_cl")

        dispatcher.utter_message(text="🔄 Haz clic en **Análisis de Datos** para comenzar de nuevo.")

        if user_intent == "corregir_envio" and tipo_consulta:
            
            return [
                ActiveLoop(None),
                SlotSet("requested_slot", None),
                SlotSet("tipo_consulta", None),
                SlotSet("destino_b", None),
                SlotSet("origen_pais_b", None),
                SlotSet("origen_ciudad_b", None),
                SlotSet("anno_b", None),
                SlotSet("date_filter", None),
                SlotSet("consulta", None),
                FollowupAction("action_listen") 
            ]
        
        elif user_intent == "corregir_envio" and tipo_consulta_v:
            return [
                ActiveLoop(None),
                SlotSet("requested_slot", None),
                SlotSet("tipo_consulta_v", None),
                SlotSet("destino_v", None),
                SlotSet("origen_pais_v", None),
                SlotSet("origen_ciudad_v", None),
                SlotSet("date_filter_v", None),
                SlotSet("consulta_v", None),
                FollowupAction("action_listen") 
            ]
            
        elif user_intent == "corregir_envio" and tipo_consulta_c:
            return [
                ActiveLoop(None),
                SlotSet("requested_slot", None),
                SlotSet("tipo_consulta_c", None),
                SlotSet("destino_c", None),
                SlotSet("origen_pais_c", None),
                SlotSet("anno_c", None),
                SlotSet("date_filter_c", None),
                SlotSet("rango_ventana", None),
                SlotSet("perfil", None),
                FollowupAction("action_listen") 
            ]
            
        elif user_intent == "corregir_envio" and tipo_consulta_cl:
            return [
                ActiveLoop(None),
                SlotSet("requested_slot", None),
                SlotSet("tipo_consulta_cl", None),
                SlotSet("destino_cl", None),
                SlotSet("origen_pais_cl", None),
                SlotSet("origen_ciudad_cl", None),
                SlotSet("date_filter_cl", None),
                SlotSet("clima_cl", None),
                FollowupAction("action_listen") 
            ]

        return []

#--------------------------------------
#  T2N INNOHUB
#--------------------------------------
class ActionT2NInnohub(Action):
    def name(self):
        return "action_t2n_innohub"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        user_text = tracker.latest_message.get('text', "")
        scope = tracker.get_slot("scope")
        print("User text:", user_text)
        print("Scope:", scope)

        # Innohub call
        load_dotenv() 
        innohub_api_key = os.getenv("INNOHUB_API_KEY")
        api_url = 'https://inno-hub.1millionbot.com/innohub/api/inno-hub/t2n_rasa_response/'
        
        params = {"user_message": user_text, "assistant": "Smarty", "scope": scope }
        headers = {
            'accept': 'application/json',
            'Authorization': str(innohub_api_key)
        }
        
        try:
            response = requests.get(api_url, params=params, headers=headers)

            
            print("T2n response:", response.json())
            
            dispatcher.utter_message(text=response.json()['response'])
        
        except Exception as e:
            print(f"Ha sucedido un error del tipo: {e}")
            dispatcher.utter_message(text="Lo siento, ha ocurrido un error. Vuelve a intentarlo, ¡gracias por ser paciente!")

        return [
            SlotSet("scope", None), 
            FollowupAction("action_listen")
        ]  
    


