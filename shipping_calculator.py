# ============================================================================
# SHIPPING CALCULATOR MODULE - EXACT LOGIC FROM REFERENCE APP
# Save this as: shipping_calculator.py
# Place in same folder as your main app
# ============================================================================

"""
This module contains the EXACT shipping calculation logic from the reference app.
Updated to match all edge cases, rounding rules, and zone determination logic.
"""

import pandas as pd

# ============================================================================
# CONSTANTS
# ============================================================================

# Origin for all shipments
DEFAULT_ORIGIN_CITY = "MUMBAI"
DEFAULT_ORIGIN_STATE = "MAHARASHTRA"
ORIGIN_B2B_ZONE = "West-2"  # Mumbai is in West-2 zone

# Special zones
SPECIAL_ZONES = ['Jammu and Kashmir', 'Himachal Pradesh', 'Kerala', 
                 'Andaman', 'Lakshadweep', 'Leh', 'Ladakh',
                 'Arunachal Pradesh', 'Assam', 'Manipur', 'Meghalaya', 
                 'Mizoram', 'Nagaland', 'Tripura', 'Sikkim',
                 'J&K', 'HP', 'KL', 'AN', 'LD', 'AR', 'AS', 'MN', 'ML', 'MZ', 'NL', 'TR', 'SK']

# ============================================================================
# B2C RATE CARD (EXACT FROM REFERENCE APP)
# ============================================================================

B2C_RATE_CARD = {
    'Bluedart Surface': {
        'Local': {'0-500': 30.0, 'add_500': 24.0, '2kg': 96.0, 'add_1kg_2-5': 46.0, '5kg': 227.0, 'add_1kg_5-10': 45.0, '10kg': 449.0, 'add_1kg_10+': 44.0},
        'Within State': {'0-500': 36.0, 'add_500': 26.0, '2kg': 104.0, 'add_1kg_2-5': 49.0, '5kg': 250.0, 'add_1kg_5-10': 47.2, '10kg': 477.0, 'add_1kg_10+': 47.0},
        'Metro to Metro': {'0-500': 42.0, 'add_500': 33.0, '2kg': 134.0, 'add_1kg_2-5': 63.0, '5kg': 312.0, 'add_1kg_5-10': 61.0, '10kg': 617.0, 'add_1kg_10+': 61.0},
        'Rest of India': {'0-500': 47.0, 'add_500': 38.0, '2kg': 153.0, 'add_1kg_2-5': 72.0, '5kg': 355.0, 'add_1kg_5-10': 69.0, '10kg': 700.0, 'add_1kg_10+': 69.0},
        'Special Zone': {'0-500': 56.0, 'add_500': 50.0, '2kg': 202.0, 'add_1kg_2-5': 95.0, '5kg': 469.0, 'add_1kg_5-10': 92.0, '10kg': 924.0, 'add_1kg_10+': 91.0},
    },
    'Bluedart Air': {
        'Local': {'0-500': 36.0, 'add_500': 35.0},
        'Within State': {'0-500': 40.0, 'add_500': 39.0},
        'Metro to Metro': {'0-500': 46.0, 'add_500': 46.0},
        'Rest of India': {'0-500': 57.0, 'add_500': 55.0},
        'Special Zone': {'0-500': 76.0, 'add_500': 74.0},
    },
    'Delhivery Surface': {
        'Local': {'0-500': 21.0, 'add_500': 17.0, '2kg': 71.0, 'add_1kg_2-5': 27.0, '5kg': 145.0, 'add_1kg_5-10': 23.0, '10kg': 238.0, 'add_1kg_10+': 14.0},
        'Within State': {'0-500': 25.0, 'add_500': 21.0, '2kg': 83.0, 'add_1kg_2-5': 32.0, '5kg': 150.0, 'add_1kg_5-10': 24.0, '10kg': 260.0, 'add_1kg_10+': 17.0},
        'Metro to Metro': {'0-500': 31.0, 'add_500': 24.0, '2kg': 90.0, 'add_1kg_2-5': 35.0, '5kg': 178.0, 'add_1kg_5-10': 24.0, '10kg': 281.0, 'add_1kg_10+': 17.0},
        'Rest of India': {'0-500': 34.0, 'add_500': 23.0, '2kg': 97.0, 'add_1kg_2-5': 37.0, '5kg': 199.0, 'add_1kg_5-10': 25.0, '10kg': 299.0, 'add_1kg_10+': 18.0},
        'Special Zone': {'0-500': 39.0, 'add_500': 25.0, '2kg': 109.0, 'add_1kg_2-5': 39.0, '5kg': 239.0, 'add_1kg_5-10': 35.0, '10kg': 387.0, 'add_1kg_10+': 22.0},
    },
    'Delhivery Air': {
        'Local': {'0-500': 30.0, 'add_500': 28.0},
        'Within State': {'0-500': 35.0, 'add_500': 34.0},
        'Metro to Metro': {'0-500': 46.0, 'add_500': 38.0},
        'Rest of India': {'0-500': 56.0, 'add_500': 48.0},
        'Special Zone': {'0-500': 68.0, 'add_500': 62.0},
    }
}

