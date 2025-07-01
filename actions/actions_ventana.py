from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FollowupAction, ActiveLoop
from typing import Any, Text, Dict, List
from datetime import datetime
from rasa_sdk.forms import FormValidationAction
from .utils import chunk_buttons

#-----------------------------------------
#  FORM SUBMISSION
#-----------------------------------------

REQUIRED_SLOTS = ["destino_v", "origen_pais_v", "origen_ciudad_v", "date_filter_v", "consulta_v"]

class ActionSubmitBusquedasForm(Action):
    def name(self):
        return "action_submit_ventana_form"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        filled_slots = {slot: tracker.get_slot(slot) for slot in REQUIRED_SLOTS}

        tipo_consulta = tracker.get_slot("tipo_consulta_v")


        missing_slots = [slot for slot, value in filled_slots.items() if not value]

        if missing_slots:
            next_slot = missing_slots[0]
            dispatcher.utter_message(text=f"Necesitamos más información. Por favor, completa '{next_slot}' antes de continuar.")
            return [FollowupAction(f"action_ask_{next_slot}")]
        
        # Nombres bonitos para mensajes
        destino_pretty = filled_slots['destino_v'] if filled_slots['destino_v'] != "Todos" else "Comunitat Valenciana"
        origen_pais_pretty = filled_slots['origen_pais_v'] if filled_slots['origen_pais_v'] != "Todos" else "todos los mercados"
        origen_ciudad_pretty = filled_slots['origen_ciudad_v'] if filled_slots['origen_ciudad_v'] != "Todas" else "todas las ciudades"
        date_filter_pretty = filled_slots['date_filter_v'].lower() if filled_slots['date_filter_v'] != "Todos" else "todos los meses"

        text = ""

        if tipo_consulta == "Ventana de oportunidad desde un mercado de origen":
            text=f"Ventana de oportunidad promedio desde {origen_pais_pretty} a {destino_pretty} en {date_filter_pretty}."

        elif tipo_consulta == "Ventana de oportunidad desde una ciudad de origen":
            text=f"Ventana de oportunidad promedio desde {origen_ciudad_pretty} a {destino_pretty} en {date_filter_pretty}."

        elif tipo_consulta == "Ranking de mercados de origen por ventana de oportunidad":
            text=f"Ranking de mercados de origen según la ventana de oportunidad promedio a {destino_pretty} en {date_filter_pretty}."

        elif tipo_consulta == "Ranking de ciudades de origen por ventana de oportunidad":
            text=f"Ranking ciudades de origen de {origen_pais_pretty} según la ventana de oportunidad promedio a {destino_pretty} en {date_filter_pretty}"
    
        
        confirmation_message = (f"⚠️ Verifica tu consulta:\n\n") + text

        buttons = [
            {"title": "✅ Continuar", "payload": "/confirmar_envio"},
            {"title": "❌ Corregir", "payload": "/corregir_envio"}
        ]

        dispatcher.utter_message(text=confirmation_message, buttons=buttons)
        return []

#--------------------------------------
#  SLOT TIPO_CONSULTA
#--------------------------------------

VALID_TIPOS_CONSULTA = ['Ranking de mercados de origen por ventana de oportunidad', 'Ranking de ciudades de origen por ventana de oportunidad' ,'Ventana de oportunidad desde un mercado de origen', 'Ventana de oportunidad desde una ciudad de origen']

