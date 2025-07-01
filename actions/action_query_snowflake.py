import os
import json
from functools import lru_cache

import pandas as pd
import openai
import snowflake.connector
from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import FollowupAction, SlotSet
from langchain.chat_models import ChatOpenAI
from langchain.agents import create_pandas_dataframe_agent
from .utils import chunk_buttons

# ---------------------------------------------------------------------------
# CONFIGURACIÓN GLOBAL
# ---------------------------------------------------------------------------
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Mapeos de meses y traducciones de países y ciudades centralizados
MONTH_NUM_TO_ES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo", 6: "junio",
    7: "julio", 8: "agosto", 9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre",
}
MONTH_ES_TO_EN = {
    "Enero": "January", "Febrero": "February", "Marzo": "March", "Abril": "April", "Mayo": "May", "Junio": "June",
    "Julio": "July", "Agosto": "August", "Septiembre": "September", "Octubre": "October", "Noviembre": "November", "Diciembre": "December",
}
COUNTRY_TRANSLATION = {
    "Germany": "Alemania", "Denmark": "Dinamarca", "Spain": "España", "France": "Francia", "Italy": "Italia",
    "Netherlands": "Países Bajos", "United Kingdom": "Reino Unido", "Sweden": "Suecia", "U.S.A.": "Estados Unidos",
    "Norway": "Noruega", "Belgium": "Bélgica", "Ireland": "Irlanda", "Finland": "Finlandia", "Kenya": "Kenia",
}

# Traducciones de ciudades
CITY_TRANSLATION = {
    "isla de pico (azores)": "Pico Island (Azores)",
    "isla de flores (azores)": "Flores Island (Azores)",
    "isla shetland": "Shetland Island",
    "stornoway outer stat hébridas": "Stornoway Outer Stat Hebrides",
    "isla graciosa (azores)": "Graciosa Island (Azores)",
    "isla de corvo (azores)": "Corvo Island (Azores)",
    "napoles": "Naples", "londres": "London", "oporto": "Porto", "bruselas": "Brussels", "bolonia": "Bologna",
    "burdeos": "Bordeaux", "lisboa": "Lisbon", "venecia": "Venice", "edimburgo": "Edinburgh", "la coruña": "La Coruna",
    "hamburgo": "Hamburg", "estocolmo": "Stockholm", "florencia": "Florence", "marsella": "Marseille", "estrasburgo": "Strasbourg",
    "augsburgo": "Augsburg", "colonia": "Cologne", "gotemburgo": "Gothenburg", "carcasona": "Carcassonne", "isla de man": "Isle Of Man",
    "perpiñán": "Perpignan", "logroño": "Logrono", "isla sao jorge": "Sao Jorge Island", "isla de laeso": "Laeso Island",
    "aquisgrán": "Aachen", "coblenza": "Koblenz", "dresde": "Dresden", "friburgo": "Freiburg", "hamburgo/finkenwerder": "Hamburg/Finkenwerder",
    "magnuci": "Mainz", "saarbrucken": "Saarbruecken", "warnemunde": "Warnemuende", "niza": "Nice", "bragança": "Braganca",
    "génova": "Genoa", "romano": "Rome", "lieja": "Liege", "condado de kerry": "Kerry County",
}

# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def normalize(text: str) -> str:
    """Lowercase & strip helper (safe for None)."""
    return (text or "").strip().lower()

def pretty_table(df: pd.DataFrame) -> str:
    """Convierte un DataFrame a una tabla HTML con estilos."""

    # Agregar estilo a las cabeceras
    html_table = df.to_html(index=False).replace("<th>", "<th style='text-align: center; font-size: 12px; padding-left: 2px; padding-right: 2px; '>")
    
    # Agregar estilo a las celdas del cuerpo
    html_table = html_table.replace(
        "<td>", "<td style='font-weight: lighter;font-size: 12px;'>"
    )

    return html_table

def get_month_name_after_days(start_month_name: str, days: int, year: int = 2024) -> str:
    """
    Recibe el nombre de un mes en español (ej. 'enero') y una cantidad de días.
    Devuelve el nombre del mes en español resultante tras sumar esos días.
    """
    # Invertir el diccionario una sola vez
    month_es_to_num = {v: k for k, v in MONTH_NUM_TO_ES.items()}
    
    month_num = month_es_to_num[start_month_name.lower().strip()]
    base_date = pd.Timestamp(year=year, month=month_num, day=1)
    result_date = base_date + pd.Timedelta(days=days)

    return MONTH_NUM_TO_ES[result_date.month]

def format_number(num):
    return f"{int(num):,}".replace(",", "\u00A0")

class CityTranslator:
    def __init__(self, mapping: dict[str, str]):
        # Guardamos ya las claves en minúsculas/strip para coincidir con normalize()
        self.mapping = {k.lower().strip(): v for k, v in mapping.items()}

    def translate(self, city: str) -> str:
        return self.mapping.get(normalize(city), city)


# Español → Inglés
translator_es_en = CityTranslator(CITY_TRANSLATION)

# Inglés → Español (diccionario invertido)
translator_en_es = CityTranslator({v: k for k, v in CITY_TRANSLATION.items()})

# -------------------------------
# CACHÉ CLAVES SNOWFLAKE
# -------------------------------

@lru_cache(maxsize=1)
def _load_private_key_bytes(path: str = "lucentia.p8.txt") -> bytes:
    """Lee y serializa la clave privada una sola vez."""
    with open(path, "rb") as key_file:
        key = serialization.load_pem_private_key(key_file.read(), password=None)
    return key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )


# ---------------------------------------------------------------------------
# CONEXIÓN Y EXTRACCIÓN DE SNOWFLAKE
# ---------------------------------------------------------------------------

def fetch_snowflake_data(query: str) -> pd.DataFrame:
    cfg = {
        "user": "LUCENTIA",
        "account": "osp-b2b",
        "warehouse": "PRE_TRANSFORM_WH",
        "database": "PRE_TOURISM_DB",
        "role": "PRE_DV_FR",
        "schema": "SIT",
    }

    try:
        with snowflake.connector.connect(private_key=_load_private_key_bytes(), ocsp_fail_open=False, **cfg) as conn:
            return pd.read_sql(query, conn)
    except Exception as exc:
        print(f"Error de conexión con Snowflake: {exc}")
        return pd.DataFrame()

# -------------------------------
# CACHÉ GLOBAL DE DATAFRAMES
# -------------------------------
_basic_df_cache: dict[str, pd.DataFrame] = {}

# -------------------------------
# FUNCIÓN PARA LIMPIAR EL CACHÉ
# -------------------------------
def clear_basic_df_cache():
    _basic_df_cache.clear()

