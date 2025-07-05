#!/usr/bin/env python3
"""
Unit tests for the get_filtered_table_contents method in the PBIXRay MCP server

Usage:
    pytest -xvs tests/test_filtered_table_contents.py                         # Use the default demo PBIX file
    pytest -xvs tests/test_filtered_table_contents.py --pbix-file=/path/to/custom.pbix  # Use a custom PBIX file
"""

import os
import pytest
import sys
import json
import asyncio
import pandas as pd
from unittest.mock import patch, MagicMock

# Add the src directory to the path so we can import the server module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

# Mock the parse_args function before importing the module
with patch("argparse.ArgumentParser.parse_args") as mock_parse_args:
    # Create a mock args object with the expected attributes
    mock_args = MagicMock()
    mock_args.disallow = []
    mock_args.max_rows = 100
    mock_args.page_size = 20
    mock_parse_args.return_value = mock_args

    # Now import the server module
    import pbixray_server


class MockPBIXRayWithFilterableData:
    """Mock PBIXRay class with data suitable for testing filters"""

    def __init__(self, file_path):
        self.file_path = file_path
        self.tables = ["Sales", "Products", "Locations"]
        self.size = 1024

    def get_table(self, table_name):
        """Return a mock pandas DataFrame with data suitable for filtering tests"""
        if table_name == "Sales":
            # Create a sales table with numeric and string columns for testing filters
            return pd.DataFrame(
                {
                    "product_id": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                    "location_id": [
                        "madrid",
                        "barcelona",
                        "albacete",
                        "madrid",
                        "barcelona",
                        "albacete",
                        "madrid",
                        "barcelona",
                        "albacete",
                        "madrid",
                    ],
                    "period": [100, 110, 120, 130, 140, 150, 160, 170, 180, 190],
                    "amount": [10.5, 20.3, 15.7, 8.2, 30.1, 25.0, 12.8, 18.9, 22.4, 17.6],
                    "is_completed": [True, False, True, True, False, True, False, True, False, True],
                }
            )
        elif table_name == "Products":
            return pd.DataFrame(
                {
                    "product_id": [1, 2, 3, 4, 5],
                    "product_name": ["Laptop", "Phone", "Tablet", "Monitor", "Keyboard"],
                    "price": [1200.50, 800.25, 350.99, 250.50, 75.00],
                }
            )
        elif table_name == "Locations":
            return pd.DataFrame(
                {
                    "location_id": ["madrid", "barcelona", "albacete", "valencia", "bilbao"],
                    "country": ["Spain", "Spain", "Spain", "Spain", "Spain"],
                    "employees": [50, 40, 20, 30, 25],
                }
            )
        else:
            # Return an empty DataFrame for unknown tables
            return pd.DataFrame()


@pytest.mark.asyncio
async def test_get_filtered_table_contents_basic():
    """Test the get_table_contents function with basic filters"""
    # Create a mock Context with async methods
    mock_context = MagicMock()
    mock_context.info = MagicMock(return_value=asyncio.Future())
    mock_context.info.return_value.set_result(None)
    mock_context.report_progress = MagicMock(return_value=asyncio.Future())
    mock_context.report_progress.return_value.set_result(None)

    # Use our mock PBIXRay class
    pbixray_server.current_model = MockPBIXRayWithFilterableData("/path/to/test.pbix")
    pbixray_server.current_model_path = "/path/to/test.pbix"

    # Test with a simple equality filter
    result = await pbixray_server.get_table_contents(
        mock_context, table_name="Sales", filters="location_id=albacete", page=1, page_size=10
    )

    # Verify the result
    assert result, "Expected filtered table contents"
    assert isinstance(result, str), "Expected JSON string"

    # Parse JSON to make sure it's valid
    parsed = json.loads(result)
    assert "pagination" in parsed, "Expected pagination info"
    assert "data" in parsed, "Expected data in response"

    # Verify the filter was applied correctly
    assert parsed["pagination"]["total_rows"] == 3, "Expected 3 rows with location_id=albacete"
    assert all(row["location_id"] == "albacete" for row in parsed["data"]), "All rows should have location_id=albacete"

    # Clean up
    pbixray_server.current_model = None
    pbixray_server.current_model_path = None


