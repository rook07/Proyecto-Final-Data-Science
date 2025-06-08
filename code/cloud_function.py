import os
import re
import json
import ast
import requests
import numpy as np
import pandas as pd
from datetime import datetime
from io import StringIO, BytesIO
import mysql.connector
from google.cloud import storage

# ---------------------------
# CONFIGURACIÓN
# ---------------------------
GCS_BUCKET = "pf-yelp-gmaps-datalake"
YELP_BUSINESS_PATH = "raw_data_parquet/yelp/business.parquet"
YELP_REVIEWS_PATH = "raw_data_parquet/yelp/review.parquet"
GMAPS_META_PATH = "raw_data_parquet/GoogleMaps/metadata-sitios"
GMAPS_REVIEW_PATH = "raw_data_parquet/GoogleMaps/review-estados/California"

MYSQL_CONFIG = {
    'host': '34.27.253.100',
    'user': 'u143586701_PF_ADMIN',
    'password': 's/qi#*/43T>',
    'database': 'bd_proyecto_fianl',
    'port': 3306
}

# ---------------------------
# LECTURA DESDE GCS
# ---------------------------

def read_parquet_from_gcs(bucket_name, blob_path):
    """Lee un archivo Parquet desde GCS"""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_path)
    
    with blob.open("rb") as f:
        return pd.read_parquet(f)

def read_multiple_parquets(bucket_name, prefix):
    """Lee múltiples archivos Parquet desde un prefijo en GCS"""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=prefix)
    
    dfs = []
    for blob in blobs:
        if blob.name.endswith(".parquet"):
            with blob.open("rb") as f:
                dfs.append(pd.read_parquet(f))
    
    return pd.concat(dfs, ignore_index=True)

# ---------------------------
# PROCESAMIENTO DE DATOS
# ---------------------------

def process_yelp_business(business_df):
    # Quitar columnas duplicadas por nombre (solo mantener la primera)
    business_df = business_df.loc[:, ~business_df.columns.duplicated()]

    # Eliminar columnas duplicadas que terminan en .1
    business = business_df.loc[:, ~business_df.columns.str.endswith('.1')]

    # Manejo de vacíos en 'categories' y otros campos clave
    business['categories'] = business['categories'].fillna("")
    business['state'] = business['state'].fillna("")
    business['categories'] = business['categories'].astype(str)

    # Filtrar por fast food
    fast_food_mask = business['categories'].apply(
        lambda x: any(re.search(r'fast food', c, re.IGNORECASE) for c in x.split(', '))
    )

    # Filtrar solo los de California
    ca_mask = business["state"] == "CA"

    # Aplicar filtros combinados con índice alineado
    filtered = business[fast_food_mask & ca_mask].copy()

    # Eliminar columnas innecesarias
    columns_to_drop = ['is_open', "hours", "postal_code", "stars", "review_count"]
    filtered = filtered.drop(columns=[col for col in columns_to_drop if col in filtered.columns], errors='ignore')

    # Limpiar nulos generales
    filtered = filtered.dropna(subset=['latitude', 'longitude', 'name'])

    return filtered

def process_yelp_reviews(reviews_df):
    review = reviews_df.drop(["funny", "cool", "useful", "review_id", "user_id"], axis=1)
    review['date'] = pd.to_datetime(review['date']).dt.normalize()
    review = review[review["date"] >= "2016-01-01"]
    review.drop_duplicates(inplace=True)
    return review

def remove_unhashable_columns_for_dedup(df: pd.DataFrame) -> pd.DataFrame:
    unhashable_types = (list, dict, np.ndarray)
    cols_unhashable = df.columns[df.map(lambda x: isinstance(x, unhashable_types)).any()]
    df_hashable = df.drop(columns=cols_unhashable)
    df = df_hashable.drop_duplicates().join(df[cols_unhashable])
    return df

def clean_and_merge_data(df_reviews: pd.DataFrame, df_sitios: pd.DataFrame) -> pd.DataFrame:
    df_reviews = remove_unhashable_columns_for_dedup(df_reviews)
    df_sitios = remove_unhashable_columns_for_dedup(df_sitios)
    df_reviews = df_reviews.dropna(subset=["rating"])
    df_reviews['date'] = pd.to_datetime(df_reviews['time'], unit='ms', errors='coerce')

    df_merged = pd.merge(df_reviews, df_sitios, how='left', on='gmap_id')
    df_merged.dropna(inplace=True)
    df_merged['category'] = df_merged['category'].astype(str).str.lower()
    df_merged = df_merged[df_merged['category'].str.contains("fast food", na=False)]
    df_merged = df_merged[df_merged['date'].dt.year >= 2016]

    df1 = df_merged[['name_y', 'longitude', 'latitude']].drop_duplicates().reset_index(drop=True)
    df1 = add_city_and_state_columns(df1)
    df1 = df1.dropna(subset=['city']).reset_index(drop=True)
    df_merged = pd.merge(df_merged, df1, on=["name_y", "longitude", "latitude"], how="inner")

    columnas_finales = ['rating', 'address', 'text', 'name_y', 'MISC', 'latitude', 'longitude', 'date', 'city']
    return df_merged[columnas_finales]