# -------------------------------
# CREACIÓN DE LOS DATAFRAMES
# -------------------------------
def basic_df(query_type: str) -> pd.DataFrame:
    """Extrae, limpia y formatea los datos provenientes de Snowflake."""

    # Para testeo: limpiar caché
    # clear_basic_df_cache()

    # Verificar si el dataframe ya está en caché
    if query_type in _basic_df_cache:
        return _basic_df_cache[query_type]


    if query_type == "ventana":
        query = """
            SELECT F.*,
                O.CITYCODE AS ORIGIN_CITY_CODE,
                O.COUNTRYNAME AS ORIGIN_COUNTRY_NAME,
                D.CITYCODE AS DESTINATION_CITY_CODE,
                O.CITYNAME AS ORIGIN_CITY_NAME,
                D.CITYNAME AS DESTINATION_CITY_NAME
            FROM
                FC_LUC_OPPORTUNITY_WINDOW F
            LEFT JOIN
                DM_REF_CITY O ON F.SEARCH_ORIGIN_CITY_KEY = O.ID
            LEFT JOIN
                DM_REF_CITY D ON F.SEARCH_DESTINATION_CITY_KEY = D.ID
            WHERE
                D.CITYCODE IN ('CDT', 'ALC', 'VLC')
            """
    elif query_type == "busquedas":
        query = """
            SELECT F.*, 
                O.CITYCODE AS ORIGIN_CITY_CODE, 
                O.COUNTRYNAME AS ORIGIN_COUNTRY_NAME,
                D.CITYCODE AS DESTINATION_CITY_CODE, 
                O.CITYNAME AS ORIGIN_CITY_NAME,
                D.CITYNAME AS DESTINATION_CITY_NAME
            FROM 
                FC_LUC_SEARCHS_PREDICTION F
            LEFT 
                JOIN DM_REF_CITY O ON F.SEARCH_ORIGIN_CITY_KEY = O.ID
            LEFT 
                JOIN DM_REF_CITY D ON F.SEARCH_DESTINATION_CITY_KEY = D.ID
            WHERE D.CITYCODE IN ('CDT', 'ALC', 'VLC')
         """
         
    elif query_type == "cluster":
        query = """
            SELECT F.*,
                O.COUNTRYNAME AS ORIGIN_COUNTRY_NAME,
                O.CITYNAME AS ORIGIN_CITY_NAME,
                D.CITYNAME AS DESTINATION_CITY_NAME
            FROM
                FC_LUC_CLUSTER_SEGMENTATION F
            LEFT JOIN
                DM_REF_CITY O ON F.SEARCH_ORIGIN_CITY_KEY = O.ID
            LEFT JOIN
                DM_REF_CITY D ON F.SEARCH_DESTINATION_CITY_KEY = D.ID
            WHERE
                D.CITYCODE IN ('CDT', 'ALC', 'VLC')
         """
    elif query_type == "clima":
        query = """
        SELECT 
            A.*, 
            B.CITYNAME AS DESTINATION_CITY_NAME,
            C.CITYNAME AS ORIGIN_CITY_NAME,
            C.COUNTRYNAME AS ORIGIN_COUNTRY_NAME
        FROM FC_LUC_TEMPERATURE_SEARCHES_PRE A
        INNER JOIN DM_REF_CITY_MLG B ON A.SEARCH_DESTINATION_CITY_KEY = B.ID AND B.LANGUAGE_KEY = 1
        INNER JOIN DM_REF_CITY_MLG C ON A.SEARCH_ORIGIN_CITY_KEY = C.ID AND C.LANGUAGE_KEY = 1
        """
    
    df = fetch_snowflake_data(query)

    if df.empty:
        return df

    if query_type != "clima":
        df["MONTH_KEY"] = df["MONTH_KEY"].replace(MONTH_NUM_TO_ES)
        
    df["ORIGIN_COUNTRY_NAME"] = (
        df["ORIGIN_COUNTRY_NAME"].map(COUNTRY_TRANSLATION).fillna(df["ORIGIN_COUNTRY_NAME"])
    )

    if query_type == "busquedas" or query_type == "clima":
        df["SEARCH_DAY_KEY"] = pd.to_datetime(df["SEARCH_DAY_KEY"], format="%Y%m%d", errors="coerce").fillna(pd.Timestamp("2000-01-01"))
        df["SEARCH_PERIOD"] = df["SEARCH_DAY_KEY"].dt.to_period("M").astype(str)

    # Normalizamos campos de texto y filtramos países indeseados
    for col in ("DESTINATION_CITY_NAME", "ORIGIN_CITY_NAME", "ORIGIN_COUNTRY_NAME"):
        df[col] = df[col].str.strip().str.lower()

    df = df[~df["ORIGIN_COUNTRY_NAME"].isin(["estados unidos", "china", "kenia"])]

    # Guardar del dataframe en caché
    _basic_df_cache[query_type] = df

    return df

def get_common_origin_city_keys() -> list:
    """
    Devuelve una lista de SEARCH_ORIGIN_CITY_KEY que aparecen en las 3 tablas:
    FC_LUC_SEARCHS_PREDICTION, FC_LUC_OPPORTUNITY_WINDOW y FC_LUC_CLUSTER_SEGMENTATION.
    """
    tables = [
        "FC_LUC_SEARCHS_PREDICTION",
        "FC_LUC_OPPORTUNITY_WINDOW",
        "FC_LUC_CLUSTER_SEGMENTATION",
    ]

    city_key_sets = []
    for table in tables:
        query = f"SELECT DISTINCT SEARCH_ORIGIN_CITY_KEY FROM {table}"
        df = fetch_snowflake_data(query)
        if "SEARCH_ORIGIN_CITY_KEY" in df.columns:
            city_key_sets.append(set(df["SEARCH_ORIGIN_CITY_KEY"].dropna().unique()))

    if len(city_key_sets) != 3:
        print("❗ No se pudieron recuperar correctamente las claves de todas las tablas.")
        return []

    return sorted(set.intersection(*city_key_sets))

# ---------------------------------------------------------------------------
# AGENTE LANGCHAIN
# ---------------------------------------------------------------------------

def ask_agent(agent, prompt: str) -> str:
    try:
        return str(agent.run(prompt))
    except openai.OpenAIError as oe:
        print(f"OpenAIError: {oe}")
        return "Lo siento, hubo un problema con la IA. Inténtalo de nuevo más tarde."
    except Exception as exc:
        print(f"Error general: {exc}")
        return "Hubo un error inesperado al procesar tu solicitud."


def decode_response(response: str):
    """Convierte la respuesta del modelo a tabla HTML o dict de error."""
    try:
        data = json.loads(response)["table"]
        df = pd.DataFrame(data["data"], columns=data["columns"])
        return df.to_html(index=False)
    except (json.JSONDecodeError, KeyError):
        return {"error": "No se pudo decodificar la respuesta del agente."}


def serialize_value(value):
    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, pd.Period):
        return str(value)
    return value


# ---------------------------------------------------------------------------
# ACTION QUERY SNOWFLAKE BÚSQUEDAS
# ---------------------------------------------------------------------------