# Default courier for B2C
DEFAULT_B2C_COURIER = 'Delhivery Surface'

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
    'North-1': ['DELHI', 'UTTAR PRADESH', 'HARYANA', 'RAJASTHAN', 'UP', 'DL', 'HR', 'RJ'],
    'North-2': ['CHANDIGARH', 'PUNJAB', 'HIMACHAL PRADESH', 'UTTARAKHAND', 'JAMMU', 'KASHMIR', 'LADAKH', 'PB', 'HP', 'UK', 'JK', 'J&K'],
    'East': ['WEST BENGAL', 'ODISHA', 'BIHAR', 'JHARKHAND', 'CHHATTISGARH', 'WB', 'OR', 'BR', 'JH', 'CG'],
    'North-East': ['ASSAM', 'MEGHALAYA', 'TRIPURA', 'ARUNACHAL PRADESH', 'MIZORAM', 'MANIPUR', 'NAGALAND', 'SIKKIM', 'AS', 'ML', 'TR', 'AR', 'MZ', 'MN', 'NL', 'SK'],
    'West-1': ['GUJARAT', 'DAMAN', 'DIU', 'DADRA', 'NAGAR HAVELI', 'GJ', 'DN', 'DD'],
    'West-2': ['MAHARASHTRA', 'GOA', 'MH', 'GA'],
    'South-1': ['ANDHRA PRADESH', 'TELANGANA', 'KARNATAKA', 'TAMIL NADU', 'TAMILNADU', 'PUDUCHERRY', 'AP', 'TG', 'KA', 'TN', 'PY'],
    'South-2': ['KERALA', 'KL'],
    'Central': ['MADHYA PRADESH', 'MP']
}

METRO_CITIES = ['DELHI', 'MUMBAI', 'BANGALORE', 'KOLKATA', 'CHENNAI', 'NEW DELHI', 'NAVI MUMBAI', 'BENGALURU', 'HYDERABAD', 'PUNE', 'AHMEDABAD']

# ============================================================================
# ZONE DETERMINATION (EXACT LOGIC FROM REFERENCE APP)
# ============================================================================

