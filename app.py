import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import os
from io import StringIO
import hashlib
import re

# PDF handling
try:
    from PyPDF2 import PdfReader
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

# Page configuration
st.set_page_config(
    page_title="P&L Management System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Outfit:wght@300;400;600;700;800&display=swap');
    
    .stApp {
        font-family: 'Outfit', sans-serif;
    }
    
    h1 {
        color: #facc15;
        font-weight: 800;
        font-size: 3rem;
    }
    
    h2, h3 {
        color: #fbbf24;
        font-weight: 700;
    }
    
    .success-box {
        background-color: #065f46;
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #10b981;
        margin: 1rem 0;
    }
    
    .warning-box {
        background-color: #92400e;
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #f59e0b;
        margin: 1rem 0;
    }
    
    .info-box {
        background-color: #1e3a8a;
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #3b82f6;
        margin: 1rem 0;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #facc15 0%, #fbbf24 100%);
        color: #0f172a;
        font-weight: 700;
        border: none;
        border-radius: 0.5rem;
        padding: 0.5rem 2rem;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
    }
</style>
""", unsafe_allow_html=True)

# Data directory for persistence
DATA_DIR = "pl_data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# File paths
ITEM_MASTER_FILE = os.path.join(DATA_DIR, "item_master.json")
INVOICES_FILE = os.path.join(DATA_DIR, "invoices.json")
CUSTOMERS_FILE = os.path.join(DATA_DIR, "customers.json")
MARKETING_FILE = os.path.join(DATA_DIR, "marketing.json")
LOGISTICS_B2B_FILE = os.path.join(DATA_DIR, "logistics_b2b.json")
LOGISTICS_B2C_FILE = os.path.join(DATA_DIR, "logistics_b2c.json")
GRN_FILE = os.path.join(DATA_DIR, "grn.json")
BANK_STATEMENTS_FILE = os.path.join(DATA_DIR, "bank_statements.json")
TRANSACTION_MAPPING_FILE = os.path.join(DATA_DIR, "transaction_mapping.json")
INVOICE_HASHES_FILE = os.path.join(DATA_DIR, "invoice_hashes.json")

# Helper functions
def load_json(filepath, default=None):
    """Load JSON data from file"""
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    return default if default is not None else []

def save_json(filepath, data):
    """Save JSON data to file"""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)

def get_row_hash(row_data):
    """Generate unique hash for a row to detect duplicates"""
    row_str = json.dumps(row_data, sort_keys=True, default=str)
    return hashlib.md5(row_str.encode()).hexdigest()

def parse_pdf_to_text(pdf_file):
    """Extract text from PDF file"""
    if not PDF_SUPPORT:
        return None
    
    try:
        pdf_reader = PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {str(e)}")
        return None

def parse_logistics_pdf(pdf_text):
    """Parse logistics rules from PDF text"""
    rules = []
    
    # Try to extract zone-based pricing tables
    lines = pdf_text.split('\n')
    
    # Look for rate card patterns
    current_zone = None
    current_weight = None
    
    for line in lines:
        line = line.strip()
        
        # Detect zone headers (e.g., "Local", "Within State", "Metro to Metro")
        if any(zone in line for zone in ['Local', 'Within State', 'Metro to Metro', 'Rest of India', 'Special Zone']):
            current_zone = line.split()[0] if line.split() else None
        
        # Detect weight slabs
        weight_match = re.search(r'(\d+)\s*-?\s*(\d+)?\s*(gms|kg|g)', line, re.IGNORECASE)
        if weight_match:
            current_weight = line
        
        # Extract numeric rates
        numbers = re.findall(r'\d+\.?\d*', line)
        if numbers and current_zone:
            rules.append({
                'zone': current_zone,
                'weight_slab': current_weight if current_weight else 'Standard',
                'rates': numbers,
                'raw_line': line
            })
    
    return rules if rules else None

# Initialize session state
def init_session_state():
    if 'item_master' not in st.session_state:
        st.session_state.item_master = load_json(ITEM_MASTER_FILE, {})
    
    if 'invoices' not in st.session_state:
        st.session_state.invoices = load_json(INVOICES_FILE, [])
    
    if 'customers' not in st.session_state:
        st.session_state.customers = load_json(CUSTOMERS_FILE, {})
    
    if 'marketing' not in st.session_state:
        st.session_state.marketing = load_json(MARKETING_FILE, [])
    
    if 'logistics_b2b' not in st.session_state:
        st.session_state.logistics_b2b = load_json(LOGISTICS_B2B_FILE, {})
    
    if 'logistics_b2c' not in st.session_state:
        st.session_state.logistics_b2c = load_json(LOGISTICS_B2C_FILE, {})
    
    if 'grn' not in st.session_state:
        st.session_state.grn = load_json(GRN_FILE, {})
    
    if 'bank_statements' not in st.session_state:
        st.session_state.bank_statements = load_json(BANK_STATEMENTS_FILE, [])
    
    if 'transaction_mapping' not in st.session_state:
        st.session_state.transaction_mapping = load_json(TRANSACTION_MAPPING_FILE, {})
    
    if 'invoice_hashes' not in st.session_state:
        st.session_state.invoice_hashes = load_json(INVOICE_HASHES_FILE, [])
        if isinstance(st.session_state.invoice_hashes, list):
            st.session_state.invoice_hashes = set(st.session_state.invoice_hashes)

init_session_state()

def save_all_data():
    """Save all data to JSON files"""
    save_json(ITEM_MASTER_FILE, st.session_state.item_master)
    save_json(INVOICES_FILE, st.session_state.invoices)
    save_json(CUSTOMERS_FILE, st.session_state.customers)
    save_json(MARKETING_FILE, st.session_state.marketing)
    save_json(LOGISTICS_B2B_FILE, st.session_state.logistics_b2b)
    save_json(LOGISTICS_B2C_FILE, st.session_state.logistics_b2c)
    save_json(GRN_FILE, st.session_state.grn)
    save_json(BANK_STATEMENTS_FILE, st.session_state.bank_statements)
    save_json(TRANSACTION_MAPPING_FILE, st.session_state.transaction_mapping)
    save_json(INVOICE_HASHES_FILE, list(st.session_state.invoice_hashes))

# Sidebar navigation
st.sidebar.title("📊 Navigation")
page = st.sidebar.radio(
    "Go to",
    ["P&L Dashboard", "Item Master", "Upload Invoices", "Customers", 
     "Logistics Rules", "GRN Management", "Receivables", "Bank Reconciliation", "Marketing Spends"]
)

# ============================================================================
# PAGE: ITEM MASTER
# ============================================================================
if page == "Item Master":
    st.title("📦 Item Master Management")
    
    st.markdown("### Add New Product")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        new_sku = st.text_input("SKU", key="new_sku")
    with col2:
        new_name = st.text_input("Product Name", key="new_name")
    with col3:
        new_category = st.text_input("Category", key="new_category")
    with col4:
        new_cogs = st.number_input("COGS (₹)", min_value=0.0, step=0.01, key="new_cogs")
    
    if st.button("➕ Add Product"):
        if new_sku and new_name:
            st.session_state.item_master[new_sku] = {
                'sku': new_sku,
                'name': new_name,
                'category': new_category,
                'cogs': new_cogs
            }
            save_all_data()
            st.success(f"✅ Product '{new_name}' added successfully!")
            st.rerun()
        else:
            st.error("⚠️ SKU and Product Name are required!")
    
    st.markdown("### Current Products")
    if st.session_state.item_master:
        df = pd.DataFrame(list(st.session_state.item_master.values()))
        
        edited_df = st.data_editor(
            df,
            hide_index=True,
            use_container_width=True,
            column_config={
                "sku": st.column_config.TextColumn("SKU", disabled=True),
                "name": st.column_config.TextColumn("Product Name"),
                "category": st.column_config.TextColumn("Category"),
                "cogs": st.column_config.NumberColumn("COGS (₹)", format="₹%.2f")
            }
        )
        
        if st.button("💾 Save Changes"):
            st.session_state.item_master = {row['sku']: row for _, row in edited_df.iterrows()}
            save_all_data()
            st.success("✅ Changes saved successfully!")
        
        st.markdown("### Delete Product")
        sku_to_delete = st.selectbox("Select SKU to delete", options=list(st.session_state.item_master.keys()))
        if st.button("🗑️ Delete Selected Product"):
            del st.session_state.item_master[sku_to_delete]
            save_all_data()
            st.success(f"✅ Product with SKU '{sku_to_delete}' deleted!")
            st.rerun()
    else:
        st.info("ℹ️ No products added yet. Add your first product above!")

# ============================================================================
# PAGE: UPLOAD INVOICES
# ============================================================================
elif page == "Upload Invoices":
    st.title("📄 Upload Invoices")
    
    st.markdown("""
    <div class="info-box">
    <strong>ℹ️ Smart Upload Features:</strong>
    <ul>
        <li>Automatically extracts item names and customer names from invoice data</li>
        <li>Detects and skips duplicate invoices (even if uploaded multiple times)</li>
        <li>Auto-classifies customers as B2B or B2C</li>
        <li>Updates item master with new products found in invoices</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    uploaded_file = st.file_uploader("Upload Invoice CSV", type=['csv'])
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            
            st.markdown("### Preview of Uploaded Data")
            st.dataframe(df.head(10), use_container_width=True)
            
            if st.button("🚀 Process and Import Invoices"):
                new_count = 0
                duplicate_count = 0
                new_customers = set()
                new_items = set()
                
                for _, row in df.iterrows():
                    row_dict = row.to_dict()
                    row_hash = get_row_hash(row_dict)
                    
                    if row_hash in st.session_state.invoice_hashes:
                        duplicate_count += 1
                        continue
                    
                    invoice_data = {
                        'invoice_id': str(row.get('Invoice ID', row.get('Invoice Number', ''))),
                        'invoice_number': str(row.get('Invoice Number', '')),
                        'date': str(row.get('Invoice Date', '')),
                        'due_date': str(row.get('Due Date', '')),
                        'customer_name': str(row.get('Customer Name', '')),
                        'item_name': str(row.get('Item Name', '')),
                        'sku': str(row.get('SKU', '')),
                        'quantity': float(row.get('Quantity', 0)),
                        'item_price': float(row.get('Item Price', 0)),
                        'item_total': float(row.get('Item Total', 0)),
                        'total': float(row.get('Total', 0)),
                        'balance': float(row.get('Balance', 0)),
                        'status': str(row.get('Invoice Status', 'Draft')),
                        'grn_status': 'Pending',
                        'grn_date': None,
                        'hash': row_hash
                    }
                    
                    customer_name = invoice_data['customer_name']
                    if 'Amazon' in customer_name.upper():
                        channel = 'Amazon'
                        customer_type = 'B2C'
                    elif any(keyword in customer_name.upper() for keyword in ['PRIVATE LIMITED', 'PVT LTD', 'LIMITED', 'LLP']):
                        channel = 'B2B'
                        customer_type = 'B2B'
                    else:
                        channel = 'D2C'
                        customer_type = 'B2C'
                    
                    invoice_data['channel'] = channel
                    
                    st.session_state.invoices.append(invoice_data)
                    st.session_state.invoice_hashes.add(row_hash)
                    new_count += 1
                    
                    if customer_name and customer_name not in st.session_state.customers:
                        st.session_state.customers[customer_name] = {
                            'name': customer_name,
                            'type': customer_type,
                            'classification': 'auto'
                        }
                        new_customers.add(customer_name)
                    
                    sku = invoice_data['sku']
                    item_name = invoice_data['item_name']
                    if sku and sku not in st.session_state.item_master:
                        st.session_state.item_master[sku] = {
                            'sku': sku,
                            'name': item_name,
                            'category': '',
                            'cogs': 0.0
                        }
                        new_items.add(item_name)
                
                save_all_data()
                
                st.markdown("### Import Summary")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("✅ New Invoices", new_count)
                with col2:
                    st.metric("⏭️ Duplicates Skipped", duplicate_count)
                with col3:
                    st.metric("📊 Total Invoices", len(st.session_state.invoices))
                
                if new_customers:
                    st.markdown(f"""
                    <div class="success-box">
                    <strong>🆕 New Customers Added ({len(new_customers)}):</strong><br>
                    {', '.join(list(new_customers)[:5])}{'...' if len(new_customers) > 5 else ''}
                    </div>
                    """, unsafe_allow_html=True)
                
                if new_items:
                    st.markdown(f"""
                    <div class="warning-box">
                    <strong>⚠️ New Items Added ({len(new_items)}):</strong><br>
                    Please set COGS for these items in Item Master
                    </div>
                    """, unsafe_allow_html=True)
                
                st.success(f"✅ Import complete! {new_count} new invoices added, {duplicate_count} duplicates skipped.")
                
        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
    
    st.markdown("---")
    st.markdown("### Current Invoices")
    if st.session_state.invoices:
        df_invoices = pd.DataFrame(st.session_state.invoices)
        st.dataframe(
            df_invoices[['invoice_number', 'date', 'customer_name', 'item_name', 'quantity', 'item_total', 'channel', 'grn_status']].head(50),
            use_container_width=True
        )
        st.markdown(f"**Total Invoice Line Items:** {len(st.session_state.invoices)}")
    else:
        st.info("ℹ️ No invoices uploaded yet.")

# ============================================================================
# PAGE: CUSTOMERS
# ============================================================================
elif page == "Customers":
    st.title("👥 Customer Management")
    
    st.markdown("""
    <div class="info-box">
    Classify customers as B2B or B2C to apply appropriate shipping and logistics costs in P&L calculations.
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.customers:
        df = pd.DataFrame(list(st.session_state.customers.values()))
        
        edited_df = st.data_editor(
            df,
            hide_index=True,
            use_container_width=True,
            column_config={
                "name": st.column_config.TextColumn("Customer Name", disabled=True),
                "type": st.column_config.SelectboxColumn("Type", options=["B2B", "B2C"]),
                "classification": st.column_config.TextColumn("Classification Method", disabled=True)
            }
        )
        
        if st.button("💾 Save Customer Classifications"):
            for _, row in edited_df.iterrows():
                st.session_state.customers[row['name']] = {
                    'name': row['name'],
                    'type': row['type'],
                    'classification': 'manual'
                }
            save_all_data()
            st.success("✅ Customer classifications updated!")
        
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        b2b_count = sum(1 for c in st.session_state.customers.values() if c['type'] == 'B2B')
        b2c_count = sum(1 for c in st.session_state.customers.values() if c['type'] == 'B2C')
        
        with col1:
            st.metric("Total Customers", len(st.session_state.customers))
        with col2:
            st.metric("B2B Customers", b2b_count)
        with col3:
            st.metric("B2C Customers", b2c_count)
    else:
        st.info("ℹ️ No customers yet. Upload invoices to automatically populate customers.")

# ============================================================================
# PAGE: LOGISTICS RULES
# ============================================================================
elif page == "Logistics Rules":
    st.title("🚚 Logistics & Shipping Rules")
    
    st.markdown("""
    <div class="info-box">
    Upload separate rate cards for B2B and B2C shipments. Supports CSV, JSON, and PDF formats.
    The system will use these rules to calculate shipping costs.
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📦 B2B Shipping Rules", "🛒 B2C Shipping Rules"])
    
    with tab1:
        st.markdown("### Upload B2B Rate Card")
        uploaded_b2b = st.file_uploader("Upload B2B Rate Card (CSV/JSON/PDF)", 
                                        type=['csv', 'json', 'pdf'], key="b2b")
        
        if uploaded_b2b and st.button("Import B2B Rules"):
            try:
                if uploaded_b2b.name.endswith('.pdf'):
                    if not PDF_SUPPORT:
                        st.error("❌ PDF support not available. Please install PyPDF2: pip install PyPDF2")
                    else:
                        pdf_text = parse_pdf_to_text(uploaded_b2b)
                        if pdf_text:
                            # Store raw text for reference
                            st.session_state.logistics_b2b = {
                                'raw_text': pdf_text,
                                'uploaded_at': datetime.now().isoformat(),
                                'filename': uploaded_b2b.name,
                                'type': 'pdf'
                            }
                            
                            # Try to parse structured rules
                            parsed_rules = parse_logistics_pdf(pdf_text)
                            if parsed_rules:
                                st.session_state.logistics_b2b['rules'] = parsed_rules
                            
                            save_all_data()
                            st.success("✅ B2B PDF shipping rules imported!")
                            
                            # Show preview
                            with st.expander("📄 View Extracted Text"):
                                st.text_area("PDF Content", pdf_text[:2000], height=300)
                        else:
                            st.error("❌ Failed to extract text from PDF")
                
                elif uploaded_b2b.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_b2b)
                    rules = df.to_dict('records')
                    st.session_state.logistics_b2b = {
                        'rules': rules,
                        'uploaded_at': datetime.now().isoformat(),
                        'filename': uploaded_b2b.name,
                        'type': 'csv'
                    }
                    save_all_data()
                    st.success("✅ B2B CSV shipping rules imported!")
                
                else:  # JSON
                    rules = json.load(uploaded_b2b)
                    st.session_state.logistics_b2b = {
                        'rules': rules,
                        'uploaded_at': datetime.now().isoformat(),
                        'filename': uploaded_b2b.name,
                        'type': 'json'
                    }
                    save_all_data()
                    st.success("✅ B2B JSON shipping rules imported!")
                    
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
        
        # Display current rules
        if st.session_state.logistics_b2b:
            st.markdown("---")
            st.markdown("### Current B2B Rules")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info(f"📁 **File:** {st.session_state.logistics_b2b.get('filename', 'Unknown')}")
            with col2:
                st.info(f"📅 **Uploaded:** {st.session_state.logistics_b2b.get('uploaded_at', 'Unknown')[:10]}")
            with col3:
                st.info(f"📋 **Type:** {st.session_state.logistics_b2b.get('type', 'Unknown').upper()}")
            
            if st.session_state.logistics_b2b.get('type') == 'pdf':
                # Show PDF content
                with st.expander("📄 View PDF Content"):
                    st.text_area("Extracted Text", 
                                st.session_state.logistics_b2b.get('raw_text', '')[:3000], 
                                height=400, key="b2b_pdf_view")
                
                if 'rules' in st.session_state.logistics_b2b:
                    st.markdown("#### Parsed Rules")
                    df_rules = pd.DataFrame(st.session_state.logistics_b2b['rules'])
                    st.dataframe(df_rules.head(20), use_container_width=True)
            
            elif 'rules' in st.session_state.logistics_b2b:
                df_rules = pd.DataFrame(st.session_state.logistics_b2b['rules'])
                st.dataframe(df_rules.head(20), use_container_width=True)
                
                # Download button for rules
                csv = df_rules.to_csv(index=False)
                st.download_button(
                    label="📥 Download Rules as CSV",
                    data=csv,
                    file_name="b2b_logistics_rules.csv",
                    mime="text/csv"
                )
        else:
            st.warning("⚠️ No B2B shipping rules loaded yet.")
    
    with tab2:
        st.markdown("### Upload B2C Rate Card")
        uploaded_b2c = st.file_uploader("Upload B2C Rate Card (CSV/JSON/PDF)", 
                                        type=['csv', 'json', 'pdf'], key="b2c")
        
        if uploaded_b2c and st.button("Import B2C Rules"):
            try:
                if uploaded_b2c.name.endswith('.pdf'):
                    if not PDF_SUPPORT:
                        st.error("❌ PDF support not available. Please install PyPDF2: pip install PyPDF2")
                    else:
                        pdf_text = parse_pdf_to_text(uploaded_b2c)
                        if pdf_text:
                            st.session_state.logistics_b2c = {
                                'raw_text': pdf_text,
                                'uploaded_at': datetime.now().isoformat(),
                                'filename': uploaded_b2c.name,
                                'type': 'pdf'
                            }
                            
                            parsed_rules = parse_logistics_pdf(pdf_text)
                            if parsed_rules:
                                st.session_state.logistics_b2c['rules'] = parsed_rules
                            
                            save_all_data()
                            st.success("✅ B2C PDF shipping rules imported!")
                            
                            with st.expander("📄 View Extracted Text"):
                                st.text_area("PDF Content", pdf_text[:2000], height=300)
                        else:
                            st.error("❌ Failed to extract text from PDF")
                
                elif uploaded_b2c.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_b2c)
                    rules = df.to_dict('records')
                    st.session_state.logistics_b2c = {
                        'rules': rules,
                        'uploaded_at': datetime.now().isoformat(),
                        'filename': uploaded_b2c.name,
                        'type': 'csv'
                    }
                    save_all_data()
                    st.success("✅ B2C CSV shipping rules imported!")
                
                else:  # JSON
                    rules = json.load(uploaded_b2c)
                    st.session_state.logistics_b2c = {
                        'rules': rules,
                        'uploaded_at': datetime.now().isoformat(),
                        'filename': uploaded_b2c.name,
                        'type': 'json'
                    }
                    save_all_data()
                    st.success("✅ B2C JSON shipping rules imported!")
                    
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
        
        # Display current rules
        if st.session_state.logistics_b2c:
            st.markdown("---")
            st.markdown("### Current B2C Rules")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info(f"📁 **File:** {st.session_state.logistics_b2c.get('filename', 'Unknown')}")
            with col2:
                st.info(f"📅 **Uploaded:** {st.session_state.logistics_b2c.get('uploaded_at', 'Unknown')[:10]}")
            with col3:
                st.info(f"📋 **Type:** {st.session_state.logistics_b2c.get('type', 'Unknown').upper()}")
            
            if st.session_state.logistics_b2c.get('type') == 'pdf':
                with st.expander("📄 View PDF Content"):
                    st.text_area("Extracted Text", 
                                st.session_state.logistics_b2c.get('raw_text', '')[:3000], 
                                height=400, key="b2c_pdf_view")
                
                if 'rules' in st.session_state.logistics_b2c:
                    st.markdown("#### Parsed Rules")
                    df_rules = pd.DataFrame(st.session_state.logistics_b2c['rules'])
                    st.dataframe(df_rules.head(20), use_container_width=True)
            
            elif 'rules' in st.session_state.logistics_b2c:
                df_rules = pd.DataFrame(st.session_state.logistics_b2c['rules'])
                st.dataframe(df_rules.head(20), use_container_width=True)
                
                csv = df_rules.to_csv(index=False)
                st.download_button(
                    label="📥 Download Rules as CSV",
                    data=csv,
                    file_name="b2c_logistics_rules.csv",
                    mime="text/csv"
                )
        else:
            st.warning("⚠️ No B2C shipping rules loaded yet.")