class ActionAskTipoConsulta(Action):
    def name(self) -> str:
        return "action_ask_tipo_consulta_v"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        dispatcher_text = (
            f"🙋🏻‍♀️ ¿Qué tipo de consulta quieres realizar? Selecciona un botón:\n\n"
        )

        message = {
            "type": "text-carousel-template",
            "payload": {
                "template_type": "generic",
                "elements": [
                    # {
                    #     "title": "Ventana de oportunidad",
                    #     "text": """Ventana de oportunidad desde un mercado o ciudad de origen para un mes específico.
                    #                 --- 
                    #                 _Se calcula el promedio de la ventana de oportunidad para el mes seleccionado._""",
                    #     "buttons": [
                    #         {
                    #             "title": "Ventana de oportunidad desde un mercado de origen",
                    #             "payload": "Ventana de oportunidad desde un mercado de origen"  
                    #         },
                    #         {
                    #             "title": "Ventana de oportunidad desde una ciudad de origen",
                    #             "payload": "Ventana de oportunidad desde una ciudad de origen"  
                    #         }
                    #     ]
                    # },
                    # {
                    #     "title": "Ranking según la ventana de oportunidad",
                    #     "text": """Ranking de mercados o ciudades de origen según la ventana de oportunidad en un mes específico. 
                    #                 ---
                    #                 _Se calcula el promedio de la ventana de oportunidad para el mes seleccionado._""",
                    #     "buttons": [
                    #         {
                    #             "title": "Ranking de mercados de origen por ventana de oportunidad",
                    #             "payload": "Ranking de mercados de origen por ventana de oportunidad"  
                    #         },
                    #         {
                    #             "title": "Ranking de ciudades de origen por ventana de oportunidad",
                    #             "payload": "Ranking de ciudades de origen por ventana de oportunidad"  
                    #         }
                    #     ]
                    # },
                    {
                        "title": "Consulta abierta IA",
                        "text": """Consulta abierta sobre la ventana de oportunidad asistida por un agente IA. 
                                    Si no especificas el año, se considerarán todos los años disponibles. 
                                    ---
                                    ⚠️ _Los resultados generados por IA generativa pueden contener imprecisiones. Verifica la información antes de tomar decisiones._""",
                        "buttons": [
                            {
                                "title": "Consulta IA",
                                "payload": "Consulta IA"  
                            }
                        ]
                    }
                ]
            }
        }

        buttons= [{"title": "❌ Salir","payload": "❌ Salir"}]

        dispatcher.utter_message(text= dispatcher_text, attachment=message, buttons=buttons)
        return []


#--------------------------------------
#  SLOT DESTINO
#--------------------------------------

VALID_DESTINOS = ['Valencia', 'Alicante', 'Castellón', 'Todos']

class ActionAskDestino(Action):
    def name(self) -> str:
        return "action_ask_destino_v"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        print("Tipo de consulta:", tracker.get_slot("tipo_consulta_v"))
        buttons = [
            {"title": "Valencia", "payload": "Valencia"},
            {"title": "Alicante", "payload": "Alicante"},
            {"title": "Castellón", "payload": "Castellón"},
            {"title": "Todos", "payload": "Todos"},
            {"title": "❌ Salir", "payload": "❌ Salir"}
        ]

        message = {
            "type": "button-carousel-template",
            "payload": {
                "template_type": "generic",
                "elements": [
                    {"buttons": group} for group in chunk_buttons(buttons, 5)
                ]
            }
        }
        
        dispatcher.utter_message(text="🏝️ ¿Con qué destino quieres trabajar? Selecciona una opción:", attachment=message)
        return []
        

#--------------------------------------
#  SLOTS MERCADO ORIGEN Y CIUDAD
#--------------------------------------

# Quizás podríamos coger de manera dinámica los países y ciudades + fechas desde Snowflake ¿?

VALID_PAISES = [
    "Todos","España", "Francia", "Reino Unido", "Italia", "Irlanda", "Portugal", "Alemania",
    "Noruega", "Suecia", "Finlandia", "Bélgica", "Países Bajos", "Dinamarca"
]

