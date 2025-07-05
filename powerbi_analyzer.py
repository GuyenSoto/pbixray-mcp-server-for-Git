import streamlit as st
import pandas as pd
import numpy as np
import json
import os
import sqlite3
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import networkx as nx
from datetime import datetime
import hashlib
import zipfile
import tempfile
import sys

# Add pbixray import (assuming it's installed)
try:
    from pbixray import PbixModel
    PBIXRAY_AVAILABLE = True
except ImportError:
    PBIXRAY_AVAILABLE = False
    st.error("PBIXRay not available. Please install: pip install pbixray")

class PowerBIDependencyAnalyzer:
    def __init__(self, db_path="powerbi_metadata.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database for storing metadata"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Projects table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                file_path TEXT,
                file_hash TEXT,
                last_analyzed TIMESTAMP,
                model_size INTEGER,
                table_count INTEGER,
                measure_count INTEGER
            )
        ''')
        
        # Tables table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tables (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                table_name TEXT,
                row_count INTEGER,
                column_count INTEGER,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
        ''')
        
        # Columns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS columns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_id INTEGER,
                column_name TEXT,
                data_type TEXT,
                is_calculated BOOLEAN,
                FOREIGN KEY (table_id) REFERENCES tables (id)
            )
        ''')
        
        # Measures table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS measures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                table_name TEXT,
                measure_name TEXT,
                dax_expression TEXT,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
        ''')
        
        # Relationships table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                from_table TEXT,
                from_column TEXT,
                to_table TEXT,
                to_column TEXT,
                cardinality TEXT,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
        ''')
        
        # Power Query table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS power_queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                query_name TEXT,
                m_expression TEXT,
                FOREIGN KEY (project_id) REFERENCES projects (id)
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
    
    def analyze_pbix_file(self, file_path, project_name=None):
        """Analyze a single PBIX file and store results in database"""
        if not PBIXRAY_AVAILABLE:
            return None
            
        try:
            # Load PBIX model
            model = PbixModel(file_path)
            
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
            
            # Insert or update project
            cursor.execute('''
                INSERT OR REPLACE INTO projects 
                (name, file_path, file_hash, last_analyzed, model_size, table_count, measure_count)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                project_name,
                file_path,
                file_hash,
                datetime.now(),
                os.path.getsize(file_path),
                len(model.tables) if hasattr(model, 'tables') else 0,
                len([m for table in model.tables for m in table.measures]) if hasattr(model, 'tables') else 0
            ))
            
            project_id = cursor.lastrowid or existing[0]
            
            # Clear existing data for this project
            cursor.execute('DELETE FROM tables WHERE project_id = ?', (project_id,))
            cursor.execute('DELETE FROM columns WHERE table_id IN (SELECT id FROM tables WHERE project_id = ?)', (project_id,))
            cursor.execute('DELETE FROM measures WHERE project_id = ?', (project_id,))
            cursor.execute('DELETE FROM relationships WHERE project_id = ?', (project_id,))
            cursor.execute('DELETE FROM power_queries WHERE project_id = ?', (project_id,))
            
            # Store tables and columns
            for table in model.tables:
                cursor.execute('''
                    INSERT INTO tables (project_id, table_name, row_count, column_count)
                    VALUES (?, ?, ?, ?)
                ''', (project_id, table.name, getattr(table, 'row_count', 0), len(table.columns)))
                
                table_id = cursor.lastrowid
                
                # Store columns
                for column in table.columns:
                    cursor.execute('''
                        INSERT INTO columns (table_id, column_name, data_type, is_calculated)
                        VALUES (?, ?, ?, ?)
                    ''', (table_id, column.name, getattr(column, 'data_type', 'Unknown'), 
                         getattr(column, 'is_calculated', False)))
                
                # Store measures
                for measure in table.measures:
                    cursor.execute('''
                        INSERT INTO measures (project_id, table_name, measure_name, dax_expression)
                        VALUES (?, ?, ?, ?)
                    ''', (project_id, table.name, measure.name, getattr(measure, 'expression', '')))
            
            # Store relationships
            for rel in model.relationships:
                cursor.execute('''
                    INSERT INTO relationships (project_id, from_table, from_column, to_table, to_column, cardinality)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (project_id, rel.from_table, rel.from_column, rel.to_table, rel.to_column, 
                     getattr(rel, 'cardinality', 'Unknown')))
            
            # Store Power Query expressions
            for query in model.queries:
                cursor.execute('''
                    INSERT INTO power_queries (project_id, query_name, m_expression)
                    VALUES (?, ?, ?)
                ''', (project_id, query.name, getattr(query, 'expression', '')))
            
            conn.commit()
            conn.close()
            
            return project_id
            
        except Exception as e:
            st.error(f"Error analyzing {file_path}: {str(e)}")
            return None
    
    def get_all_projects(self):
        """Get all analyzed projects"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query('SELECT * FROM projects ORDER BY last_analyzed DESC', conn)
        conn.close()
        return df
    
    def get_shared_tables(self):
        """Find tables that are shared across multiple projects"""
        conn = sqlite3.connect(self.db_path)
        query = '''
            SELECT t.table_name, COUNT(DISTINCT p.name) as project_count,
                   GROUP_CONCAT(DISTINCT p.name) as projects
            FROM tables t
            JOIN projects p ON t.project_id = p.id
            GROUP BY t.table_name
            HAVING COUNT(DISTINCT p.name) > 1
            ORDER BY project_count DESC
        '''
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def get_shared_measures(self):
        """Find measures with similar names across projects"""
        conn = sqlite3.connect(self.db_path)
        query = '''
            SELECT m.measure_name, COUNT(DISTINCT p.name) as project_count,
                   GROUP_CONCAT(DISTINCT p.name) as projects
            FROM measures m
            JOIN projects p ON m.project_id = p.id
            GROUP BY m.measure_name
            HAVING COUNT(DISTINCT p.name) > 1
            ORDER BY project_count DESC
        '''
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def analyze_impact(self, table_name=None, measure_name=None, column_name=None):
        """Analyze impact of changes to tables, measures, or columns"""
        conn = sqlite3.connect(self.db_path)
        results = {}
        
        if table_name:
            # Find projects using this table
            query = '''
                SELECT DISTINCT p.name as project_name
                FROM projects p
                JOIN tables t ON p.id = t.project_id
                WHERE t.table_name = ?
            '''
            df = pd.read_sql_query(query, conn, params=(table_name,))
            results['projects_using_table'] = df['project_name'].tolist()
            
            # Find measures referencing this table
            query = '''
                SELECT DISTINCT p.name as project_name, m.measure_name, m.dax_expression
                FROM projects p
                JOIN measures m ON p.id = m.project_id
                WHERE m.dax_expression LIKE ?
            '''
            df = pd.read_sql_query(query, conn, params=(f'%{table_name}%',))
            results['measures_referencing_table'] = df.to_dict('records')
        
        if measure_name:
            # Find projects with this measure
            query = '''
                SELECT DISTINCT p.name as project_name, m.table_name, m.dax_expression
                FROM projects p
                JOIN measures m ON p.id = m.project_id
                WHERE m.measure_name = ?
            '''
            df = pd.read_sql_query(query, conn, params=(measure_name,))
            results['projects_with_measure'] = df.to_dict('records')
        
        if column_name:
            # Find projects using this column
            query = '''
                SELECT DISTINCT p.name as project_name, t.table_name
                FROM projects p
                JOIN tables tb ON p.id = tb.project_id
                JOIN columns c ON tb.id = c.table_id
                WHERE c.column_name = ?
            '''
            df = pd.read_sql_query(query, conn, params=(column_name,))
            results['projects_using_column'] = df.to_dict('records')
        
        conn.close()
        return results
    
    def create_dependency_network(self):
        """Create network graph of project dependencies"""
        shared_tables = self.get_shared_tables()
        
        G = nx.Graph()
        
        # Add nodes for each project
        projects = self.get_all_projects()
        for _, project in projects.iterrows():
            G.add_node(project['name'], node_type='project')
        
        # Add edges based on shared tables
        for _, table_info in shared_tables.iterrows():
            if table_info['project_count'] > 1:
                project_list = table_info['projects'].split(',')
                # Add edges between all projects sharing this table
                for i in range(len(project_list)):
                    for j in range(i+1, len(project_list)):
                        if G.has_edge(project_list[i], project_list[j]):
                            G[project_list[i]][project_list[j]]['weight'] += 1
                        else:
                            G.add_edge(project_list[i], project_list[j], weight=1, shared_tables=[table_info['table_name']])
        
        return G

def main():
    st.set_page_config(
        page_title="Power BI Dependency Analyzer",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 Power BI Dependency Analyzer")
    st.markdown("**Analyze dependencies and impact across multiple Power BI projects**")
    
    # Initialize analyzer
    analyzer = PowerBIDependencyAnalyzer()
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page",
        ["File Upload & Analysis", "Project Overview", "Dependency Analysis", "Impact Analysis", "Network Visualization"]
    )
    
    if page == "File Upload & Analysis":
        st.header("📁 Upload and Analyze PBIX Files")
        
        uploaded_files = st.file_uploader(
            "Choose PBIX files",
            type=['pbix'],
            accept_multiple_files=True
        )
        
        if uploaded_files:
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
                project_id = analyzer.analyze_pbix_file(tmp_file_path, project_name)
                
                if project_id:
                    st.success(f"✅ Successfully analyzed {uploaded_file.name}")
                else:
                    st.error(f"❌ Failed to analyze {uploaded_file.name}")
                
                # Clean up temp file
                os.unlink(tmp_file_path)
                
                progress_bar.progress((i + 1) / len(uploaded_files))
            
            status_text.text('Analysis complete!')
    
    elif page == "Project Overview":
        st.header("📋 Project Overview")
        
        projects = analyzer.get_all_projects()
        
        if not projects.empty:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Projects", len(projects))
            with col2:
                st.metric("Total Tables", projects['table_count'].sum())
            with col3:
                st.metric("Total Measures", projects['measure_count'].sum())
            with col4:
                total_size_mb = projects['model_size'].sum() / (1024*1024)
                st.metric("Total Size (MB)", f"{total_size_mb:.1f}")
            
            st.subheader("Project Details")
            
            # Format the dataframe for display
            display_df = projects.copy()
            display_df['model_size'] = display_df['model_size'].apply(lambda x: f"{x/(1024*1024):.1f} MB")
            display_df['last_analyzed'] = pd.to_datetime(display_df['last_analyzed']).dt.strftime('%Y-%m-%d %H:%M')
            
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
        
        tab1, tab2 = st.tabs(["Shared Tables", "Shared Measures"])
        
        with tab1:
            st.subheader("Tables Used Across Multiple Projects")
            shared_tables = analyzer.get_shared_tables()
            
            if not shared_tables.empty:
                # Create bar chart
                fig = px.bar(
                    shared_tables.head(20),
                    x='table_name',
                    y='project_count',
                    title='Most Shared Tables Across Projects'
                )
                fig.update_xaxes(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
                
                st.dataframe(shared_tables, use_container_width=True)
            else:
                st.info("No shared tables found across projects.")
        
        with tab2:
            st.subheader("Measures with Same Names Across Projects")
            shared_measures = analyzer.get_shared_measures()
            
            if not shared_measures.empty:
                # Create bar chart
                fig = px.bar(
                    shared_measures.head(20),
                    x='measure_name',
                    y='project_count',
                    title='Most Common Measure Names Across Projects'
                )
                fig.update_xaxes(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
                
                st.dataframe(shared_measures, use_container_width=True)
            else:
                st.info("No shared measures found across projects.")
    
    elif page == "Impact Analysis":
        st.header("🎯 Impact Analysis")
        st.markdown("Analyze the impact of changes to tables, measures, or columns")
        
        analysis_type = st.selectbox("What do you want to analyze?", 
                                   ["Table Impact", "Measure Impact", "Column Impact"])
        
        if analysis_type == "Table Impact":
            # Get all unique table names
            conn = sqlite3.connect(analyzer.db_path)
            tables_df = pd.read_sql_query('SELECT DISTINCT table_name FROM tables ORDER BY table_name', conn)
            conn.close()
            
            if not tables_df.empty:
                table_name = st.selectbox("Select a table:", tables_df['table_name'].tolist())
                
                if st.button("Analyze Impact"):
                    impact = analyzer.analyze_impact(table_name=table_name)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("Projects Using This Table")
                        if impact.get('projects_using_table'):
                            for project in impact['projects_using_table']:
                                st.write(f"• {project}")
                        else:
                            st.info("No projects found using this table")
                    
                    with col2:
                        st.subheader("Measures Referencing This Table")
                        if impact.get('measures_referencing_table'):
                            for measure in impact['measures_referencing_table']:
                                st.write(f"**{measure['project_name']}** - {measure['measure_name']}")
                                with st.expander("Show DAX"):
                                    st.code(measure['dax_expression'])
                        else:
                            st.info("No measures found referencing this table")
        
        elif analysis_type == "Measure Impact":
            # Get all unique measure names
            conn = sqlite3.connect(analyzer.db_path)
            measures_df = pd.read_sql_query('SELECT DISTINCT measure_name FROM measures ORDER BY measure_name', conn)
            conn.close()
            
            if not measures_df.empty:
                measure_name = st.selectbox("Select a measure:", measures_df['measure_name'].tolist())
                
                if st.button("Analyze Impact"):
                    impact = analyzer.analyze_impact(measure_name=measure_name)
                    
                    st.subheader("Projects with This Measure")
                    if impact.get('projects_with_measure'):
                        for measure in impact['projects_with_measure']:
                            st.write(f"**{measure['project_name']}** - Table: {measure['table_name']}")
                            with st.expander("Show DAX"):
                                st.code(measure['dax_expression'])
                    else:
                        st.info("No projects found with this measure")
        
        elif analysis_type == "Column Impact":
            # Get all unique column names
            conn = sqlite3.connect(analyzer.db_path)
            columns_df = pd.read_sql_query('SELECT DISTINCT column_name FROM columns ORDER BY column_name', conn)
            conn.close()
            
            if not columns_df.empty:
                column_name = st.selectbox("Select a column:", columns_df['column_name'].tolist())
                
                if st.button("Analyze Impact"):
                    impact = analyzer.analyze_impact(column_name=column_name)
                    
                    st.subheader("Projects Using This Column")
                    if impact.get('projects_using_column'):
                        for usage in impact['projects_using_column']:
                            st.write(f"• **{usage['project_name']}** - Table: {usage['table_name']}")
                    else:
                        st.info("No projects found using this column")
    
    elif page == "Network Visualization":
        st.header("🕸️ Project Dependency Network")
        st.markdown("Visualize how projects are connected through shared tables")
        
        try:
            G = analyzer.create_dependency_network()
            
            if len(G.nodes()) > 0:
                # Create network layout
                pos = nx.spring_layout(G, k=1, iterations=50)
                
                # Prepare data for plotting
                edge_x = []
                edge_y = []
                edge_info = []
                
                for edge in G.edges():
                    x0, y0 = pos[edge[0]]
                    x1, y1 = pos[edge[1]]
                    edge_x.extend([x0, x1, None])
                    edge_y.extend([y0, y1, None])
                    edge_info.append(f"{edge[0]} ↔ {edge[1]}<br>Shared connections: {G[edge[0]][edge[1]]['weight']}")
                
                node_x = []
                node_y = []
                node_text = []
                node_size = []
                
                for node in G.nodes():
                    x, y = pos[node]
                    node_x.append(x)
                    node_y.append(y)
                    node_text.append(node)
                    # Size based on number of connections
                    node_size.append(10 + len(list(G.neighbors(node))) * 5)
                
                # Create the plot
                fig = go.Figure()
                
                # Add edges
                fig.add_trace(go.Scatter(
                    x=edge_x, y=edge_y,
                    line=dict(width=2, color='#888'),
                    hoverinfo='none',
                    mode='lines'
                ))
                
                # Add nodes
                fig.add_trace(go.Scatter(
                    x=node_x, y=node_y,
                    mode='markers+text',
                    hoverinfo='text',
                    text=node_text,
                    textposition="middle center",
                    marker=dict(
                        size=node_size,
                        color='lightblue',
                        line=dict(width=2, color='darkblue')
                    )
                ))
                
                fig.update_layout(
                    title="Project Dependency Network",
                    titlefont_size=16,
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=20,l=5,r=5,t=40),
                    annotations=[ dict(
                        text="Node size represents number of connections",
                        showarrow=False,
                        xref="paper", yref="paper",
                        x=0.005, y=-0.002,
                        xanchor='left', yanchor='bottom',
                        font=dict(size=12)
                    )],
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Show network statistics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Projects", len(G.nodes()))
                with col2:
                    st.metric("Total Connections", len(G.edges()))
                with col3:
                    if len(G.nodes()) > 0:
                        density = nx.density(G)
                        st.metric("Network Density", f"{density:.3f}")
            else:
                st.info("No project dependencies found. Upload more projects with shared tables to see the network.")
                
        except Exception as e:
            st.error(f"Error creating network visualization: {str(e)}")

if __name__ == "__main__":
    main()