def add_city_and_state_columns(df):
    df[['city', 'state']] = df.apply(
        lambda row: pd.Series(get_city_and_state_from_coordinates(row['latitude'], row['longitude'])),
        axis=1
    )
    return df

def get_city_and_state_from_coordinates(lat, lon):
    api_key = "AIzaSyBLoxHUAaPY44LSWhXvTlbn7PU60Uy92sM"
    url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lon}&key={api_key}"

    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        city = "Unknown"
        state = "CA"  # Por defecto California ya que filtramos por CA

        if data["results"]:
            for component in data["results"][0]["address_components"]:
                if "locality" in component["types"]:
                    city = component["long_name"]
                elif "administrative_area_level_1" in component["types"]:
                    state = component["short_name"]

        return city, state
    else:
        return "Unknown", "CA"

# ---------------------------
# PROCESAMIENTO MEJORADO DE ATRIBUTOS
# ---------------------------

def process_attributes(df, attr_col='Attributes'):
    """Procesa la columna de atributos a formato binario basado en tu función que funciona correctamente"""
    parsed_dicts = []
    all_keys = set()

    for val in df[attr_col]:
        row_dict = {}
        if pd.isna(val):
            parsed_dicts.append(row_dict)
            continue

        try:
            parsed = ast.literal_eval(val)
            if isinstance(parsed, dict):
                for k, v in parsed.items():
                    try:
                        inner_val = ast.literal_eval(v) if isinstance(v, str) else v
                        if isinstance(inner_val, dict):
                            for sub_k, sub_v in inner_val.items():
                                col_name = f"{k}_{sub_k}"
                                row_dict[col_name] = str(sub_v).strip().lower() == 'true'
                                all_keys.add(col_name)
                        else:
                            row_dict[k] = str(inner_val).strip().lower() == 'true'
                            all_keys.add(k)
                    except:
                        row_dict[k] = str(v).strip().lower() == 'true'
                        all_keys.add(k)
        except:
            pass

        parsed_dicts.append(row_dict)

    # Crear DataFrame binario con 0s y 1s
    binary_data = []
    for row in parsed_dicts:
        row_data = {key: 1 if row.get(key, False) else 0 for key in all_keys}
        binary_data.append(row_data)

    binary_df = pd.DataFrame(binary_data)

    # Unir al DataFrame original
    df_final = pd.concat([df.reset_index(drop=True), binary_df.reset_index(drop=True)], axis=1)
    
    return df_final, list(all_keys)

# ---------------------------
# CARGA A MYSQL
# ---------------------------

def process_attributes_and_insert_businesses_and_cities(df, mysql_config):
    # Procesar atributos usando la función mejorada
    df_final, attribute_columns = process_attributes(df.copy(), 'Attributes')
    
    # Crear mapa de ciudades
    unique_cities = df_final['City'].dropna().unique()
    city_map = {city: i+1 for i, city in enumerate(sorted(unique_cities))}
    df_final['county_id'] = df_final['City'].map(city_map)

    # Conexión a MySQL
    conn = mysql.connector.connect(**mysql_config)
    cursor = conn.cursor()

    # Insertar ciudades
    insert_city_stmt = """
        INSERT INTO counties (id_county, name_county) VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE name_county = VALUES(name_county)
    """

    for city, id_city in city_map.items():
        cursor.execute(insert_city_stmt, (id_city, city))
    conn.commit()

    # Insertar negocios
    df_final.drop_duplicates(subset=["Business_Id"], inplace=True)
    
    columnas_requeridas = [
        "Business_Id", "Business_Name", "Address", "county_id", "Latitude", "Longitude"
    ] + attribute_columns

    df_final = df_final[columnas_requeridas]

    columnas_sql = ",".join(f"`{col}`" for col in df_final.columns)
    placeholders = ",".join(["%s"] * len(df_final.columns))

    insert_stmt = f"""
        INSERT INTO businesses ({columnas_sql}) 
        VALUES ({placeholders})
    """
    
    # Insertar en lotes para mejor performance
    batch_size = 100
    for i in range(0, len(df_final), batch_size):
        batch = df_final.iloc[i:i+batch_size]
        rows = [tuple(row) for row in batch.values]
        cursor.executemany(insert_stmt, rows)
        conn.commit()

    cursor.close()
    conn.close()

