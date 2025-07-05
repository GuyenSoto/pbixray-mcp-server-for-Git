import streamlit as st
import pandas as pd
import numpy as np
import json
import os
import sqlite3
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
from datetime import datetime
import hashlib
import tempfile
import subprocess
import time
import threading
import socket
from contextlib import contextmanager

class MCPStreamlitBridge:
    """Bridge to connect Streamlit with MCP pbixray server"""
    
    def __init__(self, mcp_server_path=None, python_path=None):
        self.mcp_server_path = mcp_server_path or r"D:\AI\Guyen\pbixray-mcp-server-main\src\pbixray_server.py"
        self.python_path = python_path or r"D:\AI\Guyen\pbixray-mcp-server-main\.venv\Scripts\python.exe"
        self.server_process = None
        self.db_path = "powerbi_metadata.db"
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database for storing metadata"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if tables_data column exists, if not add it
        cursor.execute("PRAGMA table_info(projects)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'tables_data' not in columns:
            # Drop and recreate the table with the correct schema
            cursor.execute('DROP TABLE IF EXISTS projects')
        
        # Projects table with new schema
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                file_path TEXT,
                file_hash TEXT,
                last_analyzed TIMESTAMP,
                model_size INTEGER,
                tables_data TEXT,
                metadata_data TEXT,
                schema_data TEXT,
                measures_data TEXT,
                relationships_data TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_file_hash(self, file_path):
        """Calculate MD5 hash of file for change detection"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def analyze_pbix_file_with_mcp(self, file_path, project_name=None):
        """Analyze PBIX file using the MCP server through direct file processing"""
        if project_name is None:
            project_name = Path(file_path).stem
        
        file_hash = self.get_file_hash(file_path)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if project already exists and if file has changed
        cursor.execute('SELECT id, file_hash FROM projects WHERE name = ?', (project_name,))
        existing = cursor.fetchone()
        
        if existing and existing[1] == file_hash:
            st.info(f"Project {project_name} already analyzed and unchanged. Skipping.")
            conn.close()
            return existing[0]
        
        # Delete existing project data if it exists (avoid duplicates)
        if existing:
            cursor.execute('DELETE FROM projects WHERE name = ?', (project_name,))
            conn.commit()
        
        try:
            # Create a temporary script to run in the MCP environment
            temp_script = f"""
import sys
sys.path.append(r'{Path(self.mcp_server_path).parent}')
import json
import pbixray

try:
    # Use the correct PBIXRay class
    model = pbixray.PBIXRay(r'{file_path}')
    
    # Extract all the data we need
    result = {{
        'tables': [],
        'metadata': {{}},
        'schema': [],
        'measures': [],
        'relationships': []
    }}
    
    # Get tables - we know this method exists
    try:
        tables_data = model.tables
        print(f"TABLES_TYPE: {{type(tables_data)}}")
        print(f"TABLES_SHAPE: {{getattr(tables_data, 'shape', 'No shape attribute')}}")
        
        # Convert to list if it's a numpy array or similar
        if hasattr(tables_data, 'tolist'):
            tables_list = tables_data.tolist()
        elif hasattr(tables_data, '__iter__'):
            tables_list = list(tables_data)
        else:
            tables_list = [tables_data]
        
        print(f"TABLES_LIST_LENGTH: {{len(tables_list)}}")
        
        for i, table_name in enumerate(tables_list):
            print(f"TABLE_{{i}}: {{table_name}}")
            
            table_info = {{
                'name': str(table_name),
                'row_count': 0,
                'column_count': 0,
                'columns': []
            }}
            
            # Try to get table details using get_table method
            try:
                table_details = model.get_table(table_name)
                if table_details is not None:
                    print(f"TABLE_DETAILS_TYPE: {{type(table_details)}}")
                    # If it's a DataFrame, get column info
                    if hasattr(table_details, 'columns'):
                        columns = table_details.columns.tolist() if hasattr(table_details.columns, 'tolist') else list(table_details.columns)
                        table_info['column_count'] = len(columns)
                        for col_name in columns:
                            table_info['columns'].append({{
                                'name': str(col_name),
                                'data_type': 'Unknown',
                                'is_calculated': False
                            }})
                    
                    # Get row count if available
                    if hasattr(table_details, 'shape'):
                        table_info['row_count'] = table_details.shape[0]
                    elif hasattr(table_details, '__len__'):
                        table_info['row_count'] = len(table_details)
            except Exception as e:
                print(f"ERROR_GETTING_TABLE_DETAILS: {{e}}")
            
            result['tables'].append(table_info)
            
    except Exception as e:
        print(f"ERROR_GETTING_TABLES: {{e}}")
    
    # Get DAX measures
    try:
        measures_data = model.dax_measures
        print(f"MEASURES_TYPE: {{type(measures_data)}}")
        
        if hasattr(measures_data, 'items'):  # Dictionary-like
            for table_name, measures_list in measures_data.items():
                if hasattr(measures_list, '__iter__'):
                    for measure_item in measures_list:
                        if hasattr(measure_item, 'items'):  # Dictionary-like measure
                            measure_name = measure_item.get('Name', measure_item.get('name', 'Unknown'))
                            expression = measure_item.get('Expression', measure_item.get('expression', ''))
                        else:
                            measure_name = str(measure_item)
                            expression = ''
                        
                        result['measures'].append({{
                            'table_name': str(table_name),
                            'name': str(measure_name),
                            'expression': str(expression)
                        }})
        elif hasattr(measures_data, '__iter__'):  # List-like
            for measure_item in measures_data:
                result['measures'].append({{
                    'table_name': 'Unknown',
                    'name': str(measure_item),
                    'expression': ''
                }})
    except Exception as e:
        print(f"ERROR_GETTING_MEASURES: {{e}}")
    
    # Get relationships
    try:
        relationships_data = model.relationships
        print(f"RELATIONSHIPS_TYPE: {{type(relationships_data)}}")
        
        if hasattr(relationships_data, '__iter__'):
            for rel_item in relationships_data:
                if hasattr(rel_item, 'items'):  # Dictionary-like
                    rel_info = {{
                        'from_table': str(rel_item.get('FromTable', rel_item.get('from_table', ''))),
                        'from_column': str(rel_item.get('FromColumn', rel_item.get('from_column', ''))),
                        'to_table': str(rel_item.get('ToTable', rel_item.get('to_table', ''))),
                        'to_column': str(rel_item.get('ToColumn', rel_item.get('to_column', ''))),
                        'cardinality': str(rel_item.get('Cardinality', rel_item.get('cardinality', 'Unknown')))
                    }}
                    result['relationships'].append(rel_info)
    except Exception as e:
        print(f"ERROR_GETTING_RELATIONSHIPS: {{e}}")
    
    # Get metadata
    try:
        metadata_info = model.metadata
        print(f"METADATA_TYPE: {{type(metadata_info)}}")
        result['metadata'] = {{
            'table_count': len(result['tables']),
            'measure_count': len(result['measures']),
            'relationship_count': len(result['relationships']),
            'model_size': getattr(model, 'size', 0)
        }}
    except Exception as e:
        print(f"ERROR_GETTING_METADATA: {{e}}")
        result['metadata'] = {{
            'table_count': len(result['tables']),
            'measure_count': len(result['measures']),
            'relationship_count': len(result['relationships'])
        }}
    
    print("SUCCESS:" + json.dumps(result))

except Exception as e:
    import traceback
    print("ERROR:" + str(e))
    print("TRACEBACK:" + traceback.format_exc())
"""
            
            # Write temp script
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(temp_script)
                temp_script_path = f.name
            
            try:
                # Run the script in the MCP environment
                result = subprocess.run(
                    [self.python_path, temp_script_path],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0 and "SUCCESS:" in result.stdout:
                    # Parse the JSON result
                    json_start = result.stdout.find("SUCCESS:") + 8
                    json_data = result.stdout[json_start:].strip()
                    data = json.loads(json_data)
                    
                    # Store in database
                    cursor.execute('''
                        INSERT OR REPLACE INTO projects 
                        (name, file_path, file_hash, last_analyzed, model_size, 
                         tables_data, metadata_data, schema_data, measures_data, relationships_data)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        project_name,
                        file_path,
                        file_hash,
                        datetime.now(),
                        os.path.getsize(file_path),
                        json.dumps(data['tables']),
                        json.dumps(data['metadata']),
                        json.dumps(data.get('schema', [])),
                        json.dumps(data['measures']),
                        json.dumps(data['relationships'])
                    ))
                    
                    conn.commit()
                    project_id = cursor.lastrowid or existing[0]
                    
                else:
                    # Show detailed error information
                    error_details = f"""
                    Return code: {result.returncode}
                    STDOUT: {result.stdout}
                    STDERR: {result.stderr}
                    """
                    st.error(f"Error analyzing {project_name}:")
                    st.code(error_details)
                    project_id = None
            
            finally:
                # Clean up temp file
                os.unlink(temp_script_path)
        
        except Exception as e:
            st.error(f"Error analyzing {project_name}: {str(e)}")
            project_id = None
        
        conn.close()
        return project_id
    
    def get_all_projects(self):
        """Get all analyzed projects"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query('SELECT * FROM projects ORDER BY last_analyzed DESC', conn)
        conn.close()
        return df
    
    def get_shared_tables(self):
        """Find tables that are shared across multiple projects"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all projects with their tables data
        cursor.execute('SELECT name, tables_data FROM projects WHERE tables_data IS NOT NULL')
        projects = cursor.fetchall()
        
        table_usage = {}
        
        for project_name, tables_json in projects:
            if tables_json:
                try:
                    tables = json.loads(tables_json)
                    for table in tables:
                        table_name = table['name']
                        if table_name not in table_usage:
                            table_usage[table_name] = set()
                        table_usage[table_name].add(project_name)
                except json.JSONDecodeError:
                    continue
        
        # Filter for shared tables and create proper format
        shared = []
        for table_name, project_set in table_usage.items():
            if len(project_set) > 1:
                shared.append({
                    'table_name': table_name,
                    'project_count': len(project_set),
                    'projects': ', '.join(sorted(project_set))
                })
        
        conn.close()
        return pd.DataFrame(shared).sort_values('project_count', ascending=False) if shared else pd.DataFrame()
    
    def get_shared_measures(self):
        """Find measures with similar names across projects"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all projects with their measures data
        cursor.execute('SELECT name, measures_data FROM projects WHERE measures_data IS NOT NULL')
        projects = cursor.fetchall()
        
        measure_usage = {}
        
        for project_name, measures_json in projects:
            if measures_json:
                try:
                    measures = json.loads(measures_json)
                    for measure in measures:
                        measure_name = measure['name']
                        if measure_name not in measure_usage:
                            measure_usage[measure_name] = set()
                        measure_usage[measure_name].add(project_name)
                except json.JSONDecodeError:
                    continue
        
        # Filter for shared measures and create proper format
        shared = []
        for measure_name, project_set in measure_usage.items():
            if len(project_set) > 1:
                shared.append({
                    'measure_name': measure_name,
                    'project_count': len(project_set),
                    'projects': ', '.join(sorted(project_set))
                })
        
        conn.close()
        return pd.DataFrame(shared).sort_values('project_count', ascending=False) if shared else pd.DataFrame()
    
    def get_shared_columns(self):
        """Find columns that are shared across multiple projects"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all projects with their tables data
        cursor.execute('SELECT name, tables_data FROM projects WHERE tables_data IS NOT NULL')
        projects = cursor.fetchall()
        
        column_usage = {}
        
        for project_name, tables_json in projects:
            if tables_json:
                try:
                    tables = json.loads(tables_json)
                    for table in tables:
                        table_name = table['name']
                        for column in table.get('columns', []):
                            column_name = column['name']
                            key = f"{table_name}.{column_name}"
                            if key not in column_usage:
                                column_usage[key] = set()
                            column_usage[key].add(project_name)
                except json.JSONDecodeError:
                    continue
        
        # Filter for shared columns and create proper format
        shared = []
        for column_key, project_set in column_usage.items():
            if len(project_set) > 1:
                shared.append({
                    'column_name': column_key,
                    'project_count': len(project_set),
                    'projects': ', '.join(sorted(project_set))
                })
        
        conn.close()
        return pd.DataFrame(shared).sort_values('project_count', ascending=False) if shared else pd.DataFrame()
    
    def analyze_impact(self, search_term, search_type="all"):
        """Analyze impact of changes to tables, measures, or columns"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        results = {
            'projects_using_table': [],
            'measures_referencing_item': [],
            'projects_with_measure': [],
            'projects_using_column': []
        }
        
        search_term_lower = search_term.lower()
        
        # Get all projects data
        cursor.execute('SELECT name, tables_data, measures_data FROM projects WHERE tables_data IS NOT NULL OR measures_data IS NOT NULL')
        projects = cursor.fetchall()
        
        for project_name, tables_json, measures_json in projects:
            # Check tables
            if tables_json and (search_type in ["all", "table"]):
                try:
                    tables = json.loads(tables_json)
                    for table in tables:
                        # Check if table name matches
                        if search_term_lower in table['name'].lower():
                            results['projects_using_table'].append({
                                'project_name': project_name,
                                'table_name': table['name'],
                                'match_type': 'Table Name'
                            })
                        
                        # Check columns in this table
                        for column in table.get('columns', []):
                            if search_term_lower in column['name'].lower():
                                results['projects_using_column'].append({
                                    'project_name': project_name,
                                    'table_name': table['name'],
                                    'column_name': column['name'],
                                    'match_type': 'Column Name'
                                })
                except json.JSONDecodeError:
                    continue
            
            # Check measures
            if measures_json and (search_type in ["all", "measure"]):
                try:
                    measures = json.loads(measures_json)
                    for measure in measures:
                        # Check if measure name matches
                        if search_term_lower in measure['name'].lower():
                            results['projects_with_measure'].append({
                                'project_name': project_name,
                                'table_name': measure.get('table_name', 'Unknown'),
                                'measure_name': measure['name'],
                                'dax_expression': measure.get('expression', ''),
                                'match_type': 'Measure Name'
                            })
                        
                        # Check if measure DAX expression references the search term
                        expression = measure.get('expression', '').lower()
                        if search_term_lower in expression:
                            results['measures_referencing_item'].append({
                                'project_name': project_name,
                                'measure_name': measure['name'],
                                'dax_expression': measure.get('expression', ''),
                                'match_type': 'DAX Expression Reference'
                            })
                except json.JSONDecodeError:
                    continue
        
        conn.close()
        return results