class ActionQuerySnowflakeB(Action):
    """Consulta datos en Snowflake y devuelve respuestas formateadas."""

    def name(self):
        return "action_query_snowflake_busquedas"

    # ---------------------------------------------------------------------
    # MÉTODO PRINCIPAL
    # ---------------------------------------------------------------------
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        tipo_consulta = tracker.get_slot("tipo_consulta")
        destino = tracker.get_slot("destino_b")
        origen_pais = tracker.get_slot("origen_pais_b")
        origen_ciudad = tracker.get_slot("origen_ciudad_b")
        anno = tracker.get_slot("anno_b")
        date_filter_slot = tracker.get_slot("date_filter")
        consulta = tracker.get_slot("consulta")

        print("Datos de la consulta:", destino, origen_pais, origen_ciudad, anno, date_filter_slot, consulta)

        # Traducción ciudad
        if origen_ciudad:
            origen_ciudad = translator_es_en.translate(origen_ciudad)
            print("Traducción ciudad origen:", origen_ciudad)

        # Obtención de datos
        df = basic_df("busquedas")
        df_v = basic_df("ventana")

        print("df_busquedas:", df.head())
        print("df_ventana:", df_v.head())

        if df.empty or df_v.empty:
            dispatcher.utter_message(text="No se encontraron datos en la base de datos, para esta consulta.")
            return [
                SlotSet("tipo_consulta", None),
                SlotSet("destino_b", None),
                SlotSet("origen_pais_b", None),
                SlotSet("origen_ciudad_b", None),
                SlotSet("anno_b", None),
                SlotSet("date_filter", None),
                SlotSet("consulta", None),
                FollowupAction("action_listen"),
            ]

        # Normalización de entradas
        destino_norm = normalize(destino)
        origen_pais_norm = normalize(origen_pais)
        origen_ciudad_norm = normalize(origen_ciudad)
        consulta_norm = normalize(consulta)
        date_filter_norm = normalize(date_filter_slot)

        if not all([destino_norm, origen_pais_norm, origen_ciudad_norm, consulta_norm]):
            dispatcher.utter_message(text="Falta información en los datos proporcionados. Por favor, verifica la información e inténtalo nuevamente.")
            return []

        # Ajuste especial de castellón
        if destino_norm == "castellón":
            destino_norm = "castellon de la plana"

        # ------------------------------------------
        #  FILTRADO
        # ------------------------------------------
        # Máscara para df
        mask = pd.Series(True, index=df.index)
        if destino_norm != "todos":
            mask &= df["DESTINATION_CITY_NAME"] == destino_norm
        if origen_pais_norm != "todos":
            mask &= df["ORIGIN_COUNTRY_NAME"] == origen_pais_norm
        if origen_ciudad_norm != "todas":
            mask &= df["ORIGIN_CITY_NAME"] == origen_ciudad_norm
        if anno:
            mask &= df["SEARCH_DAY_KEY"].dt.year == int(anno)
        if date_filter_norm and date_filter_norm != "todos los meses":
            mask &= df["MONTH_KEY"] == date_filter_norm

        filtered_df = df[mask]

        # Máscara para df_v (repite la lógica pero sobre df_v)
        mask_v = pd.Series(True, index=df_v.index)
        if destino_norm != "todos":
            mask_v &= df_v["DESTINATION_CITY_NAME"] == destino_norm
        if origen_pais_norm != "todos":
            mask_v &= df_v["ORIGIN_COUNTRY_NAME"] == origen_pais_norm
        if origen_ciudad_norm != "todas":
            mask_v &= df_v["ORIGIN_CITY_NAME"] == origen_ciudad_norm
        if anno:
            mask_v &= df_v["YEAR_KEY"] == int(anno)
        if date_filter_norm and date_filter_norm != "todos los meses":
            mask_v &= df_v["MONTH_KEY"] == date_filter_norm

        filtered_df_v = df_v[mask_v]

        print("Filas después del filtrado:", len(filtered_df))
        if filtered_df.empty or filtered_df_v.empty:
            print("No se encontraron resultados después del filtrado.")

        # Nombres bonitos para mensajes
        destino_pretty = destino.capitalize() if destino_norm != "todos" else "Comunitat Valenciana"
        origen_pais_pretty = origen_pais.title() if origen_pais_norm != "todos" else "todos los mercados"
        origen_ciudad_pretty = translator_en_es.translate(origen_ciudad).title() if origen_ciudad_norm != "todas" else "todas las ciudades"
        month_pretty = date_filter_slot.lower() if date_filter_slot != "todos" else "todos los meses"

        # ------------------------------------------------------------------
        #  RESPUESTAS SEGÚN TIPO DE CONSULTA
        # ------------------------------------------------------------------
        try:
            if filtered_df.empty or filtered_df_v.empty:
                dispatcher.utter_message(text="Lamentablemente, no existen datos para la consulta realizada.")
            
            elif tipo_consulta == "Ventana media y búsquedas desde un mercado de origen":
                n_busquedas = filtered_df["SEARCHS_MEAN_WINDOW_NUM"].sum()
                ventana_media = round(filtered_df_v["WINDOW_DAYS_NUM"].mean())

                dispatcher.utter_message(text=f"La ventana media y el número de búsquedas totales desde {origen_pais_pretty} a {destino_pretty} en {month_pretty} de {anno} son: **{ventana_media} días** y **{round(n_busquedas)} búsquedas**.")
                
                if date_filter_norm != "todos los meses":
                    month_flight = get_month_name_after_days(month_pretty, ventana_media, int(anno))

                    dispatcher.utter_message(text=f"_⇨ Se esperan {round(n_busquedas)} búsquedas en {month_pretty} para volar en {month_flight}_")

            elif tipo_consulta == "Ventana media y búsquedas desde una ciudad de origen":
                n_busquedas = filtered_df["SEARCHS_MEAN_WINDOW_NUM"].sum()
                ventana_media = round(filtered_df_v["WINDOW_DAYS_NUM"].mean())

                dispatcher.utter_message(text=f"La ventana media y el número de búsquedas totales desde {origen_ciudad_pretty} ({origen_pais_pretty}) a {destino_pretty} en {month_pretty} de {anno} son: **{ventana_media} días** y **{round(n_busquedas)} búsquedas**.")

                if date_filter_norm != "todos los meses":
                    month_flight = get_month_name_after_days(month_pretty, ventana_media, int(anno))

                    dispatcher.utter_message(text=f"_⇨ Se esperan {round(n_busquedas)} búsquedas en {month_pretty} para volar en {month_flight}_")


            elif tipo_consulta == "Ranking de mercados de origen por ventana media":
                ranking_vo = filtered_df_v.groupby(["ORIGIN_COUNTRY_NAME"])["WINDOW_DAYS_NUM"].mean().round().astype(int).reset_index()
                ranking_b = filtered_df.groupby(["ORIGIN_COUNTRY_NAME"])["SEARCHS_MEAN_WINDOW_NUM"].sum().round().astype(int).reset_index()
                
                merged = pd.merge(ranking_vo, ranking_b, on="ORIGIN_COUNTRY_NAME", how="inner")
                merged = merged.sort_values(by="WINDOW_DAYS_NUM", ascending=False)
                merged["ORIGIN_COUNTRY_NAME"] = merged["ORIGIN_COUNTRY_NAME"].str.title()
                merged.rename(columns={"ORIGIN_COUNTRY_NAME": "Origen", "WINDOW_DAYS_NUM":"Ventana media", "SEARCHS_MEAN_WINDOW_NUM": "Búsq. totales"}, inplace=True)
                
                html_table = pretty_table(merged)
                dispatcher.utter_message(text=f"El ranking de mercados de origen según la ventana promedio a {destino_pretty} en {month_pretty} de {anno} es:\n\n {html_table}")

            elif tipo_consulta == "Ranking de ciudades de origen por ventana media":
                ranking_vo = filtered_df_v.groupby(["ORIGIN_CITY_NAME"])["WINDOW_DAYS_NUM"].mean().round().astype(int).reset_index()
                ranking_b = filtered_df.groupby(["ORIGIN_CITY_NAME"])["SEARCHS_MEAN_WINDOW_NUM"].sum().round().astype(int).reset_index()
                
                merged = pd.merge(ranking_vo, ranking_b, on="ORIGIN_CITY_NAME", how="inner")
                merged = merged.sort_values(by="WINDOW_DAYS_NUM", ascending=False)
                merged["ORIGIN_CITY_NAME"] = merged["ORIGIN_CITY_NAME"].apply(translator_en_es.translate).str.title()                
                merged.rename(columns={"ORIGIN_CITY_NAME": "Origen", "WINDOW_DAYS_NUM":"Ventana media", "SEARCHS_MEAN_WINDOW_NUM": "Búsq. totales"}, inplace=True)  
                html_table = pretty_table(merged.head(15))
                dispatcher.utter_message(text=f"El ranking ciudades de origen de {origen_pais_pretty} según la ventana promedio a {destino_pretty} en {month_pretty} de {anno} es:\n\n {html_table}")

            elif tipo_consulta == "Búsquedas diarias desde un mercado de origen":
                grouped = filtered_df.groupby("SEARCH_DAY_KEY")["SEARCHS_MEAN_WINDOW_NUM"].sum()
                n_busquedas = grouped.mean()
                dispatcher.utter_message(text=f"El número de búsquedas diarias promedio desde {origen_pais_pretty} a {destino_pretty} en {month_pretty} de {anno} es {round(n_busquedas)}.")

            elif tipo_consulta == "Búsquedas diarias desde una ciudad de origen":
                grouped = filtered_df.groupby("SEARCH_DAY_KEY")["SEARCHS_MEAN_WINDOW_NUM"].sum()
                n_busquedas = grouped.mean()
                dispatcher.utter_message(text=f"El número de búsquedas diarias promedio desde {origen_ciudad_pretty} a {destino_pretty} en {month_pretty} de {anno} es {round(n_busquedas)}.")

            elif tipo_consulta == "Ranking de mercados de origen por ventana media diarias":
                grouped = (filtered_df.groupby(["SEARCH_DAY_KEY", "ORIGIN_COUNTRY_NAME"])["SEARCHS_MEAN_WINDOW_NUM"].sum()
                                        .reset_index()                            # búsquedas por día y país
                                        .groupby("ORIGIN_COUNTRY_NAME")["SEARCHS_MEAN_WINDOW_NUM"].mean()
                                        .round().astype(int).sort_values(ascending=False)
                                        .reset_index())
                grouped["ORIGIN_COUNTRY_NAME"] = grouped["ORIGIN_COUNTRY_NAME"].str.title()
                
                grouped.rename(columns={"ORIGIN_COUNTRY_NAME": "Origen", "SEARCHS_MEAN_WINDOW_NUM": "Búsquedas al día"}, inplace=True)
                html_table = pretty_table(grouped)
                dispatcher.utter_message(text=f"El ranking de mercados de origen según las búsquedas al día promedio a {destino_pretty} en {month_pretty} de {anno} es:\n\n {html_table}")

            elif tipo_consulta == "Ranking de ciudades de origen por ventana media diarias":
                grouped = (filtered_df.groupby(["SEARCH_DAY_KEY", "ORIGIN_CITY_NAME"])["SEARCHS_MEAN_WINDOW_NUM"].sum()
                                        .reset_index()
                                        .groupby("ORIGIN_CITY_NAME")["SEARCHS_MEAN_WINDOW_NUM"].mean()
                                        .round().astype(int).sort_values(ascending=False)
                                        .reset_index())
                grouped["ORIGIN_CITY_NAME"] = grouped["ORIGIN_CITY_NAME"].apply(translator_en_es.translate).str.title()

                grouped.rename(columns={"ORIGIN_CITY_NAME": "Origen", "SEARCHS_MEAN_WINDOW_NUM": "Búsquedas al día"}, inplace=True)
                html_table = pretty_table(grouped.head(15))
                dispatcher.utter_message(text=f"El ranking ciudades de origen de de {origen_pais_pretty} según las búsquedas al día promedio a {destino_pretty} en {month_pretty} de {anno} es:\n\n {html_table}")

            elif tipo_consulta == "Consulta abierta":
                agent = create_pandas_dataframe_agent(ChatOpenAI(model_name="gpt-4-turbo-preview", temperature=0), filtered_df, verbose=True)
                print("Agente creado con éxito.")
                query_description = {
                    "tipo_consulta": tipo_consulta,
                    "destino": destino_norm,
                    "origen_pais": origen_pais_norm,
                    "origen_ciudad": origen_ciudad_norm,
                    # "date_filter": date_filter or "No especificado",
                    "consulta": consulta_norm,
                }
                prompt = (
                    """Eres un experto interpretando las solicitudes que los usuarios hacen a información estructurada en un "
                    "dataframe a través del lenguaje natural y dando el resultado correcto.\n\n" \
                    "Tus entradas son los posibles parámetros de la consulta (no todos serán necesarios):\n" \
                    f"- Destino: {query_description['destino']}\n" \
                    f"- Pais o mercado de origen: {query_description['origen_pais']}\n" \
                    f"- Ciudad de origen: {query_description['origen_ciudad']}\n" \
                    f"- Fecha de interés (periodo): {query_description['date_filter']}\n" \
                    f"- Consulta: {query_description['consulta']}\n\n" \
                    "1. Interpreta rigurosamente la consulta del usuario teniendo en cuenta los parámetros y su relación con "
                    "las columnas del dataframe.\n" \
                    "2. Calcula el resultado correcto según la consulta.\n" \
                    "3. Responde siempre en español, clara y concisamente."""
                )
                response = ask_agent(agent, prompt)
                dispatcher.utter_message(text=response)
        except Exception as exc:
            dispatcher.utter_message(text=f"Error al procesar la consulta. Por favor prueba de nuevo.")
            print(f"Error al procesar la consulta: {exc}")

        # Reset de slots y vuelta a escuchar
        return [
            SlotSet("tipo_consulta", None),
            SlotSet("destino_b", None),
            SlotSet("origen_pais_b", None),
            SlotSet("origen_ciudad_b", None),
            SlotSet("anno_b", None),
            SlotSet("date_filter", None),
            SlotSet("consulta", None),
            FollowupAction("action_listen"),
        ]