def determine_zone(origin_city, dest_city, dest_state, origin_state=None):
    """
    Determine shipping zone based on origin and destination
    EXACT LOGIC FROM REFERENCE APP
    """
    origin_city = str(origin_city).strip().title() if pd.notna(origin_city) else ""
    dest_city = str(dest_city).strip().title() if pd.notna(dest_city) else ""
    dest_state = str(dest_state).strip().upper() if pd.notna(dest_state) else ""
    origin_state = str(origin_state).strip().upper() if pd.notna(origin_state) and origin_state else "MAHARASHTRA"
    
    # Normalize state names - EXACT MAPPING FROM REFERENCE
    state_mapping = {
        'MH': 'MAHARASHTRA', 'MAHARASHTRA': 'MAHARASHTRA',
        'DL': 'DELHI', 'DELHI': 'DELHI',
        'KA': 'KARNATAKA', 'KARNATAKA': 'KARNATAKA',
        'TN': 'TAMIL NADU', 'TAMILNADU': 'TAMIL NADU', 'TAMIL NADU': 'TAMIL NADU',
        'WB': 'WEST BENGAL', 'WEST BENGAL': 'WEST BENGAL',
        'GJ': 'GUJARAT', 'GUJARAT': 'GUJARAT',
        'UP': 'UTTAR PRADESH', 'UTTAR PRADESH': 'UTTAR PRADESH',
        'RJ': 'RAJASTHAN', 'RAJASTHAN': 'RAJASTHAN',
        'HR': 'HARYANA', 'HARYANA': 'HARYANA',
        'PB': 'PUNJAB', 'PUNJAB': 'PUNJAB',
        'AP': 'ANDHRA PRADESH', 'ANDHRA PRADESH': 'ANDHRA PRADESH',
        'TG': 'TELANGANA', 'TELANGANA': 'TELANGANA',
        'KL': 'KERALA', 'KERALA': 'KERALA',
        'OR': 'ODISHA', 'ODISHA': 'ODISHA',
        'BR': 'BIHAR', 'BIHAR': 'BIHAR',
        'JH': 'JHARKHAND', 'JHARKHAND': 'JHARKHAND',
        'CG': 'CHHATTISGARH', 'CHHATTISGARH': 'CHHATTISGARH',
        'MP': 'MADHYA PRADESH', 'MADHYA PRADESH': 'MADHYA PRADESH',
        'AS': 'ASSAM', 'ASSAM': 'ASSAM',
        'HP': 'HIMACHAL PRADESH', 'HIMACHAL PRADESH': 'HIMACHAL PRADESH',
        'J&K': 'JAMMU AND KASHMIR', 'JAMMU AND KASHMIR': 'JAMMU AND KASHMIR',
        'JK': 'JAMMU AND KASHMIR',
        'UT': 'UTTARAKHAND', 'UTTARAKHAND': 'UTTARAKHAND'
    }
    
    # Normalize origin and destination states
    for code, full_name in state_mapping.items():
        if code in origin_state:
            origin_state = full_name
            break
    
    for code, full_name in state_mapping.items():
        if code in dest_state:
            dest_state = full_name
            break
    
    # Check for special zones first - EXACT LOGIC
    special_zone_states = [
        'JAMMU AND KASHMIR', 'HIMACHAL PRADESH', 'KERALA',
        'ANDAMAN', 'LAKSHADWEEP', 'ARUNACHAL PRADESH', 
        'ASSAM', 'MANIPUR', 'MEGHALAYA', 'MIZORAM', 
        'NAGALAND', 'TRIPURA', 'SIKKIM'
    ]
    
    special_zone_keywords = ['ANDAMAN', 'LAKSHADWEEP', 'LEH', 'LADAKH']
    
    for sz_state in special_zone_states:
        if sz_state in dest_state:
            return 'Special Zone'
    
    for keyword in special_zone_keywords:
        if keyword in dest_state.upper() or keyword in dest_city.upper():
            return 'Special Zone'
    
    # Check if Local (same city or nearby areas in same metro) - EXACT LOGIC
    local_city_groups = {
        'MUMBAI': ['MUMBAI', 'NAVI MUMBAI', 'THANE', 'BHIWANDI', 'KALYAN', 'DOMBIVLI', 'VASAI', 'VIRAR'],
        'DELHI': ['DELHI', 'NEW DELHI', 'GURGAON', 'GURUGRAM', 'NOIDA', 'GREATER NOIDA', 'FARIDABAD', 'GHAZIABAD'],
        'BANGALORE': ['BANGALORE', 'BENGALURU', 'BANGALORE URBAN'],
        'CHENNAI': ['CHENNAI'],
        'KOLKATA': ['KOLKATA', 'HOWRAH'],
        'PUNE': ['PUNE', 'PIMPRI', 'CHINCHWAD'],
        'HYDERABAD': ['HYDERABAD', 'SECUNDERABAD']
    }
    
    for metro, cities in local_city_groups.items():
        origin_in_metro = any(city in origin_city.upper() for city in cities)
        dest_in_metro = any(city in dest_city.upper() for city in cities)
        if origin_in_metro and dest_in_metro:
            return 'Local'
    
    # Check if metro to metro (different metros) - EXACT LOGIC
    metro_cities_list = ['MUMBAI', 'NAVI MUMBAI', 'DELHI', 'NEW DELHI', 'BANGALORE', 
                         'BENGALURU', 'CHENNAI', 'KOLKATA', 'HYDERABAD', 'PUNE']
    
    origin_is_metro = any(metro.upper() in origin_city.upper() for metro in metro_cities_list)
    dest_is_metro = any(metro.upper() in dest_city.upper() for metro in metro_cities_list)
    
    if origin_is_metro and dest_is_metro:
        # Check if same metro (should be Local, not Metro to Metro)
        same_metro = False
        for metro, cities in local_city_groups.items():
            origin_in_metro = any(city in origin_city.upper() for city in cities)
            dest_in_metro = any(city in dest_city.upper() for city in cities)
            if origin_in_metro and dest_in_metro:
                same_metro = True
                break
        
        if not same_metro:
            return 'Metro to Metro'
    
    # Check if within same state
    if origin_state == dest_state:
        return 'Within State'
    
    # Default to Rest of India
    return 'Rest of India'

