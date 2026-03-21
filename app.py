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

# Custom CSS
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
SHIPPING_CALCULATIONS_FILE = os.path.join(DATA_DIR, "shipping_calculations.json")

# Helper functions
def load_json(filepath, default=None):
    """Load JSON data from file"""
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except:
            return default if default is not None else []
    return default if default is not None else []

def save_json(filepath, data):
    """Save JSON data to file"""
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        return True
    except Exception as e:
        st.error(f"Error saving data: {str(e)}")
        return False

def get_row_hash(row_data):
    """Generate unique hash for a row"""
    row_str = json.dumps(row_data, sort_keys=True, default=str)
    return hashlib.md5(row_str.encode()).hexdigest()

def parse_pdf_to_text(pdf_file):
    """Extract text from PDF"""
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

# Rate calculation functions (from uploaded code)
def determine_zone(origin_city, dest_city, dest_state, origin_state="MAHARASHTRA"):
    """Determine shipping zone"""
    origin_city = str(origin_city).strip().title() if pd.notna(origin_city) else ""
    dest_city = str(dest_city).strip().title() if pd.notna(dest_city) else ""
    dest_state = str(dest_state).strip().upper() if pd.notna(dest_state) else ""
    origin_state = str(origin_state).strip().upper()
    
    state_mapping = {
        'MH': 'MAHARASHTRA', 'MAHARASHTRA': 'MAHARASHTRA',
        'DL': 'DELHI', 'DELHI': 'DELHI',
        'KA': 'KARNATAKA', 'KARNATAKA': 'KARNATAKA',
        'TN': 'TAMIL NADU', 'TAMILNADU': 'TAMIL NADU',
        'WB': 'WEST BENGAL',
        'KL': 'KERALA', 'KERALA': 'KERALA',
        'HP': 'HIMACHAL PRADESH',
        'J&K': 'JAMMU AND KASHMIR',
    }
    
    for code, full_name in state_mapping.items():
        if code in origin_state:
            origin_state = full_name
            break
    for code, full_name in state_mapping.items():
        if code in dest_state:
            dest_state = full_name
            break
    
    # Special zones
    special_zones = ['JAMMU AND KASHMIR', 'HIMACHAL PRADESH', 'KERALA',
                     'ARUNACHAL PRADESH', 'ASSAM', 'MANIPUR', 'MEGHALAYA',
                     'MIZORAM', 'NAGALAND', 'TRIPURA', 'SIKKIM']
    
    for sz in special_zones:
        if sz in dest_state:
            return 'Special Zone'
    
    # Local city groups
    local_groups = {
        'MUMBAI': ['MUMBAI', 'NAVI MUMBAI', 'THANE'],
        'DELHI': ['DELHI', 'NEW DELHI', 'GURGAON', 'NOIDA'],
        'BANGALORE': ['BANGALORE', 'BENGALURU'],
        'CHENNAI': ['CHENNAI'],
        'KOLKATA': ['KOLKATA']
    }
    
    for metro, cities in local_groups.items():
        origin_in = any(c in origin_city.upper() for c in cities)
        dest_in = any(c in dest_city.upper() for c in cities)
        if origin_in and dest_in:
            return 'Local'
    
    # Metro to Metro
    metros = ['MUMBAI', 'DELHI', 'BANGALORE', 'CHENNAI', 'KOLKATA']
    origin_metro = any(m in origin_city.upper() for m in metros)
    dest_metro = any(m in dest_city.upper() for m in metros)
    
    if origin_metro and dest_metro:
        return 'Metro to Metro'
    
    # Within state
    if origin_state == dest_state:
        return 'Within State'
    
    return 'Rest of India'

def calculate_freight_cost(weight_kg, zone, courier_name, rate_card):
    """Calculate shipping cost based on weight and zone"""
    if courier_name not in rate_card:
        return 0
    
    if zone not in rate_card[courier_name]:
        return 0
    
    rates = rate_card[courier_name][zone]
    weight_grams = weight_kg * 1000
    
    # Air courier (simpler)
    if 'Air' in courier_name:
        if weight_grams <= 500:
            return rates.get('0-500', 0)
        else:
            additional_slabs = int((weight_grams - 500) / 500) + (1 if (weight_grams - 500) % 500 > 0 else 0)
            return rates.get('0-500', 0) + (additional_slabs * rates.get('add_500', 0))
    
    # Surface courier
    if weight_kg <= 0.5:
        return rates.get('0-500', 0)
    elif weight_kg <= 2.0:
        additional_slabs = int((weight_grams - 500) / 500) + (1 if (weight_grams - 500) % 500 > 0 else 0)
        return rates.get('0-500', 0) + (additional_slabs * rates.get('add_500', 0))
    elif weight_kg <= 5.0:
        additional_kg = int(weight_kg - 2.0) + (1 if (weight_kg - 2.0) % 1 > 0 else 0)
        return rates.get('2kg', 0) + (additional_kg * rates.get('add_1kg_2-5', 0))
    elif weight_kg <= 10.0:
        additional_kg = int(weight_kg - 5.0) + (1 if (weight_kg - 5.0) % 1 > 0 else 0)
        return rates.get('5kg', 0) + (additional_kg * rates.get('add_1kg_5-10', 0))
    else:
        additional_kg = int(weight_kg - 10.0) + (1 if (weight_kg - 10.0) % 1 > 0 else 0)
        return rates.get('10kg', 0) + (additional_kg * rates.get('add_1kg_10+', 0))