# ---------------------------------------------------------------------------
# ACTION QUERY SNOWFLAKE VENTANA DE OPORTUNIDAD
# ---------------------------------------------------------------------------

class ActionQuerySnowflakeV(Action):
    """Consulta datos en Snowflake y devuelve respuestas formateadas."""

    def name(self):
        return "action_query_snowflake_ventana"

    # ---------------------------------------------------------------------
    # MÉTODO PRINCIPAL
    # ---------------------------------------------------------------------
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        tipo_consulta = tracker.get_slot("tipo_consulta_v")
        destino = tracker.get_slot("destino_v")
        origen_pais = tracker.get_slot("origen_pais_v")
        origen_ciudad = tracker.get_slot("origen_ciudad_v")
        date_filter_slot = tracker.get_slot("date_filter_v")
        consulta = tracker.get_slot("consulta_v")

        print("Datos de la consulta:", destino, origen_pais, origen_ciudad, date_filter_slot, consulta)

        # Traducción ciudad
        if origen_ciudad:
            origen_ciudad = translator_es_en.translate(origen_ciudad)
            print("Traducción ciudad origen:", origen_ciudad)

        # Obtención de datos
        df = basic_df("ventana")
        if df.empty:
            dispatcher.utter_message(text="No se encontraron datos en la base de datos, para esta consulta.")
            return [
                SlotSet("tipo_consulta_v", None),
                SlotSet("destino_v", None),
                SlotSet("origen_pais_v", None),
                SlotSet("origen_ciudad_v", None),
                SlotSet("date_filter_v", None),
                SlotSet("consulta_v", None),
                FollowupAction("action_listen"),
            ]
        
        print("-" * 20)
        print("DF ventana:", df.head())
        print("columnas:", df.columns)
        print("Destino:", destino)
        print("Origen país:", origen_pais)
        print("Origen ciudad:", origen_ciudad)
        print("Fecha:", date_filter_slot)
        print("Consulta:", consulta)

        # Normalización de entradas
        destino_norm = normalize(destino)
        origen_pais_norm = normalize(origen_pais)
        origen_ciudad_norm = normalize(origen_ciudad)
        consulta_norm = normalize(consulta)

        if not all([destino_norm, origen_pais_norm, origen_ciudad_norm, consulta_norm]):
            dispatcher.utter_message(text="Falta información en los datos proporcionados. Por favor, verifica la información e inténtalo nuevamente.")
            return []

        # Procesar fecha
        month_name = "todos"
        date_filter_period = None

        if date_filter_slot and date_filter_slot != "Todos los meses":
            try:
                month_name_es, year_str = date_filter_slot.split()
                month_name = month_name_es.capitalize()
                date_filter = pd.to_datetime(f"{MONTH_ES_TO_EN.get(month_name_es, month_name_es)} {year_str}", format="%B %Y", errors="coerce")
                if pd.isna(date_filter):
                    dispatcher.utter_message(text=f"Fecha no válida: {date_filter_slot}. Inténtalo de nuevo.")
                    return []
                date_filter_period = date_filter.strftime("%Y-%m")
            except Exception as exc:
                dispatcher.utter_message(text=f"Error al procesar la fecha: {exc}")
                return []

        # Ajuste especial de castellón
        if destino_norm == "castellón":
            destino_norm = "castellon de la plana"

        # ------------------------------------------
        #  FILTRADO
        # ------------------------------------------
        mask = pd.Series(True, index=df.index)
        if destino_norm != "todos":
            mask &= df["DESTINATION_CITY_NAME"] == destino_norm
        if origen_pais_norm != "todos":
            mask &= df["ORIGIN_COUNTRY_NAME"] == origen_pais_norm
        if origen_ciudad_norm != "todas":
            mask &= df["ORIGIN_CITY_NAME"] == origen_ciudad_norm
        if date_filter_period:
            mask &= df["MONTH_KEY"] == month_name_es.lower()

        filtered_df = df[mask]
        filtered_df = filtered_df[[
            "WINDOW_DAYS_NUM", "ORIGIN_COUNTRY_NAME", "ORIGIN_CITY_NAME", "DESTINATION_CITY_NAME", "MONTH_KEY"
        ]].rename(columns={"WINDOW_DAYS_NUM": "Ventana de oportunidad"})

        print("Filas después del filtrado:", len(filtered_df))
        if filtered_df.empty:
            print("No se encontraron resultados después del filtrado.")

        # Nombres bonitos para mensajes
        destino_pretty = destino.capitalize() if destino_norm != "todos" else "Comunitat Valenciana"
        origen_pais_pretty = origen_pais.capitalize() if origen_pais_norm != "todos" else "todos los mercados"
        origen_ciudad_pretty = translator_en_es.translate(origen_ciudad).capitalize() if origen_ciudad_norm != "todas" else "todas las ciudades"
        month_pretty = month_name.lower() if month_name != "todos" else "todos los meses"

        # ------------------------------------------------------------------
        #  RESPUESTAS SEGÚN TIPO DE CONSULTA
        # ------------------------------------------------------------------
        try: 
            if filtered_df.empty:
                dispatcher.utter_message(text="Lamentablemente, no existen datos para la consulta realizada.")

            elif tipo_consulta == "Ventana de oportunidad desde un mercado de origen":
                ventana = filtered_df["Ventana de oportunidad"].mean()
                dispatcher.utter_message(text=f"La ventana de oportunidad promedio desde {origen_pais_pretty} a {destino_pretty} en {month_pretty} de {anno} es {round(ventana)}.")

            elif tipo_consulta == "Ventana de oportunidad desde una ciudad de origen":
                ventana = filtered_df["Ventana de oportunidad"].mean()
                dispatcher.utter_message(text=f"La ventana de oportunidad promedio desde {origen_ciudad_pretty} a {destino_pretty} en {month_pretty} de {anno} es {round(ventana)}.")

            elif tipo_consulta == "Ranking de mercados de origen por ventana de oportunidad":
                grouped = (filtered_df.groupby(["MONTH_KEY", "ORIGIN_COUNTRY_NAME"])["Ventana de oportunidad"].mean()
                                        .reset_index()                            # búsquedas por día y país
                                        .groupby("ORIGIN_COUNTRY_NAME")["Ventana de oportunidad"].mean()
                                        .round().astype(int).sort_values(ascending=False)
                                        .reset_index())
                grouped["ORIGIN_COUNTRY_NAME"] = grouped["ORIGIN_COUNTRY_NAME"].str.title()
                
                grouped.rename(columns={"ORIGIN_COUNTRY_NAME": "Origen", "Ventana de oportunidad": "Ventana"}, inplace=True)
                html_table = pretty_table(grouped)
                dispatcher.utter_message(text=f"El ranking de mercados de origen según la ventana de oportunidad promedio a {destino_pretty} en {month_pretty} de {anno} es:\n\n {html_table}")

            elif tipo_consulta == "Ranking de ciudades de origen por ventana de oportunidad":
                grouped = (filtered_df.groupby(["MONTH_KEY", "ORIGIN_CITY_NAME"])["Ventana de oportunidad"].mean()
                                        .reset_index()
                                        .groupby("ORIGIN_CITY_NAME")["Ventana de oportunidad"].mean()
                                        .round().astype(int).sort_values(ascending=False)
                                        .reset_index())
                grouped["ORIGIN_CITY_NAME"] = grouped["ORIGIN_CITY_NAME"].apply(translator_en_es.translate).str.title()

                grouped.rename(columns={"ORIGIN_CITY_NAME": "Origen", "Ventana de oportunidad": "Ventana"}, inplace=True)
                html_table = pretty_table(grouped.head(15))
                dispatcher.utter_message(text=f"El ranking ciudades de origen de {origen_pais_pretty} según la ventana de oportunidad promedio a {destino_pretty} en {month_pretty} de {anno} es:\n\n {html_table}")

            elif tipo_consulta == "Consulta abierta":
                agent = create_pandas_dataframe_agent(ChatOpenAI(model_name="gpt-4-turbo-preview", temperature=0), filtered_df, verbose=True)
                print("Agente creado con éxito.")
                query_description = {
                    "tipo_consulta_v": tipo_consulta,
                    "destino": destino_norm,
                    "origen_pais": origen_pais_norm,
                    "origen_ciudad": origen_ciudad_norm,
                    "date_filter_v": date_filter_period or "No especificado",
                    "consulta_v": consulta_norm,
                }
                prompt = (
                    """Eres un experto interpretando las solicitudes que los usuarios hacen a información estructurada en un "
                    "dataframe a través del lenguaje natural y dando el resultado correcto.\n\n" \
                    "Tus entradas son los posibles parámetros de la consulta (no todos serán necesarios):\n" \
                    f"- Destino: {query_description['destino']}\n" \
                    f"- Pais o mercado de origen: {query_description['origen_pais']}\n" \
                    f"- Ciudad de origen: {query_description['origen_ciudad']}\n" \
                    f"- Fecha de interés (periodo): {query_description['date_filter']}\n" \
                    f"- Consulta: {query_description['consulta']}\n\n" \
                    "1. Interpreta rigurosamente la consulta del usuario teniendo en cuenta los parámetros y su relación con "
                    "las columnas del dataframe.\n" \
                    "2. Calcula el resultado correcto según la consulta.\n" \
                    "3. Responde siempre en español, clara y concisamente."""
                )
                response = ask_agent(agent, prompt)
                dispatcher.utter_message(text=response)
        except Exception as exc:
            dispatcher.utter_message(text=f"Error al procesar la consulta. Por favor prueba de nuevo.")
            print(f"Error al procesar la consulta: {exc}")

        # Reset de slots y vuelta a escuchar
        return [
            SlotSet("tipo_consulta_v", None),
            SlotSet("destino_v", None),
            SlotSet("origen_pais_v", None),
            SlotSet("origen_ciudad_v", None),
            SlotSet("date_filter_v", None),
            SlotSet("consulta_v", None),
            FollowupAction("action_listen"),
        ]
        