def determine_b2b_zone(dest_state):
    """Determine B2B zone from state - FOR SAFEXPRESS"""
    dest_state_upper = str(dest_state).strip().upper()
    
    # Normalize state name first
    state_mapping = {
        'MH': 'MAHARASHTRA', 'DL': 'DELHI', 'KA': 'KARNATAKA',
        'TN': 'TAMIL NADU', 'TAMILNADU': 'TAMIL NADU',
        'WB': 'WEST BENGAL', 'GJ': 'GUJARAT', 'UP': 'UTTAR PRADESH',
        'RJ': 'RAJASTHAN', 'HR': 'HARYANA', 'PB': 'PUNJAB',
        'AP': 'ANDHRA PRADESH', 'TG': 'TELANGANA', 'KL': 'KERALA',
        'OR': 'ODISHA', 'BR': 'BIHAR', 'JH': 'JHARKHAND',
        'CG': 'CHHATTISGARH', 'MP': 'MADHYA PRADESH', 'AS': 'ASSAM',
        'HP': 'HIMACHAL PRADESH', 'J&K': 'JAMMU AND KASHMIR',
        'JK': 'JAMMU AND KASHMIR', 'UT': 'UTTARAKHAND'
    }
    
    for code, full_name in state_mapping.items():
        if code in dest_state_upper:
            dest_state_upper = full_name
            break
    
    # Find zone
    for zone, states in B2B_ZONE_MAP.items():
        for state in states:
            if state in dest_state_upper:
                return zone
    
    return 'Central'  # Default

# ============================================================================
# COST CALCULATION (EXACT LOGIC FROM REFERENCE APP)
# ============================================================================