VALID_PAISES_CIUDADES= {
        'Todas': ["Todas"],
        'Alemania': ["Altenburg", "Ansbach", "Aquisgrán", "Aschaffenburg", "Augsburgo", "Bamberg", "Bayreuth", "Berlin", "Bielefeld", "Bochum", "Bonn", "Bremen", "Bremerhaven", "Chemnitz", "Coblenza", "Cochstedt", "Colonia", "Cottbus", "Cuxhaven", "Dortmund", "Dresde", "Duisburg", "Dusseldorf", "Egelsbach", "Eisenach", "Emden", "Erfurt", "Essen", "Flensburg", "Frankfurt", "Frankfurt an der Oder", "Friburgo", "Friedrichshafen", "Fritzlar", "Fuerstenfeldbruch", "Fulda", "Gelsenkirchen", "Gera", "Goettingen", "Greifswald", "Guetersloh", "Hagen", "Hamburgo", "Hamburgo/Finkenwerder", "Hamm", "Hanover", "Heide-Buesum", "Helgoland", "Heringsdorf", "Holf", "Illesheim", "Ingolstadt", "Jena", "Karlsruhe", "Kassel", "Kiel", "Lahr", "Lindau", "Lübeck", "Lueneburg", "Magnucia", "Mannheim", "Memmingen", "Minden", "Muenster", "Munich", "Neumuenster", "Norden", "Norderney", "Nuremberg", "Oberhausen", "Offenburg", "Oldernburg", "Paderborn", "Passau", "Peenemuende", "Ramstein", "Ratisbona", "Rechlin", "Riesa", "Rostock-Laage" "Saarbrucken", "Schkeuditz", "Schoena", "Schwerin", "Siegburg", "Solingen", "Spangdahlem", "Stendal", "Stralsund", "Straubing", "Suttgart", "Suhl", "Ulm", "Varrelbusch", "Wangerooge", "Warnemunde", "Westerland", "Wiesbaden", "Wilhelmshaven", "Wismar", "Worms", "Wuerzburg", "Wuppertal", "Wyk", "Zweibrucken"], 
        'Noruega': ["Aalesund", "Alta", "Andenes", "Bardufoss", "Barsfjord", "Bergen",  "Berlevag", "Bodo", "Bronnoysund", "Floro", "Forde", "Hammerfest", "Harstad-Narvik", "Hasvik", "Haugesund", "Honningsvag", "Kirkenes", "Kristiansand", "Kristiansund", "Lakselv", "Leknes", "Longyearbyen", "Mehamn", "Mo i Rana", "Molde", "Mosjoen", "Namsos", "Orland", "Orsta-Volda", "Oslo", "Roervik", "Roros" "Rost", "Sandane", "Sandnessjoen", "Sogndal", "Sorkjosen", "Stavanger", "Stokmarknes", "Stord", "Svolvaer", "Tromso", "Trondheim" "Vadso", "Vardoe"], 
        'Suecia': ["Angelholm", "Arvidsjaur", "Estocolmo", "Gallivare", "Gotemburgo", "Hagfors", "Halmstad", "Hemavan", "Kalmar", "Kiruna", "Kramfors", "Kristianstad", "Linkoping", "Lulea", "Lycksele", "Malmo", "Mora", "Norrkoping", "Orebro", "Ornskoldsvik", "Pajala", "Ronneby", "Skelleftea", "Sundsvall", "Sveg", "Torsby", "Umea", "Vaxjo", "Vilhelmina", "Visby"], 
        'Francia': ["Ajaccio", "Aurillac", "Bastia", "Bergerac", "Beziers", "Biarritz", "Brest", "Brive-La-Gaillarde", "Burdeos", "Caen", "Calvi", "Carcasona", "Castres", "Chambery", "Clermont-Ferrand", "Deauville", "Dole", "Estrasburgo", "Figari", "Goin", "Grenoble", "La Rochelle", "Le Puy", "Lille", "Limoges", "Lorient", "Lourdes", "Lyon", "Marsella", "Montpellier", "Nantes", "Nimes", "Niza", "Paris", "Pau", "Perpiñán", "Poitiers", "Rennes", "Rodez", "Saint Nazaire", "Toulon", "Toulouse"], 
        'Portugal': ["Bragança", "Faro", "Funchal", "Horta (Azores)", "Isla de Corvo (Azores)", "Isla de Flores (Azores)", "Isla de Pico (Azores)", "Isla Graciosa (Azores)", "Isla Sao Jorge", "Lisboa", "Oporto", "Ponta Delgada (Azores)", "Portimao", "Porto Santo (Madeira)", "Santa María (Azores)", "Terceira", "Vila Real", "Viseu"],
        'Finlandia': ["Helsinki", "Ivalo", "Joensuu", "Jyvaskyla", "Kajaani", "Kemi", "Kittila", "Kronoby", "Kuopio", "Kuusamo", "Lappeenranta", "Mariehamn", "Oulu", "Rovaniemi", "Tampere", "Turku", "Vaasa"], 
        'España': ["Alicante", "Almeria", "Asturias", "Badajoz", "Barcelona", "Bilbao", "Burgos", "Castellon De La Plana", "Corvera", "Fuerteventura", "Girona", "Granada", "Ibiza", "Jerez De La Frontera", "La Coruña", "Lanzarote", "Las Palmas", "León", "Lleida", "Logroño", "Madrid", "Malaga", "Melilla", "Menorca", "Palma Mallorca", "Pamplona", "Reus", "Salamanca", "San Sebastian", "San Sebastian de la Gomera", "Santa Cruz De la Palma", "Santander", "Santiago De Compostela", "Seo De Urgel", "Sevilla", "Tenerife", "Valencia", "Valladolid", "Valverde", "Vigo", "Vitoria", "Zaragoza"], 
        'Reino Unido': ["Aberdeen", "Alderney", "Barra", "Belfast", "Benbecula", "Birmingham", "Bournemouth", "Bristol", "Campbeltown", "Cardiff", "Derry", "Dundee", "Durham Tees Valley", "Eday", "Edimburgo", "Exeter", "Glasgow", "Guernsey", "Inverness", "Isla de Man", "Isla Shetland", "Islay", "Jersey",  "Kirkwall", "Leeds", "Liverpool", "Londres", "Manchester", "Newcastle", "Newquay", "North Ronaldsay", "Norwich", "Nottingham", "Papa Westray", "Sanday", "Southampton", "Stornoway Outer Stat Hébridas", "Stronsay", "Tiree Inner Hebrides", "Westray", "Wick"], 
        'Italia': ["Alguero", "Ancona", "Bari", "Bolonia", "Bolzano", "Brindisi", "Cagliari", "Catania", "Comiso", "Crotone", "Cuneo", "Florencia", "Foggia", "Forli", "Génova", "Lamezia-Terme", "Lampedusa", "Milan", "Napoles", "Olbia", "Palermo", "Pantelleria", "Perugia", "Pescara", "Pisa", "Reggio Calabria", "Rimini", "Roma", "Trapani", "Trieste", "Turin", "Venecia", "Verona"],
        'Países Bajos': ["Amsterdam", "Eindhoven", "Groningen" "Maastricht", "Rotterdam"], 
        'Dinamarca': ["Aalborg", "Aarhus", "Billund", "Bornholm", "Copenhagen", "Esbjerg", "Isla de Laeso", "Karup", "Sonderborg"], 
        'Bélgica': ["Bruselas", "Lieja", "Ostende"],         
        'Irlanda': ["Condado de Kerry", "Cork", "Donegal", "Dublin", "Knock", "Shannon"]
        
}



