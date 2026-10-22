import os
import requests

from utils.extract import scrape_main
from utils.transform import transform
from utils.load import save_to_csv, save_to_google_sheets, save_to_postgresql


# ── Konfigurasi ──────────────────────────────────────────────────────────────
CSV_OUTPUT = "products.csv"
SERVICE_ACCOUNT = "google-sheets-api.json"

SPREADSHEET_ID = os.getenv(
    "SPREADSHEET_ID",
    "1dcbhUs9ZgI4O5c_49oU614ONF9moO_-nYMmtqmRAAtw"
)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    ""
)
# ─────────────────────────────────────────────────────────────────────────────


def validate_config():
    if not SPREADSHEET_ID or SPREADSHEET_ID == "YOUR_SPREADSHEET_ID_HERE":
        raise ValueError("SPREADSHEET_ID belum dikonfigurasi dengan ID Google Sheets asli.")

    if not DATABASE_URL or "user:password" in DATABASE_URL or "localhost" in DATABASE_URL:
        raise ValueError("DATABASE_URL belum dikonfigurasi dengan connection string Supabase/PostgreSQL asli.")

    if not os.path.exists(SERVICE_ACCOUNT):
        raise FileNotFoundError(f"File service account tidak ditemukan: {SERVICE_ACCOUNT}")


def main():
    print("=" * 60)
    print("  ETL Pipeline — Fashion Studio Dicoding")
    print("=" * 60)

    try:
        validate_config()

        # ── EXTRACT ──────────────────────────────────────────────────
        print("\n[STEP 1] EXTRACT — Scraping data dari website…")
        session = requests.Session()
        raw_df = scrape_main(session)
        print(f"[EXTRACT] Selesai. Total baris mentah: {len(raw_df)}")

        # ── TRANSFORM ────────────────────────────────────────────────
        print("\n[STEP 2] TRANSFORM — Membersihkan dan mengonversi data…")
        clean_df = transform(raw_df)
        print(f"[TRANSFORM] Selesai. Total baris bersih: {len(clean_df)}")

        if clean_df.empty:
            raise ValueError("Data hasil transformasi kosong. Periksa proses extract atau transform.")

        # ── LOAD — CSV ───────────────────────────────────────────────
        print("\n[STEP 3a] LOAD — Menyimpan ke CSV…")
        save_to_csv(clean_df, CSV_OUTPUT)

        # ── LOAD — Google Sheets ─────────────────────────────────────
        print("\n[STEP 3b] LOAD — Menyimpan ke Google Sheets…")
        save_to_google_sheets(clean_df, SPREADSHEET_ID, SERVICE_ACCOUNT)

        # ── LOAD — PostgreSQL ────────────────────────────────────────
        print("\n[STEP 3c] LOAD — Menyimpan ke PostgreSQL…")
        save_to_postgresql(clean_df, DATABASE_URL)

        print("\n" + "=" * 60)
        print("  ETL Pipeline selesai!")
        print("  Data berhasil disimpan ke CSV, Google Sheets, dan PostgreSQL.")
        print("=" * 60)

    except Exception as e:
        print("\n" + "=" * 60)
        print("  ETL Pipeline gagal!")
        print(f"  Penyebab: {e}")
        print("=" * 60)
        raise


if __name__ == "__main__":
    main()
