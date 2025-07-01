from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FollowupAction, ActiveLoop
from typing import Any, Text, Dict, List
from datetime import datetime
from rasa_sdk.forms import FormValidationAction
from .utils import chunk_buttons


class ActionButtonsST(Action):
    def name(self) -> str:
        return "action_gva_smart_tourism"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        buttons = [
            {"title": "Visualizaciones Genéricas", "payload": "/gva_visualizaciones_genericas"},
            {"title": "Casos de uso", "payload": "/gva_casos_uso"},
            {"title": "Soluciones IA y Analítica avanzada", "payload": "/gva_modelos_IA"},
            {"title": "Informes", "payload": "/gva_informes"},
            {"title": "Smart Academy", "payload": "/gva_smart_academy"},
            {"title": "Notas Metodológicas", "payload": "/gva_notas_metodologicas"},
        ]
        message = {
            "type": "button-carousel-template",
            "payload": {
                "template_type": "generic",
                "elements": [
                    {"buttons": group} for group in chunk_buttons(buttons, 3)
                ]
            }
        }
        
        dispatcher.utter_message(text="Smart Tourism es una plataforma donde encontrar información sobre **Inteligencia Turística** en la Comunitat Valenciana. \n\n Puedes explorar el portal o pulsar estos botones para **saber más**:", attachment=message)
        return []


class ActionButtonsVD(Action):
    def name(self) -> str:
        return "action_gva_visualizaciones_dinamicas"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        buttons = [
            {"title": "Visualizaciones genéricas", "payload": "/gva_visualizaciones_genericas"},
            {"title": "Casos de uso", "payload": "/gva_casos_uso"},
            {"title": "Soluciones IA y Analítica avanzada", "payload": "/gva_modelos_IA"},
        ]
        message = {
            "type": "button-carousel-template",
            "payload": {
                "template_type": "generic",
                "elements": [
                    {"buttons": group} for group in chunk_buttons(buttons, 3)
                ]
            }
        }
        
        dispatcher.utter_message(text="Las **Visualizaciones dinámicas** son útiles para **explorar** y **analizar** interactivamente los datos en forma de gráficas. \n\n 🤓💡 Además, puedes filtrarlas y **personalizarlas** según tus necesidades. \n\n ¿Te gustaría que te diera **más información** sobre alguna de ellas?", attachment=message)
        return []


class ActionButtonsVG(Action):
    def name(self) -> str:
        return "action_gva_visualizaciones_genericas"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        buttons = [
            {"title": "Comportamiento turístico", "payload": "/gva_VG_comportamiento_turismo"},
            {"title": "Alojamientos", "payload": "/gva_VG_alojamientos"},
            {"title": "Vuelos", "payload": "/gva_VG_vuelos"},
            {"title": "Presencia y movilidad", "payload": "/gva_VG_presencia_movilidad"},
        ]
        message = {
            "type": "button-carousel-template",
            "payload": {
                "template_type": "generic",
                "elements": [
                    {"buttons": group} for group in chunk_buttons(buttons, 4)
                ]
            }
        }
        
        dispatcher.utter_message(text="Las **Visualizaciones Genéricas** 📊 son gráficos interactivos que te permiten examinar una gran variedad de datos de forma **sencilla** y **exhaustiva**. \n\n ¿Te gustaría saber más sobre alguno de los temas que tratan? 🤔", attachment=message)
        return []

class ActionButtonsCUS(Action):
    def name(self) -> str:
        return "action_gva_casos_uso"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        buttons = [
            {"title": "Población flotante y densidad", "payload": "/gva_CUS_poblacion_flotante"},
            {"title": "Programación y negociación", "payload": "/gva_CUS_programacion_aerolineas"},
            {"title": "Marketing aéreo", "payload": "/gva_CUS_marketing_aereo"},
        ]
        message = {
            "type": "button-carousel-template",
            "payload": {
                "template_type": "generic",
                "elements": [
                    {"buttons": group} for group in chunk_buttons(buttons, 3)
                ]
            }
        }
        
        dispatcher.utter_message(text="Los **Casos de uso** ⚙️ son ejemplos prácticos de cómo aplicar los datos y los análisis de la plataforma a **situaciones reales**. \n\n ¿Te interesa alguno de los que están **disponibles en la plataforma**?", attachment=message)
        return []


