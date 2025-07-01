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

REQUIRED_SLOTS = ["destino_b", "origen_pais_b", "origen_ciudad_b", "anno_b", "date_filter", "consulta"]

class ActionSubmitBusquedasForm(Action):
    def name(self):
        return "action_submit_busquedas_form"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        filled_slots = {slot: tracker.get_slot(slot) for slot in REQUIRED_SLOTS}
        missing_slots = [slot for slot, value in filled_slots.items() if not value]

        tipo_consulta = tracker.get_slot("tipo_consulta")

        if missing_slots:
            next_slot = missing_slots[0]
            dispatcher.utter_message(text=f"Necesitamos más información. Por favor, completa '{next_slot}' antes de continuar.")
            return [FollowupAction(f"action_ask_{next_slot}")]
        
        # Nombres bonitos para mensajes
        destino_pretty = filled_slots['destino_b'] if filled_slots['destino_b'] != "Todos" else "Comunitat Valenciana"
        origen_pais_pretty = filled_slots['origen_pais_b'] if filled_slots['origen_pais_b'] != "Todos" else "todos los mercados"
        origen_ciudad_pretty = filled_slots['origen_ciudad_b'] if filled_slots['origen_ciudad_b'] != "Todas" else "todas las ciudades"
        date_filter_pretty = date_filter_pretty = (f"{filled_slots['date_filter'].lower()} {filled_slots['anno_b']}" if filled_slots['date_filter'] != "Todos" else f"todos los meses {filled_slots['anno_b']}")

        text = ""

        if tipo_consulta == "Ventana media y búsquedas desde un mercado de origen":
            text=f"Ventana media y número de búsquedas totales desde {origen_pais_pretty} a {destino_pretty} en {date_filter_pretty}."

        elif tipo_consulta == "Ventana media y búsquedas desde una ciudad de origen":
            text=f"Ventana media y número de búsquedas totales desde {origen_ciudad_pretty} ({origen_pais_pretty}) a {destino_pretty} en {date_filter_pretty}."

        elif tipo_consulta == "Ranking de mercados de origen por ventana media":
            text=f"Ranking de mercados de origen según la ventana media a {destino_pretty} en {date_filter_pretty}."

        elif tipo_consulta == "Ranking de ciudades de origen por ventana media":
            text=f"Ranking ciudades de origen de {origen_pais_pretty} según la ventana media a {destino_pretty} en {date_filter_pretty}"

        elif tipo_consulta == "Búsquedas diarias desde un mercado de origen":
            text=f"Número de búsquedas diarias promedio desde {origen_pais_pretty} a {destino_pretty} en {date_filter_pretty}."

        elif tipo_consulta == "Búsquedas diarias desde una ciudad de origen":
            text=f"Número de búsquedas diarias promedio desde {origen_ciudad_pretty} a {destino_pretty} en {date_filter_pretty}."

        elif tipo_consulta == "Ranking de mercados de origen por ventana media diarias":
            text=f"Ranking de mercados de origen según las búsquedas al día promedio a {destino_pretty} en {date_filter_pretty}."

        elif tipo_consulta == "Ranking de ciudades de origen por ventana media diarias":
            text=f"El ranking ciudades de origen de de {origen_pais_pretty} según las búsquedas al día promedio a {destino_pretty} en {date_filter_pretty}"
    
        
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

VALID_TIPOS_CONSULTA = ['Ranking de mercados de origen por ventana media diarias', 
                        'Ranking de ciudades de origen por ventana media diarias' ,
                        'Búsquedas diarias desde un mercado de origen', 
                        'Búsquedas diarias desde una ciudad de origen', 
                        'Ventana media y búsquedas desde un mercado de origen',
                        'Ventana media y búsquedas desde una ciudad de origen',
                        'Ranking de mercados de origen por ventana media',
                        'Ranking de ciudades de origen por ventana media']

