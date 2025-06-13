
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
from sklearn.utils import resample
from xgboost import XGBClassifier
from collections import Counter
import warnings
warnings.filterwarnings("ignore")

# Leer datos desde GCS
modelo = pd.read_csv('https://storage.googleapis.com/ml_exito/modelo.csv')

# Columnas de entrada
features = [
    'latitude', 'longitude','locales_en_condado','prom_resenas_condado',
    'mujeres_total','porc_positivas_condado','hombres_total',
    'GoodForKids','edad_media', 'locales_por_1000hab',
    'poblacion_total', 'prom_stars_condado','Caters','meal_dinner','music_dj',
    'meal_lunch','dietary_gluten_free','OutdoorSeating','Alcohol','meal_breakfast','bestnight_friday'
]

X = modelo[features].apply(pd.to_numeric, errors='coerce').fillna(0)
y = modelo['exito']

# Oversampling para balancear clases
X_0 = X[y == 0]
X_1 = X[y == 1]
y_0 = y[y == 0]
y_1 = y[y == 1]
X_1_upsampled, y_1_upsampled = resample(X_1, y_1,
    replace=True, n_samples=len(y_0) // 2, random_state=42)
X_train = pd.concat([X_0, X_1_upsampled])
y_train = pd.concat([y_0, y_1_upsampled])

# Conjunto de test
X_test, _, y_test, _ = train_test_split(X, y, test_size=0.3, stratify=y, random_state=42)

# Entrenar modelo
scale_pos_weight = 0.6
xgb = XGBClassifier(
    n_estimators=400,
    max_depth=5,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    gamma=1,
    min_child_weight=3,
    scale_pos_weight=scale_pos_weight,
    use_label_encoder=False,
    eval_metric='logloss',
    random_state=42
)
xgb.fit(X_train, y_train)
# Evaluación
umbral = 0.8
y_proba = xgb.predict_proba(X_test)[:, 1]
y_pred = (y_proba >= umbral).astype(int)

import joblib
joblib.dump(xgb, 'modelo_exito.pkl')
