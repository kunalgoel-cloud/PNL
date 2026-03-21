# ============================================================================
# SHIPPING CALCULATOR MODULE
# Save this as: shipping_calculator.py
# Place in same folder as your main app
# ============================================================================

"""
HOW TO USE:
1. Save this file as shipping_calculator.py
2. In your main app, the shipping calculator page will use this
3. Make sure Item Master has: dead_weight_kg and volumetric_weight_kg columns
4. Make sure Customers has: is_marketplace column
"""

# ============================================================================
# CONSTANTS
# ============================================================================

# Origin for all shipments
DEFAULT_ORIGIN_CITY = "MUMBAI"
DEFAULT_ORIGIN_STATE = "MAHARASHTRA"
ORIGIN_B2B_ZONE = "West-2"  # Mumbai is in West-2 zone

# ============================================================================
# B2C RATE CARD (From Enterprise Commercials PDF)
# ============================================================================

B2C_RATE_CARD = {
    'Delhivery': {
        'Local': {'0-500': 21.0, 'add_500': 17.0, '2kg': 71.0, 'add_1kg_2-5': 27.0, '5kg': 145.0, 'add_1kg_5-10': 23.0, '10kg': 238.0, 'add_1kg_10+': 14.0},
        'Within State': {'0-500': 25.0, 'add_500': 21.0, '2kg': 83.0, 'add_1kg_2-5': 32.0, '5kg': 150.0, 'add_1kg_5-10': 24.0, '10kg': 260.0, 'add_1kg_10+': 17.0},
        'Metro to Metro': {'0-500': 31.0, 'add_500': 24.0, '2kg': 90.0, 'add_1kg_2-5': 35.0, '5kg': 178.0, 'add_1kg_5-10': 24.0, '10kg': 281.0, 'add_1kg_10+': 17.0},
        'Rest of India': {'0-500': 34.0, 'add_500': 23.0, '2kg': 97.0, 'add_1kg_2-5': 37.0, '5kg': 199.0, 'add_1kg_5-10': 25.0, '10kg': 299.0, 'add_1kg_10+': 18.0},
        'Special Zone': {'0-500': 39.0, 'add_500': 25.0, '2kg': 109.0, 'add_1kg_2-5': 39.0, '5kg': 239.0, 'add_1kg_5-10': 35.0, '10kg': 387.0, 'add_1kg_10+': 22.0}
    },
    'Bluedart': {
        'Local': {'0-500': 30.0, 'add_500': 24.0, '2kg': 96.0, 'add_1kg_2-5': 46.0, '5kg': 227.0, 'add_1kg_5-10': 45.0, '10kg': 449.0, 'add_1kg_10+': 44.0},
        'Within State': {'0-500': 36.0, 'add_500': 26.0, '2kg': 104.0, 'add_1kg_2-5': 49.0, '5kg': 250.0, 'add_1kg_5-10': 47.2, '10kg': 477.0, 'add_1kg_10+': 47.0},
        'Metro to Metro': {'0-500': 42.0, 'add_500': 33.0, '2kg': 134.0, 'add_1kg_2-5': 63.0, '5kg': 312.0, 'add_1kg_5-10': 61.0, '10kg': 617.0, 'add_1kg_10+': 61.0},
        'Rest of India': {'0-500': 47.0, 'add_500': 38.0, '2kg': 153.0, 'add_1kg_2-5': 72.0, '5kg': 355.0, 'add_1kg_5-10': 69.0, '10kg': 700.0, 'add_1kg_10+': 69.0},
        'Special Zone': {'0-500': 56.0, 'add_500': 50.0, '2kg': 202.0, 'add_1kg_2-5': 95.0, '5kg': 469.0, 'add_1kg_5-10': 92.0, '10kg': 924.0, 'add_1kg_10+': 91.0}
    }
}

# ============================================================================
# B2B RATE CARD (From Safexpress PDF)
# ============================================================================

# Base rates per kg from West-2 (Mumbai) to other zones
B2B_BASE_RATES = {
    'West-2 to North-1': 8.64,
    'West-2 to North-2': 10.8,
    'West-2 to East': 10.8,
    'West-2 to North-East': 16.2,
    'West-2 to West-1': 6.48,
    'West-2 to West-2': 6.48,
    'West-2 to South-1': 7.56,
    'West-2 to South-2': 6.48,
    'West-2 to Central': 7.56
}

B2B_DOCKET_CHARGE = 100
B2B_FOV_RATE = 0.001  # 0.1%
B2B_FOV_MIN = 100
B2B_FSC_RATE = 0.20  # 20%
B2B_MIN_WEIGHT = 15
B2B_MIN_FREIGHT = 400
B2B_METRO_CHARGE = 100

