import os
import io
import shutil
import pandas as pd
from io import StringIO
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.cloud import storage
import pyarrow.parquet as pq
import pyarrow.fs as pafs
from collections import defaultdict

def data_summ_on_parquet_by_folder(bucket_name, root_folder_gcs):
    '''
    Aplica la función data_summ a cada carpeta de Parquet dentro de un bucket en GCS.
    Consolida todos los archivos .parquet de cada carpeta en un solo DataFrame antes de resumir.

    Parámetros:
    - bucket_name (str): Nombre del bucket de GCS.
    - root_folder_gcs (str): Ruta base donde se encuentran las subcarpetas de archivos Parquet (sin "gs://").

    Retorna:
    - summaries (list): Lista de DataFrames con la información resumen por carpeta.
    '''
    summaries = []
    gcs = pafs.GcsFileSystem()
    root_path = f"{bucket_name}/{root_folder_gcs}".rstrip('/')

    # Buscar todos los archivos bajo la raíz, incluyendo subcarpetas
    files_info = gcs.get_file_info(pafs.FileSelector(root_path, recursive=True))
    
    # Agrupar archivos por carpeta
    folder_files = defaultdict(list)
    for f in files_info:
        if f.is_file and f.path.endswith('.parquet'):
            folder = '/'.join(f.path.split('/')[:-1])
            folder_files[folder].append(f.path)

    for folder_path, file_paths in folder_files.items():
        dataframes = []

        for file_path in file_paths:
            try:
                with gcs.open_input_file(file_path) as f:
                    df = pq.read_table(f).to_pandas()
                    dataframes.append(df)
            except Exception as e:
                print(f"⚠️ Error leyendo {file_path}: {e}")

        if dataframes:
            try:
                df_all = pd.concat(dataframes, ignore_index=True)
                title = folder_path.split('/')[-1]
                summary = data_summ(df_all, title=title)
                summaries.append(summary)
            except Exception as e:
                print(f"❌ Error procesando carpeta {folder_path}: {e}")
    
    return summaries

def data_summ(df, title=None):
    '''
    Function to provide detailed information about the dtype, null values,
    and outliers for each column in a DataFrame.

    Parameters:
    - df (pd.DataFrame): The DataFrame for generating information.
    - title (str, optional): Title to be used in the summary. If None, the title will be omitted.

    Returns:
    - df_info (pd.DataFrame): A DataFrame containing information about each column,
                              including data type, non-missing quantity, percentage of
                              missing values, missing quantity, and information about outliers.
    '''
    info_dict = {"Column": [], "Data_type": [], "No_miss_Qty": [], "%Missing": [], "Missing_Qty": []}

    for column in df.columns:
        info_dict["Column"].append(column)
        info_dict["Data_type"].append(df[column].apply(type).unique())
        info_dict["No_miss_Qty"].append(df[column].count())
        info_dict["%Missing"].append(round(df[column].isnull().sum() * 100 / len(df), 2))
        info_dict['Missing_Qty'].append(df[column].isnull().sum())

  
    df_info = pd.DataFrame(info_dict)

    if title:
        print(f"{title} Summary")
        print("\nTotal rows: ", len(df))
        print("\nTotal full null rows: ", df.isna().all(axis=1).sum())
        print(df_info.to_string(index=False))
        print("=====================================")

    return df_info

def data_summ_on_parquet_gcs(bucket_name, folder_path_gcs):
    '''
    Aplica la función data_summ a cada archivo Parquet en una carpeta de un bucket en GCS.

    Parámetros:
    - bucket_name (str): Nombre del bucket de GCS.
    - folder_path_gcs (str): Ruta de la carpeta dentro del bucket (sin "gs://").

    Retorna:
    - summaries (list): Lista de DataFrames con la información resumen de cada archivo Parquet.
    '''
    summaries = []
    
    # Crear sistema de archivos para acceder GCS
    gcs = pafs.GcsFileSystem()
    base_path = f"{bucket_name}/{folder_path_gcs}".rstrip('/')

    # Listar archivos en el directorio de GCS
    files_info = gcs.get_file_info(pafs.FileSelector(base_path, recursive=False))
    
    for file_info in files_info:
        if file_info.is_file and file_info.path.endswith('.parquet'):
            file_path = file_info.path
            title = file_path.split('/')[-1].replace('.parquet', '')
            
            # Leer el archivo Parquet desde GCS
            with gcs.open_input_file(file_path) as f:
                df = pq.read_table(f).to_pandas()
            
            # Aplicar función de resumen
            summary = data_summ(df, title=title)
            summaries.append(summary)

    return summaries

    
