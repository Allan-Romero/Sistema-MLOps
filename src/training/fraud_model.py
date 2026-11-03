"""Adaptador persistible: mismo contrato predict/predict_proba que churn."""

import numpy as np


class ThresholdClassifier:
    """Aplica un umbral aprendido en validación; nunca usa etiquetas del test."""

    def __init__(self, estimator, threshold, feature_names):
        self.estimator = estimator
        self.threshold = float(threshold)
        if not (0 < self.threshold <= 1):
            raise ValueError("El umbral debe estar entre 0 (exclusivo) y 1.")
        self.feature_names_in_ = np.asarray(tuple(feature_names), dtype=object)

    def predict_proba(self, x):
        return self.estimator.predict_proba(x)

    def predict(self, x):
        probabilidad = self.predict_proba(x)[:, 1]
        return (probabilidad >= self.threshold).astype(int)
