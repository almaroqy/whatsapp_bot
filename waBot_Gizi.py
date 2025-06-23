from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import pandas as pd
import re

app = Flask(__name__)

# Load data makanan
df = pd.read_csv("Database_Makanan_Lengkap.csv")
df["nama_lower"] = df["Nama Makanan"].str.lower().str.strip()

# Mapping gizi dan satuan
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
    # Kontrol akses bot
    bot_aktif = os.getenv("BOT_AKTIF", "true").lower() == "true"
    nomor_admin = "whatsapp:+6285838810436"

    resp = MessagingResponse()
    msg = resp.message()

    sender = request.values.get("From", "")

    if not bot_aktif and nomor_admin not in sender:
        msg.body("⚠️ Bot saat ini tidak tersedia untuk umum.")
        return str(resp)
        
    # Ambil pesan masuk
    incoming_msg = request.values.get("Body", "").strip().lower()
    resp = MessagingResponse()
    msg = resp.message()

    # Cek input IMT
    match_berat = re.search(r"berat\s*(\d+)", incoming_msg)
    match_tinggi = re.search(r"tinggi\s*(\d+)", incoming_msg)

    if match_berat and match_tinggi:
        berat = float(match_berat.group(1))
        tinggi_cm = float(match_tinggi.group(1))
        tinggi_m = tinggi_cm / 100

        imt = berat / (tinggi_m**2)
        if imt < 18.5:
            kategori = "Kurus (Underweight)"
        elif imt < 23:
            kategori = "Normal"
        elif imt < 25:
            kategori = "Overweight"
        elif imt < 30:
            kategori = "Obesitas I"
        else:
            kategori = "Obesitas II"

        response_text = (
            f"Berat: {berat} kg\n"
            f"Tinggi: {tinggi_cm} cm\n"
            f"IMT kamu: {imt:.2f} ({kategori})\n"
            "Tetap jaga pola makan seimbang dan rutin beraktivitas ya!"
        )

        msg.body(response_text)
        return str(resp)

    # Cek makanan
    data_makanan = None
    for nama in df["nama_lower"]:
        if nama in incoming_msg:
            data_makanan = nama
            break

    if data_makanan:
        row = df[df["nama_lower"] == data_makanan].iloc[0]
        gizi_diminta = [k for k in gizi_keywords if k in incoming_msg]

        warning = []
        if row["Kalori (kkal)"] > 800:
            warning.append("⚠️ Kalori tinggi, perhatikan porsi makan.")
        if row["Gula (g)"] > 25:
            warning.append("⚠️ Kandungan gula tinggi.")
        if row["Lemak (g)"] > 30:
            warning.append("⚠️ Lemak cukup tinggi, batasi konsumsi.")

        if gizi_diminta:
            gizi_info = "\n".join(
                [
                    f"{g.capitalize()}: {row[gizi_keywords[g]]} {satuan[g.lower()]}"
                    for g in gizi_diminta
                ]
            )
        else:
            gizi_info = (
                f"Kalori: {row['Kalori (kkal)']} kkal\n"
                f"Gula: {row['Gula (g)']} g\n"
                f"Karbohidrat: {row['Karbohidrat (g)']} g\n"
                f"Protein: {row['Protein (g)']} g\n"
                f"Lemak: {row['Lemak (g)']} g"
            )

        response_text = (
            f"*{row['Nama Makanan']}* (Warung: {row['Warung']})\n"
            f"{gizi_info}\n" + ("\n".join(warning) if warning else "")
        )
    else:
        response_text = (
            "Maaf, makanan tidak ditemukan atau format tidak sesuai.\n"
            "Contoh perhitungan IMT: 'berat 60 tinggi 165'\n"
            "Contoh cek makanan: 'mie goreng', 'ayam geprek', dst."
        )

    msg.body(response_text)
    return str(resp)


if __name__ == "__main__":
    app.run(port=5000)
