import pytest
import pandas as pd
import numpy as np

from utils.transform import (
    convert_price,
    clean_rating,
    clean_colors,
    clean_size,
    clean_gender,
    remove_invalid_titles,
    drop_nulls,
    drop_duplicates,
    enforce_dtypes,
    transform,
    EXCHANGE_RATE,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "Title":     ["Casual T-Shirt", "Stylish Jacket", "Unknown Product", "Cool Pants"],
        "Price":     ["$29.99", "$45.00", "Price Unavailable", "$15.50"],
        "Rating":    ["Rating: ⭐ 4.5 / 5", "Rating: ⭐ 4.0 / 5", "Invalid Rating", "Rating: ⭐ 3.8 / 5"],
        "Colors":    ["3 Colors", "2 Colors", "5 Colors", "1 Colors"],
        "Size":      ["Size: M", "Size: L", "Size: S", "Size: XL"],
        "Gender":    ["Gender: Men", "Gender: Women", "Gender: Unisex", "Gender: Men"],
        "timestamp": ["2025-01-01 00:00:00"] * 4,
    })


@pytest.fixture
def clean_df():
    return pd.DataFrame({
        "Title":     ["Casual T-Shirt", "Stylish Jacket"],
        "Price":     [479840.0, 720000.0],
        "Rating":    [4.5, 4.0],
        "Colors":    [3, 2],
        "Size":      ["M", "L"],
        "Gender":    ["Men", "Women"],
        "timestamp": ["2025-01-01 00:00:00", "2025-01-01 00:00:00"],
    })


# ── Tests: convert_price ──────────────────────────────────────────────────────

class TestConvertPrice:
    def test_converts_usd_to_idr(self, sample_df):
        result = convert_price(sample_df)
        assert result["Price"].iloc[0] == pytest.approx(29.99 * EXCHANGE_RATE)

    def test_price_unavailable_becomes_na(self, sample_df):
        result = convert_price(sample_df)
        assert pd.isna(result["Price"].iloc[2])

    def test_returns_dataframe(self, sample_df):
        result = convert_price(sample_df)
        assert isinstance(result, pd.DataFrame)

    def test_missing_price_column_raises_error(self):
        df = pd.DataFrame({"Title": ["A"]})
        with pytest.raises(RuntimeError):
            convert_price(df)

    def test_does_not_modify_original(self, sample_df):
        original = sample_df["Price"].copy()
        convert_price(sample_df)
        pd.testing.assert_series_equal(sample_df["Price"], original)


# ── Tests: clean_rating ───────────────────────────────────────────────────────

class TestCleanRating:
    def test_extracts_float_value(self, sample_df):
        result = clean_rating(sample_df)
        assert result["Rating"].iloc[0] == pytest.approx(4.5)

    def test_invalid_rating_becomes_na(self, sample_df):
        result = clean_rating(sample_df)
        assert pd.isna(result["Rating"].iloc[2])

    def test_returns_dataframe(self, sample_df):
        result = clean_rating(sample_df)
        assert isinstance(result, pd.DataFrame)

    def test_missing_rating_column_raises_error(self):
        df = pd.DataFrame({"Title": ["A"]})
        with pytest.raises(RuntimeError):
            clean_rating(df)


# ── Tests: clean_colors ───────────────────────────────────────────────────────

class TestCleanColors:
    def test_extracts_number(self, sample_df):
        result = clean_colors(sample_df)
        assert result["Colors"].iloc[0] == 3

    def test_returns_numeric(self, sample_df):
        result = clean_colors(sample_df)
        assert pd.api.types.is_numeric_dtype(result["Colors"])

    def test_missing_colors_column_raises_error(self):
        df = pd.DataFrame({"Title": ["A"]})
        with pytest.raises(RuntimeError):
            clean_colors(df)


# ── Tests: clean_size ─────────────────────────────────────────────────────────

class TestCleanSize:
    def test_removes_size_prefix(self, sample_df):
        result = clean_size(sample_df)
        assert result["Size"].iloc[0] == "M"
        assert result["Size"].iloc[1] == "L"

    def test_returns_dataframe(self, sample_df):
        result = clean_size(sample_df)
        assert isinstance(result, pd.DataFrame)

    def test_missing_size_column_raises_error(self):
        df = pd.DataFrame({"Title": ["A"]})
        with pytest.raises(RuntimeError):
            clean_size(df)


# ── Tests: clean_gender ───────────────────────────────────────────────────────

class TestCleanGender:
    def test_removes_gender_prefix(self, sample_df):
        result = clean_gender(sample_df)
        assert result["Gender"].iloc[0] == "Men"
        assert result["Gender"].iloc[1] == "Women"

    def test_returns_dataframe(self, sample_df):
        result = clean_gender(sample_df)
        assert isinstance(result, pd.DataFrame)

    def test_missing_gender_column_raises_error(self):
        df = pd.DataFrame({"Title": ["A"]})
        with pytest.raises(RuntimeError):
            clean_gender(df)


# ── Tests: remove_invalid_titles ─────────────────────────────────────────────