# ============================================================================
# PAGE: GRN MANAGEMENT
# ============================================================================
elif page == "GRN Management":
    st.title("📋 GRN Management")
    
    grn_method = st.radio("Select GRN Method", ["Upload GRN Report", "Manual Bulk Update"])
    
    if grn_method == "Upload GRN Report":
        uploaded_grn = st.file_uploader("Upload GRN Report (CSV)", type=['csv'])
        
        if uploaded_grn and st.button("Process GRN Report"):
            df_grn = pd.read_csv(uploaded_grn)
            matched = 0
            for _, row in df_grn.iterrows():
                invoice_num = str(row.get('Invoice Number', ''))
                grn_date = str(row.get('GRN Date', ''))
                
                for inv in st.session_state.invoices:
                    if inv.get('invoice_number') == invoice_num:
                        inv['grn_status'] = 'Completed'
                        inv['grn_date'] = grn_date
                        matched += 1
            
            save_all_data()
            st.success(f"✅ {matched} invoices updated!")
    
    else:
        pending_invoices = [inv for inv in st.session_state.invoices if inv.get('grn_status') == 'Pending']
        
        if pending_invoices:
            selected_indices = st.multiselect(
                "Select invoices to mark as GRN",
                options=range(len(pending_invoices)),
                format_func=lambda x: f"{pending_invoices[x]['invoice_number']} - ₹{pending_invoices[x]['total']:.2f}"
            )
            
            grn_date = st.date_input("GRN Date", datetime.now())
            
            if st.button("✅ Mark Selected as GRN"):
                for idx in selected_indices:
                    inv = pending_invoices[idx]
                    for i, invoice in enumerate(st.session_state.invoices):
                        if invoice.get('invoice_number') == inv['invoice_number']:
                            st.session_state.invoices[i]['grn_status'] = 'Completed'
                            st.session_state.invoices[i]['grn_date'] = str(grn_date)
                
                save_all_data()
                st.success(f"✅ Marked {len(selected_indices)} invoices as GRN!")
                st.rerun()
        else:
            st.success("✅ All invoices marked as GRN!")
    
    total = len(st.session_state.invoices)
    completed = sum(1 for inv in st.session_state.invoices if inv.get('grn_status') == 'Completed')
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Invoices", total)
    with col2:
        st.metric("GRN Completed", completed)
    with col3:
        st.metric("GRN Pending", total - completed)

