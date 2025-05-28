
# gmaps_etl_final_column_filtered_multicategory_filtered.py

import os
import pandas as pd

# -----------------------------
# FUNCIONES
# -----------------------------

def load_json_folder(folder_path: str, file_count: int) -> pd.DataFrame:
    """
    Carga múltiples archivos JSON desde una carpeta y los concatena en un solo DataFrame.
    """
    dataframes = []
    for i in range(1, file_count + 1):
        path = os.path.join(folder_path, f'{i}.json')
        df = pd.read_json(path, lines=True)
        dataframes.append(df)
    return pd.concat(dataframes, ignore_index=True)

def remove_unhashable_columns_for_dedup(df: pd.DataFrame) -> pd.DataFrame:
    """
    Elimina duplicados ignorando columnas con listas o diccionarios no hashables.
    """
    unhashable_types = (list, dict)
    cols_unhashable = df.columns[df.applymap(lambda x: isinstance(x, unhashable_types)).any()]
    df_hashable = df.drop(columns=cols_unhashable)
    df = df_hashable.drop_duplicates().join(df[cols_unhashable])
    return df

def clean_and_merge_data(df_reviews: pd.DataFrame, df_sitios: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica transformaciones:
    - Limpia duplicados
    - Convierte timestamp a fecha
    - Une datasets
    - Filtra categorías fast food y hamburger
    - Filtra por fecha desde 2016
    - Deja columnas finales
    """
    df_reviews = remove_unhashable_columns_for_dedup(df_reviews)
    df_sitios = remove_unhashable_columns_for_dedup(df_sitios)

    df_reviews = df_reviews.dropna(subset=["rating"])

    df_reviews['date'] = pd.to_datetime(df_reviews['time'], unit='ms', errors='coerce')

    df_merged = pd.merge(df_reviews, df_sitios, how='left', on='gmap_id')

    # Limpiar columna 'category' manteniendo múltiples categorías
    df_merged['category'] = (
        df_merged['category']
        .astype(str)
        .str.replace(r"[\[\]']", "", regex=True)
        .str.lower()
        .str.strip()
    )

    # Filtrar solo si contiene 'fast food' o 'hamburger'
    df_merged = df_merged[df_merged['category'].str.contains("fast food|hamburger", na=False)]

    # Filtrar por fecha desde 2016
    df_merged = df_merged[df_merged['date'].dt.year >= 2016]

    columnas_finales = [
        'user_id', 'time', 'rating', 'text', 'name_y', 'address',
        'latitude', 'longitude', 'category', 'MISC', 'date'
    ]
    df_merged = df_merged[columnas_finales]

    return df_merged

# -----------------------------
# FUNCIÓN PRINCIPAL
# -----------------------------

def main():
    """
    Ejecuta la limpieza y exporta el CSV final con categorías relevantes.
    """
    folder_reviews = '/Users/michel/Desktop/Proyecto Grupal Axon/Datasets Google/review-California'
    folder_sitios = '/Users/michel/Desktop/Proyecto Grupal Axon/Datasets Google/metadata-sitios'

    df_reviews = load_json_folder(folder_reviews, 18)
    df_sitios = load_json_folder(folder_sitios, 11)

    df_final = clean_and_merge_data(df_reviews, df_sitios)

    output_path = '/Users/michel/Desktop/gmaps_data_clean_filtered.csv'
    df_final.to_csv(output_path, index=False)
    print(f"✅ Transformación completada y archivo guardado en: {output_path}")

# -----------------------------
# EJECUCIÓN
# -----------------------------
if __name__ == '__main__':
    main()
