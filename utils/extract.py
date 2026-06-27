import requests
import re
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime


BASE_URL = "https://fashion-studio.dicoding.dev"


def get_page(session, url):
    """Fetch a single page and return BeautifulSoup object."""
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"HTTP error saat mengambil halaman {url}: {e}")
    except requests.exceptions.ConnectionError as e:
        raise RuntimeError(f"Koneksi gagal untuk halaman {url}: {e}")
    except requests.exceptions.Timeout as e:
        raise RuntimeError(f"Request timeout untuk halaman {url}: {e}")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Request error untuk halaman {url}: {e}")


def parse_products(soup, timestamp):
    """Parse product cards from a BeautifulSoup object."""
    try:
        products = []
        cards = soup.select("div.collection-card")

        if not cards:
            raise ValueError("Tidak ditemukan product card di halaman ini.")

        for card in cards:
            try:
                title_el = card.select_one("h3.product-title")
                title = title_el.get_text(strip=True) if title_el else None

                card_text = card.get_text("\n", strip=True)
                lines = [line.strip() for line in card_text.split("\n") if line.strip()]

                price = None
                price_match = re.search(r"\$\s*[\d.]+", card_text)
                if price_match:
                    price = price_match.group(0).replace(" ", "")
                elif "Price Unavailable" in card_text:
                    price = "Price Unavailable"

                rating = next(
                    (line for line in lines if line.startswith("Rating") or "Not Rated" in line),
                    None
                )

                colors = next(
                    (line for line in lines if "Colors" in line),
                    None
                )

                size = next(
                    (line for line in lines if line.startswith("Size")),
                    None
                )

                gender = next(
                    (line for line in lines if line.startswith("Gender")),
                    None
                )

                products.append({
                    "Title": title,
                    "Price": price,
                    "Rating": rating,
                    "Colors": colors,
                    "Size": size,
                    "Gender": gender,
                    "timestamp": timestamp,
                })

            except Exception as e:
                print(f"[WARNING] Gagal parsing satu produk: {e}")
                continue

        return products

    except Exception as e:
        raise RuntimeError(f"Error saat parsing produk: {e}")


def scrape_main(session=None):
    """Scrape all products from all pages (1-50) of the fashion website."""
    try:
        if session is None:
            session = requests.Session()

        all_products = []
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for page in range(1, 51):
            try:
                if page == 1:
                    url = BASE_URL
                else:
                    url = f"{BASE_URL}/page{page}"

                print(f"[INFO] Scraping halaman {page}: {url}")
                soup = get_page(session, url)
                products = parse_products(soup, timestamp)
                all_products.extend(products)
                print(f"[INFO] Halaman {page}: {len(products)} produk ditemukan.")
            except RuntimeError as e:
                print(f"[WARNING] Halaman {page} dilewati karena error: {e}")
                continue

        if not all_products:
            raise RuntimeError("Tidak ada produk yang berhasil di-scrape dari seluruh halaman.")

        df = pd.DataFrame(all_products)
        print(f"[INFO] Total data yang berhasil di-scrape: {len(df)} baris.")
        return df

    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"Error tidak terduga saat scraping: {e}")
