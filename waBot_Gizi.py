from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import pandas as pd
import re

app = Flask(__name__)

# Load data
DATA_PATH = "Database_Makanan_Lengkap.csv"
df = pd.read_csv(DATA_PATH)
df["nama_lower"] = df["Nama Makanan"].str.lower().str.strip()

# Keyword mapping
gizi_keywords = {
    "kalori": "Kalori (kkal)",
    "gula": "Gula (g)",
    "karbohidrat": "Karbohidrat (g)",
    "protein": "Protein (g)",
    "lemak": "Lemak (g)",
}

satuan = {
    "kalori": "kkal",
    "gula": "g",
    "karbohidrat": "g",
    "protein": "g",
    "lemak": "g",
}


@app.route("/whatsapp", methods=["POST"])
@app.route("/", methods=["POST"])
def whatsapp_reply():
    incoming_msg = request.values.get("Body", "").strip().lower()

    # Ambil makanan berdasarkan kata kunci yang cocok sebagian
    makanan_ditemukan = None
    for nama in df["nama_lower"]:
        if nama in incoming_msg:
            makanan_ditemukan = nama
            break

    resp = MessagingResponse()
    msg = resp.message()

    if makanan_ditemukan:
        row = df[df["nama_lower"] == makanan_ditemukan].iloc[0]

        # Cek apakah user menyebut salah satu gizi
        gizi_diminta = [k for k in gizi_keywords if k in incoming_msg]

        if gizi_diminta:
            # Jika hanya sebagian gizi diminta
            gizi_info = "\n".join(
                [
                    f"{g.capitalize()}: {row[gizi_keywords[g]]} {satuan[g.lower()]}"
                    for g in gizi_diminta
                ]
            )
        else:
            # Jika tidak disebutkan, tampilkan semuanya
            gizi_info = (
                f"Kalori: {row['Kalori (kkal)']} kkal\n"
                f"Gula: {row['Gula (g)']} g\n"
                f"Karbohidrat: {row['Karbohidrat (g)']} g\n"
                f"Protein: {row['Protein (g)']} g\n"
                f"Lemak: {row['Lemak (g)']} g"
            )

        response_text = (
            f"*{row['Nama Makanan']}* (Warung: {row['Warung']})\n{gizi_info}"
        )

    else:
        response_text = (
            "Maaf, makanan tidak ditemukan.\n"
            "Pastikan mengetik nama makanan dengan tepat atau gunakan kata kunci umum.\n"
            "Contoh: Nasi Goreng, Ayam Geprek, Mie Goreng"
        )

    msg.body(response_text)
    return str(resp)


if __name__ == "__main__":
    app.run(port=5000)