# Zone mapping
B2B_ZONE_MAP = {
    'North-1': ['Delhi', 'Uttar Pradesh', 'Haryana', 'Rajasthan', 'UP', 'DL', 'HR', 'RJ'],
    'North-2': ['Chandigarh', 'Punjab', 'Himachal Pradesh', 'Uttarakhand', 'Jammu', 'Kashmir', 'Ladakh', 'PB', 'HP', 'UK', 'JK'],
    'East': ['West Bengal', 'Odisha', 'Bihar', 'Jharkhand', 'Chhattisgarh', 'WB', 'OR', 'BR', 'JH', 'CG'],
    'North-East': ['Assam', 'Meghalaya', 'Tripura', 'Arunachal Pradesh', 'Mizoram', 'Manipur', 'Nagaland', 'Sikkim'],
    'West-1': ['Gujarat', 'Daman', 'Diu', 'Dadra', 'GJ', 'DN', 'DD'],
    'West-2': ['Maharashtra', 'Goa', 'MH', 'GA'],
    'South-1': ['Andhra Pradesh', 'Telangana', 'Karnataka', 'Tamil Nadu', 'Puducherry', 'AP', 'TG', 'KA', 'TN', 'PY'],
    'South-2': ['Kerala', 'KL'],
    'Central': ['Madhya Pradesh', 'MP']
}

SPECIAL_ZONES = ['J&K', 'Himachal Pradesh', 'HP', 'Kerala', 'KL', 'Andaman', 'Lakshadweep', 'Leh', 'Ladakh',
                 'Arunachal Pradesh', 'Assam', 'Manipur', 'Meghalaya', 'Mizoram', 'Nagaland', 'Tripura', 'Sikkim']

LOCAL_MUMBAI = ['MUMBAI', 'NAVI MUMBAI', 'THANE', 'KALYAN', 'BHIWANDI', 'VASAI']
METRO_CITIES = ['DELHI', 'NEW DELHI', 'CHENNAI', 'KOLKATA', 'BANGALORE', 'BENGALURU', 'MUMBAI', 'PUNE', 'AHMEDABAD', 'HYDERABAD']

# ============================================================================
# ZONE DETERMINATION FUNCTIONS
# ============================================================================

def determine_b2c_zone(dest_city, dest_state):
    """Determine B2C zone from Mumbai origin"""
    dest_city_upper = str(dest_city).strip().upper()
    dest_state_upper = str(dest_state).strip().upper()
    
    # Special zones
    for special in SPECIAL_ZONES:
        if special.upper() in dest_state_upper or special.upper() in dest_city_upper:
            return 'Special Zone'
    
    # Local
    if any(area in dest_city_upper for area in LOCAL_MUMBAI):
        return 'Local'
    
    # Within State
    if 'MAHARASHTRA' in dest_state_upper or 'MH' in dest_state_upper:
        return 'Within State'
    
    # Metro to Metro
    if any(metro in dest_city_upper for metro in METRO_CITIES):
        return 'Metro to Metro'
    
    return 'Rest of India'

def determine_b2b_zone(dest_state):
    """Determine B2B zone from state"""
    dest_state_upper = str(dest_state).strip().upper()
    
    for zone, states in B2B_ZONE_MAP.items():
        for state in states:
            if state.upper() in dest_state_upper:
                return zone
    
    return 'Central'

# ============================================================================
# SHIPPING COST CALCULATION FUNCTIONS
# ============================================================================

def calculate_b2c_cost(weight_kg, zone, courier='Delhivery'):
    """Calculate B2C shipping cost"""
    if courier not in B2C_RATE_CARD or zone not in B2C_RATE_CARD[courier]:
        return 0, "Rate not found"
    
    rates = B2C_RATE_CARD[courier][zone]
    
    if weight_kg <= 0.5:
        return rates['0-500'], "Base (0-500g)"
    elif weight_kg <= 2.0:
        slabs = int((weight_kg * 1000 - 500) / 500) + (1 if (weight_kg * 1000 - 500) % 500 > 0 else 0)
        return rates['0-500'] + slabs * rates['add_500'], f"0-2kg: Base + {slabs}×500g"
    elif weight_kg <= 5.0:
        kg = int(weight_kg - 2) + (1 if (weight_kg - 2) % 1 > 0 else 0)
        return rates['2kg'] + kg * rates['add_1kg_2-5'], f"2-5kg: 2kg + {kg}×1kg"
    elif weight_kg <= 10.0:
        kg = int(weight_kg - 5) + (1 if (weight_kg - 5) % 1 > 0 else 0)
        return rates['5kg'] + kg * rates['add_1kg_5-10'], f"5-10kg: 5kg + {kg}×1kg"
    else:
        kg = int(weight_kg - 10) + (1 if (weight_kg - 10) % 1 > 0 else 0)
        return rates['10kg'] + kg * rates['add_1kg_10+'], f"10kg+: 10kg + {kg}×1kg"