@pytest.mark.asyncio
async def test_get_filtered_table_contents_numeric_comparison():
    """Test the get_table_contents function with numeric comparison filters"""
    # Create a mock Context with async methods
    mock_context = MagicMock()
    mock_context.info = MagicMock(return_value=asyncio.Future())
    mock_context.info.return_value.set_result(None)
    mock_context.report_progress = MagicMock(return_value=asyncio.Future())
    mock_context.report_progress.return_value.set_result(None)

    # Use our mock PBIXRay class
    pbixray_server.current_model = MockPBIXRayWithFilterableData("/path/to/test.pbix")
    pbixray_server.current_model_path = "/path/to/test.pbix"

    # Test with numeric comparison filters
    result = await pbixray_server.get_table_contents(
        mock_context, table_name="Sales", filters="period>150;period<180", page=1, page_size=10
    )

    # Verify the result
    parsed = json.loads(result)
    assert parsed["pagination"]["total_rows"] == 2, "Expected 2 rows with period between 150 and 180"
    assert all(150 < row["period"] < 180 for row in parsed["data"]), "All rows should have period between 150 and 180"

    # Clean up
    pbixray_server.current_model = None
    pbixray_server.current_model_path = None


@pytest.mark.asyncio
async def test_get_filtered_table_contents_multiple_filters():
    """Test the get_table_contents function with multiple filters of different types"""
    # Create a mock Context with async methods
    mock_context = MagicMock()
    mock_context.info = MagicMock(return_value=asyncio.Future())
    mock_context.info.return_value.set_result(None)
    mock_context.report_progress = MagicMock(return_value=asyncio.Future())
    mock_context.report_progress.return_value.set_result(None)

    # Use our mock PBIXRay class
    pbixray_server.current_model = MockPBIXRayWithFilterableData("/path/to/test.pbix")
    pbixray_server.current_model_path = "/path/to/test.pbix"

    # Test with multiple filters of different types
    result = await pbixray_server.get_table_contents(
        mock_context, table_name="Sales", filters="location_id=madrid;period>120;amount<20", page=1, page_size=10
    )

    # Verify the result
    parsed = json.loads(result)
    assert parsed["pagination"]["total_rows"] > 0, "Expected at least one row matching all filters"

    # Verify all filters were applied correctly
    for row in parsed["data"]:
        assert row["location_id"] == "madrid", "All rows should have location_id=madrid"
        assert row["period"] > 120, "All rows should have period>120"
        assert row["amount"] < 20, "All rows should have amount<20"

    # Clean up
    pbixray_server.current_model = None
    pbixray_server.current_model_path = None


@pytest.mark.asyncio
async def test_get_filtered_table_contents_pagination():
    """Test the pagination functionality of get_table_contents with filters"""
    # Create a mock Context with async methods
    mock_context = MagicMock()
    mock_context.info = MagicMock(return_value=asyncio.Future())
    mock_context.info.return_value.set_result(None)
    mock_context.report_progress = MagicMock(return_value=asyncio.Future())
    mock_context.report_progress.return_value.set_result(None)

    # Use our mock PBIXRay class
    pbixray_server.current_model = MockPBIXRayWithFilterableData("/path/to/test.pbix")
    pbixray_server.current_model_path = "/path/to/test.pbix"

    # Test with a filter that returns multiple rows and use pagination
    result_page1 = await pbixray_server.get_table_contents(
        mock_context, table_name="Sales", filters="period>100", page=1, page_size=3
    )

    result_page2 = await pbixray_server.get_table_contents(
        mock_context, table_name="Sales", filters="period>100", page=2, page_size=3
    )

    # Verify the pagination
    parsed_page1 = json.loads(result_page1)
    parsed_page2 = json.loads(result_page2)

    assert parsed_page1["pagination"]["current_page"] == 1, "First result should be page 1"
    assert parsed_page2["pagination"]["current_page"] == 2, "Second result should be page 2"

    assert len(parsed_page1["data"]) == 3, "Page 1 should have 3 rows"
    assert len(parsed_page2["data"]) > 0, "Page 2 should have at least 1 row"

    # Verify the rows are different between pages
    page1_ids = [row["product_id"] for row in parsed_page1["data"]]
    page2_ids = [row["product_id"] for row in parsed_page2["data"]]
    assert not any(pid in page2_ids for pid in page1_ids), "Pages should contain different rows"

    # Clean up
    pbixray_server.current_model = None
    pbixray_server.current_model_path = None


