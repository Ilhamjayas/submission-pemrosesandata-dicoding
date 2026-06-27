import pytest
import os
import pandas as pd
from unittest.mock import MagicMock, patch, mock_open

from utils.load import save_to_csv, save_to_google_sheets, save_to_postgresql


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "Title":     ["Casual T-Shirt", "Stylish Jacket"],
        "Price":     [479840.0, 720000.0],
        "Rating":    [4.5, 4.0],
        "Colors":    [3, 2],
        "Size":      ["M", "L"],
        "Gender":    ["Men", "Women"],
        "timestamp": ["2025-01-01 00:00:00", "2025-01-01 00:00:00"],
    })


@pytest.fixture
def empty_df():
    return pd.DataFrame()


# ── Tests: save_to_csv ────────────────────────────────────────────────────────

class TestSaveToCsv:
    def test_creates_csv_file(self, sample_df, tmp_path):
        filepath = str(tmp_path / "output.csv")
        save_to_csv(sample_df, filepath)
        assert os.path.exists(filepath)

    def test_csv_has_correct_rows(self, sample_df, tmp_path):
        filepath = str(tmp_path / "output.csv")
        save_to_csv(sample_df, filepath)
        loaded = pd.read_csv(filepath)
        assert len(loaded) == len(sample_df)

    def test_csv_has_correct_columns(self, sample_df, tmp_path):
        filepath = str(tmp_path / "output.csv")
        save_to_csv(sample_df, filepath)
        loaded = pd.read_csv(filepath)
        for col in sample_df.columns:
            assert col in loaded.columns

    def test_returns_filepath(self, sample_df, tmp_path):
        filepath = str(tmp_path / "output.csv")
        result = save_to_csv(sample_df, filepath)
        assert result == filepath

    def test_empty_dataframe_raises_error(self, empty_df, tmp_path):
        filepath = str(tmp_path / "output.csv")
        with pytest.raises((ValueError, RuntimeError)):
            save_to_csv(empty_df, filepath)

    def test_none_raises_error(self, tmp_path):
        filepath = str(tmp_path / "output.csv")
        with pytest.raises((ValueError, RuntimeError, AttributeError)):
            save_to_csv(None, filepath)

    def test_csv_values_match(self, sample_df, tmp_path):
        filepath = str(tmp_path / "output.csv")
        save_to_csv(sample_df, filepath)
        loaded = pd.read_csv(filepath)
        assert loaded["Title"].iloc[0] == "Casual T-Shirt"
        assert loaded["Price"].iloc[0] == pytest.approx(479840.0)


# ── Tests: save_to_google_sheets ──────────────────────────────────────────────

class TestSaveToGoogleSheets:
    def test_raises_if_service_account_missing(self, sample_df):
        with pytest.raises((FileNotFoundError, RuntimeError)):
            save_to_google_sheets(sample_df, "fake-id", "nonexistent.json")

    def test_raises_on_empty_dataframe(self, empty_df):
        with pytest.raises((ValueError, RuntimeError)):
            save_to_google_sheets(empty_df, "fake-id")

    def test_raises_on_none_dataframe(self):
        with pytest.raises((ValueError, RuntimeError, AttributeError)):
            save_to_google_sheets(None, "fake-id")

    @patch("utils.load.build")
    @patch("utils.load.Credentials.from_service_account_file")
    @patch("os.path.exists", return_value=True)
    def test_calls_sheets_api(self, mock_exists, mock_creds, mock_build, sample_df):
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_sheets = MagicMock()
        mock_service.spreadsheets.return_value = mock_sheets

        mock_values = MagicMock()
        mock_sheets.values.return_value = mock_values

        mock_update = MagicMock()
        mock_values.update.return_value = mock_update
        mock_update.execute.return_value = {"updatedCells": 14}

        result = save_to_google_sheets(sample_df, "test-spreadsheet-id", "fake.json")
        assert result is not None
        mock_values.update.assert_called_once()

    @patch("utils.load.build")
    @patch("utils.load.Credentials.from_service_account_file")
    @patch("os.path.exists", return_value=True)
    def test_spreadsheet_id_passed_correctly(self, mock_exists, mock_creds, mock_build, sample_df):
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_sheets = MagicMock()
        mock_service.spreadsheets.return_value = mock_sheets
        mock_values = MagicMock()
        mock_sheets.values.return_value = mock_values
        mock_update = MagicMock()
        mock_values.update.return_value = mock_update
        mock_update.execute.return_value = {"updatedCells": 14}

        save_to_google_sheets(sample_df, "my-sheet-123", "fake.json")
        call_kwargs = mock_values.update.call_args[1]
        assert call_kwargs["spreadsheetId"] == "my-sheet-123"

    @patch("utils.load.build")
    @patch("utils.load.Credentials.from_service_account_file")
    @patch("os.path.exists", return_value=True)
    def test_header_row_included(self, mock_exists, mock_creds, mock_build, sample_df):
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_sheets = MagicMock()
        mock_service.spreadsheets.return_value = mock_sheets
        mock_values = MagicMock()
        mock_sheets.values.return_value = mock_values
        mock_update = MagicMock()
        mock_values.update.return_value = mock_update
        mock_update.execute.return_value = {"updatedCells": 14}

        save_to_google_sheets(sample_df, "my-sheet-123", "fake.json")
        body = mock_values.update.call_args[1]["body"]
        # First row should be the header
        assert body["values"][0] == sample_df.columns.tolist()


# ── Tests: save_to_postgresql ─────────────────────────────────────────────────

class TestSaveToPostgresql:
    def test_raises_on_empty_dataframe(self, empty_df):
        with pytest.raises((ValueError, RuntimeError)):
            save_to_postgresql(empty_df, "postgresql://user:pass@localhost/db")

    def test_raises_on_none_dataframe(self):
        with pytest.raises((ValueError, RuntimeError, AttributeError)):
            save_to_postgresql(None, "postgresql://user:pass@localhost/db")

    def test_raises_on_empty_db_url(self, sample_df):
        with pytest.raises((ValueError, RuntimeError)):
            save_to_postgresql(sample_df, "")

    @patch("utils.load.create_engine")
    def test_calls_to_sql(self, mock_create_engine, sample_df):
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)

        with patch.object(sample_df.__class__, "to_sql") as mock_to_sql:
            save_to_postgresql(sample_df, "postgresql://user:pass@localhost/db")
            mock_to_sql.assert_called_once()

    @patch("utils.load.create_engine")
    def test_returns_table_name(self, mock_create_engine, sample_df):
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)

        with patch.object(pd.DataFrame, "to_sql"):
            result = save_to_postgresql(sample_df, "postgresql://user:pass@localhost/db", "fashion_products")
            assert result == "fashion_products"

    @patch("utils.load.create_engine")
    def test_raises_on_db_error(self, mock_create_engine, sample_df):
        mock_create_engine.side_effect = Exception("Connection refused")
        with pytest.raises(RuntimeError, match="PostgreSQL"):
            save_to_postgresql(sample_df, "postgresql://user:pass@localhost/db")