def calculate_b2b_cost(weight_kg, dest_zone, invoice_value=0):
    """Calculate B2B shipping cost"""
    zone_key = f"{ORIGIN_B2B_ZONE} to {dest_zone}"
    base_rate = B2B_BASE_RATES.get(zone_key, 8.64)
    
    chargeable_weight = max(weight_kg, B2B_MIN_WEIGHT)
    base_freight = max(chargeable_weight * base_rate, B2B_MIN_FREIGHT)
    fsc = base_freight * B2B_FSC_RATE
    fov = max(invoice_value * B2B_FOV_RATE, B2B_FOV_MIN)
    docket = B2B_DOCKET_CHARGE
    
    total = base_freight + fsc + fov + docket
    
    breakdown = {
        'base_freight': base_freight,
        'fsc': fsc,
        'fov': fov,
        'docket': docket,
        'total': total,
        'zone': zone_key
    }
    
    return total, breakdown

# ============================================================================
# MAIN CALCULATION FUNCTION
# ============================================================================

def calculate_invoice_shipping_costs(invoices, item_master, customers):
    """
    Calculate shipping costs for all invoices
    
    Returns: Dict mapping invoice_id to shipping calculation details
    """
    results = {}
    
    # Get unique invoice IDs
    invoice_ids = list(set(inv.get('invoice_id') or inv.get('invoice_number') for inv in invoices))
    
    for inv_id in invoice_ids:
        # Get all line items for this invoice
        invoice_items = [inv for inv in invoices if inv.get('invoice_id') == inv_id or inv.get('invoice_number') == inv_id]
        
        if not invoice_items:
            continue
        
        # Get customer info
        customer_name = invoice_items[0].get('customer_name', '')
        customer = customers.get(customer_name, {})
        customer_type = customer.get('type', 'B2C')
        is_marketplace = customer.get('is_marketplace', False)
        
        # Skip if marketplace (they have own pickup)
        if is_marketplace:
            results[inv_id] = {
                'invoice_id': inv_id,
                'customer': customer_name,
                'customer_type': customer_type,
                'is_marketplace': True,
                'total_shipping_cost': 0,
                'line_items': [],
                'note': 'Marketplace - Own Pickup'
            }
            continue
        
        # Get destination
        dest_city = invoice_items[0].get('dest_city', '')
        dest_state = invoice_items[0].get('dest_state', '')
        total_invoice_value = sum(item.get('item_total', 0) for item in invoice_items)
        
        # Calculate shipping for each line item
        line_calculations = []
        total_shipping = 0
        
        for item in invoice_items:
            sku = item.get('sku', '')
            quantity = item.get('quantity', 1)
            
            # Get weights from item master
            product = item_master.get(sku, {})
            dead_weight = product.get('dead_weight_kg', 0.5)
            vol_weight = product.get('volumetric_weight_kg', 0.5)
            
            # Chargeable weight = Max(dead, volumetric)
            chargeable_per_unit = max(dead_weight, vol_weight)
            total_weight = chargeable_per_unit * quantity
            
            # Calculate cost
            if customer_type == 'B2C':
                zone = determine_b2c_zone(dest_city, dest_state)
                cost, breakdown = calculate_b2c_cost(total_weight, zone)
            else:  # B2B
                dest_zone = determine_b2b_zone(dest_state)
                cost, breakdown = calculate_b2b_cost(total_weight, dest_zone, total_invoice_value)
                zone = breakdown['zone'] if isinstance(breakdown, dict) else dest_zone
            
            total_shipping += cost
            
            line_calculations.append({
                'sku': sku,
                'item_name': item.get('item_name', ''),
                'quantity': quantity,
                'dead_weight': dead_weight,
                'vol_weight': vol_weight,
                'chargeable_weight': chargeable_per_unit,
                'total_weight': total_weight,
                'zone': zone,
                'cost': cost,
                'breakdown': breakdown
            })
        
        results[inv_id] = {
            'invoice_id': inv_id,
            'customer': customer_name,
            'customer_type': customer_type,
            'is_marketplace': False,
            'dest_city': dest_city,
            'dest_state': dest_state,
            'invoice_value': total_invoice_value,
            'total_shipping_cost': total_shipping,
            'line_items': line_calculations
        }
    
    return results

# ============================================================================
# END OF MODULE
# ============================================================================