# ---------------------------------------------------------------------------
# ACTION QUERY SNOWFLAKE CLUSTERS
# ---------------------------------------------------------------------------       

CITY_TRANSLATION_CLUSTERS = {
    "aalesund": "Alesund", "augsburg": "Augsburgo", "malaga": "Málaga", "amsterdam": "Ámsterdam", "antwerp": "Amberes", 
    "avignon": "Aviñón", "berlin": "Berlín", "braganca": "Bragança", "borlange": "Borlänge", "bologna": "Bolonia",
    "bonn": "Bonn", "bordeaux": "Burdeos", "bodo": "Bodø", "brussels": "Bruselas", "braunschweig": "Brunswick", "laeso island": "Isla de Laeso",
    "carcassonne": "Carcasona", "castellon de la plana": "Castellón de la Plana", "cologne": "Colonia",
    "chateauroux": "Châteauroux", "chambery": "Chambéry", "copenhagen": "Copenhague", "dresden": "Dresde", "dublin": "Dublín",
    "dusseldorf": "Düsseldorf", "san sebastian": "San Sebastián", "elba island": "Isla de Elba", "saint etienne": "Saint-Étienne",
    "edinburgh": "Edimburgo", "epinal": "Épinal", "florence": "Florencia", "flores island (azores)": "Isla de Flores (Azores)",
    "muenster": "Múnster", "frankfurt": "Fráncfort", "floro": "Florø", "san sebastian de la gomera": "San Sebastián de la Gomera",
    "genoa": "Génova", "gothenburg": "Gotemburgo", "girona": "Gerona", "groningen": "Groninga", "graciosa island (azores)": "Isla Graciosa (Azores)",
    "hamburg": "Hamburgo", "orsta-volda": "Ørsta-Volda", "honningsvag": "Honningsvåg", "lleida": "Lérida", "isle of man": "Isla de Man",
    "jonkoping": "Jönköping", "jyvaskyla": "Jyväskylä", "kerry county": "Condado de Kerry", "kittila": "Kittilä",
    "la coruna": "La Coruña", "almeria": "Almería", "leon": "León", "lands end": "Land's End", "liege": "Lieja", "lisbon": "Lisboa",
    "lulea": "Luleå", "london": "Londres", "linkoping": "Linköping", "manchester": "Mánchester", "milan": "Milán",
    "malmo": "Malmö", "marseille": "Marsella", "munich": "Múnich", "naples": "Nápoles", "nice": "Niza",
    "norrkoping": "Norrköping", "nuremberg": "Núremberg", "cordoba": "Córdoba", "ornskoldsvik": "Örnsköldsvik",
    "porto": "Oporto", "orebro": "Örebro", "ostersund": "Östersund", "ostend": "Ostende", "paris": "París",
    "ponta delgada (azores)": "Ponta Delgada (Azores)", "perpignan": "Perpiñán", "vardoe": "Vardø", "vadso": "Vadsø",
    "pico island (azores)": "Isla de Pico (Azores)", "palma mallorca": "Palma de Mallorca", "pantelleria": "Pantelaria",
    "portimao": "Portimão", "logrono": "Logroño", "rome": "Roma", "roros": "Røros", "saarbruecken": "Saarbrücken",
    "santiago de compostela": "Santiago de Compostela", "skelleftea": "Skellefteå", "sonderborg": "Sønderborg",
    "sao jorge island": "Isla de São Jorge", "santa cruz de la palma": "Santa Cruz de La Palma", "stockholm": "Estocolmo",
    "svolvaer": "Svolvær", "strasbourg": "Estrasburgo", "trollhattan": "Trollhättan", "tromso": "Tromsø",
    "turin": "Turín", "trieste": "Trieste", "umea": "Umeå", "rouen": "Ruán", "venice": "Venecia", "chalons-en-champagne": "Châlons-en-Champagne",
    "jerez de la frontera": "Jerez de la Frontera", "bronnoysund": "Brønnøysund", "berlevag": "Berlevåg", "corvo island (azores)": "Isla de Corvo (Azores)",
    "forde": "Førde", "gallivare": "Gällivare", "mosjoen": "Mosjøen", "orland": "Ørland", "rost": "Røst", "roervik": "Rørvik",
    "salen": "Sälen", "shetland islands": "Islas Shetland", "sorkjosen": "Sørkjosen", "sandnessjoen": "Sandnessjøen",
    "stornoway outer stat hebrides": "Stornoway (Hébridas Exteriores)", "tiree inner hebrides": "Tiree (Hébridas Interiores)",
    "alghero":"Alguero", "batsfjord":"Båtsfjord", "beziers":"Béziers", "santa maria (azores)":"Santa María (Azores)", "epinal":"Épinal",
}

