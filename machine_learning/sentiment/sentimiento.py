import pandas as pd
from sqlalchemy import create_engine, text
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from tqdm import tqdm
import time


nltk.download('vader_lexicon')
sia = SentimentIntensityAnalyzer()

df =pd.read_csv(r"C:\Users\ruizr\Desktop\datos\data_limpia\reviews actualizada.csv")
df = df.drop_duplicates(subset='id_review') 
print(f"Total de filas a procesar: {len(df)}")

# Clasificación de sentimiento
def analizar_sentimiento(texto):
    if not isinstance(texto, str):
        return (0, 0, 0)
    scores = sia.polarity_scores(texto)
    if scores['compound'] >= 0.05:
        return (1, 0, 0)
    elif scores['compound'] <= -0.05:
        return (0, 1, 0)
    else:
        return (0, 0, 1)

df[['positive_sentiment', 'neutral_sentiment', 'negativ_sentiment']] = df['text_review'].apply(lambda x: pd.Series(analizar_sentimiento(x)))

# Guardar backup local
df.to_csv("dataset_analizado.csv", index=False)

# Conexión a la base
user = "u143586701_PF_ADMIN"
password = "s/qi#*/43T>"
host = '34.27.253.100'
port = "3306"
database = 'bd_proyecto_fianl'
engine = create_engine(f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}")

# Dividir en bloques pequeños
bloque_size = 50
total = len(df)
bloques = [df[i:i+bloque_size] for i in range(0, total, bloque_size)]

print(f"🔄 Procesando {total} filas en {len(bloques)} bloques...")

#Ejecutar bloque por bloque
for bloque in tqdm(bloques, desc="Actualizando por bloques"):
    time.sleep(1.5)  #tiempo de espera
    with engine.begin() as conn:
        query = text("""
            UPDATE business_reviews
            SET positive_sentiment = :pos,
                neutral_sentiment = :neu,
                negative_sentiment = :neg
            WHERE id_review = :id
        """)
        conn.execute(query, [
            {
                'pos': int(row['positive_sentiment']),
                'neg': int(row['negative_sentiment']),
                'neu': int(row['neutral_sentiment']),
                'id': int(row['id_review'])
            }
            for _, row in bloque.iterrows()
        ])

print("✅ Actualización completada correctamente.")
