from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from rasa_sdk.types import DomainDict
from rasa_sdk.forms import FormValidationAction
from .utils import chunk_buttons

class ActionCarousel(Action):
    def name(self) -> Text:
        return "action_carousel"
    
    def run(self, dispatcher, tracker: Tracker, domain: Dict) -> List[Dict[Text, Any]]:
        message = {
            "type": "template",
            "payload": {
                "template_type": "generic",
                "elements": [
                    {
                        "title": "Quiénes somos - Invat·tur",
                        "subtitle": "Haz click en el siguiente enlace para saber más sobre Invat·tur.",
                        "image_url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSqhmyBRCngkU_OKSL6gBQxCSH-cufgmZwb2w&usqp=CAU",
                        "buttons": [
                            {
                                "title": "Visitar web",
                                "url": "https://invattur.es/quienes-somos.html",
                                "type": "web_url"
                            }
                        ]
                    },
                    {
                        "title": "Organigrama - Invat·tur",
                        "subtitle": "Haz click en el siguiente enlace para saber más sobre el organigrama de Invat·tur.",
                        "image_url": "https://image.freepik.com/free-vector/city-illustration23-2147514701.jpg",
                        "buttons": [
                            {
                                "title": "Visitar web",
                                "url": "https://invattur.es/organigrama.html",
                                "type": "web_url"
                            }
                        ]
                    }
                ] 
                }
        }
        dispatcher.utter_message(attachment=message)
        return []


class ActionLastUtterance(Action):
    def name(self) -> Text:
        return "action_comprobar_query"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        last_bot_utterance = None
        for event in reversed(tracker.events):
            if event.get('event') == 'bot' and 'text' in event:
                last_bot_utterance = event['text']
                break

        if last_bot_utterance == "utter_ask_query_v":
            pass
        else:
            dispatcher.utter_message("👀 Para poder realizar ese tipo de consultas, por favor, haz clic en el botón de análisis de datos. Este botón aparecerá en la parte inferior del chat cuando te encuentres en la sección de ventana de oportunidad.")
        return [
            SlotSet("mes", None),
            SlotSet("origen", None),
            SlotSet("destino", None),
            SlotSet("exp_temporal", None),
            SlotSet("exp_mediana", None),
            SlotSet("exp_promedio", None),
            SlotSet("consulta_amplia", None),
            SlotSet("consulta_menor", None),
            SlotSet("consulta_mayor", None)  
        ]    
    

      
   
class ActionCarousel(Action):
    def name(self) -> Text:
        return "action_SIT_general"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        message = {
            "type": "template",
            "payload": {
                "template_type": "generic",
                "elements": [
                    {
                        "image_url": "https://img.freepik.com/vector-premium/hombre-esta-pie-frente-pantalla-computadora-ilustracion-plana-grafico1134986-5555.jpg?w=1060",
                        "buttons": [
                            {
                                "type": "web_url",  
                                "title": "Acceder a la sección de informes",
                                "url": "https://34.175.122.246/report" 
                                    }
                        ]
                    },
                    {
                        "image_url": "https://img.freepik.com/vector-premium/idea-ahorro-costes-reduccion-costes-disminucion-gastos1134986-8180.jpg?w=1060",
                        "buttons": [
                            {
                                "type": "web_url",
                                "title": "Acceder a Smart Academy",
                                "url": "https://34.175.122.246/smartacademy"
                            }
                        ]
                    },
                    {
                        "image_url": "https://img.freepik.com/vector-gratis/concepto-comunicacion-empresarial-diseno-plano_52683-76243.jpg?t=st=1726818151~exp=1726821751~hmac=0f2a9370bf92a45d426df52f83295fe5daf7c48c2765b34bd9bc6a2d7c70ed18&w=1380",
                        "buttons": [
                            {
                                "type": "web_url",
                                "title": "Acceder a las Notas Metdológicas",
                                "url": "https://34.175.122.246/notas-metodologicas"
                            }
                        ]
                    },
                    {
                        "image_url": "https://img.freepik.com/vector-gratis/ilustracion-lider-equipo-femenino-dibujado-mano-plana_52683-55543.jpg",
                        "buttons": [
                            {
                                "type": "web_url",
                                "title": "Acceder a las Visualizaciones Dinámicas",
                                "url": "https://34.175.122.246/"
                            }
                        ]
                    }
                ]
            }
        }
        dispatcher.utter_message(attachment=message)
        return []

class ActionCarousel(Action):
    def name(self) -> Text:
        return "action_carousel_analisis_datos"
    
    def run(self, dispatcher, tracker: Tracker, domain: Dict) -> List[Dict[Text, Any]]:
        buttons = [
            {"title": "Ventana media y búsquedas previstas", "payload": "/talk2numbers_busquedas"},
            {"title": "Ventana de oportunidad media", "payload": "/talk2numbers_ventana_test"},
            # {"title": "Búsquedas Diarias", "payload": "/talk2numbers_busquedas"},
            
        ]

        message = {
            "type": "button-carousel-template",
            "payload": {
                "template_type": "generic",
                "elements": [
                    {"buttons": group} for group in chunk_buttons(buttons, 2)
                ]
            }
        }
        dispatcher.utter_message(text="Selecciona el tema de interés",attachment=message)
        return []



class ActionDeleteSlotError(Action):
    def name(self) -> Text:
        return "action_delete_slot_error"
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        return [SlotSet("error", None)]

class ActionDeleteSlotsForms(Action):
    def name(self) -> Text:
        return "action_delete_slot_forms"
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        dispatcher.utter_message("ℹ️ Resultado no disponible para esta versión del asistente. Disculpa las molestias.")

        return [SlotSet("tipo_consulta", None),
                SlotSet("origen_ciudad_b", None),
                SlotSet("origen_pais_b", None),
                SlotSet("destino_b", None),
                SlotSet("anno_b", None),
                SlotSet("date_filter", None),
                SlotSet("consulta", None),
                SlotSet("tipo_consulta_v", None),
                SlotSet("origen_ciudad_v", None),
                SlotSet("origen_pais_v", None),
                SlotSet("destino_v", None),
                SlotSet("date_filter_v", None),
                SlotSet("consulta_v", None)]