def insert_reviews_from_final_df(df_final, mysql_config):
    # Validar columnas necesarias
    required_cols = ["Business_Id", "Stars", "Date", "Text"]
    for col in required_cols:
        if col not in df_final.columns:
            raise ValueError(f"Falta la columna requerida: {col}")

    # Preparar los datos
    df_reviews = df_final[required_cols].copy()
    df_reviews.dropna(subset=["Business_Id", "Stars", "Date", "Text"], inplace=True)
    #df_reviews["Date"] = pd.to_datetime(df_reviews["Date"], errors="coerce")
    df_reviews.dropna(subset=["Date"], inplace=True)
    df_reviews["Text"] = df_reviews["Text"].astype(str).str.strip()
    df_reviews['Date'] = df_reviews['Date'].dt.date
    # Asignar columnas de sentimiento por defecto
    df_reviews["positive_sentiment"] = 0
    df_reviews["neutral_sentiment"] = 0
    df_reviews["negative_sentiment"] = 0

    # Conectar a MySQL
    conn = mysql.connector.connect(**mysql_config)
    cursor = conn.cursor()

    insert_review_stmt = """
        INSERT INTO business_reviews (
            business_id, stars, review_date, text_review,
            positive_sentiment, neutral_sentiment, negative_sentiment
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    # Insertar en lotes para mejor performance
    batch_size = 100
    for i in range(0, len(df_reviews), batch_size):
        batch = df_reviews.iloc[i:i+batch_size]
        rows = []
        for _, row in batch.iterrows():
            rows.append((
                row["Business_Id"],
                row["Stars"],
                row["Date"],
                row["Text"],
                row["positive_sentiment"],
                row["neutral_sentiment"],
                row["negative_sentiment"]
            ))
        cursor.executemany(insert_review_stmt, rows)
        conn.commit()

    cursor.close()
    conn.close()

# ---------------------------
# FUNCIÓN PRINCIPAL PARA CLOUD RUN
# ---------------------------

def etl_entry_point(request):
    """Función principal que se ejecuta en Cloud Run"""
    try:
        print("📦 Leyendo Yelp...")
        yelp_business = read_parquet_from_gcs(GCS_BUCKET, YELP_BUSINESS_PATH)
        yelp_reviews = read_parquet_from_gcs(GCS_BUCKET, YELP_REVIEWS_PATH)
        
        df_yelp_business_processed = process_yelp_business(yelp_business)
        df_yelp_reviews_processed = process_yelp_reviews(yelp_reviews)
        
        df_yelp_processed = df_yelp_reviews_processed.merge(
            df_yelp_business_processed, on="business_id", how="inner"
        )
        
        df_yelp_processed = df_yelp_processed[[
            "stars", "text", "date", "name", "address", "city", 
            "latitude", "longitude", "attributes"
        ]]
        
        df_yelp_processed = df_yelp_processed.rename(columns={
            "name": 'Business_Name', "stars": 'Stars', "address": 'Address',
            "city": 'City', "latitude": 'Latitude', "longitude": 'Longitude',
            "date": "Date", "text": 'Text', "attributes": "Attributes"
        })

        print("📦 Leyendo Google Maps...")
        gmaps_meta = read_multiple_parquets(GCS_BUCKET, GMAPS_META_PATH)
        gmaps_reviews = read_multiple_parquets(GCS_BUCKET, GMAPS_REVIEW_PATH)
        
        df_gmaps_processed = clean_and_merge_data(gmaps_reviews, gmaps_meta)
        df_gmaps_processed = df_gmaps_processed.rename(columns={
            "name_y": 'Business_Name', "rating": 'Stars', "address": 'Address',
            "city": 'City', "latitude": 'Latitude', "longitude": 'Longitude',
            "date": "Date", "text": 'Text', "MISC": "Attributes"
        })

        print("🔗 Uniendo datasets...")
        combined_df = pd.concat([df_yelp_processed, df_gmaps_processed]).reset_index(drop=True)
        
        df_business = combined_df[["Business_Name", 'Latitude', 'Longitude']].drop_duplicates().reset_index(drop=True)
        df_business["Business_Id"] = df_business.index + 1
        combined_df = pd.merge(combined_df, df_business, on=["Business_Name", 'Latitude', 'Longitude'], how="left")
        
        final_df = combined_df[[
            'Business_Id', 'Business_Name', 'Stars', 'Address', 'City',
            'Latitude', 'Longitude', "Date", 'Text', "Attributes"
        ]]
        final_df["Date"] = pd.to_datetime(final_df["Date"], errors="coerce")
        # Guardar CSV en GCS
        print("💾 Guardando CSV en GCS...")
        storage_client = storage.Client()
        bucket = storage_client.bucket(GCS_BUCKET)
        blob = bucket.blob("processed_data/final_output.csv")
        
        csv_buffer = StringIO()
        final_df.to_csv(csv_buffer, index=False)
        blob.upload_from_string(csv_buffer.getvalue(), content_type="text/csv")

        # Cargar a MySQL
        print("🗄 Cargando datos a MySQL...")
        process_attributes_and_insert_businesses_and_cities(final_df.copy(), MYSQL_CONFIG)
        insert_reviews_from_final_df(final_df, MYSQL_CONFIG)

        return "✅ ETL completado exitosamente", 200

    except Exception as e:
        print(f"❌ Error en el proceso ETL: {str(e)}")
        return f"Error en el proceso ETL: {str(e)}", 500

if __name__ == "__main__":
    # Para pruebas locales, simular el entorno de Cloud Run
    etl_entry_point(None)