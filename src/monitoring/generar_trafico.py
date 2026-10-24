import os
import random

import requests

# Dentro de docker compose se apunta al servicio api (API_URL=http://api:8000)
API_URL = os.getenv("API_URL", "http://localhost:8000")
URL = f"{API_URL}/predict"

CONTRATOS = ["Month-to-month", "One year", "Two year"]
PAGOS = ["Electronic check", "Mailed check",
         "Bank transfer (automatic)", "Credit card (automatic)"]
SI_NO = ["Yes", "No"]
INTERNET = ["DSL", "Fiber optic", "No"]
SERVICIO = ["Yes", "No", "No internet service"]


def cliente_aleatorio():
    tenure = random.randint(1, 72)
    cargo_mensual = round(random.uniform(20, 120), 2)
    return {
        "gender": random.choice(["Female", "Male"]),
        "SeniorCitizen": random.choice([0, 1]),
        "Partner": random.choice(SI_NO),
        "Dependents": random.choice(SI_NO),
        "tenure": tenure,
        "PhoneService": "Yes",
        "MultipleLines": random.choice(["Yes", "No"]),
        "InternetService": random.choice(INTERNET),
        "OnlineSecurity": random.choice(SERVICIO),
        "OnlineBackup": random.choice(SERVICIO),
        "DeviceProtection": random.choice(SERVICIO),
        "TechSupport": random.choice(SERVICIO),
        "StreamingTV": random.choice(SERVICIO),
        "StreamingMovies": random.choice(SERVICIO),
        "Contract": random.choice(CONTRATOS),
        "PaperlessBilling": random.choice(SI_NO),
        "PaymentMethod": random.choice(PAGOS),
        "MonthlyCharges": cargo_mensual,
        "TotalCharges": round(cargo_mensual * tenure, 2),
    }


def main(cantidad=150):
    exitosas = 0
    for i in range(cantidad):
        respuesta = requests.post(URL, json=cliente_aleatorio(), timeout=10)
        if respuesta.status_code == 200:
            exitosas += 1
        else:
            print(f"Error en la petición {i + 1}: {respuesta.status_code}")

    print(f"\nPredicciones generadas correctamente: {exitosas} de {cantidad}")


if __name__ == "__main__":
    main()