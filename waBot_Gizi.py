from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import pandas as pd
import re, os

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
    bot_aktif = os.getenv("BOT_AKTIF", "true").lower() == "true"
    nomor_admin = "whatsapp:+6285838810436"

    resp = MessagingResponse()
    msg = resp.message()

    sender = request.values.get("From", "")
    if not bot_aktif and nomor_admin not in sender:
        msg.body("⚠️ Bot saat ini tidak tersedia untuk umum.")
        return str(resp)

    incoming_msg = request.values.get("Body", "").strip().lower()

    # Hitung IMT
    match_berat = re.search(r"berat\s*(\d+)", incoming_msg)
    match_tinggi = re.search(r"tinggi\s*(\d+)", incoming_msg)
    if match_berat and match_tinggi:
        berat = float(match_berat.group(1))
        tinggi_cm = float(match_tinggi.group(1))
        tinggi_m = tinggi_cm / 100
        imt = berat / (tinggi_m ** 2)

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

        msg.body(f"Berat: {berat} kg\nTinggi: {tinggi_cm} cm\nIMT kamu: {imt:.2f} ({kategori})\nTetap jaga pola makan seimbang dan rutin beraktivitas ya!")
        return str(resp)

    # Hitung total gizi dari beberapa makanan sekaligus
    pola_makanan = re.findall(r"(\d*)\s*([a-zA-Z\s]+?)(?:,|dan|$)", incoming_msg)
    total_gizi = {"Kalori (kkal)": 0, "Gula (g)": 0, "Karbohidrat (g)": 0, "Protein (g)": 0, "Lemak (g)": 0}
    makanan_terproses = []

    for jumlah, nama_makanan in pola_makanan:
        nama_makanan = nama_makanan.strip().lower()
        jumlah = int(jumlah) if jumlah else 1
        match = df[df["nama_lower"].str.contains(nama_makanan)]
        if not match.empty:
            row = match.iloc[0]
            makanan_terproses.append(f"{jumlah}x {row['Nama Makanan']}")
            total_gizi["Kalori (kkal)"] += row["Kalori (kkal)"] * jumlah
            total_gizi["Gula (g)"] += row["Gula (g)"] * jumlah
            total_gizi["Karbohidrat (g)"] += row["Karbohidrat (g)"] * jumlah
            total_gizi["Protein (g)"] += row["Protein (g)"] * jumlah
            total_gizi["Lemak (g)"] += row["Lemak (g)"] * jumlah

    if makanan_terproses:
        gizi_diminta = [k for k in gizi_keywords if k in incoming_msg]
        if gizi_diminta:
            info = "\n".join([f"{g.capitalize()}: {total_gizi[gizi_keywords[g]]} {satuan[g]}" for g in gizi_diminta])
        else:
            info = (f"Kalori: {total_gizi['Kalori (kkal)']} kkal\nGula: {total_gizi['Gula (g)']} g\nKarbohidrat: {total_gizi['Karbohidrat (g)']} g\nProtein: {total_gizi['Protein (g)']} g\nLemak: {total_gizi['Lemak (g)']} g")

        peringatan = ""
        if total_gizi["Gula (g)"] > 25:
            peringatan += "\n⚠️ Gula melebihi batas harian WHO (25g)"
        if total_gizi["Lemak (g)"] > 67:
            peringatan += "\n⚠️ Lemak melebihi batas harian"

        saran = "\nPerhatikan komposisi Isi Piringku: 1/3 nasi/karbo, 1/3 lauk/protein, 1/3 sayur & buah"

        msg.body(f"Makanan: {', '.join(makanan_terproses)}\n{info}{peringatan}{saran}")
        return str(resp)

    msg.body("Maaf, makanan tidak ditemukan atau format tidak sesuai.\nContoh cek gizi: '3 nasi goreng, 2 bakso, 1 kebab'\nContoh cek IMT: 'berat 70 tinggi 170'")
    return str(resp)

if __name__ == "__main__":
    app.run(port=5000)
