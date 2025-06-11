from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import pandas as pd

# Load data dari file CSV
DATA_PATH = "Database_Makanan_Lengkap.csv"
df = pd.read_csv(DATA_PATH)

# Buat kolom lowercase untuk pencarian mudah
df["nama_lower"] = df["Nama Makanan"].str.lower()

# Inisialisasi Flask
app = Flask(__name__)


# Route untuk halaman utama
@app.route("/index")
# Route untuk WhatsApp API
@app.route("/whatsapp", methods=["POST"])
@app.route("/")
def whatsapp_reply():
    incoming_msg = request.values.get("Body", "").strip().lower()
    resp = MessagingResponse()
    msg = resp.message()

    match = df[df["nama_lower"].str.contains(incoming_msg)]

    if not match.empty:
        row = match.iloc[0]
        response_text = (
            f"*{row['Nama Makanan']}* (Warung: {row['Warung']})\n"
            f"Kalori: {row['Kalori (kkal)']} kkal\n"
            f"Gula: {row['Gula (g)']} g\n"
            f"Karbohidrat: {row['Karbohidrat (g)']} g\n"
            f"Protein: {row['Protein (g)']} g\n"
            f"Lemak: {row['Lemak (g)']} g"
        )
    else:
        response_text = (
            "Maaf, makanan tidak ditemukan.\n"
            "Pastikan mengetik nama makanan dengan tepat sesuai database.\n"
            "Contoh: Nasi Goreng, Ayam Geprek, Mie Goreng"
        )

    msg.body(response_text)
    return str(resp)


# Menjalankan aplikasi
if __name__ == "__main__":
    app.run(port=5000)