@pytest.mark.asyncio
async def test_get_filtered_table_contents_error_handling():
    """Test error handling in get_table_contents with filters"""
    # Create a mock Context with async methods
    mock_context = MagicMock()
    mock_context.info = MagicMock(return_value=asyncio.Future())
    mock_context.info.return_value.set_result(None)
    mock_context.report_progress = MagicMock(return_value=asyncio.Future())
    mock_context.report_progress.return_value.set_result(None)

    # Use our mock PBIXRay class
    pbixray_server.current_model = MockPBIXRayWithFilterableData("/path/to/test.pbix")
    pbixray_server.current_model_path = "/path/to/test.pbix"

    # Test with non-existent column
    result = await pbixray_server.get_table_contents(
        mock_context, table_name="Sales", filters="nonexistent_column=value", page=1, page_size=10
    )

    assert "Error" in result, "Expected error message for non-existent column"
    assert "not found" in result, "Error should indicate column not found"

    # Test with invalid filter syntax
    result = await pbixray_server.get_table_contents(
        mock_context, table_name="Sales", filters="invalid_filter_syntax", page=1, page_size=10
    )

    assert "Error" in result, "Expected error message for invalid filter syntax"
    assert "Invalid filter condition" in result, "Error should indicate invalid filter condition"

    # Test with invalid page number
    result = await pbixray_server.get_table_contents(
        mock_context, table_name="Sales", filters="location_id=madrid", page=999, page_size=10
    )

    assert "Error" in result, "Expected error message for invalid page number"
    assert "does not exist" in result, "Error should indicate page does not exist"

    # Clean up
    pbixray_server.current_model = None
    pbixray_server.current_model_path = None


@pytest.mark.asyncio
async def test_get_filtered_table_contents_with_real_file(pbix_file_path):
    """Test get_table_contents with filters on an actual PBIX file if available"""
    # Create a mock Context with async methods
    mock_context = MagicMock()
    mock_context.info = MagicMock(return_value=asyncio.Future())
    mock_context.info.return_value.set_result(None)
    mock_context.report_progress = MagicMock(return_value=asyncio.Future())
    mock_context.report_progress.return_value.set_result(None)

    if not pbix_file_path.exists():
        pytest.skip(f"PBIX file not found: {pbix_file_path}, skipping real file test")

    # Load the PBIX file
    await pbixray_server.load_pbix_file(str(pbix_file_path), mock_context)

    # Get the list of tables
    tables_json = pbixray_server.get_tables(mock_context)
    tables = json.loads(tables_json)

    if not tables:
        pytest.skip("No tables found in PBIX file")

    # Get the first table
    first_table = tables[0]

    # Get the table contents to find a column to filter on
    table_contents_json = await pbixray_server.get_table_contents(mock_context, table_name=first_table, page=1, page_size=5)

    table_contents = json.loads(table_contents_json)

    if not table_contents["data"]:
        pytest.skip(f"No data found in table {first_table}")

    # Get the first column name from the data
    first_column = list(table_contents["data"][0].keys())[0]
    first_value = table_contents["data"][0][first_column]

    # Create a filter based on the first column and value
    if isinstance(first_value, (int, float)):
        # For numeric values, use a range filter
        filter_expr = f"{first_column}>0"
    else:
        # For string values, use an equality filter
        filter_expr = f"{first_column}={first_value}"

    # Test the filtered table contents
    result = await pbixray_server.get_table_contents(
        mock_context, table_name=first_table, filters=filter_expr, page=1, page_size=5
    )

    # Verify the result
    assert result, "Expected filtered table contents"
    assert isinstance(result, str), "Expected JSON string"

    # Parse JSON to make sure it's valid
    parsed = json.loads(result)
    assert "pagination" in parsed, "Expected pagination info"
    assert "data" in parsed, "Expected data in response"

    # Verify that we got some data back
    assert len(parsed["data"]) > 0, "Expected at least one row in the filtered results"

    # Clean up
    pbixray_server.current_model = None
    pbixray_server.current_model_path = None