PAISES_CIUDADES_CLUSTERS = {
    'Alemania': ["Altenburg", "Ansbach", "Aquisgrán", "Aschaffenburg", "Augsburgo", "Bamberg", "Bayreuth", "Berlín", "Bielefeld", "Bochum", "Bonn", "Bremen", "Bremerhaven", "Brunswick", "Chemnitz", "Coblenza", "Cochstedt", "Colonia", "Cottbus", "Cuxhaven", "Dortmund", "Dresde", "Duisburg", "Düsseldorf", "Egelsbach", "Eisenach", "Emden", "Erfurt", "Essen", "Flensburg", "Fráncfort", "Frankfurt an der Oder", "Friburgo", "Friedrichshafen", "Fritzlar", "Fuerstenfeldbruch", "Fulda", "Gelsenkirchen", "Gera", "Goettingen", "Greifswald", "Guetersloh", "Hagen", "Hamburgo", "Hamburgo/Finkenwerder", "Hamm", "Hanover", "Heide-Buesum", "Helgoland", "Heringsdorf", "Holf", "Illesheim", "Ingolstadt", "Jena", "Karlsruhe", "Kassel", "Kiel", "Lahr", "Lindau", "Lübeck", "Lueneburg", "Magnucia", "Mannheim", "Memmingen", "Minden", "Múnster", "Múnich", "Neumuenster", "Norden", "Norderney", "Núremberg", "Oberhausen", "Offenburg", "Oldernburg", "Paderborn", "Passau", "Peenemuende", "Ramstein", "Ratisbona", "Rechlin", "Riesa", "Rostock-Laage", "Saarbrücken", "Schkeuditz", "Schoena", "Schwerin", "Siegburg", "Solingen", "Spangdahlem", "Stendal", "Stralsund", "Straubing", "Stuttgart", "Suhl", "Ulm", "Varrelbusch", "Wangerooge", "Warnemunde", "Westerland", "Wiesbaden", "Wilhelmshaven", "Wismar", "Worms", "Wuerzburg", "Wuppertal", "Wyk", "Zweibrucken" ],
    'Noruega': ["Alesund", "Alta", "Andenes", "Bardufoss", "Båtsfjord", "Bergen", "Berlevåg", "Bodø", "Brønnøysund", "Florø", "Førde", "Hammerfest", "Harstad-Narvik", "Hasvik", "Haugesund", "Honningsvåg", "Kirkenes", "Kristiansand", "Kristiansund", "Lakselv", "Leknes", "Longyearbyen", "Mehamn", "Mo i Rana", "Molde", "Mosjøen", "Namsos", "Ørland", "Ørsta-Volda", "Oslo", "Rørvik", "Røros", "Røst", "Sandane", "Sandnessjøen", "Sogndal", "Sørkjosen", "Stavanger", "Stokmarknes", "Stord", "Svolvær", "Trollhättan", "Tromsø", "Trondheim", "Vadsø", "Vardø"],
    'Suecia': ["Angelholm", "Arvidsjaur", "Estocolmo", "Gällivare", "Gotemburgo", "Hagfors", "Halmstad", "Hemavan", "Kalmar", "Kiruna", "Kramfors", "Kristianstad", "Linköping", "Luleå", "Lycksele", "Malmö", "Mora", "Norrköping", "Örebro", "Örnsköldsvik", "Östersund", "Pajala", "Ronneby", "Sälen", "Skellefteå", "Sundsvall", "Sveg", "Torsby", "Umeå", "Vaxjo", "Vilhelmina", "Visby", "Borlänge", "Jönköping", "Karlstad", "Trollhättan"],
    'Francia': ["Épinal", "Ajaccio", "Aurillac", "Bastia", "Bergerac", "Béziers", "Biarritz", "Brest", "Brive-La-Gaillarde", "Burdeos", "Caen", "Calvi", "Carcasona", "Castres", "Chambéry", "Clermont-Ferrand", "Deauville", "Dole", "Estrasburgo", "Figari", "Goin", "Grenoble", "La Rochelle", "Le Puy", "Lille", "Limoges", "Lorient", "Lourdes", "Lyon", "Marsella", "Montpellier", "Nantes", "Nimes", "Niza", "París", "Pau", "Perpiñán", "Poitiers", "Rennes", "Rodez", "Saint Nazaire", "Toulon", "Toulouse", "Tours", "Angers", "Aviñón", "Châteauroux", "Dijon", "Dinard", "Mulhouse", "Quimper", "Ruán", "Saint-Étienne", "Toussus-Le-Noble", "Châlons-en-Champagne", "Annecy"],
    'Portugal': ["Bragança", "Faro", "Funchal", "Horta (Azores)", "Isla de Corvo (Azores)", "Isla de Flores (Azores)", "Isla de Pico (Azores)", "Isla Graciosa (Azores)", "Isla de São Jorge", "Lisboa", "Oporto", "Ponta Delgada (Azores)", "Portimão", "Porto Santo (Madeira)", "Santa María (Azores)", "Terceira", "Vila Real", "Viseu"],
    'Finlandia': ["Helsinki", "Ivalo", "Joensuu", "Jyväskylä", "Kajaani", "Kemi", "Kittilä", "Kronoby", "Kuopio", "Kuusamo", "Lappeenranta", "Mariehamn", "Oulu", "Rovaniemi", "Tampere", "Turku", "Vaasa"],
    'España': ["Alicante", "Almería", "Asturias", "Badajoz", "Barcelona", "Bilbao", "Burgos", "Castellón de la Plana", "Corvera", "Fuerteventura", "Gerona", "Granada", "Ibiza", "Jerez de la Frontera", "La Coruña", "Lanzarote", "Las Palmas", "León", "Lérida", "Logroño", "Madrid", "Málaga", "Melilla", "Menorca", "Palma de Mallorca", "Pamplona", "Reus", "Salamanca", "San Sebastián", "San Sebastián de la Gomera", "Santa Cruz de La Palma", "Santander", "Santiago de Compostela", "Seo De Urgel", "Sevilla", "Tenerife", "Valencia", "Valladolid", "Valverde", "Vigo", "Vitoria", "Zaragoza", "Albacete", "Algeciras", "Benidorm", "Ceuta", "Córdoba", "Murcia", "Tarragona"],
    'Reino Unido': ["Blackpool", "Carlisle", "Cambridge", "Doncaster", "Gloucester", "Land's End", "Oban", "Oxford", "Plymouth", "Southend", "Swansea", "Valley", "Aberdeen", "Alderney", "Barra", "Belfast", "Benbecula", "Birmingham", "Bournemouth", "Bristol", "Campbeltown", "Cardiff", "Derry", "Dundee", "Durham Tees Valley", "Eday", "Edimburgo", "Exeter", "Glasgow", "Guernsey", "Humberside", "Inverness", "Isla de Man", "Islas Shetland", "Islay", "Jersey", "Kirkwall", "Leeds", "Liverpool", "Londres", "Mánchester", "Newcastle", "Newquay", "North Ronaldsay", "Norwich", "Nottingham", "Papa Westray", "Sanday", "Southampton", "Stornoway (Hébridas Exteriores)", "Stronsay", "Tiree (Hébridas Interiores)", "Westray", "Wick"],
    'Italia': ["Isla de Elba", "Salerno", "Siena", "Vieste", "Alguero", "Ancona", "Bari", "Bolonia", "Bolzano", "Brindisi", "Cagliari", "Catania", "Comiso", "Crotone", "Cuneo", "Florencia", "Foggia", "Forli", "Génova", "Lamezia-Terme", "Lampedusa", "Milán", "Nápoles", "Olbia", "Palermo", "Pantelaria", "Perugia", "Pescara", "Pisa", "Reggio Calabria", "Rimini", "Roma", "Tires", "Trapani", "Trieste", "Turín", "Venecia", "Verona"],
    'Países Bajos': ["Amberes", "Ámsterdam", "Eindhoven", "Groninga", "Maastricht", "Rotterdam"],
    'Dinamarca': ["Aalborg", "Aarhus", "Billund", "Bornholm", "Copenhague", "Esbjerg", "Isla de Laeso", "Karup", "Sønderborg"],
    'Bélgica': ["Bruselas", "Lieja", "Odense", "Ostende"],
    'Irlanda': ["Condado de Kerry", "Cork", "Donegal", "Dublín", "Knock", "Shannon", "Spiddal"]
}

