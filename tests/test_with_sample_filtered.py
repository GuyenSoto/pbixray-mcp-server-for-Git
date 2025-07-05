#!/usr/bin/env python3
"""
Test the PBIXRay MCP server's filtered table contents functionality with a sample PBIX file
"""

import os
import asyncio
import json
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client
from mcp import StdioServerParameters


async def main():
    """Test the get_filtered_table_contents method with a sample file"""
    server_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "pbixray_server.py")
    sample_file_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "demo", "AdventureWorks Sales.pbix"
    )

    # Make sure the sample file exists
    if not os.path.exists(sample_file_path):
        print(f"Error: Sample file not found at {sample_file_path}")
        return

    # Start the server process
    server_params = StdioServerParameters(command="python", args=[server_path], env=None)

    print(f"Connecting to PBIXRay server and testing filtered table contents with file: {os.path.basename(sample_file_path)}")

    async with stdio_client(server_params) as streams:
        async with ClientSession(streams[0], streams[1]) as session:
            # Initialize the session
            await session.initialize()

            # Load the sample PBIX file
            print("\n1. Loading PBIX file...")
            load_result = await session.call_tool("load_pbix_file", {"file_path": sample_file_path})
            print_result(load_result)

            # List tables
            print("\n2. Listing tables...")
            tables_result = await session.call_tool("get_tables", {})
            print_result(tables_result)

            # Parse the tables result to get the first table
            tables = []
            for content in tables_result.content:
                if hasattr(content, "text") and content.text:
                    try:
                        tables = json.loads(content.text)
                        break
                    except json.JSONDecodeError:
                        pass

            if not tables:
                print("No tables found in the PBIX file")
                return

            first_table = tables[0]
            print(f"\nUsing table: {first_table}")

            # Get the schema to find columns to filter on
            print("\n3. Getting schema for the first table...")
            schema_result = await session.call_tool("get_schema", {"table_name": first_table})
            print_result(schema_result)

            # Get a sample of the table contents to find values to filter on
            print("\n4. Getting sample table contents...")
            contents_result = await session.call_tool(
                "get_table_contents", {"table_name": first_table, "page": 1, "page_size": 5}
            )
            print_result(contents_result)

            # Parse the contents to find a column to filter on
            column_to_filter = None
            filter_value = None

            for content in contents_result.content:
                if hasattr(content, "text") and content.text:
                    try:
                        data = json.loads(content.text)
                        if data.get("data") and len(data["data"]) > 0:
                            # Get the first column and its value from the first row
                            first_row = data["data"][0]
                            column_to_filter = list(first_row.keys())[0]
                            filter_value = first_row[column_to_filter]
                            break
                    except (json.JSONDecodeError, KeyError, IndexError):
                        pass

            if not column_to_filter:
                print("Could not find a column to filter on")
                return

            # Create filter expressions based on the data type
            if isinstance(filter_value, (int, float)):
                # For numeric values, create a range filter
                filter_expr = f"{column_to_filter}>0"
                print(f"\n5. Testing numeric filter: {filter_expr}")
            else:
                # For string values, create an equality filter
                filter_expr = f"{column_to_filter}={filter_value}"
                print(f"\n5. Testing equality filter: {filter_expr}")

            # Test the filtered table contents
            filtered_result = await session.call_tool(
                "get_table_contents", {"table_name": first_table, "filters": filter_expr, "page": 1, "page_size": 5}
            )
            print_result(filtered_result)

            # Test multiple filters if we have numeric columns
            # Try to find a numeric column
            numeric_column = None
            for content in contents_result.content:
                if hasattr(content, "text") and content.text:
                    try:
                        data = json.loads(content.text)
                        if data.get("data") and len(data["data"]) > 0:
                            # Look for a numeric column
                            first_row = data["data"][0]
                            for col, val in first_row.items():
                                if isinstance(val, (int, float)):
                                    numeric_column = col
                                    break
                            if numeric_column:
                                break
                    except (json.JSONDecodeError, KeyError, IndexError):
                        pass

            if numeric_column:
                # Create a multi-filter expression
                multi_filter_expr = f"{column_to_filter}={filter_value};{numeric_column}>0"
                print(f"\n6. Testing multiple filters: {multi_filter_expr}")

                multi_filtered_result = await session.call_tool(
                    "get_table_contents", {"table_name": first_table, "filters": multi_filter_expr, "page": 1, "page_size": 5}
                )
                print_result(multi_filtered_result)

            print("\nAll tests completed successfully!")


def print_result(result):
    """Print tool call results in a readable format"""
    for content in result.content:
        if hasattr(content, "text") and content.text:
            try:
                # Try to parse and pretty print JSON
                data = json.loads(content.text)
                print(json.dumps(data, indent=2))
            except json.JSONDecodeError:
                # Regular text output
                print(content.text)


if __name__ == "__main__":
    asyncio.run(main())