ALL_CITIES = list({city for cities in VALID_PAISES_CIUDADES.values() for city in cities})
ALL_CITIES.append("Todas")

class ActionAskOrigenPais(Action):
    def name(self):
        return "action_ask_origen_pais_v"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        tipo_consulta = tracker.get_slot("tipo_consulta_v")

        buttons = [{"title": "❌ Salir", "payload": "❌ Salir"}] + [{"title": pais, "payload": pais} for pais in VALID_PAISES]

        message = {
            "type": "button-carousel-template",
            "payload": {
                "template_type": "generic",
                "elements": [
                    {"buttons": group} for group in chunk_buttons(buttons, 4)
                ]
            }
        }

        if tipo_consulta == "Ranking de mercados de origen por ventana de oportunidad":
            
            return [
                    SlotSet("origen_pais_v", "Todos"),
                    SlotSet("origen_ciudad_v", "Todas"),
                    FollowupAction("ventana_form"),
                    ]

        else:
            dispatcher.utter_message(text="🌍 Selecciona el mercado de origen:", attachment=message)
            
            return []
        

class ActionAskOrigenCiudad(Action):
    def name(self):
        return "action_ask_origen_ciudad_v"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        tipo_consulta = tracker.get_slot("tipo_consulta_v")
        origen_pais_v = tracker.get_slot("origen_pais_v")

        if origen_pais_v:
            origen_pais_v = origen_pais_v.strip()
            if origen_pais_v.lower() == "todos":
                available_cities = ALL_CITIES
            elif origen_pais_v in VALID_PAISES_CIUDADES: 
                available_cities = VALID_PAISES_CIUDADES[origen_pais_v] + ["Todas"]
            else:
                available_cities = ALL_CITIES
        else:
            available_cities = ALL_CITIES

        buttons = [{"title": "❌ Salir", "payload": "❌ Salir"}] + [{"title": city, "payload": city} for city in available_cities]


        message = {
            "type": "button-carousel-template",
            "payload": {
                "template_type": "generic",
                "elements": [
                    {"buttons": group} for group in chunk_buttons(buttons, 4)
                ]
            }
        }
        
        if tipo_consulta == "Ranking de ciudades de origen por ventana de oportunidad":
            return [
                    SlotSet("origen_ciudad_v", "Todas"),
                    SlotSet("consulta_v", tipo_consulta),
                    FollowupAction("ventana_form"),
                    ]
        
        elif tipo_consulta in ["Ventana de oportunidad desde un mercado de origen"]:
            return [
                    SlotSet("origen_ciudad_v", "Todas"),
                    FollowupAction("ventana_form"),
                    ]

        else:
            dispatcher.utter_message(text="🏙️ Selecciona la ciudad de origen:",attachment=message)
            return []
        