class ActionQuerySnowflakeC(Action):
    """Consulta datos en Snowflake y devuelve respuestas formateadas."""

    def name(self):
        return "action_query_snowflake_cluster"
    

    # ---------------------------------------------------------------------
    # MÉTODO PRINCIPAL
    # ---------------------------------------------------------------------
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        tipo_consulta = tracker.get_slot("tipo_consulta_c")
        destino = tracker.get_slot("destino_c")
        anno = tracker.get_slot("anno_c")
        date_filter_slot = tracker.get_slot("date_filter_c")
        rango_ventana = tracker.get_slot("rango_ventana")
        perfil = tracker.get_slot("perfil")
        
        color_num_map = {
            "Coral": 14, "Gris": 9, "Lima": 13, "Marfil": 11, "Marrón": 7, "Morado": 5,
            "Naranja": 4, "Negro": 10, "Turquesa": 6, "Celeste": 12, "Amarillo": 3, "Rojo": 1,
            "Verde": 2, "Azul": 0, "Naranja": 4
        }
        
        print("Datos de la consulta:", destino, anno, date_filter_slot, rango_ventana, perfil)

        # Obtención de datos
        df = basic_df("cluster")
        if df.empty:
            dispatcher.utter_message(text="No se encontraron datos en la base de datos para esta consulta.")
            return [
                SlotSet("tipo_consulta_c", None),
                SlotSet("destino_c", None),
                SlotSet("anno_c", None),
                SlotSet("date_filter_c", None),
                SlotSet("rango_ventana", None),
                SlotSet("perfil", None),
                FollowupAction("action_listen"),
            ]
        
        print("-" * 20)
        print("DF ventana:", df.head())
        print("columnas:", df.columns)
        print("Destino:", destino)
        print("Año:", anno)
        print("Mes:", date_filter_slot)
        print("Rango ventana:", rango_ventana)
        print("Perfil:", perfil)

        destino_norm = normalize(destino)
        date_filter_slot_norm = normalize(date_filter_slot)

        if not all([destino_norm, anno, date_filter_slot_norm, rango_ventana, perfil]):
            dispatcher.utter_message(text="Falta información en los datos proporcionados. Por favor, verifica la información e inténtalo nuevamente.")
            return []
        
        # Ajuste especial de castellón
        if destino_norm == "castellón":
            destino_norm = "castellon de la plana"

        # ------------------------------------------
        #  FILTRADO
        # ------------------------------------------

        mask = pd.Series(True, index=df.index)
        if destino_norm != "todos":
            mask &= df["DESTINATION_CITY_NAME"] == destino_norm
        if anno:
            mask &= df["YEAR_KEY"] == int(anno)
        if date_filter_slot_norm and date_filter_slot_norm != "todos los meses":
            mask &= df["MONTH_KEY"] == date_filter_slot_norm
        if perfil and perfil != "Todos los perfiles":
            perfil_num = color_num_map.get(perfil)
            if perfil_num is not None:
                mask &= df["PAX_PROFILE_KEY"] == perfil_num         
        if rango_ventana:
            try:
                min_rango, max_rango = map(int, rango_ventana.split('-'))
                mask &= df["WINDOW_DAYS_NUM"].between(min_rango, max_rango)
            except Exception as e:
                print(f"Error al procesar rango_ventana: {rango_ventana} -> {e}")        

        filtered_df = df[mask]
        filtered_df = filtered_df[[
            "WINDOW_DAYS_NUM", "ORIGIN_COUNTRY_NAME", "ORIGIN_CITY_NAME", "YEAR_KEY", "PAX_PROFILE_KEY", "DESTINATION_CITY_NAME", "MONTH_KEY"
        ]].rename(columns={"WINDOW_DAYS_NUM": "Ventana de oportunidad"})

        print("Perfiles disponibles:", filtered_df["PAX_PROFILE_KEY"].unique())
        
        print("Filas después del filtrado:", len(filtered_df))
        if filtered_df.empty:
            print("No se encontraron resultados después del filtrado.")

        # destino_pretty = destino.capitalize() if destino_norm != "todos" else "Comunitat Valenciana"
        # origen_pais_pretty = origen_pais.title() if origen_pais_norm != "todos" else "todos los mercados"
        # month_pretty = date_filter_slot.lower() if date_filter_slot != "todos" else "todos los meses"

        # ------------------------------------------------------------------
        #  RESPUESTAS SEGÚN TIPO DE CONSULTA
        # ------------------------------------------------------------------
        try:
            if filtered_df.empty or filtered_df.empty:
                dispatcher.utter_message(text="Lamentablemente, no existe ninguna agrupación de ciudades con un comportamiento similar en las condiciones especificadas.")
         
            elif tipo_consulta == "Número y lista de ciudades":
                lista_ciudades = filtered_df["ORIGIN_CITY_NAME"].unique()
                n_ciudades = len(lista_ciudades)

                from collections import defaultdict

                CITY_TO_COUNTRY = {}
                for country, cities in PAISES_CIUDADES_CLUSTERS.items():
                    for city in cities:
                        CITY_TO_COUNTRY[city] = country.upper()

                ciudades_por_pais = defaultdict(list)
                for ciudad in lista_ciudades:
                    if ciudad == "mo i rana":
                        ciudad_pretty = "Mo i Rana"
                    else: 
                        ciudad_pretty = CITY_TRANSLATION_CLUSTERS.get(ciudad, ciudad.title())
                    pais = CITY_TO_COUNTRY.get(ciudad_pretty, "OTROS").upper()
                    ciudades_por_pais[pais].append(ciudad_pretty)

                if n_ciudades < 10:
                    ciudades_pretty_str = ""
                    for pais, ciudades in ciudades_por_pais.items():
                        ciudades_pretty_str += f"**{pais.title()}**  \n" + ", ".join(ciudades) + "  \n"
                    dispatcher.utter_message(text=f"Estas son las ciudades de origen con **comportamientos comunes**, agrupadas por país: \n\n {ciudades_pretty_str}")
                else:
                    def chunk_list(lst, n):
                        for i in range(0, len(lst), n):
                            yield lst[i:i + n]

                    elements = []
                    for pais, ciudades in sorted(ciudades_por_pais.items()):
                        chunks = list(chunk_list([f"▫️ {ciudad}" for ciudad in ciudades], 6))
                        for i, chunk in enumerate(chunks):
                            text = f"**{pais}**\n" + "\n".join(chunk) if i == 0 else "\n".join(chunk)
                            elements.append({"text": text})

                    message = {
                        "type": "text-carousel-template",
                        "payload": {
                            "template_type": "generic",
                            "elements": elements
                        }
                    }

                    dispatcher.utter_message(
                        text=f"☝️💡 Hay **{n_ciudades} ciudades** con un comportamiento similar en las condiciones especificadas. Aquí están agrupadas por país:",
                        attachment=message
                    )
         
         
            elif tipo_consulta == "Ranking de mercados por nº de ciudades":
                filtered_df["ORIGIN_COUNTRY_NAME"] = filtered_df["ORIGIN_COUNTRY_NAME"].str.title()
                df_ranking = (
                    filtered_df.groupby("ORIGIN_COUNTRY_NAME")["ORIGIN_CITY_NAME"]
                    .nunique()
                    .reset_index(name="Nº CIUDADES")
                    .sort_values(by="Nº CIUDADES", ascending=False)
                    .rename(columns={"ORIGIN_COUNTRY_NAME": "PAÍS"})
                )
                
                html_table = pretty_table(df_ranking)
                styled_html_table = f"""
                <div style="width: 109%; overflow-x: auto;">
                    <style>
                        table {{
                            width: 95%;
                            text-align: center;
                        }}
                        th, td {{
                            text-align: center;
                        }}
                    </style>
                    {html_table}
                </div>
                """

                dispatcher.utter_message(
                    text=f"{styled_html_table}"
    )

                    #     if date_filter_norm != "todos los meses":
            #         month_flight = get_month_name_after_days(month_pretty, ventana_media, int(anno))

            #         dispatcher.utter_message(text=f"_⇨ Se esperan {round(n_busquedas)} búsquedas en {month_pretty} para volar en {month_flight}_")


            # elif tipo_consulta == "Ranking de mercados de origen por ventana media":
            #     ranking_vo = filtered_df_v.groupby(["ORIGIN_COUNTRY_NAME"])["WINDOW_DAYS_NUM"].mean().round().astype(int).reset_index()
            #     ranking_b = filtered_df.groupby(["ORIGIN_COUNTRY_NAME"])["SEARCHS_MEAN_WINDOW_NUM"].sum().round().astype(int).reset_index()
                
            #     merged = pd.merge(ranking_vo, ranking_b, on="ORIGIN_COUNTRY_NAME", how="inner")
            #     merged = merged.sort_values(by="WINDOW_DAYS_NUM", ascending=False)
            #     merged["ORIGIN_COUNTRY_NAME"] = merged["ORIGIN_COUNTRY_NAME"].str.title()
            #     merged.rename(columns={"ORIGIN_COUNTRY_NAME": "Origen", "WINDOW_DAYS_NUM":"Ventana media", "SEARCHS_MEAN_WINDOW_NUM": "Búsq. totales"}, inplace=True)
                
            #     html_table = pretty_table(merged)
            #     dispatcher.utter_message(text=f"El ranking de mercados de origen según la ventana promedio a {destino_pretty} en {month_pretty} de {anno} es:\n\n {html_table}")

        except Exception as exc:
            dispatcher.utter_message(text=f"Error al procesar la consulta. Por favor prueba de nuevo.")
            print(f"Error al procesar la consulta: {exc}")

        # # Reset de slots y vuelta a escuchar
        return [
            SlotSet("tipo_consulta_c", None),
            SlotSet("destino_c", None),
            SlotSet("anno_c", None),
            SlotSet("date_filter_c", None),
            SlotSet("rango_ventana", None),
            SlotSet("perfil", None),
            FollowupAction("action_listen"),
        ]