class ActionButtonsCTVG(Action):
    def name(self) -> str:
        return "action_gva_VG_comportamiento_turismo"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        buttons = [
            {"title": "Internacional", "payload": "/gva_VG_CT_turismo_internacional"},
            {"title": "Nacional", "payload": "/gva_VG_CT_turismo_nacional"},
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
        
        dispatcher.utter_message(text="Las visualizaciones de 🌍 **Comportamiento del turismo** desglosan datos sobre diversos aspectos turísticos:  \n ▫️ El **número** de turistas  \n ▫️ El **perfil** del turista o las **características** del viaje  \n ▫️ El **gasto** turístico  \n\n ¿Prefieres profundizar en el **turismo nacional** o en el **internacional**?", attachment=message)
        return []


class ActionButtonsALOJ(Action):
    def name(self) -> str:
        return "action_gva_VG_alojamientos"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        buttons = [
            {"title": "Todos los alojamientos", "payload": "/gva_VG_ALOJ_todos"},
            {"title": "Hoteles, apartamentos y campings", "payload": "/gva_VG_ALOJ_especificos"},
            {"title": "Alojamientos rurales", "payload": "/gva_VG_ALOJ_rurales"},
        ]
        message = {
            "type": "button-carousel-template",
            "payload": {
                "template_type": "generic",
                "elements": [
                    {"buttons": group} for group in chunk_buttons(buttons, 3)
                ]
            }
        }
        
        dispatcher.utter_message(text="En la sección de **alojamientos** 🏠 encontrarás datos evolutivos y comparativos sobre **todo tipo de hospedajes.** \n\n El apartado de **demanda** explora:  \n ▫️ El número de viajeros  \n ▫️ Las pernoctaciones  \n ▫️ La estancia media \n\n El de **oferta** muestra:  \n ▫️ La cantidad de establecimientos  \n ▫️ El número de plazas  \n ▫️ El grado de ocupación  \n ▫️ El personal empleado", attachment=message)
        return []

class ActionButtonsVG_PM(Action):
    def name(self) -> str:
        return "action_gva_VG_presencia_movilidad"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        buttons = [
            {"title": "Estancia diurna", "payload": "/gva_VG_PM_estancia_diurna"},
            {"title": "Estancia nocturna", "payload": "/gva_VG_PM_estancia_nocturna"},
            {"title": "Llegadas y salidas", "payload": "/gva_VG_PM_llegadas_salidas"},
            {"title": "Movilidad diurna y nocturna", "payload": "/gva_VG_PM_movilidad"},
            {"title": "Turistas, pernoctaciones y estancia media", "payload": "/gva_VG_PM_presencia"},
            
        ]
        message = {
            "type": "button-carousel-template",
            "payload": {
                "template_type": "generic",
                "elements": [
                    {"buttons": group} for group in chunk_buttons(buttons, 3)
                ]
            }
        }
        
        dispatcher.utter_message(text="En el apartado de visualizaciones de **presencia y movilidad** podrás encontrar toda la información sobre diversos aspectos turísticos esenciales a nivel de:  \n ▫️ Turismo **receptor**  \n ▫️ Turismo **interprovincial**  \n ▫️ Turismo **intraprovincial**  \n\n ¿Qué tema te interesa más? 🤔", attachment=message)
        return []
   

       
class ActionButtonsMIA(Action):
    def name(self) -> str:
        return "action_gva_modelos_IA"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        buttons = [
            {"title": "Oportunidad en marketing", "payload": "/gva_MIA_ventana_oportunidad"},
            {"title": "Previsión de visitantes", "payload": "/gva_MIA_predict_estancia_diurna"},
            {"title": "Influencia climática", "payload": "/gva_MIA_factor_climatico"},
            {"title": "Tendencia de viajes nacionales", "payload": "/gva_MIA_predict_viajes_nacionales"},
            {"title": "Patrones de comportamiento", "payload": "/gva_MIA_patrones_comportamiento"},
            # {"title": "Relación de factores clave", "payload": "/gva_MIA_factores_clave"},
        ]
        message = {
            "type": "button-carousel-template",
            "payload": {
                "template_type": "generic",
                "elements": [
                    {"buttons": group} for group in chunk_buttons(buttons, 3)
                ]
            }
        }
        dispatcher.utter_message(text="Las **Soluciones IA y Analítica avanzada** 🤖 son herramientas que utilizan **modelos predictivos avanzados** basados inteligencia artificial para analizar datos y hacer previsiones turísticas. \n\n Haz clic sobre el tema que te interese para **profundizar** en él.", attachment=message)
        return []



class ActionButtonsIntro(Action):
    def name(self) -> str:
        return "action_gva_intro"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        buttons = [
            {"title": "Visualizaciones Genéricas", "payload": "/gva_visualizaciones_genericas"},
            {"title": "Casos de uso", "payload": "/gva_casos_uso"},
            {"title": "Soluciones IA y Analítica avanzada", "payload": "/gva_modelos_IA"},
            {"title": "Informes", "payload": "/gva_informes"},
            {"title": "Smart Academy", "payload": "/gva_smart_academy"},
            {"title": "Notas Metodológicas", "payload": "/gva_notas_metodologicas"},
        ]
        message = {
            "type": "button-carousel-template",
            "payload": {
                "template_type": "generic",
                "elements": [
                    {"buttons": group} for group in chunk_buttons(buttons, 3)
                ]
            }
        }
        
        dispatcher.utter_message(text="Para indagar en el **turismo en la Comunitat Valenciana** y los datos que ofrece la **plataforma**, puedes: \n\n ▫️ **Inspeccionar** el portal libremente  \n ▫️ Pulsar cualquiera de estos **botones** para centrarte en un **aspecto concreto**", attachment=message)
        return []


class ActionButtonsVuelos(Action):
    def name(self) -> str:
        return "action_gva_vuelos"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        buttons = [
            {"title": "Visualizaciones Genéricas", "payload": "/gva_VG_vuelos"},
            {"title": "Soluciones IA", "payload": "/gva_MIA_vuelos"}
        ]
        message = {
            "type": "button-carousel-template",
            "payload": {
                "template_type": "generic",
                "elements": [
                    {"buttons": group} for group in chunk_buttons(buttons, 3)
                ]
            }
        }
        
        dispatcher.utter_message(text="Sobre **vuelos**, la plataforma ofrece información en forma de:  \n ▫️ **Visualizaciones genéricas**: representaciones gráficas de los datos disponibles  \n ▫️ **Soluciones IA y analítica avanzada**: predicciones a futuro y representaciones complejas \n\n ¿Cuál de ellas te interesa más? 🤔", attachment=message)
        return []


class ActionButtonsPM(Action):
    def name(self) -> str:
        return "action_gva_presencia_movilidad"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        buttons = [
            {"title": "Visualizaciones Genéricas", "payload": "/gva_VG_presencia_movilidad"},
            {"title": "Soluciones IA", "payload": "/gva_MIA_presencia_movilidad"}
        ]
        message = {
            "type": "button-carousel-template",
            "payload": {
                "template_type": "generic",
                "elements": [
                    {"buttons": group} for group in chunk_buttons(buttons, 3)
                ]
            }
        }
        
        dispatcher.utter_message(text="Los datos sobre **presencia y movilidad** pueden consultarse como:  \n ▫️ **Visualizaciones genéricas**: representaciones gráficas de los datos disponibles  \n ▫️ **Soluciones IA y analítica avanzada**: predicciones a futuro y representaciones complejas \n\n 💬 Pulsa el **botón** que prefieras para continuar", attachment=message)
        return []
    
    
class ActionButtonsCTgeneral(Action):
    def name(self) -> str:
        return "action_gva_comportamiento_turismo"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        buttons = [
            {"title": "Visualizaciones Genéricas", "payload": "/gva_VG_comportamiento_turismo"},
            {"title": "Soluciones IA", "payload": "/gva_MIA_comportamiento_turismo"}
        ]
        message = {
            "type": "button-carousel-template",
            "payload": {
                "template_type": "generic",
                "elements": [
                    {"buttons": group} for group in chunk_buttons(buttons, 3)
                ]
            }
        }
        
        dispatcher.utter_message(text="El **comportamiento del turismo** se analiza en el portal desde dos perspectivas:  \n ▫️ **Visualizaciones genéricas**: representaciones gráficas de los datos disponibles  \n ▫️ **Soluciones IA y analítica avanzada**: predicciones a futuro y representaciones complejas \n\n 🙂 Escoge el **botón** que más interese.", attachment=message)
        return []

    class ActionButtonsMIAvuelos(Action):
        def name(self) -> str:
            return "action_gva_MIA_vuelos"

        def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
            buttons = [
                {"title": "Oportunidad en marketing", "payload": "/gva_MIA_ventana_oportunidad"},
                {"title": "Influencia climática", "payload": "/gva_MIA_factor_climatico"}
            ]
            message = {
                "type": "button-carousel-template",
                "payload": {
                    "template_type": "generic",
                    "elements": [
                        {"buttons": group} for group in chunk_buttons(buttons, 3)
                    ]
                }
            }
            
            dispatcher.utter_message(text="Las **soluciones** 🤖 de inteligencia artificial y analítica avanzada disponibles sobre **vuelos** te ayudarán a: \n\n ▫️ Aprovechar los tiempos del journey del viajero para **campañas de marketing**  \n ▫️ Comprender cómo las **condiciones meteorológicas** repercuten sobre la movilidad aérea \n\n Selecciona la que quieras explorar:", attachment=message)
            return []
    


class ActionButtonsMIAPM(Action):
    def name(self) -> str:
        return "action_gva_MIA_presencia_movilidad"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        buttons = [
            {"title": "Previsión de visitantes", "payload": "/gva_MIA_predict_estancia_diurna"},
            {"title": "Patrones de comportamiento", "payload": "/gva_MIA_patrones_comportamiento"},
        ]
        message = {
            "type": "button-carousel-template",
            "payload": {
                "template_type": "generic",
                "elements": [
                    {"buttons": group} for group in chunk_buttons(buttons, 3)
                ]
            }
        }
        
        dispatcher.utter_message(text="En relación con la **presencia y la movilidad**, esta sección te permite 👀 explorar: \n\n ▫️ El número de **visitantes diarios** que se prevén, atendiendo a diversas variables  \n ▫️ Representaciones en **tres dimensiones** y **mapas de calor** que reflejan los **patrones** en el **comportamiento** turístico \n\n Haz clic en el **botón** que te interese para saber más.", attachment=message)
        return []