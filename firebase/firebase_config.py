# firebase/firebase_config.py
import firebase_admin
from firebase_admin import credentials

# Jangan inisialisasi ulang jika sudah pernah
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")  # atau path lengkapnya
    firebase_admin.initialize_app(cred)
