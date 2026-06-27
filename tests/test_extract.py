import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from bs4 import BeautifulSoup

from utils.extract import get_page, parse_products, scrape_main


# ── Fixtures ──────────────────────────────────────────────────────────────────

SAMPLE_HTML = """
<html><body>
  <div class="collection-card">
    <h3 class="product-title">Casual T-Shirt</h3>
    <div class="price-container"><span class="price">$29.99</span></div>
    <p class="rating">Rating: ⭐ 4.5 / 5</p>
    <p class="product-detail">3 Colors</p>
    <p class="product-detail">Size: M</p>
    <p class="product-detail">Gender: Men</p>
  </div>
  <div class="collection-card">
    <h3 class="product-title">Stylish Jacket</h3>
    <p class="price-unavailable">Price Unavailable</p>
    <p class="rating">Rating: ⭐ 4.0 / 5</p>
    <p class="product-detail">2 Colors</p>
    <p class="product-detail">Size: L</p>
    <p class="product-detail">Gender: Women</p>
  </div>
</body></html>
"""

EMPTY_HTML = "<html><body><div>No products here</div></body></html>"


@pytest.fixture
def sample_soup():
    return BeautifulSoup(SAMPLE_HTML, "html.parser")


@pytest.fixture
def empty_soup():
    return BeautifulSoup(EMPTY_HTML, "html.parser")


@pytest.fixture
def mock_session():
    session = MagicMock()
    response = MagicMock()
    response.text = SAMPLE_HTML
    response.raise_for_status = MagicMock()
    session.get.return_value = response
    return session


# ── Tests: get_page ───────────────────────────────────────────────────────────

class TestGetPage:
    def test_get_page_returns_beautifulsoup(self, mock_session):
        soup = get_page(mock_session, "http://example.com")
        assert isinstance(soup, BeautifulSoup)

    def test_get_page_calls_session_get(self, mock_session):
        get_page(mock_session, "http://example.com/page2")
        mock_session.get.assert_called_once_with("http://example.com/page2", timeout=10)

    def test_get_page_raises_on_http_error(self):
        import requests
        session = MagicMock()
        session.get.side_effect = requests.exceptions.HTTPError("404")
        with pytest.raises(RuntimeError, match="HTTP error"):
            get_page(session, "http://example.com")

    def test_get_page_raises_on_connection_error(self):
        import requests
        session = MagicMock()
        session.get.side_effect = requests.exceptions.ConnectionError("timeout")
        with pytest.raises(RuntimeError, match="Koneksi gagal"):
            get_page(session, "http://example.com")

    def test_get_page_raises_on_timeout(self):
        import requests
        session = MagicMock()
        session.get.side_effect = requests.exceptions.Timeout()
        with pytest.raises(RuntimeError, match="timeout"):
            get_page(session, "http://example.com")

    def test_get_page_raises_on_request_exception(self):
        import requests
        session = MagicMock()
        session.get.side_effect = requests.exceptions.RequestException("error")
        with pytest.raises(RuntimeError, match="Request error"):
            get_page(session, "http://example.com")


# ── Tests: parse_products ─────────────────────────────────────────────────────

class TestParseProducts:
    def test_parse_returns_list(self, sample_soup):
        result = parse_products(sample_soup, "2025-01-01 00:00:00")
        assert isinstance(result, list)

    def test_parse_returns_correct_count(self, sample_soup):
        result = parse_products(sample_soup, "2025-01-01 00:00:00")
        assert len(result) == 2

    def test_parse_product_title(self, sample_soup):
        result = parse_products(sample_soup, "2025-01-01 00:00:00")
        assert result[0]["Title"] == "Casual T-Shirt"

    def test_parse_product_price_with_value(self, sample_soup):
        result = parse_products(sample_soup, "2025-01-01 00:00:00")
        assert result[0]["Price"] == "$29.99"

    def test_parse_product_price_unavailable(self, sample_soup):
        result = parse_products(sample_soup, "2025-01-01 00:00:00")
        assert result[1]["Price"] == "Price Unavailable"

    def test_parse_product_rating(self, sample_soup):
        result = parse_products(sample_soup, "2025-01-01 00:00:00")
        assert "4.5" in result[0]["Rating"]

    def test_parse_product_colors(self, sample_soup):
        result = parse_products(sample_soup, "2025-01-01 00:00:00")
        assert result[0]["Colors"] == "3 Colors"

    def test_parse_product_size(self, sample_soup):
        result = parse_products(sample_soup, "2025-01-01 00:00:00")
        assert result[0]["Size"] == "Size: M"

    def test_parse_product_gender(self, sample_soup):
        result = parse_products(sample_soup, "2025-01-01 00:00:00")
        assert result[0]["Gender"] == "Gender: Men"

    def test_parse_product_has_timestamp(self, sample_soup):
        ts = "2025-01-01 12:00:00"
        result = parse_products(sample_soup, ts)
        assert result[0]["timestamp"] == ts

    def test_parse_empty_page_raises_error(self, empty_soup):
        with pytest.raises(RuntimeError, match="product card"):
            parse_products(empty_soup, "2025-01-01 00:00:00")


# ── Tests: scrape_main ────────────────────────────────────────────────────────

class TestScrapeMain:
    def test_scrape_main_returns_dataframe(self, mock_session):
        df = scrape_main(mock_session)
        assert isinstance(df, pd.DataFrame)

    def test_scrape_main_has_required_columns(self, mock_session):
        df = scrape_main(mock_session)
        for col in ["Title", "Price", "Rating", "Colors", "Size", "Gender", "timestamp"]:
            assert col in df.columns

    def test_scrape_main_creates_session_if_none(self):
        with patch("utils.extract.requests.Session") as MockSession:
            mock_sess = MagicMock()
            MockSession.return_value = mock_sess
            response = MagicMock()
            response.text = SAMPLE_HTML
            response.raise_for_status = MagicMock()
            mock_sess.get.return_value = response
            df = scrape_main(None)
            assert isinstance(df, pd.DataFrame)

    def test_scrape_main_scrapes_50_pages(self, mock_session):
        scrape_main(mock_session)
        assert mock_session.get.call_count == 50

    def test_scrape_main_first_page_url(self, mock_session):
        scrape_main(mock_session)
        calls = [str(c) for c in mock_session.get.call_args_list]
        assert any("fashion-studio.dicoding.dev'" in c or "fashion-studio.dicoding.dev\"" in c
                   or "fashion-studio.dicoding.dev" in c for c in calls)

    def test_scrape_main_continues_on_page_error(self):
        import requests as req
        session = MagicMock()
        good_response = MagicMock()
        good_response.text = SAMPLE_HTML
        good_response.raise_for_status = MagicMock()

        def side_effect(url, timeout):
            if "page2" in url:
                raise req.exceptions.ConnectionError("fail")
            return good_response

        session.get.side_effect = side_effect
        df = scrape_main(session)
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

    def test_scrape_main_raises_if_no_products(self):
        session = MagicMock()
        response = MagicMock()
        response.text = EMPTY_HTML
        response.raise_for_status = MagicMock()
        session.get.return_value = response
        with pytest.raises(RuntimeError, match="Tidak ada produk"):
            scrape_main(session)