#--------------------------------------
#  SLOT FECHA
#--------------------------------------
VALID_DATES = [
    "Todos los meses",
    "Enero", "Febrero", "Marzo", "Abril",
    "Mayo", "Junio", "Julio", "Agosto",
    "Septiembre", "Octubre", "Noviembre", "Diciembre",
]

class ActionAskDateFilter(Action):
    def name(self):
        return "action_ask_date_filter_v"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        tipo_consulta = tracker.get_slot("tipo_consulta_v")
        
        buttons = [{"title": "❌ Salir", "payload": "❌ Salir"}] + [{"title": date, "payload": date} for date in VALID_DATES]

        message = {
            "type": "button-carousel-template",
            "payload": {
                "template_type": "generic",
                "elements": [
                    {"buttons": group} for group in chunk_buttons(buttons, 4)
                ]
            }
        }

        dispatcher.utter_message(text="📅 Selecciona un mes:", attachment=message)
        return []

    
#--------------------------------------
#  SLOT CONSULTA
#--------------------------------------

class ActionAskConsulta(Action):
    def name(self):
        return "action_ask_consulta_v"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        tipo_consulta = tracker.get_slot("tipo_consulta_v")

        if "Ranking" in tipo_consulta or "Ventana" in tipo_consulta:
            return [
                SlotSet("consulta_v", tipo_consulta),
                FollowupAction("ventana_form"),
                ]
        
        else:
            buttons = [
                {"title": "❌ Salir", "payload": "❌ Salir"}
            ]
            dispatcher.utter_message(text="📌 Escribe tu consulta acerca de la ventana de oportunidad", buttons=buttons)
            return []

#--------------------------------------
#  CONSULTA IA
#--------------------------------------

class ActionAskQueryV(Action):
    def name(self):
        return "action_ask_user_query_v"

    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message(text="📝 Escribe tu consulta para el agente IA.")

        return [
            SlotSet("scope", "FC_LUC_OPPORTUNITY_WINDOW"),
        ]

#--------------------------------------
#  VALIDATE FORM
#--------------------------------------

