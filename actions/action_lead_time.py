from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, ActiveLoop, FollowupAction
from rasa_sdk.forms import FormValidationAction



slots_marketing = ["LT_boton_fin", "LT_boton_inicio", "LT_interrupcion", "LT_vistas_gen", 
                   "LT_vista1", "LT_vista1_exp", "LT_vista2", "LT_vista2_exp", "LT_vista3", "LT_vista3_exp", 
                   "LT_vistas_check", "LT_pantallas_gen", 
                   "LT_pantalla1", "LT_pantalla1_gen", "LT_pantalla1_graf1", "LT_pantalla1_graf1_exp", "LT_pantalla1_graf2", "LT_pantalla1_graf2_exp", 
                   "LT_pantalla2", "LT_pantalla2_gen", "LT_pantalla2_evtemp", "LT_pantalla2_evtemp_gen", "LT_pantalla2_evtemp_graf1", "LT_pantalla2_evtemp_graf1_exp", "LT_pantalla2_evtemp_graf2", "LT_pantalla2_evtemp_graf2_exp", "LT_pantalla2_evtemp_graf3", "LT_pantalla2_evtemp_graf3_exp", "LT_pantalla2_anticip", "LT_pantalla2_anticip_gen", "LT_pantalla2_anticip_graf1", "LT_pantalla2_anticip_graf1_exp", "LT_pantalla2_anticip_graf2", "LT_pantalla2_anticip_graf2_exp", 
                   "LT_pantalla3", "LT_pantalla3_gen", "LT_pantalla3_graf1", "LT_pantalla3_graf1_exp"]

class ActionDeleteSlotUseCase(Action):
    def name(self) -> Text:
        return "action_delete_slot_caso_de_uso_LT"
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        return [SlotSet(slot, None) for slot in slots_marketing]


class ValidateForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_caso_de_uso_LT_form"

    def __init__(self):
        self.slot_mapping = {
            "LT_boton_fin": "LT_boton_fin",
            "LT_boton_inicio": "LT_vistas_gen",
            "LT_vista1": "LT_vista1_exp",
            "LT_vista2": "LT_vista2_exp",
            "LT_vista3": "LT_vista3_exp",
            "LT_vistas_check": "LT_pantallas_gen",
            "LT_pantalla1": "LT_pantalla1_gen",
            "LT_pantalla1_graf1": "LT_pantalla1_graf1_exp",
            "LT_pantalla1_graf2": "LT_pantalla1_graf2_exp",
            "LT_pantalla2": "LT_pantalla2_gen",
            "LT_pantalla2_evtemp": "LT_pantalla2_evtemp_gen",
            "LT_pantalla2_evtemp_graf1": "LT_pantalla2_evtemp_graf1_exp",
            "LT_pantalla2_evtemp_graf2": "LT_pantalla2_evtemp_graf2_exp",
            "LT_pantalla2_evtemp_graf3": "LT_pantalla2_evtemp_graf3_exp",
            "LT_pantalla2_anticip": "LT_pantalla2_anticip_gen",
            "LT_pantalla2_anticip_graf1": "LT_pantalla2_anticip_graf1_exp",
            "LT_pantalla2_anticip_graf2": "LT_pantalla2_anticip_graf2_exp",
            "LT_pantalla3": "LT_pantalla3_gen",
            "LT_pantalla3_graf1": "LT_pantalla3_graf1_exp",
        }

    def last_intent(self, tracker) -> str:
        for event in reversed(tracker.events):
            if event.get("event") == "user" and "intent" in event.get("parse_data", {}):
                return event["parse_data"]["intent"]["name"]
        return None  

    async def required_slots(
        self,
        domain_slots: List[Text],
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Text]:
        additional_slots = []
        updated_slots = domain_slots.copy()
        
        ultima_intencion = self.last_intent(tracker)
        print(f"Última intención: {ultima_intencion}")
        
        if tracker.get_slot("LT_boton_fin") and ultima_intencion == "LT_boton_fin":
            print("LT_boton_fin detectado")
            if "LT_boton_inicio" in updated_slots:
                updated_slots.remove("LT_boton_inicio")
            additional_slots.append("LT_boton_fin")
        
        elif ultima_intencion in self.slot_mapping:
            slot_generado = self.slot_mapping[ultima_intencion]
            print(f"{ultima_intencion} detectado")
            additional_slots.append(slot_generado)
            print(f"He añadido {slot_generado}")

        elif ultima_intencion not in slots_marketing and ultima_intencion != "bienvenida":
            print("Interrupción detectada")
            additional_slots.append("LT_interrupcion")
        
 
        print(f"Slots adicionales: {additional_slots}")
        print(f"Slots del dominio: {updated_slots}")

        return additional_slots + updated_slots  

    def extract_slot(self, slot_name: Text, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> Dict[Text, Any]:
        value = tracker.get_slot(slot_name)
        print(f"Extracting {slot_name}: {value}")
        return {slot_name: value}

    def __getattr__(self, name: Text):
    # Se usa cuando intentamos llamar a un atributo o método que no existe (no hemos definido) en la clase    
        if name.startswith("extract_"):
            slot_name = name[len("extract_"):]
            return lambda dispatcher, tracker, domain: self.extract_slot(slot_name, dispatcher, tracker, domain)
        if name.startswith("validate_"):
            slot_name = name[len("validate_"):]
            return lambda value, dispatcher, tracker, domain: self.validate_slot(slot_name, value, dispatcher, tracker, domain)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
        
    def validate_slot(self, slot_name: Text, value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> Dict[Text, Any]:
        """Validar el valor del slot genérico."""
        if value is not None:
            return {slot_name: value}
        else:
            return {slot_name: None}
        
    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
        ) -> List:
        
        if "start!.," in tracker.latest_message.get("text"):
            return [
            ActiveLoop(None),
            FollowupAction("action_listen") 
            ]
        
        else:
            return await super().run(dispatcher, tracker, domain)