class TestRemoveInvalidTitles:
    def test_removes_unknown_product(self, sample_df):
        result = remove_invalid_titles(sample_df)
        assert "Unknown Product" not in result["Title"].values

    def test_preserves_valid_titles(self, sample_df):
        result = remove_invalid_titles(sample_df)
        assert "Casual T-Shirt" in result["Title"].values

    def test_removes_null_titles(self):
        df = pd.DataFrame({
            "Title": ["Good Product", None, "Another Product"],
            "Price": ["$10", "$20", "$30"],
        })
        result = remove_invalid_titles(df)
        assert len(result) == 2

    def test_missing_title_column_raises_error(self):
        df = pd.DataFrame({"Price": ["$10"]})
        with pytest.raises(RuntimeError):
            remove_invalid_titles(df)


# ── Tests: drop_nulls ─────────────────────────────────────────────────────────

class TestDropNulls:
    def test_drops_rows_with_null(self):
        df = pd.DataFrame({
            "A": [1, None, 3],
            "B": ["x", "y", None],
        })
        result = drop_nulls(df)
        assert len(result) == 1
        assert result["A"].iloc[0] == 1

    def test_no_nulls_unchanged(self):
        df = pd.DataFrame({"A": [1, 2], "B": ["x", "y"]})
        result = drop_nulls(df)
        assert len(result) == 2


# ── Tests: drop_duplicates ────────────────────────────────────────────────────

class TestDropDuplicates:
    def test_removes_duplicate_rows(self):
        df = pd.DataFrame({"A": [1, 1, 2], "B": ["x", "x", "y"]})
        result = drop_duplicates(df)
        assert len(result) == 2

    def test_no_duplicates_unchanged(self):
        df = pd.DataFrame({"A": [1, 2], "B": ["x", "y"]})
        result = drop_duplicates(df)
        assert len(result) == 2


# ── Tests: enforce_dtypes ─────────────────────────────────────────────────────

class TestEnforceDtypes:
    def test_price_is_float(self, clean_df):
        result = enforce_dtypes(clean_df)
        assert result["Price"].dtype == float

    def test_rating_is_float(self, clean_df):
        result = enforce_dtypes(clean_df)
        assert result["Rating"].dtype == float

    def test_colors_is_int(self, clean_df):
        result = enforce_dtypes(clean_df)
        assert result["Colors"].dtype == int

    def test_title_is_string(self, clean_df):
        result = enforce_dtypes(clean_df)
        assert result["Title"].dtype == object

    def test_size_is_string(self, clean_df):
        result = enforce_dtypes(clean_df)
        assert result["Size"].dtype == object

    def test_gender_is_string(self, clean_df):
        result = enforce_dtypes(clean_df)
        assert result["Gender"].dtype == object


# ── Tests: transform (full pipeline) ─────────────────────────────────────────

class TestTransform:
    def test_transform_returns_dataframe(self, sample_df):
        result = transform(sample_df)
        assert isinstance(result, pd.DataFrame)

    def test_transform_removes_invalid_data(self, sample_df):
        result = transform(sample_df)
        assert "Unknown Product" not in result["Title"].values

    def test_transform_no_nulls_in_result(self, sample_df):
        result = transform(sample_df)
        assert result.isnull().sum().sum() == 0

    def test_transform_price_converted_to_idr(self, sample_df):
        result = transform(sample_df)
        # $29.99 * 16000
        assert result[result["Title"] == "Casual T-Shirt"]["Price"].iloc[0] == pytest.approx(29.99 * EXCHANGE_RATE)

    def test_transform_colors_is_int(self, sample_df):
        result = transform(sample_df)
        assert result["Colors"].dtype == int

    def test_transform_size_no_prefix(self, sample_df):
        result = transform(sample_df)
        assert all(not str(s).startswith("Size:") for s in result["Size"])

    def test_transform_gender_no_prefix(self, sample_df):
        result = transform(sample_df)
        assert all(not str(g).startswith("Gender:") for g in result["Gender"])

    def test_transform_has_timestamp_column(self, sample_df):
        result = transform(sample_df)
        assert "timestamp" in result.columns

    def test_transform_empty_dataframe_raises_error(self):
        with pytest.raises((ValueError, RuntimeError)):
            transform(pd.DataFrame())

    def test_transform_none_raises_error(self):
        with pytest.raises((ValueError, RuntimeError, AttributeError)):
            transform(None)

    def test_transform_no_duplicates(self):
        df = pd.DataFrame({
            "Title":     ["Shirt", "Shirt"],
            "Price":     ["$10.00", "$10.00"],
            "Rating":    ["Rating: ⭐ 4.0 / 5", "Rating: ⭐ 4.0 / 5"],
            "Colors":    ["2 Colors", "2 Colors"],
            "Size":      ["Size: M", "Size: M"],
            "Gender":    ["Gender: Men", "Gender: Men"],
            "timestamp": ["2025-01-01 00:00:00", "2025-01-01 00:00:00"],
        })
        result = transform(df)
        assert len(result) == result.drop_duplicates().shape[0]