# Initialize session state with persistence
def init_session_state():
    # Load all data from files
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
        hashes = load_json(INVOICE_HASHES_FILE, [])
        st.session_state.invoice_hashes = set(hashes) if isinstance(hashes, list) else set()
    
    if 'shipping_calculations' not in st.session_state:
        st.session_state.shipping_calculations = load_json(SHIPPING_CALCULATIONS_FILE, {})

init_session_state()

def save_all_data():
    """Save all session data to files"""
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
    save_json(SHIPPING_CALCULATIONS_FILE, st.session_state.shipping_calculations)

# Sidebar navigation
st.sidebar.title("📊 Navigation")
page = st.sidebar.radio(
    "Go to",
    ["P&L Dashboard", "Item Master", "Upload Invoices", "Customers", 
     "Logistics Rules", "Shipping Calculator", "GRN Management", "Receivables", "Bank Reconciliation", "Marketing Spends"]
)

# ============================================================================
# PAGE: ITEM MASTER (FIXED - Now fully editable)
# ============================================================================
# ============================================================================
# PAGE: ITEM MASTER (REDESIGNED - B2C & B2B SUPPORT)
# ============================================================================
if page == "Item Master":
    st.title("📦 Item Master Management")
    
    st.markdown("""
    <div class="info-box">
    <strong>Manage products with COGS and shipping configuration</strong><br>
    • <strong>B2C Items</strong>: Unit-based (dead weight, volumetric weight per unit)<br>
    • <strong>B2B Items</strong>: Case-based (units per case, weight per case)
    </div>
    """, unsafe_allow_html=True)
    
    # Toggle between B2C and B2B entry
    st.markdown("### Add New Product")
    config_mode = st.radio("Product Type", ["B2C (Unit Weight)", "B2B (Case Pack)"], horizontal=True)
    
    if config_mode == "B2C (Unit Weight)":
        st.markdown("#### Add B2C Item (Sold by Units)")
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        with col1:
            new_sku = st.text_input("SKU", key="new_sku_b2c")
        with col2:
            new_name = st.text_input("Product Name", key="new_name_b2c")
        with col3:
            new_category = st.text_input("Category", key="new_category_b2c")
        with col4:
            new_cogs = st.number_input("COGS (₹)", min_value=0.0, step=0.01, key="new_cogs_b2c")
        with col5:
            new_dead_weight = st.number_input("Dead Weight (kg/unit)", min_value=0.0, step=0.001, value=0.5, format="%.3f", key="new_dead_b2c")
        with col6:
            new_vol_weight = st.number_input("Vol Weight (kg/unit)", min_value=0.0, step=0.001, value=0.5, format="%.3f", key="new_vol_b2c")
        
        if st.button("➕ Add B2C Product"):
            if new_sku and new_name:
                st.session_state.item_master[new_sku] = {
                    'sku': new_sku,
                    'name': new_name,
                    'category': new_category,
                    'cogs': new_cogs,
                    'item_type': 'B2C',
                    'dead_weight': new_dead_weight,
                    'volumetric_weight': new_vol_weight
                }
                save_all_data()
                st.success(f"✅ B2C Product '{new_name}' added!")
                st.rerun()
            else:
                st.error("⚠️ SKU and Product Name required!")
    
    else:  # B2B Case Pack
        st.markdown("#### Add B2B Item (Sold by Cases)")
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        with col1:
            new_sku = st.text_input("SKU", key="new_sku_b2b")
        with col2:
            new_name = st.text_input("Product Name", key="new_name_b2b")
        with col3:
            new_category = st.text_input("Category", key="new_category_b2b")
        with col4:
            new_cogs = st.number_input("COGS (₹)", min_value=0.0, step=0.01, key="new_cogs_b2b")
        with col5:
            new_case_qty = st.number_input("Units per Case", min_value=1, step=1, value=75, key="new_case_qty")
        with col6:
            new_case_weight = st.number_input("Weight per Case (kg)", min_value=0.0, step=0.1, value=15.0, format="%.2f", key="new_case_weight")
        
        st.info(f"📦 Each case contains {new_case_qty} units and weighs {new_case_weight} kg")
        
        if st.button("➕ Add B2B Product"):
            if new_sku and new_name:
                st.session_state.item_master[new_sku] = {
                    'sku': new_sku,
                    'name': new_name,
                    'category': new_category,
                    'cogs': new_cogs,
                    'item_type': 'B2B',
                    'case_pack_qty': new_case_qty,
                    'case_weight': new_case_weight
                }
                save_all_data()
                st.success(f"✅ B2B Product '{new_name}' added!")
                st.rerun()
            else:
                st.error("⚠️ SKU and Product Name required!")
    
    st.markdown("---")
    st.markdown("### Current Products")
    
    # Filter by type
    filter_type = st.selectbox("Filter by Type", ["All", "B2C Only", "B2B Only"])
    
    if st.session_state.item_master:
        items_list = list(st.session_state.item_master.values())
        df = pd.DataFrame(items_list)
        
        # Ensure item_type exists (for backward compatibility)
        if 'item_type' not in df.columns:
            df['item_type'] = 'B2C'
        
        # Apply filter
        if filter_type == "B2C Only":
            df = df[df['item_type'] == 'B2C']
        elif filter_type == "B2B Only":
            df = df[df['item_type'] == 'B2B']
        
        # Display B2C items
        b2c_items = df[df['item_type'] == 'B2C'].copy()
        if len(b2c_items) > 0 and filter_type in ["All", "B2C Only"]:
            st.markdown("#### B2C Items (Unit Weight)")
            
            # Ensure columns exist
            for col in ['dead_weight', 'volumetric_weight']:
                if col not in b2c_items.columns:
                    b2c_items[col] = 0.5
            
            display_cols = ['sku', 'name', 'category', 'cogs', 'dead_weight', 'volumetric_weight']
            edited_b2c = st.data_editor(
                b2c_items[display_cols],
                hide_index=True,
                use_container_width=True,
                num_rows="dynamic",
                column_config={
                    "sku": st.column_config.TextColumn("SKU", required=True),
                    "name": st.column_config.TextColumn("Product Name", required=True),
                    "category": st.column_config.TextColumn("Category"),
                    "cogs": st.column_config.NumberColumn("COGS (₹)", format="₹%.2f", min_value=0.0),
                    "dead_weight": st.column_config.NumberColumn("Dead Weight (kg)", format="%.3f", min_value=0.0),
                    "volumetric_weight": st.column_config.NumberColumn("Vol Weight (kg)", format="%.3f", min_value=0.0)
                },
                key="b2c_editor"
            )
            
            if st.button("💾 Save B2C Changes", type="primary"):
                for _, row in edited_b2c.iterrows():
                    if row['sku']:
                        st.session_state.item_master[row['sku']] = {
                            'sku': row['sku'],
                            'name': row['name'],
                            'category': row['category'],
                            'cogs': float(row['cogs']),
                            'item_type': 'B2C',
                            'dead_weight': float(row['dead_weight']),
                            'volumetric_weight': float(row['volumetric_weight'])
                        }
                save_all_data()
                st.success("✅ B2C items saved!")
                st.rerun()
        
        # Display B2B items
        b2b_items = df[df['item_type'] == 'B2B'].copy()
        if len(b2b_items) > 0 and filter_type in ["All", "B2B Only"]:
            st.markdown("#### B2B Items (Case Pack)")
            
            # Ensure columns exist
            for col in ['case_pack_qty', 'case_weight']:
                if col not in b2b_items.columns:
                    if col == 'case_pack_qty':
                        b2b_items[col] = 75
                    else:
                        b2b_items[col] = 15.0
            
            display_cols = ['sku', 'name', 'category', 'cogs', 'case_pack_qty', 'case_weight']
            edited_b2b = st.data_editor(
                b2b_items[display_cols],
                hide_index=True,
                use_container_width=True,
                num_rows="dynamic",
                column_config={
                    "sku": st.column_config.TextColumn("SKU", required=True),
                    "name": st.column_config.TextColumn("Product Name", required=True),
                    "category": st.column_config.TextColumn("Category"),
                    "cogs": st.column_config.NumberColumn("COGS (₹)", format="₹%.2f", min_value=0.0),
                    "case_pack_qty": st.column_config.NumberColumn("Units/Case", min_value=1, step=1),
                    "case_weight": st.column_config.NumberColumn("Weight/Case (kg)", format="%.2f", min_value=0.0)
                },
                key="b2b_editor"
            )
            
            if st.button("💾 Save B2B Changes", type="primary", key="save_b2b"):
                for _, row in edited_b2b.iterrows():
                    if row['sku']:
                        st.session_state.item_master[row['sku']] = {
                            'sku': row['sku'],
                            'name': row['name'],
                            'category': row['category'],
                            'cogs': float(row['cogs']),
                            'item_type': 'B2B',
                            'case_pack_qty': int(row['case_pack_qty']),
                            'case_weight': float(row['case_weight'])
                        }
                save_all_data()
                st.success("✅ B2B items saved!")
                st.rerun()
        
        # Summary metrics
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        b2c_count = len(df[df['item_type'] == 'B2C'])
        b2b_count = len(df[df['item_type'] == 'B2B'])
        
        with col1:
            st.metric("Total Products", len(df))
        with col2:
            st.metric("B2C Products", b2c_count)
        with col3:
            st.metric("B2B Products", b2b_count)
    
    else:
        st.info("ℹ️ No products yet. Add your first product above!")