def main():
    st.set_page_config(
        page_title="Power BI Dependency Analyzer (MCP Bridge)",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 Power BI Dependency Analyzer")
    st.markdown("**Using MCP PBIXRay Server as Backend**")
    
    # Initialize bridge
    bridge = MCPStreamlitBridge()
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page",
        ["File Upload & Analysis", "Project Overview", "Dependency Analysis", "Impact Analysis"]
    )
    
    if page == "File Upload & Analysis":
        st.header("📁 Upload and Analyze PBIX Files")
        
        # Add clear database option
        col1, col2 = st.columns([3, 1])
        
        with col2:
            if st.button("🗑️ Clear All Data"):
                if st.session_state.get('confirm_clear', False):
                    # Clear the database
                    conn = sqlite3.connect(bridge.db_path)
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM projects')
                    conn.commit()
                    conn.close()
                    st.success("✅ All data cleared!")
                    st.session_state.confirm_clear = False
                    st.rerun()
                else:
                    st.session_state.confirm_clear = True
                    st.warning("⚠️ Click again to confirm deletion of all data")
        
        with col1:
            uploaded_files = st.file_uploader(
                "Choose PBIX files",
                type=['pbix'],
                accept_multiple_files=True
            )
        
        # Show current projects in database
        current_projects = bridge.get_all_projects()
        if not current_projects.empty:
            st.subheader("📋 Current Projects in Database")
            
            # Add individual delete options
            for _, project in current_projects.iterrows():
                col_name, col_delete = st.columns([4, 1])
                with col_name:
                    st.write(f"📊 {project['name']} - {project['last_analyzed']}")
                with col_delete:
                    if st.button(f"❌", key=f"delete_{project['id']}"):
                        # Delete individual project
                        conn = sqlite3.connect(bridge.db_path)
                        cursor = conn.cursor()
                        cursor.execute('DELETE FROM projects WHERE id = ?', (project['id'],))
                        conn.commit()
                        conn.close()
                        st.success(f"Deleted {project['name']}")
                        st.rerun()
        
        if uploaded_files:
            if st.button("🔄 Analyze Files (Replace if exists)"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, uploaded_file in enumerate(uploaded_files):
                    status_text.text(f'Analyzing {uploaded_file.name}...')
                    
                    # Save uploaded file temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pbix') as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_file_path = tmp_file.name
                    
                    # Analyze the file
                    project_name = uploaded_file.name.replace('.pbix', '')
                    
                    # First, delete existing project if it exists
                    conn = sqlite3.connect(bridge.db_path)
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM projects WHERE name = ?', (project_name,))
                    conn.commit()
                    conn.close()
                    
                    project_id = bridge.analyze_pbix_file_with_mcp(tmp_file_path, project_name)
                    
                    if project_id:
                        st.success(f"✅ Successfully analyzed {uploaded_file.name}")
                    else:
                        st.error(f"❌ Failed to analyze {uploaded_file.name}")
                    
                    # Clean up temp file
                    os.unlink(tmp_file_path)
                    
                    progress_bar.progress((i + 1) / len(uploaded_files))
                
                status_text.text('Analysis complete!')
                st.rerun()  # Refresh the page to show updated data
    
    elif page == "Project Overview":
        st.header("📋 Project Overview")
        
        projects = bridge.get_all_projects()
        
        if not projects.empty:
            col1, col2, col3, col4 = st.columns(4)
            
            # Calculate metrics from JSON data
            total_tables = 0
            total_measures = 0
            
            for _, row in projects.iterrows():
                if row['metadata_data']:
                    metadata = json.loads(row['metadata_data'])
                    total_tables += metadata.get('table_count', 0)
                    total_measures += metadata.get('measure_count', 0)
            
            with col1:
                st.metric("Total Projects", len(projects))
            with col2:
                st.metric("Total Tables", total_tables)
            with col3:
                st.metric("Total Measures", total_measures)
            with col4:
                total_size_mb = projects['model_size'].sum() / (1024*1024)
                st.metric("Total Size (MB)", f"{total_size_mb:.1f}")
            
            st.subheader("Project Details")
            
            # Format the dataframe for display
            display_df = projects.copy()
            display_df['model_size'] = display_df['model_size'].apply(lambda x: f"{x/(1024*1024):.1f} MB")
            display_df['last_analyzed'] = pd.to_datetime(display_df['last_analyzed']).dt.strftime('%Y-%m-%d %H:%M')
            
            # Add calculated columns
            display_df['table_count'] = display_df['metadata_data'].apply(
                lambda x: json.loads(x).get('table_count', 0) if x else 0
            )
            display_df['measure_count'] = display_df['metadata_data'].apply(
                lambda x: json.loads(x).get('measure_count', 0) if x else 0
            )
            
            st.dataframe(
                display_df[['name', 'table_count', 'measure_count', 'model_size', 'last_analyzed']],
                column_config={
                    'name': 'Project Name',
                    'table_count': 'Tables',
                    'measure_count': 'Measures',
                    'model_size': 'Size',
                    'last_analyzed': 'Last Analyzed'
                },
                use_container_width=True
            )
        else:
            st.info("No projects analyzed yet. Please upload PBIX files first.")
    
    elif page == "Dependency Analysis":
        st.header("🔗 Dependency Analysis")
        
        tab1, tab2, tab3 = st.tabs(["Shared Tables", "Shared Measures", "Shared Columns"])
        
        with tab1:
            st.subheader("Tables Used Across Multiple Projects")
            shared_tables = bridge.get_shared_tables()
            
            if not shared_tables.empty:
                # Create bar chart
                fig = px.bar(
                    shared_tables.head(20),
                    x='table_name',
                    y='project_count',
                    title='Most Shared Tables Across Projects',
                    hover_data=['projects']
                )
                fig.update_xaxes(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
                
                st.dataframe(
                    shared_tables,
                    column_config={
                        'table_name': 'Table Name',
                        'project_count': 'Used in # Projects',
                        'projects': 'Project Names'
                    },
                    use_container_width=True
                )
            else:
                st.info("No shared tables found across projects.")
        
        with tab2:
            st.subheader("Measures with Same Names Across Projects")
            shared_measures = bridge.get_shared_measures()
            
            if not shared_measures.empty:
                # Create bar chart
                fig = px.bar(
                    shared_measures.head(20),
                    x='measure_name',
                    y='project_count',
                    title='Most Common Measure Names Across Projects',
                    hover_data=['projects']
                )
                fig.update_xaxes(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
                
                st.dataframe(
                    shared_measures,
                    column_config={
                        'measure_name': 'Measure Name',
                        'project_count': 'Used in # Projects',
                        'projects': 'Project Names'
                    },
                    use_container_width=True
                )
            else:
                st.info("No shared measures found across projects.")
        
        with tab3:
            st.subheader("Columns Used Across Multiple Projects")
            shared_columns = bridge.get_shared_columns()
            
            if not shared_columns.empty:
                # Create bar chart
                fig = px.bar(
                    shared_columns.head(20),
                    x='column_name',
                    y='project_count',
                    title='Most Shared Columns Across Projects',
                    hover_data=['projects']
                )
                fig.update_xaxes(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
                
                st.dataframe(
                    shared_columns,
                    column_config={
                        'column_name': 'Table.Column',
                        'project_count': 'Used in # Projects',
                        'projects': 'Project Names'
                    },
                    use_container_width=True
                )
            else:
                st.info("No shared columns found across projects.")
    
    elif page == "Impact Analysis":
        st.header("🎯 Impact Analysis")
        st.markdown("Search for any table, measure, or column name to see where it's used across all projects")
        
        # Free text input instead of dropdown
        search_term = st.text_input(
            "Enter table name, measure name, or column name to search:",
            placeholder="e.g., Sales, Total Revenue, CustomerID"
        )
        
        search_type = st.selectbox(
            "Search in:",
            ["all", "table", "measure", "column"],
            format_func=lambda x: {
                "all": "All (Tables, Measures, Columns)",
                "table": "Tables only",
                "measure": "Measures only", 
                "column": "Columns only"
            }[x]
        )
        
        if search_term and len(search_term.strip()) > 0:
            with st.spinner(f"Searching for '{search_term}'..."):
                impact = bridge.analyze_impact(search_term.strip(), search_type)
                
                # Display results in tabs
                tab1, tab2, tab3, tab4 = st.tabs([
                    f"Tables ({len(impact.get('projects_using_table', []))})",
                    f"Columns ({len(impact.get('projects_using_column', []))})",
                    f"Measures ({len(impact.get('projects_with_measure', []))})",
                    f"DAX References ({len(impact.get('measures_referencing_item', []))})"
                ])
                
                with tab1:
                    st.subheader(f"Tables matching '{search_term}'")
                    if impact.get('projects_using_table'):
                        df = pd.DataFrame(impact['projects_using_table'])
                        st.dataframe(
                            df,
                            column_config={
                                'project_name': 'Project',
                                'table_name': 'Table Name',
                                'match_type': 'Match Type'
                            },
                            use_container_width=True
                        )
                    else:
                        st.info(f"No tables found matching '{search_term}'")
                
                with tab2:
                    st.subheader(f"Columns matching '{search_term}'")
                    if impact.get('projects_using_column'):
                        df = pd.DataFrame(impact['projects_using_column'])
                        st.dataframe(
                            df,
                            column_config={
                                'project_name': 'Project',
                                'table_name': 'Table',
                                'column_name': 'Column Name',
                                'match_type': 'Match Type'
                            },
                            use_container_width=True
                        )
                    else:
                        st.info(f"No columns found matching '{search_term}'")
                
                with tab3:
                    st.subheader(f"Measures matching '{search_term}'")
                    if impact.get('projects_with_measure'):
                        for i, measure in enumerate(impact['projects_with_measure']):
                            with st.expander(f"📊 {measure['project_name']} - {measure['measure_name']}"):
                                col1, col2 = st.columns([1, 2])
                                with col1:
                                    st.write(f"**Project:** {measure['project_name']}")
                                    st.write(f"**Table:** {measure['table_name']}")
                                    st.write(f"**Measure:** {measure['measure_name']}")
                                with col2:
                                    st.write("**DAX Expression:**")
                                    st.code(measure['dax_expression'], language='dax')
                    else:
                        st.info(f"No measures found matching '{search_term}'")
                
                with tab4:
                    st.subheader(f"DAX expressions referencing '{search_term}'")
                    if impact.get('measures_referencing_item'):
                        for i, measure in enumerate(impact['measures_referencing_item']):
                            with st.expander(f"🔗 {measure['project_name']} - {measure['measure_name']}"):
                                col1, col2 = st.columns([1, 2])
                                with col1:
                                    st.write(f"**Project:** {measure['project_name']}")
                                    st.write(f"**Measure:** {measure['measure_name']}")
                                with col2:
                                    st.write("**DAX Expression:**")
                                    st.code(measure['dax_expression'], language='dax')
                    else:
                        st.info(f"No DAX expressions found referencing '{search_term}'")
        else:
            st.info("👆 Enter a search term above to analyze impact across all projects")

if __name__ == "__main__":
    main()