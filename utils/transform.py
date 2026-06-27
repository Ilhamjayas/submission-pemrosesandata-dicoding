import pandas as pd


EXCHANGE_RATE = 16000


def convert_price(df):
    """Convert price from USD string to IDR float."""
    try:
        if "Price" not in df.columns:
            raise ValueError("Kolom 'Price' tidak ditemukan dalam DataFrame.")

        df = df.copy()
        df["Price"] = df["Price"].replace("Price Unavailable", pd.NA)
        df["Price"] = df["Price"].str.extract(r"\$([\d.]+)")
        df["Price"] = pd.to_numeric(df["Price"], errors="coerce")
        df["Price"] = df["Price"] * EXCHANGE_RATE
        return df
    except Exception as e:
        raise RuntimeError(f"Error saat mengonversi harga: {e}")


def clean_rating(df):
    """Clean and convert rating column to float."""
    try:
        if "Rating" not in df.columns:
            raise ValueError("Kolom 'Rating' tidak ditemukan dalam DataFrame.")

        df = df.copy()
        df["Rating"] = df["Rating"].replace("Invalid Rating", pd.NA)
        df["Rating"] = df["Rating"].str.extract(r"([\d.]+)")
        df["Rating"] = pd.to_numeric(df["Rating"], errors="coerce")
        return df
    except Exception as e:
        raise RuntimeError(f"Error saat membersihkan rating: {e}")


def clean_colors(df):
    """Extract numeric value from Colors column."""
    try:
        if "Colors" not in df.columns:
            raise ValueError("Kolom 'Colors' tidak ditemukan dalam DataFrame.")

        df = df.copy()
        df["Colors"] = df["Colors"].str.extract(r"(\d+)")
        df["Colors"] = pd.to_numeric(df["Colors"], errors="coerce")
        return df
    except Exception as e:
        raise RuntimeError(f"Error saat membersihkan kolom Colors: {e}")


def clean_size(df):
    """Remove 'Size: ' prefix from Size column."""
    try:
        if "Size" not in df.columns:
            raise ValueError("Kolom 'Size' tidak ditemukan dalam DataFrame.")

        df = df.copy()
        df["Size"] = df["Size"].str.replace(r"^Size:\s*", "", regex=True).str.strip()
        return df
    except Exception as e:
        raise RuntimeError(f"Error saat membersihkan kolom Size: {e}")


def clean_gender(df):
    """Remove 'Gender: ' prefix from Gender column."""
    try:
        if "Gender" not in df.columns:
            raise ValueError("Kolom 'Gender' tidak ditemukan dalam DataFrame.")

        df = df.copy()
        df["Gender"] = df["Gender"].str.replace(r"^Gender:\s*", "", regex=True).str.strip()
        return df
    except Exception as e:
        raise RuntimeError(f"Error saat membersihkan kolom Gender: {e}")


def remove_invalid_titles(df):
    """Remove rows with invalid titles like 'Unknown Product'."""
    try:
        if "Title" not in df.columns:
            raise ValueError("Kolom 'Title' tidak ditemukan dalam DataFrame.")

        df = df.copy()
        df["Title"] = df["Title"].astype("string").str.strip()
        df = df[df["Title"].notna()]
        df = df[df["Title"].str.lower() != "unknown product"]
        return df
    except Exception as e:
        raise RuntimeError(f"Error saat menghapus judul tidak valid: {e}")


def drop_nulls(df):
    """Drop rows with any null values."""
    try:
        df = df.copy()
        before = len(df)
        df = df.dropna()
        after = len(df)
        print(f"[INFO] Menghapus {before - after} baris dengan nilai null.")
        return df
    except Exception as e:
        raise RuntimeError(f"Error saat menghapus nilai null: {e}")


def drop_duplicates(df):
    """Drop duplicate rows."""
    try:
        df = df.copy()
        before = len(df)
        df = df.drop_duplicates()
        after = len(df)
        print(f"[INFO] Menghapus {before - after} baris duplikat.")
        return df
    except Exception as e:
        raise RuntimeError(f"Error saat menghapus duplikat: {e}")


def enforce_dtypes(df):
    """Enforce proper data types for each column."""
    try:
        df = df.copy()
        df["Title"] = df["Title"].astype(str)
        df["Price"] = df["Price"].astype(float)
        df["Rating"] = df["Rating"].astype(float)
        df["Colors"] = df["Colors"].astype(int)
        df["Size"] = df["Size"].astype(str)
        df["Gender"] = df["Gender"].astype(str)
        df["timestamp"] = df["timestamp"].astype(str)
        return df
    except Exception as e:
        raise RuntimeError(f"Error saat mengonversi tipe data: {e}")


def transform(df):
    """Run all transformation steps on the raw DataFrame."""
    try:
        if df is None or df.empty:
            raise ValueError("DataFrame input kosong atau None.")

        print(f"[INFO] Mulai transformasi. Jumlah awal: {len(df)} baris.")

        df = remove_invalid_titles(df)
        df = convert_price(df)
        df = clean_rating(df)
        df = clean_colors(df)
        df = clean_size(df)
        df = clean_gender(df)
        df = drop_nulls(df)
        df = drop_duplicates(df)
        df = enforce_dtypes(df)

        print(f"[INFO] Transformasi selesai. Jumlah akhir: {len(df)} baris.")
        return df

    except (ValueError, RuntimeError):
        raise
    except Exception as e:
        raise RuntimeError(f"Error tidak terduga saat transformasi: {e}")
