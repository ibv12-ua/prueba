import os
import requests
from dotenv import load_dotenv
from typing import Any, Dict, List, Text
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher


class ActionChitChat(Action):
    def name(self) -> Text:
        return "action_chit_chat"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        load_dotenv()
        api_token = os.getenv("INNOHUB_TOKEN", "")
        user_message = tracker.latest_message.get("text", "")
        url = "https://inno-hub.1millionbot.com/innohub/api/hub/chichat_rasa_response/"
        headers = {"Authorization": f"Bearer {api_token}"}

        try:
            response = requests.post(url, json={"message": user_message}, headers=headers, timeout=10)
            if response.ok:
                data = response.json()
                reply = data.get("response", "")
            else:
                reply = "Lo siento, hubo un problema al procesar tu consulta."
        except Exception:
            reply = "Lo siento, no pude procesar tu consulta en este momento."

        dispatcher.utter_message(text=reply)
        return []