class ActionAskTipoConsultaB(Action):
    def name(self) -> str:
        return "action_ask_tipo_consulta"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        buttons = [{"title": tipo, "payload": tipo} for tipo in VALID_TIPOS_CONSULTA]
        buttons.append({"title": "❌ Salir", "payload": "❌ Salir"})

        dispatcher_text = (
            f"🙋🏻‍♀️ ¿Qué tipo de consulta quieres realizar? Selecciona un botón:\n\n"
        )

        message = {
            "type": "text-carousel-template",
            "payload": {
                "template_type": "generic",
                "elements": [
                    {
                        "title": "Ventana Media & Búsquedas Previstas",
                        "text": """Ventana de oportunidad media y búsquedas previstas asociadas a esa ventana, desde un mercado o ciudad de origen, para un mes específico. 
                                    ---
                                    _¿Cuántas búsquedas se esperan para la ventana media de un mercado o ciudad en un determinado mes?_""",
                        "buttons": [
                            {
                                "title": "Desde un mercado de origen",
                                "payload": "Ventana media y búsquedas desde un mercado de origen"  
                            },
                            {
                                "title": "Desde una ciudad de origen",
                                "payload": "Ventana media y búsquedas desde una ciudad de origen"  
                            }
                        ]
                    },
                     {
                        "title": "Ranking según la ventana media",
                        "text": """Ranking de mercados o ciudades de origen por ventana media, con sus correspondientes búsquedas previstas totales, para un mes específico.
                                    ---
                                    _¿Qué países tienen mayor ventana media y qué búsquedas se esperan en un determinado mes?_""",
                        "buttons": [
                            {
                                "title": "Ranking de mercados de origen",
                                "payload": "Ranking de mercados de origen por ventana media"  
                            },
                            {
                                "title": "Ranking de ciudades de origen",
                                "payload": "Ranking de ciudades de origen por ventana media"  
                            }
                        ]
                    },

                    # {
                    #     "title": "Búsquedas diarias previstas",
                    #     "text": """Número de búsquedas diarias previstas desde un mercado o ciudad de origen para un mes específico. 
                    #                 ---
                    #                 _Se calcula el promedio de las búsquedas diarias para el mes seleccionado._""",
                    #     "buttons": [
                    #         {
                    #             "title": "Búsquedas diarias desde un mercado de origen",
                    #             "payload": "Búsquedas diarias desde un mercado de origen"  
                    #         },
                    #         {
                    #             "title": "Búsquedas diarias desde una ciudad de origen",
                    #             "payload": "Búsquedas diarias desde una ciudad de origen"  
                    #         }
                    #     ]
                    # },
                    # {
                    #     "title": "Ranking según el número de búsquedas diarias previstas",
                    #     "text": """Ranking de mercados o ciudades de origen por búsquedas diarias previstas para un mes específico. 
                    #                 ---
                    #                 _Se calcula el promedio de las búsquedas diarias para el mes seleccionado._""",
                    #     "buttons": [
                    #         {
                    #             "title": "Ranking de mercados de origen por ventana media diarias",
                    #             "payload": "Ranking de mercados de origen por ventana media diarias"  
                    #         },
                    #         {
                    #             "title": "Ranking de ciudades de origen por ventana media diarias",
                    #             "payload": "Ranking de ciudades de origen por ventana media diarias"  
                    #         }
                    #     ]
                    # },
                    {
                        "title": "Consulta abierta IA",
                        "text": """Consulta abierta sobre la ventana media y búsquedas previstas asistida por un agente IA. 
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

class ActionAskDestinoB(Action):
    def name(self) -> str:
        return "action_ask_destino_b"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        print("Tipo de consulta:", tracker.get_slot("tipo_consulta"))
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
        'Países Bajos': ["Amsterdam", "Eindhoven", "Groningen", "Maastricht", "Rotterdam"], 
        'Dinamarca': ["Aalborg", "Aarhus", "Billund", "Bornholm", "Copenhagen", "Esbjerg", "Isla de Laeso", "Karup", "Sonderborg"], 
        'Bélgica': ["Bruselas", "Lieja", "Ostende"],         
        'Irlanda': ["Condado de Kerry", "Cork", "Donegal", "Dublin", "Knock", "Shannon"]
        
}



ALL_CITIES = list({city for cities in VALID_PAISES_CIUDADES.values() for city in cities})
ALL_CITIES.append("Todas")

class ActionAskOrigenPaisB(Action):
    def name(self):
        return "action_ask_origen_pais_b"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        tipo_consulta = tracker.get_slot("tipo_consulta")

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

        if tipo_consulta in ["Ranking de mercados de origen por ventana media","Ranking de mercados de origen por ventana media diarias"]:
            
            return [
                    SlotSet("origen_pais_b", "Todos"),
                    SlotSet("origen_ciudad_b", "Todas"),
                    FollowupAction("busquedas_form"),
                    ]

        elif tipo_consulta in ['Ranking de ciudades de origen por ventana media diarias', 'Ranking de ciudades de origen por ventana media']:
            dispatcher.utter_message(text="🌍 Selecciona el mercado de origen para elegir sus ciudades:", attachment=message)
            
            return []

        else:
            dispatcher.utter_message(text="🌍 Selecciona el mercado de origen:", attachment=message)
            
            return []
        

class ActionAskOrigenCiudadB(Action):
    def name(self):
        return "action_ask_origen_ciudad_b"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        tipo_consulta = tracker.get_slot("tipo_consulta")
        origen_pais_b = tracker.get_slot("origen_pais_b")

        if origen_pais_b:
            origen_pais_b = origen_pais_b.strip()
            if origen_pais_b.lower() == "todos":
                available_cities = ALL_CITIES
            elif origen_pais_b in VALID_PAISES_CIUDADES: 
                available_cities = VALID_PAISES_CIUDADES[origen_pais_b] + ["Todas"]
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
        
        if tipo_consulta in ["Ranking de ciudades de origen por ventana media", "Ranking de ciudades de origen por ventana media diarias"]:
            return [
                    SlotSet("origen_ciudad_b", "Todas"),
                    SlotSet("consulta", tipo_consulta),
                    FollowupAction("busquedas_form"),
                    ]
        
        elif tipo_consulta in ["Ventana media y búsquedas desde un mercado de origen","Búsquedas diarias desde un mercado de origen"]:
            return [
                    SlotSet("origen_ciudad_b", "Todas"),
                    FollowupAction("busquedas_form"),
                    ]

        else:
            dispatcher.utter_message(text="🏙️ Selecciona la ciudad de origen:",attachment=message)
            return []

#--------------------------------------
#  SLOT AÑO
#--------------------------------------
VALID_ANNOS = ["2024", "2025"]

class ActionAskAnnoB(Action):
    def name(self):
        return "action_ask_anno_b"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        buttons = [{"title": "❌ Salir", "payload": "❌ Salir"}] + [{"title": anno, "payload": anno} for anno in VALID_ANNOS]

        message = {
            "type": "button-carousel-template",
            "payload": {
                "template_type": "generic",
                "elements": [
                    {"buttons": group} for group in chunk_buttons(buttons, 3)
                ]
            }
        }

        dispatcher.utter_message(text="📅 Selecciona un año:", attachment=message)
        return []


#--------------------------------------
#  SLOT MES
#--------------------------------------
VALID_DATES = [
    "Todos los meses",
    "Enero", "Febrero", "Marzo", "Abril",
    "Mayo", "Junio", "Julio", "Agosto",
    "Septiembre", "Octubre", "Noviembre", "Diciembre",  
]

class ActionAskDateFilterB(Action):
    def name(self):
        return "action_ask_date_filter"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
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

class ActionAskConsultaB(Action):
    def name(self):
        return "action_ask_consulta"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        tipo_consulta = tracker.get_slot("tipo_consulta")

        if "ranking" in tipo_consulta.lower() or "búsquedas" in tipo_consulta.lower():
            return [
                SlotSet("consulta", tipo_consulta),
                FollowupAction("busquedas_form"),
                ]
        
        else:
            buttons = [
                {"title": "❌ Salir", "payload": "❌ Salir"}
            ]
            dispatcher.utter_message(text="📌 Escribe tu consulta acerca del número de búsquedas", buttons=buttons)
            return []

#--------------------------------------
#  CONSULTA IA
#--------------------------------------

class ActionAskQueryB(Action):
    def name(self):
        return "action_ask_user_query_b"

    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message(text="📝 Escribe tu consulta para el agente IA.")

        return [
            SlotSet("scope", "FC_LUC_SEARCHS_PREDICTION"),
        ]

class ValidateBusquedasForm(FormValidationAction):
    def name(self) -> str:
        return "validate_busquedas_form"
    
    async def validate_tipo_consulta(
        self, 
        slot_value: str, 
        dispatcher: CollectingDispatcher, 
        tracker: Tracker, 
        domain
    ) -> Dict[Text, Any]:
        """Validate tipo_consulta value."""
        
        if slot_value and slot_value in VALID_TIPOS_CONSULTA:
            return {"tipo_consulta": slot_value}
        
        else:
            dispatcher.utter_message(
                text="Opción no válida. Por favor, haz clic en el botón con la opción deseada."
            )
            return {"tipo_consulta": None}

    async def validate_destino_b(
        self, 
        slot_value: str, 
        dispatcher: CollectingDispatcher, 
        tracker: Tracker, 
        domain
    ) -> Dict[Text, Any]:
        """Validate destino_b value."""
        print("Validating destino_b:", slot_value)
        
        if slot_value and slot_value in VALID_DESTINOS:
            return {"destino_b": slot_value}
        
        else:
            dispatcher.utter_message(
                text="Opción no válida. Por favor, haz clic en el botón con la opción deseada."
            )
            return {"destino_b": None}
    
    async def validate_origen_pais_b(
        self, 
        slot_value: str, 
        dispatcher: CollectingDispatcher, 
        tracker: Tracker, 
        domain
    ) -> Dict[Text, Any]:
        """Validate origen_pais_b value."""

        print("Validating origen_pais_b:", slot_value)
        
        if slot_value and slot_value in VALID_PAISES and slot_value != "Todos":
            return {"origen_pais_b": slot_value}
        
        elif slot_value and slot_value == "Todos":
            return {"origen_pais_b": slot_value, "origen_ciudad_b": "Todas"}
            
        
        else:
            dispatcher.utter_message(
                text="Opción no válida. Por favor, haz clic en el botón con la opción deseada."
            )
            return {"origen_pais_b": None}
    
    async def validate_origen_ciudad_b(
        self, 
        slot_value: str, 
        dispatcher: CollectingDispatcher, 
        tracker: Tracker, 
        domain
    ) -> Dict[Text, Any]:
        """Validate origen_ciudad_b value."""

        print("Validating origen_ciudad_b:", slot_value)
        
        if slot_value and any(slot_value in cities for cities in VALID_PAISES_CIUDADES.values()):
            return {"origen_ciudad_b": slot_value}
        
        else:
            dispatcher.utter_message(
                text="Opción no válida. Por favor, haz clic en el botón con la opción deseada."
            )
            return {"origen_ciudad_b": None}
    
    async def validate_anno_b(
        self, 
        slot_value: str, 
        dispatcher: CollectingDispatcher, 
        tracker: Tracker, 
        domain
    ) -> Dict[Text, Any]:
        """Validate anno_b value."""

        print("Validating anno_b:", slot_value)
        
        if slot_value and any(slot_value in anno for anno in VALID_ANNOS):
            return {"anno_b": slot_value}
        
        else:
            dispatcher.utter_message(
                text="Opción no válida. Por favor, haz clic en el botón con la opción deseada."
            )
            return {"anno_b": None}
    
    async def validate_date_filter(
        self, 
        slot_value: str, 
        dispatcher: CollectingDispatcher, 
        tracker: Tracker, 
        domain
    ) -> Dict[Text, Any]:
        """Validate date_filter value."""

        print("Validating date_filter:", slot_value)

        anno = tracker.get_slot("anno_b")
        
        if slot_value in VALID_DATES:
            return {"date_filter": f"{slot_value}" if slot_value != "Todos los meses" else slot_value}
            
        
        else:
            dispatcher.utter_message(
                text="Opción no válida. Por favor, haz clic en el botón con la opción deseada."
            )
            return {"date_filter": None}
    
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
            SlotSet("tipo_consulta", None),
            SlotSet("destino_b", None),
            SlotSet("origen_pais_b", None),
            SlotSet("origen_ciudad_b", None),
            SlotSet("anno_b", None),
            SlotSet("date_filter", None),
            SlotSet("consulta", None),
            FollowupAction("action_listen") 
            ]
        
        elif 'Consulta IA' in tracker.latest_message.get("text"):

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
                FollowupAction("action_ask_user_query_b")
            ] 
        
        else:
            # RASA standard logic
            return await super().run(dispatcher, tracker, domain)