elif page == "Upload Invoices":
    st.title("📄 Upload Invoices")
    
    st.markdown("""
    <div class="info-box">
    <strong>ℹ️ Smart Upload Features:</strong>
    <ul>
        <li>Automatically extracts item names and customer names</li>
        <li>Detects and skips duplicates</li>
        <li>Auto-classifies customers as B2B or B2C</li>
        <li>Updates item master with new products</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Upload Invoice CSV", type=['csv'])
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            st.markdown("### Preview")
            st.dataframe(df.head(10), use_container_width=True)
            
            if st.button("🚀 Process and Import"):
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
                        'hash': row_hash,
                        'dest_city': str(row.get('Place of Supply(With State Code)', '').split('-')[-1] if '-' in str(row.get('Place of Supply(With State Code)', '')) else ''),
                        'dest_state': str(row.get('Place of Supply(With State Code)', '').split('-')[-1] if '-' in str(row.get('Place of Supply(With State Code)', '')) else '')
                    }
                    
                    customer_name = invoice_data['customer_name']
                    if 'Amazon' in customer_name.upper():
                        channel = 'Amazon'
                        customer_type = 'B2C'
                    elif any(k in customer_name.upper() for k in ['PRIVATE LIMITED', 'PVT LTD', 'LIMITED', 'LLP']):
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
                            'classification': 'auto',
                            'channel': channel,
                            'credit_days': 30  # Default credit days
                        }
                        new_customers.add(customer_name)
                    
                    sku = invoice_data['sku']
                    item_name = invoice_data['item_name']
                    if sku and sku not in st.session_state.item_master:
                        st.session_state.item_master[sku] = {
                            'sku': sku,
                            'name': item_name,
                            'category': '',
                            'cogs': 0.0,
                            'item_type': 'B2C',
                            'dead_weight': 0.5,
                            'volumetric_weight': 0.5
                        }
                        new_items.add(item_name)
                
                save_all_data()
                
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
                    <strong>🆕 New Customers Added ({len(new_customers)})</strong>
                    </div>
                    """, unsafe_allow_html=True)
                
                if new_items:
                    st.markdown(f"""
                    <div class="warning-box">
                    <strong>⚠️ New Items Added ({len(new_items)}) - Please set COGS in Item Master</strong>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.success(f"✅ Import complete!")
                
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
    
    st.markdown("---")
    st.markdown("### Current Invoices")
    if st.session_state.invoices:
        df_inv = pd.DataFrame(st.session_state.invoices)
        st.dataframe(df_inv[['invoice_number', 'date', 'customer_name', 'item_name', 'quantity', 'item_total', 'channel']].head(50))
        st.markdown(f"**Total: {len(st.session_state.invoices)} invoice line items**")

# ============================================================================
# PAGE: CUSTOMERS (FIXED - Now fully editable with channel linking)
# ============================================================================
elif page == "Customers":
    st.title("👥 Customer Management")
    
    st.markdown("""
    <div class="info-box">
    Manage customer classifications, credit terms, and channel linking
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.customers:
        # Convert to DataFrame
        customers_list = []
        for name, data in st.session_state.customers.items():
            customers_list.append({
                'name': name,
                'type': data.get('type', 'B2C'),
                'channel': data.get('channel', ''),
                'credit_days': data.get('credit_days', 30),
                'is_marketplace': data.get('is_marketplace', False),
                'classification': data.get('classification', 'auto')
            })
        
        df = pd.DataFrame(customers_list)
        
        st.markdown("### Customer List (Fully Editable)")
        
        # Editable table
        edited_df = st.data_editor(
            df,
            hide_index=True,
            use_container_width=True,
            column_config={
                "name": st.column_config.TextColumn("Customer Name", disabled=True),
                "type": st.column_config.SelectboxColumn("Type", options=["B2B", "B2C"], required=True),
                "channel": st.column_config.TextColumn("Channel"),
                "credit_days": st.column_config.NumberColumn("Credit Days", min_value=0, max_value=365, step=1),
                "is_marketplace": st.column_config.CheckboxColumn("Is Marketplace (Own Pickup)"),
                "classification": st.column_config.TextColumn("Classification", disabled=True)
            },
            key="customers_editor"
        )
        
        if st.button("💾 Save Customer Changes", type="primary"):
            # Update customers with edited values
            new_customers = {}
            for _, row in edited_df.iterrows():
                new_customers[row['name']] = {
                    'name': row['name'],
                    'type': row['type'],
                    'channel': row['channel'],
                    'credit_days': int(row['credit_days']),
                    'is_marketplace': bool(row['is_marketplace']),
                    'classification': 'manual'
                }
            st.session_state.customers = new_customers
            save_all_data()
            st.success("✅ Customer data updated!")
            st.rerun()
        
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        b2b_count = sum(1 for c in st.session_state.customers.values() if c.get('type') == 'B2B')
        b2c_count = sum(1 for c in st.session_state.customers.values() if c.get('type') == 'B2C')
        marketplace_count = sum(1 for c in st.session_state.customers.values() if c.get('is_marketplace') == True)
        
        with col1:
            st.metric("Total Customers", len(st.session_state.customers))
        with col2:
            st.metric("B2B Customers", b2b_count)
        with col3:
            st.metric("B2C Customers", b2c_count)
        with col4:
            st.metric("Marketplaces (Own Pickup)", marketplace_count)
    else:
        st.info("ℹ️ No customers yet. Upload invoices to populate.")

# ============================================================================
# PAGE: LOGISTICS RULES (With PDF support)
# ============================================================================
elif page == "Logistics Rules":
    st.title("🚚 Logistics & Shipping Rules")
    
    st.markdown("""
    <div class="info-box">
    Upload rate cards in CSV, JSON, or PDF format. The system will use zone-based pricing for shipping calculations.
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📦 B2B Shipping", "🛒 B2C Shipping"])
    
    with tab1:
        st.markdown("### Upload B2B Rate Card")
        uploaded_b2b = st.file_uploader("Upload (CSV/JSON/PDF)", type=['csv', 'json', 'pdf'], key="b2b")
        
        if uploaded_b2b and st.button("Import B2B Rules"):
            try:
                if uploaded_b2b.name.endswith('.pdf'):
                    if PDF_SUPPORT:
                        pdf_text = parse_pdf_to_text(uploaded_b2b)
                        if pdf_text:
                            st.session_state.logistics_b2b = {
                                'raw_text': pdf_text,
                                'uploaded_at': datetime.now().isoformat(),
                                'filename': uploaded_b2b.name,
                                'type': 'pdf'
                            }
                            save_all_data()
                            st.success("✅ B2B PDF imported!")
                    else:
                        st.error("❌ PDF support not available")
                
                elif uploaded_b2b.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_b2b)
                    st.session_state.logistics_b2b = {
                        'rules': df.to_dict('records'),
                        'uploaded_at': datetime.now().isoformat(),
                        'filename': uploaded_b2b.name,
                        'type': 'csv'
                    }
                    save_all_data()
                    st.success("✅ B2B CSV imported!")
                
                else:
                    rules = json.load(uploaded_b2b)
                    st.session_state.logistics_b2b = {
                        'rules': rules,
                        'uploaded_at': datetime.now().isoformat(),
                        'filename': uploaded_b2b.name,
                        'type': 'json'
                    }
                    save_all_data()
                    st.success("✅ B2B JSON imported!")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
        
        if st.session_state.logistics_b2b:
            st.markdown("---")
            st.info(f"📁 **File:** {st.session_state.logistics_b2b.get('filename', 'Unknown')}")
            
            if st.session_state.logistics_b2b.get('type') == 'pdf':
                with st.expander("📄 View PDF Content"):
                    st.text_area("Text", st.session_state.logistics_b2b.get('raw_text', '')[:2000], height=300)
            elif 'rules' in st.session_state.logistics_b2b:
                df_rules = pd.DataFrame(st.session_state.logistics_b2b['rules'])
                st.dataframe(df_rules.head(20), use_container_width=True)
    
    with tab2:
        st.markdown("### Upload B2C Rate Card")
        uploaded_b2c = st.file_uploader("Upload (CSV/JSON/PDF)", type=['csv', 'json', 'pdf'], key="b2c")
        
        if uploaded_b2c and st.button("Import B2C Rules"):
            try:
                if uploaded_b2c.name.endswith('.pdf'):
                    if PDF_SUPPORT:
                        pdf_text = parse_pdf_to_text(uploaded_b2c)
                        if pdf_text:
                            st.session_state.logistics_b2c = {
                                'raw_text': pdf_text,
                                'uploaded_at': datetime.now().isoformat(),
                                'filename': uploaded_b2c.name,
                                'type': 'pdf'
                            }
                            save_all_data()
                            st.success("✅ B2C PDF imported!")
                    else:
                        st.error("❌ PDF support not available")
                
                elif uploaded_b2c.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_b2c)
                    st.session_state.logistics_b2c = {
                        'rules': df.to_dict('records'),
                        'uploaded_at': datetime.now().isoformat(),
                        'filename': uploaded_b2c.name,
                        'type': 'csv'
                    }
                    save_all_data()
                    st.success("✅ B2C CSV imported!")
                
                else:
                    rules = json.load(uploaded_b2c)
                    st.session_state.logistics_b2c = {
                        'rules': rules,
                        'uploaded_at': datetime.now().isoformat(),
                        'filename': uploaded_b2c.name,
                        'type': 'json'
                    }
                    save_all_data()
                    st.success("✅ B2C JSON imported!")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
        
        if st.session_state.logistics_b2c:
            st.markdown("---")
            st.info(f"📁 **File:** {st.session_state.logistics_b2c.get('filename', 'Unknown')}")
            
            if st.session_state.logistics_b2c.get('type') == 'pdf':
                with st.expander("📄 View PDF Content"):
                    st.text_area("Text", st.session_state.logistics_b2c.get('raw_text', '')[:2000], height=300)
            elif 'rules' in st.session_state.logistics_b2c:
                df_rules = pd.DataFrame(st.session_state.logistics_b2c['rules'])
                st.dataframe(df_rules.head(20), use_container_width=True)

# ============================================================================
# PAGE: GRN MANAGEMENT (FIXED - Tabular view with checkboxes)
# ============================================================================
# ============================================================================
# PAGE: SHIPPING CALCULATOR
# ============================================================================
elif page == "Shipping Calculator":
    st.title("🚚 Shipping Cost Calculator")
    
    st.markdown("""
    <div class="info-box">
    <strong>Calculate accurate shipping costs with volumetric weight</strong><br>
    • Origin: Mumbai, Maharashtra (all shipments)<br>
    • Chargeable Weight = Max(Dead Weight, Volumetric Weight)<br>
    • Marketplaces with own pickup excluded (₹0 shipping)
    </div>
    """, unsafe_allow_html=True)
    
    try:
        from shipping_calculator import calculate_invoice_shipping_costs
        
        if st.button("🔄 Calculate All Shipping Costs", type="primary"):
            with st.spinner("Calculating shipping costs..."):
                results = calculate_invoice_shipping_costs(
                    st.session_state.invoices,
                    st.session_state.item_master,
                    st.session_state.customers
                )
                st.session_state.shipping_calculations = results
                save_all_data()
                st.success(f"✅ Calculated shipping for {len(results)} invoices")
        
        if st.session_state.shipping_calculations:
            # Summary table
            st.markdown("### Shipping Cost Summary")
            summary_data = []
            for inv_id, calc in st.session_state.shipping_calculations.items():
                summary_data.append({
                    'Invoice ID': inv_id,
                    'Customer': calc['customer'],
                    'Type': calc['customer_type'],
                    'Is Marketplace': 'Yes' if calc.get('is_marketplace') else 'No',
                    'Shipping Cost': calc['total_shipping_cost']
                })
            
            df_summary = pd.DataFrame(summary_data)
            st.dataframe(df_summary, use_container_width=True, column_config={
                "Shipping Cost": st.column_config.NumberColumn("Shipping Cost", format="₹%.2f")
            })
            
            # Detailed view
            st.markdown("---")
            st.markdown("### Detailed Breakdown")
            selected_inv = st.selectbox("Select Invoice for Details", list(st.session_state.shipping_calculations.keys()))
            
            if selected_inv:
                calc = st.session_state.shipping_calculations[selected_inv]
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Customer", calc['customer'])
                    st.metric("Type", calc['customer_type'])
                with col2:
                    st.metric("Destination", f"{calc.get('dest_city', '')}, {calc.get('dest_state', '')}")
                    marketplace_status = "Yes - Own Pickup" if calc.get('is_marketplace') else "No"
                    st.metric("Is Marketplace", marketplace_status)
                with col3:
                    st.metric("Invoice Value", f"₹{calc.get('invoice_value', 0):,.2f}")
                    st.metric("Total Shipping Cost", f"₹{calc['total_shipping_cost']:,.2f}")
                
                if calc.get('is_marketplace'):
                    st.markdown("""
                    <div class="info-box">
                    🏪 <strong>Marketplace Customer:</strong> This customer has own pickup arrangement. No shipping charges applied.
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # Line items breakdown
                    st.markdown("#### Line Items Breakdown")
                    if calc.get('line_items'):
                        items_data = []
                        for item in calc['line_items']:
                            items_data.append({
                                'SKU': item['sku'],
                                'Item': item['item_name'],
                                'Qty': item['quantity'],
                                'Dead Wt (kg)': item['dead_weight'],
                                'Vol Wt (kg)': item['vol_weight'],
                                'Chargeable (kg)': item['chargeable_weight'],
                                'Total Wt (kg)': item['total_weight'],
                                'Zone': item['zone'],
                                'Shipping Cost': item['cost']
                            })
                        
                        df_items = pd.DataFrame(items_data)
                        st.dataframe(df_items, use_container_width=True, column_config={
                            "Shipping Cost": st.column_config.NumberColumn("Shipping (₹)", format="₹%.2f")
                        })
                        
                        # B2B breakdown if applicable
                        if calc['customer_type'] == 'B2B' and calc.get('line_items') and isinstance(calc['line_items'][0].get('breakdown'), dict):
                            st.markdown("#### B2B Cost Components")
                            bd = calc['line_items'][0]['breakdown']
                            
                            col_a, col_b, col_c, col_d, col_e = st.columns(5)
                            with col_a:
                                st.metric("Base Freight", f"₹{bd.get('base_freight', 0):.2f}")
                            with col_b:
                                st.metric("FSC (20%)", f"₹{bd.get('fsc', 0):.2f}")
                            with col_c:
                                st.metric("FOV (0.1%)", f"₹{bd.get('fov', 0):.2f}")
                            with col_d:
                                st.metric("Docket", f"₹{bd.get('docket', 0):.2f}")
                            with col_e:
                                st.metric("Total", f"₹{bd.get('total', 0):.2f}")
        else:
            st.info("Click 'Calculate All Shipping Costs' to generate shipping calculations")
    
    except ImportError:
        st.error("❌ shipping_calculator.py not found")
        st.info("Please place shipping_calculator.py in the same folder as this app")

elif page == "GRN Management":
    st.title("📋 GRN Management")
    
    grn_method = st.radio("Method", ["Tabular Bulk Update", "Upload GRN Report"], horizontal=True)
    
    if grn_method == "Tabular Bulk Update":
        st.markdown("### Pending GRN Invoices")
        
        pending_invoices = [inv for inv in st.session_state.invoices if inv.get('grn_status') == 'Pending']
        
        if pending_invoices:
            # Create DataFrame for display
            pending_df = pd.DataFrame(pending_invoices)
            pending_df['select'] = False  # Add checkbox column
            
            # Display with checkboxes
            display_cols = ['select', 'invoice_number', 'date', 'customer_name', 'item_name', 'quantity', 'total']
            if all(col in pending_df.columns for col in display_cols):
                edited_df = st.data_editor(
                    pending_df[display_cols],
                    hide_index=True,
                    use_container_width=True,
                    column_config={
                        "select": st.column_config.CheckboxColumn("Select", default=False),
                        "invoice_number": st.column_config.TextColumn("Invoice #", disabled=True),
                        "date": st.column_config.TextColumn("Date", disabled=True),
                        "customer_name": st.column_config.TextColumn("Customer", disabled=True),
                        "item_name": st.column_config.TextColumn("Item", disabled=True),
                        "quantity": st.column_config.NumberColumn("Qty", disabled=True),
                        "total": st.column_config.NumberColumn("Amount", format="₹%.2f", disabled=True)
                    },
                    key="grn_table"
                )
                
                col1, col2 = st.columns([2, 4])
                with col1:
                    grn_date = st.date_input("GRN Date", datetime.now())
                with col2:
                    if st.button("✅ Mark Selected as GRN", type="primary"):
                        selected_count = 0
                        selected_invoices = edited_df[edited_df['select'] == True]['invoice_number'].tolist()
                        
                        for i, inv in enumerate(st.session_state.invoices):
                            if inv.get('invoice_number') in selected_invoices:
                                st.session_state.invoices[i]['grn_status'] = 'Completed'
                                st.session_state.invoices[i]['grn_date'] = str(grn_date)
                                
                                # Calculate credit expiry
                                customer = inv.get('customer_name', '')
                                credit_days = st.session_state.customers.get(customer, {}).get('credit_days', 30)
                                expiry_date = grn_date + timedelta(days=credit_days)
                                st.session_state.invoices[i]['credit_expiry'] = str(expiry_date)
                                selected_count += 1
                        
                        save_all_data()
                        st.success(f"✅ Marked {selected_count} invoices as GRN!")
                        st.rerun()
        else:
            st.success("✅ All invoices have GRN!")
    
    else:  # Upload GRN Report
        uploaded_grn = st.file_uploader("Upload GRN Report (CSV)", type=['csv'])
        
        if uploaded_grn and st.button("Process GRN"):
            df_grn = pd.read_csv(uploaded_grn)
            matched = 0
            for _, row in df_grn.iterrows():
                invoice_num = str(row.get('Invoice Number', ''))
                grn_date = str(row.get('GRN Date', ''))
                
                for i, inv in enumerate(st.session_state.invoices):
                    if inv.get('invoice_number') == invoice_num:
                        st.session_state.invoices[i]['grn_status'] = 'Completed'
                        st.session_state.invoices[i]['grn_date'] = grn_date
                        matched += 1
            
            save_all_data()
            st.success(f"✅ {matched} invoices updated!")
    
    # Summary
    st.markdown("---")
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
# PAGE: BANK RECONCILIATION (FIXED - Error handling)
# ============================================================================
elif page == "Bank Reconciliation":
    st.title("🏦 Bank Reconciliation")
    
    st.markdown("""
    <div class="info-box">
    Upload bank statements and map transactions. Once mapped, only new transactions need mapping.
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_bank = st.file_uploader("Upload Bank Statement (CSV)", type=['csv'])
    
    if uploaded_bank and st.button("🚀 Import Bank Statement"):
        try:
            # Read CSV with error handling
            df_bank = pd.read_csv(uploaded_bank, encoding='utf-8', on_bad_lines='skip')
            df_bank.columns = df_bank.columns.str.strip()
            
            new_count = 0
            duplicate_count = 0
            existing_hashes = set(t.get('hash', '') for t in st.session_state.bank_statements)
            
            for idx, row in df_bank.iterrows():
                # Skip header rows or empty rows
                if pd.isna(row.get('Transaction Date')) or str(row.get('Transaction Date')).strip() == '':
                    continue
                
                # Skip if it's a header row
                if str(row.get('Transaction Date')).strip().lower() in ['transaction date', 'sl. no.']:
                    continue
                
                try:
                    trans_dict = {
                        'date': str(row.get('Transaction Date', '')),
                        'description': str(row.get('Description', '')),
                        'amount': str(row.get('Amount', '0'))
                    }
                    trans_hash = get_row_hash(trans_dict)
                    
                    if trans_hash in existing_hashes:
                        duplicate_count += 1
                        continue
                    
                    # Parse amount (remove commas)
                    amount_str = str(row.get('Amount', '0')).replace(',', '').strip()
                    try:
                        amount = float(amount_str) if amount_str else 0.0
                    except:
                        amount = 0.0
                    
                    transaction = {
                        'date': str(row.get('Transaction Date', '')),
                        'description': str(row.get('Description', '')),
                        'reference': str(row.get('Chq / Ref No.', row.get('Reference', ''))),
                        'amount': amount,
                        'type': str(row.get('Dr / Cr', '')),
                        'hash': trans_hash,
                        'customer': None,
                        'mapped': False
                    }
                    
                    st.session_state.bank_statements.append(transaction)
                    existing_hashes.add(trans_hash)
                    new_count += 1
                except Exception as e:
                    st.warning(f"Skipped row {idx}: {str(e)}")
                    continue
            
            save_all_data()
            st.success(f"✅ {new_count} new, {duplicate_count} duplicates skipped!")
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
            st.info("💡 Tip: Ensure your CSV has columns: Transaction Date, Description, Amount, Dr / Cr")
    
    # Transaction mapping
    unmapped = [t for t in st.session_state.bank_statements if not t.get('mapped', False)]
    
    if unmapped:
        st.warning(f"⚠️ {len(unmapped)} transactions need mapping")
        customer_list = ['[Skip]'] + list(st.session_state.customers.keys())
        
        for i, trans in enumerate(unmapped[:10]):
            with st.expander(f"₹{trans.get('amount', 0):,.2f} - {trans.get('description', '')[:50]}"):
                selected = st.selectbox("Map to Customer", customer_list, key=f"map_{i}")
                
                if st.button("Save", key=f"save_{i}"):
                    for t in st.session_state.bank_statements:
                        if t.get('hash') == trans.get('hash'):
                            t['customer'] = None if selected == '[Skip]' else selected
                            t['mapped'] = True
                            break
                    save_all_data()
                    st.success("✅ Mapped!")
                    st.rerun()
    else:
        st.success("✅ All transactions mapped!")
    
    # Summary
    if st.session_state.bank_statements:
        df = pd.DataFrame(st.session_state.bank_statements)
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Transactions", len(df))
        with col2:
            st.metric("Mapped", len(df[df['mapped'] == True]))
        with col3:
            credits = df[df['type'] == 'CR']['amount'].sum()
            st.metric("Credits", f"₹{credits:,.2f}")
        with col4:
            debits = df[df['type'] == 'DR']['amount'].sum()
            st.metric("Debits", f"₹{debits:,.2f}")

# ============================================================================
# PAGE: RECEIVABLES (With credit days tracking)
# ============================================================================
elif page == "Receivables":
    st.title("💰 Receivables Dashboard")
    
    receivables = {}
    for inv in st.session_state.invoices:
        if inv.get('balance', 0) > 0:
            customer = inv['customer_name']
            if customer not in receivables:
                receivables[customer] = {'customer': customer, 'total_due': 0, 'invoices': []}
            
            # Calculate days based on credit expiry (from GRN date + credit days)
            if inv.get('credit_expiry'):
                try:
                    expiry_date = datetime.strptime(inv['credit_expiry'], '%Y-%m-%d')
                    days_overdue = (datetime.now() - expiry_date).days
                except:
                    days_overdue = 0
            else:
                # Fallback to due date
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
                'Status': 'Current' if max_overdue <= 0 else f'{max_overdue} days'
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
    
    if uploaded_marketing and st.button("Import"):
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
        st.success("✅ Imported!")
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
            st.metric("📊 Avg ROAS", f"{(total_revenue/total_spend):.2f}x" if total_spend > 0 else "0x")
        
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
        date_from = st.date_input("From", datetime.now() - timedelta(days=30))
    
    with col4:
        date_to = st.date_input("To", datetime.now())
    
    # Filter invoices
    filtered = st.session_state.invoices
    
    if selected_channel != 'All':
        filtered = [inv for inv in filtered if inv.get('channel') == selected_channel]
    if selected_product != 'All':
        filtered = [inv for inv in filtered if inv.get('item_name') == selected_product]
    
    filtered = [inv for inv in filtered 
                if date_from <= datetime.strptime(inv['date'], '%Y-%m-%d').date() <= date_to]
    
    if filtered:
        sales = sum(inv.get('item_total', 0) for inv in filtered)
        
        # COGS calculation
        cogs = 0
        for inv in filtered:
            sku = inv.get('sku', '')
            qty = inv.get('quantity', 0)
            if sku in st.session_state.item_master:
                cogs += st.session_state.item_master[sku].get('cogs', 0) * qty
        
        # Shipping cost (simplified for now - can be enhanced with rate calculator)
        shipping = 0
        for inv in filtered:
            customer = inv.get('customer_name', '')
            qty = inv.get('quantity', 0)
            cust_type = st.session_state.customers.get(customer, {}).get('type', 'B2C')
            shipping += qty * (30 if cust_type == 'B2B' else 45)
        
        # Marketing spend
        marketing_spend = 0
        for spend in st.session_state.marketing:
            spend_date = datetime.strptime(spend['date'].split('T')[0], '%Y-%m-%d').date()
            if date_from <= spend_date <= date_to:
                if selected_channel == 'All' or spend.get('channel', '') == selected_channel:
                    marketing_spend += spend.get('spend', 0)
        
        brand_marketing = marketing_spend * 0.1
        
        # Calculate margins
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
        
        # Waterfall chart
        fig = go.Figure(go.Waterfall(
            x = ['Sales', 'COGS', 'GM', 'Shipping', 'CM1', 'Perf Mktg', 'CM2', 'Brand Mktg', 'CM3'],
            y = [sales, -cogs, 0, -shipping, 0, -marketing_spend, 0, -brand_marketing, 0],
            measure = ['absolute', 'relative', 'total', 'relative', 'total', 'relative', 'total', 'relative', 'total'],
            decreasing = {"marker":{"color":"#ef4444"}},
            increasing = {"marker":{"color":"#10b981"}},
            totals = {"marker":{"color":"#facc15"}}
        ))
        fig.update_layout(title="P&L Waterfall", template="plotly_dark", height=500)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("⚠️ No data for selected filters")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #64748b;'><strong>P&L Management System</strong> | Data persists across sessions</div>", unsafe_allow_html=True)