# ---------------------------------------------------------------------------
# ACTION QUERY SNOWFLAKE INFLUENCIA CLIMA - PROVISIONAL
# ---------------------------------------------------------------------------

class ActionQuerySnowflakeClima(Action):
    def name(self):
        return "action_query_snowflake_clima"
    

    # ---------------------------------------------------------------------
    # MÉTODO PRINCIPAL
    # ---------------------------------------------------------------------
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        tipo_consulta = tracker.get_slot("tipo_consulta_cl")
        destino = tracker.get_slot("destino_cl")
        origen_pais = tracker.get_slot("origen_pais_cl")
        origen_ciudad = tracker.get_slot("origen_ciudad_cl")
        date_filter_slot = tracker.get_slot("date_filter_cl")
        clima = tracker.get_slot("clima_cl")
        tipo_variacion = tracker.get_slot("tipo_variacion_cl")
        
        print("Datos de la consulta:", destino, origen_pais, origen_ciudad, date_filter_slot, clima)

        df = basic_df("clima")
        df['YEAR_KEY'] = df['SEARCH_DAY_KEY'].dt.year
        df['MONTH_KEY'] = df['SEARCH_DAY_KEY'].dt.month        
        df["MONTH_KEY"] = df["MONTH_KEY"].replace(MONTH_NUM_TO_ES)
        
        df = df.drop(columns=["TEMPERATURE_MEAN_NUM", "TEMPERATURE_MIN_NUM", "TEMPERATURE_MAX_NUM"])
        
        if df.empty:
            dispatcher.utter_message(text="No se encontraron datos en la base de datos para esta consulta.")
            return [
                SlotSet("tipo_consulta_cl", None),
                SlotSet("destino_cl", None),
                SlotSet("origen_pais_cl", None),
                SlotSet("origen_ciudad_cl", None),
                SlotSet("date_filter_cl", None),
                SlotSet("clima_cl", None),
                SlotSet("tipo_variacion_cl", None),
                FollowupAction("action_listen"),
            ]
        
        print("-" * 20)
        print("DF clima:", df.head())
        print("Columnas:", df.columns)
        print("Destino:", destino)
        print("Origen país:", origen_pais)
        print("Origen ciudad:", origen_ciudad)
        print("Mes:", date_filter_slot)
        print("Clima:", clima)

        destino_norm = normalize(destino)
        origen_pais_norm = normalize(origen_pais)
        origen_ciudad_norm = normalize(origen_ciudad)
        date_filter_slot_norm = normalize(date_filter_slot)

        if not all([destino_norm, origen_pais_norm, origen_ciudad_norm, date_filter_slot_norm, clima]):
            dispatcher.utter_message(text="Falta información en los datos proporcionados. Por favor, verifica la información e inténtalo nuevamente.")
            return []
        
        if destino_norm == "castellón":
            destino_norm = "castellon de la plana"

        mask = pd.Series(True, index=df.index)
        if destino_norm != "todos":
            mask &= df["DESTINATION_CITY_NAME"] == destino_norm
        if origen_pais_norm != "todos":
            mask &= df["ORIGIN_COUNTRY_NAME"] == origen_pais_norm
        if origen_ciudad_norm != "todas":
            mask &= df["ORIGIN_CITY_NAME"] == origen_ciudad_norm
        if date_filter_slot_norm and date_filter_slot_norm != "todos los meses":
            mask &= df["MONTH_KEY"] == date_filter_slot_norm
        if clima and clima != "Todos los climas":
            if clima == 'Clima medio':
                df = df.drop(columns=["SEARCH_MIN_TEMPERATURE_NUM", "SEARCH_MAX_TEMPERATURE_NUM"])
            elif clima == 'Clima cálido':
                df = df.drop(columns=["SEARCH_MIN_TEMPERATURE_NUM", "SEARCH_MEAN_TEMPERATURE_NUM"])
            elif clima == 'Clima frío':
                df = df.drop(columns=["SEARCH_MEAN_TEMPERATURE_NUM", "SEARCH_MAX_TEMPERATURE_NUM"])    
     

        filtered_df = df[mask]
        print("Filas después del filtrado:", len(filtered_df))
        if filtered_df.empty:
            print("No se encontraron resultados después del filtrado.")

        # ------------------------------------------------------------------
        #  RESPUESTAS SEGÚN TIPO DE CONSULTA
        # ------------------------------------------------------------------
        try:
            if filtered_df.empty or filtered_df.empty:
                dispatcher.utter_message(text="Lamentablemente, no existen datos de búsquedas en las condiciones especificadas.")
            
            elif tipo_consulta == "Total de búsquedas según clima por origen":
                if clima and clima != "Todos los climas":
                    col_busquedas = None
                    for col in ["SEARCH_MIN_TEMPERATURE_NUM", "SEARCH_MEAN_TEMPERATURE_NUM", "SEARCH_MAX_TEMPERATURE_NUM"]:
                        if col in filtered_df.columns:
                            col_busquedas = col
                            break
                    if col_busquedas:
                        n_busquedas = filtered_df[col_busquedas].sum()
                        n_busquedas_pretty = format_number(n_busquedas)
                        clima = clima.lower()
                        dispatcher.utter_message(text=f"El **total de búsquedas** con {clima} para los parámetros seleccionados es de **{n_busquedas_pretty}.**")
                    else:
                        dispatcher.utter_message(text="No se encontró información al respecto en la base de datos.")
                else:
                    n_busquedas_tmedia = filtered_df["SEARCH_MEAN_TEMPERATURE_NUM"].sum()
                    n_busquedas_tmin = filtered_df["SEARCH_MIN_TEMPERATURE_NUM"].sum()
                    n_busquedas_tmax = filtered_df["SEARCH_MAX_TEMPERATURE_NUM"].sum()
                    df_clima = pd.DataFrame([{
                        "CLIMA FRÍO": int(n_busquedas_tmin),
                        "CLIMA MEDIO": int(n_busquedas_tmedia),
                        "CLIMA CÁLIDO": int(n_busquedas_tmax)
                    }])

                    html_table = pretty_table(df_clima)
                    styled_html_table = f"""
                    <div style="width: 105%; overflow-x: auto;">
                        <style>
                            th, td {{
                                text-align: center;
                            }}
                        </style>
                        {html_table}
                    </div>
                    """
                    dispatcher.utter_message(
                        text=f"**Total de búsquedas** según clima para los parámetros seleccionados: \n\n{styled_html_table}"
                    )
        
        except Exception as exc:
            dispatcher.utter_message(text=f"Error al procesar la consulta. Por favor prueba de nuevo.")
            print(f"Error al procesar la consulta: {exc}")

        return [
            SlotSet("tipo_consulta_cl", None),
            SlotSet("destino_cl", None),
            SlotSet("origen_pais_cl", None),
            SlotSet("origen_ciudad_cl", None),
            SlotSet("date_filter_cl", None),
            SlotSet("clima_cl", None),
            SlotSet("tipo_variacion_cl", None),
            FollowupAction("action_listen"),
        ]