def calculate_freight_cost(weight_kg, zone, courier):
    """
    Calculate freight cost based on weight, zone, and courier
    EXACT LOGIC FROM REFERENCE APP - INCLUDING ROUNDING RULES
    """
    if courier not in B2C_RATE_CARD:
        return None, "Courier not in rate card"
    
    if zone not in B2C_RATE_CARD[courier]:
        return None, f"Zone {zone} not found for {courier}"
    
    rates = B2C_RATE_CARD[courier][zone]
    
    # Convert weight to grams for easier calculation
    weight_grams = weight_kg * 1000
    
    # For Air couriers (simpler rate structure) - EXACT LOGIC
    if 'Air' in courier:
        if weight_grams <= 500:
            return rates['0-500'], "Base rate (0-500g)"
        else:
            # Calculate additional 500g slabs - EXACT ROUNDING LOGIC
            additional_slabs = ((weight_grams - 500) / 500)
            if additional_slabs != int(additional_slabs):
                additional_slabs = int(additional_slabs) + 1
            else:
                additional_slabs = int(additional_slabs)
            
            cost = rates['0-500'] + (additional_slabs * rates['add_500'])
            return cost, f"Base + {additional_slabs} x 500g"
    
    # For Surface couriers (more complex structure) - EXACT LOGIC
    if weight_kg <= 0.5:
        return rates['0-500'], "Base rate (0-500g)"
    elif weight_kg <= 2.0:
        # Between 0.5kg and 2kg - EXACT ROUNDING
        additional_slabs = ((weight_grams - 500) / 500)
        if additional_slabs != int(additional_slabs):
            additional_slabs = int(additional_slabs) + 1
        else:
            additional_slabs = int(additional_slabs)
        cost = rates['0-500'] + (additional_slabs * rates['add_500'])
        return cost, f"0-2kg: Base + {additional_slabs} x 500g"
    elif weight_kg <= 5.0:
        # Between 2kg and 5kg - EXACT ROUNDING
        additional_kg = weight_kg - 2.0
        if additional_kg != int(additional_kg):
            additional_kg = int(additional_kg) + 1
        else:
            additional_kg = int(additional_kg)
        cost = rates['2kg'] + (additional_kg * rates['add_1kg_2-5'])
        return cost, f"2-5kg: 2kg base + {additional_kg} x 1kg"
    elif weight_kg <= 10.0:
        # Between 5kg and 10kg - EXACT ROUNDING
        additional_kg = weight_kg - 5.0
        if additional_kg != int(additional_kg):
            additional_kg = int(additional_kg) + 1
        else:
            additional_kg = int(additional_kg)
        cost = rates['5kg'] + (additional_kg * rates['add_1kg_5-10'])
        return cost, f"5-10kg: 5kg base + {additional_kg} x 1kg"
    else:
        # Above 10kg - EXACT ROUNDING
        additional_kg = weight_kg - 10.0
        if additional_kg != int(additional_kg):
            additional_kg = int(additional_kg) + 1
        else:
            additional_kg = int(additional_kg)
        cost = rates['10kg'] + (additional_kg * rates['add_1kg_10+'])
        return cost, f"10+kg: 10kg base + {additional_kg} x 1kg"

def calculate_b2b_cost(weight_kg, dest_zone, invoice_value=0):
    """Calculate B2B shipping cost (Safexpress logic)"""
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
    EXACT LOGIC - matches reference app
    
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
        
        # Determine origin
        origin_city = DEFAULT_ORIGIN_CITY
        origin_state = DEFAULT_ORIGIN_STATE
        
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
            
            # Chargeable weight = Max(dead, volumetric) - EXACT LOGIC
            chargeable_per_unit = max(dead_weight, vol_weight)
            total_weight = chargeable_per_unit * quantity
            
            # Calculate cost
            if customer_type == 'B2C':
                # Use B2C logic with zone determination
                zone = determine_zone(origin_city, dest_city, dest_state, origin_state)
                courier = customer.get('preferred_courier', DEFAULT_B2C_COURIER)
                if courier not in B2C_RATE_CARD:
                    courier = DEFAULT_B2C_COURIER
                
                cost, breakdown = calculate_freight_cost(total_weight, zone, courier)
                if cost is None:
                    cost = 0
                    breakdown = "Rate not found"
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
