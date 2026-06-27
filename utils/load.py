import os
import pandas as pd
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from sqlalchemy import create_engine, text


SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def save_to_csv(df, filepath="products.csv"):
    """Save DataFrame to a CSV file."""
    try:
        if df is None or df.empty:
            raise ValueError("DataFrame kosong, tidak ada data untuk disimpan ke CSV.")

        df.to_csv(filepath, index=False)
        print(f"[INFO] Data berhasil disimpan ke CSV: {filepath}")
        return filepath
    except PermissionError as e:
        raise RuntimeError(f"Tidak memiliki izin untuk menulis ke {filepath}: {e}")
    except Exception as e:
        raise RuntimeError(f"Error saat menyimpan ke CSV: {e}")


def save_to_google_sheets(df, spreadsheet_id, service_account_file="google-sheets-api.json", sheet_name="Sheet1"):
    """Save DataFrame to Google Sheets."""
    try:
        if df is None or df.empty:
            raise ValueError("DataFrame kosong, tidak ada data untuk disimpan ke Google Sheets.")

        if not os.path.exists(service_account_file):
            raise FileNotFoundError(f"Service account file tidak ditemukan: {service_account_file}")

        creds = Credentials.from_service_account_file(service_account_file, scopes=SCOPES)
        service = build("sheets", "v4", credentials=creds)
        sheet = service.spreadsheets()

        # Prepare data: header + rows
        values = [df.columns.tolist()] + df.astype(str).values.tolist()

        body = {"values": values}
        range_notation = f"{sheet_name}!A1"

        result = sheet.values().update(
            spreadsheetId=spreadsheet_id,
            range=range_notation,
            valueInputOption="RAW",
            body=body,
        ).execute()

        updated_cells = result.get("updatedCells", 0)
        print(f"[INFO] Data berhasil disimpan ke Google Sheets. Sel diperbarui: {updated_cells}")
        return result
    except FileNotFoundError:
        raise
    except ValueError:
        raise
    except Exception as e:
        raise RuntimeError(f"Error saat menyimpan ke Google Sheets: {e}")


def save_to_postgresql(df, db_url, table_name="products"):
    """Save DataFrame to PostgreSQL database."""
    try:
        if df is None or df.empty:
            raise ValueError("DataFrame kosong, tidak ada data untuk disimpan ke PostgreSQL.")

        if not db_url:
            raise ValueError("Database URL tidak boleh kosong.")

        engine = create_engine(db_url)

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        df.to_sql(table_name, engine, if_exists="replace", index=False)
        print(f"[INFO] Data berhasil disimpan ke PostgreSQL, tabel: {table_name}")
        return table_name
    except ValueError:
        raise
    except Exception as e:
        raise RuntimeError(f"Error saat menyimpan ke PostgreSQL: {e}")