class ValidateVentanaForm(FormValidationAction):
    def name(self) -> str:
        return "validate_ventana_form"
    
    async def validate_tipo_consulta_v(
        self, 
        slot_value: str, 
        dispatcher: CollectingDispatcher, 
        tracker: Tracker, 
        domain
    ) -> Dict[Text, Any]:
        """Validate tipo_consulta_v value."""

        print("Validating tipo_consulta_v:", slot_value)
        print("Tracker text", tracker.latest_message.get("text"))
        
        if slot_value and slot_value in VALID_TIPOS_CONSULTA:
            return {"tipo_consulta_v": slot_value}
        
        else:
            dispatcher.utter_message(
                text="Opción no válida. Por favor, haz clic en el botón con la opción deseada deseada."
            )
            return {"tipo_consulta_v": None}

    async def validate_destino_v(
        self, 
        slot_value: str, 
        dispatcher: CollectingDispatcher, 
        tracker: Tracker, 
        domain
    ) -> Dict[Text, Any]:
        """Validate destino_v value."""
        print("Validating destino_v:", slot_value)
        
        if slot_value and slot_value in VALID_DESTINOS:
            return {"destino_v": slot_value}
        
        else:
            dispatcher.utter_message(
                text="Opción no válida. Por favor, haz clic en el botón con la opción deseada deseada."
            )
            return {"destino_v": None}
    
    async def validate_origen_pais_v(
        self, 
        slot_value: str, 
        dispatcher: CollectingDispatcher, 
        tracker: Tracker, 
        domain
    ) -> Dict[Text, Any]:
        """Validate origen_pais_v value."""

        print("Validating origen_pais_v:", slot_value)
        
        if slot_value and slot_value in VALID_PAISES and slot_value != "Todos":
            return {"origen_pais_v": slot_value}
        
        elif slot_value and slot_value == "Todos":
            return {"origen_pais_v": slot_value, "origen_ciudad_v": "Todas"}
            
        
        else:
            dispatcher.utter_message(
                text="Opción no válida. Por favor, haz clic en el botón con la opción deseada deseada."
            )
            return {"origen_pais_v": None}
    
    async def validate_origen_ciudad_v(
        self, 
        slot_value: str, 
        dispatcher: CollectingDispatcher, 
        tracker: Tracker, 
        domain
    ) -> Dict[Text, Any]:
        """Validate origen_ciudad_v value."""

        print("Validating origen_ciudad_v:", slot_value)
        
        if slot_value and any(slot_value in cities for cities in VALID_PAISES_CIUDADES.values()):
            return {"origen_ciudad_v": slot_value}
        
        else:
            dispatcher.utter_message(
                text="Opción no válida. Por favor, haz clic en el botón con la opción deseada deseada."
            )
            return {"origen_ciudad_v": None}
    
    async def validate_date_filter_v(
        self, 
        slot_value: str, 
        dispatcher: CollectingDispatcher, 
        tracker: Tracker, 
        domain
    ) -> Dict[Text, Any]:
        """Validate date_filter_v value."""

        print("Validating date_filter_v:", slot_value)
        
        if slot_value in VALID_DATES:
            return {"date_filter_v": f"{slot_value} 2024" if slot_value != "Todos los meses" else slot_value}
            
        
        else:
            dispatcher.utter_message(
                text="Opción no válida. Por favor, haz clic en el botón con la opción deseada deseada."
            )
            return {"date_filter_v": None}
    
    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
        ) -> List:
        
        if '❌ Salir' in tracker.latest_message.get("text"):

            dispatcher.utter_message(text="Has cancelado el formulario.\n Haz clic en **Análisis de Datos** para comenzar de nuevo.")


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
        
        elif 'Consulta IA' in tracker.latest_message.get("text"):

            return [
                ActiveLoop(None),
                SlotSet("requested_slot", None),
                SlotSet("tipo_consulta_v", None),
                SlotSet("destino_v", None),
                SlotSet("origen_pais_v", None),
                SlotSet("origen_ciudad_v", None),
                SlotSet("date_filter_v", None),
                SlotSet("consulta_v", None),
                FollowupAction("action_ask_user_query_v")
            ] 
        
        else:
            # RASA standard logic
            return await super().run(dispatcher, tracker, domain)