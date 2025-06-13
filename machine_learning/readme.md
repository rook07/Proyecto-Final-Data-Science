# Modelo de Éxito para Locales Comerciales

Este proyecto utiliza XGBoost para predecir la probabilidad de éxito de un local en función de atributos del negocio, características demográficas y contexto geográfico.

## 🧠 Metodología

1. Limpieza y selección de variables relevantes.
2. Balanceo de clases con `resample` (oversampling).
3. Entrenamiento con `XGBoostClassifier`, ajustando `scale_pos_weight`.
4. Evaluación con métricas como precisión, recall y AUC.
5. Ajuste de umbral de decisión a 0.8 para mejorar precisión en clase positiva.

## 🏆 Resultado

El modelo logra una precisión del ~81% para la clase de éxito, con un recall de ~74% y AUC superior a 0.97.

## 📊 Features utilizados

- Ubicación (`latitude`, `longitude`)
- Demografía (`mujeres_total`, `hombres_total`, `edad_media`)
- Popularidad y reputación (`prom_stars_condado`, `prom_resenas_condado`, `porc_positivas_condado`)
- Atributos del local (`GoodForKids`, `Caters`, etc.)

## 🛠️ Cómo usar

```bash
pip install -r requirements.txt
python src/entrenamiento.py
```