# ============================================================================
# PAGE: BANK RECONCILIATION
# ============================================================================
elif page == "Bank Reconciliation":
    st.title("🏦 Bank Reconciliation")
    
    st.markdown("""
    <div class="info-box">
    Upload bank statements and map transactions to customers. Once mapped, only new transactions need mapping.
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_bank = st.file_uploader("Upload Bank Statement (CSV)", type=['csv'])
    
    if uploaded_bank and st.button("🚀 Import Bank Statement"):
        try:
            df_bank = pd.read_csv(uploaded_bank)
            df_bank.columns = df_bank.columns.str.strip()
            
            new_count = 0
            duplicate_count = 0
            existing_hashes = set(t.get('hash') for t in st.session_state.bank_statements)
            
            for _, row in df_bank.iterrows():
                if pd.isna(row.get('Transaction Date')):
                    continue
                
                trans_dict = {
                    'date': str(row.get('Transaction Date', '')),
                    'description': str(row.get('Description', '')),
                    'amount': str(row.get('Amount', ''))
                }
                trans_hash = get_row_hash(trans_dict)
                
                if trans_hash in existing_hashes:
                    duplicate_count += 1
                    continue
                
                transaction = {
                    'date': str(row.get('Transaction Date', '')),
                    'description': str(row.get('Description', '')),
                    'reference': str(row.get('Chq / Ref No.', '')),
                    'amount': float(str(row.get('Amount', '0')).replace(',', '')),
                    'type': str(row.get('Dr / Cr', '')),
                    'hash': trans_hash,
                    'customer': None,
                    'mapped': False
                }
                
                st.session_state.bank_statements.append(transaction)
                new_count += 1
            
            save_all_data()
            st.success(f"✅ {new_count} new transactions, {duplicate_count} duplicates skipped!")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
    
    unmapped = [t for t in st.session_state.bank_statements if not t.get('mapped', False)]
    
    if unmapped:
        st.warning(f"⚠️ {len(unmapped)} transactions need mapping")
        customer_list = ['[Skip]'] + list(st.session_state.customers.keys())
        
        for i, trans in enumerate(unmapped[:10]):
            with st.expander(f"₹{trans['amount']:,.2f} - {trans['description'][:50]}"):
                selected = st.selectbox("Map to Customer", customer_list, key=f"map_{i}")
                
                if st.button("Save", key=f"save_{i}"):
                    for t in st.session_state.bank_statements:
                        if t['hash'] == trans['hash']:
                            t['customer'] = None if selected == '[Skip]' else selected
                            t['mapped'] = True
                            break
                    save_all_data()
                    st.success("✅ Mapped!")
                    st.rerun()
    else:
        st.success("✅ All transactions mapped!")
    
    if st.session_state.bank_statements:
        df = pd.DataFrame(st.session_state.bank_statements)
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Transactions", len(df))
        with col2:
            st.metric("Mapped", len(df[df['mapped'] == True]))
        with col3:
            st.metric("Credits", f"₹{df[df['type']=='CR']['amount'].sum():,.2f}")
        with col4:
            st.metric("Debits", f"₹{df[df['type']=='DR']['amount'].sum():,.2f}")

# ============================================================================
# PAGE: RECEIVABLES
# ============================================================================
elif page == "Receivables":
    st.title("💰 Receivables Dashboard")
    
    receivables = {}
    for inv in st.session_state.invoices:
        if inv.get('balance', 0) > 0:
            customer = inv['customer_name']
            if customer not in receivables:
                receivables[customer] = {'customer': customer, 'total_due': 0, 'invoices': []}
            
            try:
                due_date = datetime.strptime(inv['due_date'], '%Y-%m-%d')
                days_overdue = (datetime.now() - due_date).days
            except:
                days_overdue = 0
            
            receivables[customer]['total_due'] += inv['balance']
            receivables[customer]['invoices'].append({**inv, 'days_overdue': days_overdue})
    
    total_receivables = sum(r['total_due'] for r in receivables.values())
    overdue_customers = sum(1 for r in receivables.values() if any(i['days_overdue'] > 0 for i in r['invoices']))
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("💵 Total Receivables", f"₹{total_receivables:,.2f}")
    with col2:
        st.metric("⚠️ Overdue Customers", overdue_customers)
    with col3:
        st.metric("👥 Customers", len(receivables))
    
    if receivables:
        receivables_list = []
        for customer, data in receivables.items():
            max_overdue = max([inv['days_overdue'] for inv in data['invoices']], default=0)
            receivables_list.append({
                'Customer': customer,
                'Total Due': data['total_due'],
                'Invoices': len(data['invoices']),
                'Max Overdue': max_overdue,
                'Status': 'Current' if max_overdue == 0 else f'{max_overdue} days'
            })
        
        df = pd.DataFrame(receivables_list).sort_values('Total Due', ascending=False)
        st.dataframe(df, use_container_width=True, column_config={
            "Total Due": st.column_config.NumberColumn("Total Due", format="₹%.2f")
        })

# ============================================================================
# PAGE: MARKETING SPENDS
# ============================================================================
elif page == "Marketing Spends":
    st.title("📱 Marketing Spends")
    
    uploaded_marketing = st.file_uploader("Upload Marketing CSV", type=['csv'])
    
    if uploaded_marketing and st.button("Import Marketing Data"):
        df = pd.read_csv(uploaded_marketing)
        for _, row in df.iterrows():
            st.session_state.marketing.append({
                'date': str(row.get('Date', '')),
                'channel': str(row.get('Channel', '')),
                'product': str(row.get('Product', '')),
                'campaign': str(row.get('Campaign', '')),
                'spend': float(row.get('Marketing Spend (₹)', 0)),
                'revenue': float(row.get('Ad Revenue (₹)', 0)),
                'roas': float(row.get('ROAS', 0))
            })
        save_all_data()
        st.success("✅ Marketing data imported!")
        st.rerun()
    
    if st.session_state.marketing:
        df = pd.DataFrame(st.session_state.marketing)
        total_spend = df['spend'].sum()
        total_revenue = df['revenue'].sum()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("💸 Total Spend", f"₹{total_spend:,.2f}")
        with col2:
            st.metric("💰 Total Revenue", f"₹{total_revenue:,.2f}")
        with col3:
            st.metric("📊 Avg ROAS", f"{(total_revenue/total_spend):.2f}x" if total_spend > 0 else "0.00x")
        
        st.dataframe(df, use_container_width=True)

# ============================================================================
# PAGE: P&L DASHBOARD
# ============================================================================
elif page == "P&L Dashboard":
    st.title("📊 Profit & Loss Dashboard")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        channels = ['All'] + list(set(inv.get('channel', 'Unknown') for inv in st.session_state.invoices))
        selected_channel = st.selectbox("Channel", channels)
    
    with col2:
        products = ['All'] + list(set(inv.get('item_name', 'Unknown') for inv in st.session_state.invoices))
        selected_product = st.selectbox("Product", products[:20])
    
    with col3:
        date_from = st.date_input("From Date", datetime.now() - timedelta(days=30))
    
    with col4:
        date_to = st.date_input("To Date", datetime.now())
    
    filtered = st.session_state.invoices
    
    if selected_channel != 'All':
        filtered = [inv for inv in filtered if inv.get('channel') == selected_channel]
    if selected_product != 'All':
        filtered = [inv for inv in filtered if inv.get('item_name') == selected_product]
    
    filtered = [inv for inv in filtered 
                if date_from <= datetime.strptime(inv['date'], '%Y-%m-%d').date() <= date_to]
    
    if filtered:
        sales = sum(inv.get('item_total', 0) for inv in filtered)
        
        cogs = 0
        for inv in filtered:
            sku = inv.get('sku', '')
            qty = inv.get('quantity', 0)
            if sku in st.session_state.item_master:
                cogs += st.session_state.item_master[sku].get('cogs', 0) * qty
        
        shipping = 0
        for inv in filtered:
            customer = inv.get('customer_name', '')
            qty = inv.get('quantity', 0)
            cust_type = st.session_state.customers.get(customer, {}).get('type', 'B2C')
            shipping += qty * (30 if cust_type == 'B2B' else 45)
        
        marketing_spend = 0
        for spend in st.session_state.marketing:
            spend_date = datetime.strptime(spend['date'].split('T')[0], '%Y-%m-%d').date()
            if date_from <= spend_date <= date_to:
                if selected_channel == 'All' or spend.get('channel', '') == selected_channel:
                    marketing_spend += spend.get('spend', 0)
        
        brand_marketing = marketing_spend * 0.1
        
        gross_margin = sales - cogs
        gross_margin_pct = (gross_margin / sales * 100) if sales > 0 else 0
        
        cm1 = gross_margin - shipping
        cm1_pct = (cm1 / sales * 100) if sales > 0 else 0
        
        cm2 = cm1 - marketing_spend
        cm2_pct = (cm2 / sales * 100) if sales > 0 else 0
        
        cm3 = cm2 - brand_marketing
        cm3_pct = (cm3 / sales * 100) if sales > 0 else 0
        
        st.markdown("---")
        st.markdown("## 📈 P&L Statement")
        
        pl_data = [
            {'Line Item': 'Sales', 'Amount': sales, 'Percentage': 100.0},
            {'Line Item': 'Cost of Goods Sold', 'Amount': -cogs, 'Percentage': (cogs/sales*100) if sales > 0 else 0},
            {'Line Item': 'Gross Margin', 'Amount': gross_margin, 'Percentage': gross_margin_pct},
            {'Line Item': 'Shipping & Warehousing', 'Amount': -shipping, 'Percentage': (shipping/sales*100) if sales > 0 else 0},
            {'Line Item': 'Contribution Margin 1', 'Amount': cm1, 'Percentage': cm1_pct},
            {'Line Item': 'Performance Marketing', 'Amount': -marketing_spend, 'Percentage': (marketing_spend/sales*100) if sales > 0 else 0},
            {'Line Item': 'Contribution Margin 2', 'Amount': cm2, 'Percentage': cm2_pct},
            {'Line Item': 'Brand Marketing', 'Amount': -brand_marketing, 'Percentage': (brand_marketing/sales*100) if sales > 0 else 0},
            {'Line Item': 'Contribution Margin 3', 'Amount': cm3, 'Percentage': cm3_pct}
        ]
        
        df_pl = pd.DataFrame(pl_data)
        st.dataframe(df_pl, use_container_width=True, column_config={
            "Amount": st.column_config.NumberColumn("Amount (₹)", format="₹%.2f"),
            "Percentage": st.column_config.NumberColumn("% of Sales", format="%.2f%%")
        }, hide_index=True)
        
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("💰 Sales", f"₹{sales:,.2f}")
        with col2:
            st.metric("📊 Gross Margin %", f"{gross_margin_pct:.1f}%")
        with col3:
            st.metric("🎯 CM1 %", f"{cm1_pct:.1f}%")
        with col4:
            st.metric("✨ CM3 %", f"{cm3_pct:.1f}%")
        
        fig = go.Figure(go.Waterfall(
            x = ['Sales', 'COGS', 'Gross Margin', 'Shipping', 'CM1', 'Perf Mktg', 'CM2', 'Brand Mktg', 'CM3'],
            y = [sales, -cogs, 0, -shipping, 0, -marketing_spend, 0, -brand_marketing, 0],
            measure = ['absolute', 'relative', 'total', 'relative', 'total', 'relative', 'total', 'relative', 'total'],
            decreasing = {"marker":{"color":"#ef4444"}},
            increasing = {"marker":{"color":"#10b981"}},
            totals = {"marker":{"color":"#facc15"}}
        ))
        fig.update_layout(title="P&L Waterfall Analysis", template="plotly_dark", height=500)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("⚠️ No data for selected filters.")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #64748b;'><strong>P&L Management System</strong> | Built with Streamlit</div>", unsafe_allow_html=True)