def extract_to_parquet_GCS(FOLDER_ID: str, BUCKET_NAME: str, GCS_FOLDER: str) -> None:
    """
    Descarga archivos desde una carpeta de Google Drive, los transforma a formato Parquet si es necesario 
    (JSON o PKL), y los sube a un bucket de Google Cloud Storage (GCS). 
    Los archivos originales se almacenan y procesan temporalmente en el disco de la instancia 
    y luego se eliminan.

    Archivos soportados:
        - .json: procesado por chunks y consolidado en un único archivo Parquet.
        - .pkl: convertido a Parquet.
        - .parquet: subido directamente sin transformación.
    
    Requiere credenciales de servicio para autenticación con Google Drive y GCS.

    Parámetros:
    ----------
    FOLDER_ID : str
        ID de la carpeta de Google Drive que contiene los archivos a procesar.
    BUCKET_NAME : str
        Nombre del bucket de Google Cloud Storage donde se almacenarán los archivos transformados.
    GCS_FOLDER : str
        Ruta dentro del bucket de GCS donde se guardarán los archivos Parquet (puede incluir subcarpetas).

    Ejemplo de uso:
    --------------
    extract_to_parquet_GCS(
        FOLDER_ID='1abcD23EfGhIjKlmNopQ456rsTuvWxYz9',
        BUCKET_NAME='mi-datalake-bucket',
        GCS_FOLDER='raw/parquet_files/'
    )
    """
    # --- Variables para autenticación y path temporal
    CREDENTIALS_PATH = './credentials.json'
    TEMP_DIR = '/home/jupyter/temp_drive_files'
    # --- AUTENTICACIÓN CON GOOGLE DRIVE Y GCS ---
    credentials = service_account.Credentials.from_service_account_file(
        CREDENTIALS_PATH,
        scopes=["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/cloud-platform"]
        )
    drive_service = build('drive', 'v3', credentials=credentials)
    storage_client = storage.Client(credentials=credentials)

    # --- CREAR CARPETA TEMPORAL ---
    os.makedirs(TEMP_DIR, exist_ok=True)

    # --- LISTAR ARCHIVOS EN LA CARPETA DE GOOGLE DRIVE ---
    results = drive_service.files().list(q=f"'{FOLDER_ID}' in parents").execute()
    files = results.get('files', [])

    # --- PROCESAR ARCHIVOS ---
    for file in files:
        file_id = file['id']
        file_name = file['name']
        local_path = os.path.join(TEMP_DIR, file_name)

        # Descargar archivo
        request = drive_service.files().get_media(fileId=file_id)
        with io.FileIO(local_path, 'wb') as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                print(f"Descargando {file_name}... {int(status.progress() * 100)}%", end="\r")

        try:
            if file_name.endswith('.json'):
                CHUNK_SIZE = 100_000  # Puedes ajustar según RAM
                temp_chunks = []

                with open(local_path, 'r') as f:
                    buffer = []
                    for i, line in enumerate(f):
                        buffer.append(line)
                        if (i + 1) % CHUNK_SIZE == 0:
                            try:
                                df_chunk = pd.read_json(StringIO(''.join(buffer)), lines=True)
                                temp_chunks.append(df_chunk)
                                buffer.clear()
                            except Exception as e:
                                print(f"⚠️ Error procesando chunk {len(temp_chunks)} de {file_name}: {e}")
                                buffer.clear()
                                continue

                    # Último chunk restante
                    if buffer:
                        try:
                            df_chunk = pd.read_json(StringIO(''.join(buffer)), lines=True)
                            temp_chunks.append(df_chunk)
                        except Exception as e:
                            print(f"⚠️ Error procesando chunk final de {file_name}: {e}")

                try:
                    # Consolidar todos los chunks
                    df_all = pd.concat(temp_chunks, ignore_index=True)
                    df_all = df_all.loc[:, ~df_all.columns.duplicated()]  # Eliminar columnas duplicadas

                    # Guardar Parquet final
                    parquet_name = file_name.replace('.json', '.parquet')
                    parquet_path = os.path.join(TEMP_DIR, parquet_name)
                    df_all.to_parquet(parquet_path, index=False)
                
                except Exception as e:
                    print(f"❌ Error consolidando y subiendo {file_name}: {e}")

                
            elif file_name.endswith('.pkl'):
                df = pd.read_pickle(local_path)
                df = df.loc[:, ~df.columns.duplicated()]  # Eliminar columnas duplicadas
                parquet_name = file_name.replace('.pkl', '.parquet')
                parquet_path = os.path.join(TEMP_DIR, parquet_name)
                df.to_parquet(parquet_path, index=False)
                
            elif file_name.endswith('.parquet'):
                # Ya está en formato parquet, se sube directamente
                parquet_path = local_path
                parquet_name = file_name
                
            else:
                print(f"❌ Formato no soportado: {file_name}")
                continue

            # Subir a GCS
            blob_path = f"{GCS_FOLDER}{parquet_name}"
            bucket = storage_client.bucket(BUCKET_NAME)
            blob = bucket.blob(blob_path)
            blob.upload_from_filename(parquet_path)
            print(f"\n✅ {parquet_name} subido a gs://{BUCKET_NAME}/{blob_path}")

        except Exception as e:
            print(f"⚠️ Error procesando {file_name}: {e}")
            continue

    # --- LIMPIAR ARCHIVOS TEMPORALES ---
    shutil.rmtree(TEMP_DIR)
    print("🚮 Todos los archivos temporales fueron eliminados.")
