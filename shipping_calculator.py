# ============================================================================
# SHIPPING CALCULATOR MODULE - WITH B2B CASE PACK SUPPORT
# Save this as: shipping_calculator.py
# ============================================================================

"""
COMPLETE SHIPPING CALCULATOR WITH:
- B2C: Unit-based (dead weight, volumetric weight)
- B2B: Case-based (units per case, weight per case)
- Exact logic from reference app
"""

import pandas as pd
import math

# ============================================================================
# CONSTANTS
# ============================================================================

DEFAULT_ORIGIN_CITY = "MUMBAI"
DEFAULT_ORIGIN_STATE = "MAHARASHTRA"
ORIGIN_B2B_ZONE = "West-2"

SPECIAL_ZONES = ['Jammu and Kashmir', 'Himachal Pradesh', 'Kerala', 
                 'Andaman', 'Lakshadweep', 'Leh', 'Ladakh',
                 'Arunachal Pradesh', 'Assam', 'Manipur', 'Meghalaya', 
                 'Mizoram', 'Nagaland', 'Tripura', 'Sikkim',
                 'J&K', 'HP', 'KL', 'AN', 'LD', 'AR', 'AS', 'MN', 'ML', 'MZ', 'NL', 'TR', 'SK']

# B2B Constants
B2B_MIN_WEIGHT = 15  # Minimum chargeable weight for B2B
B2B_MIN_FREIGHT = 400
LOOSE_CASE_4KG = 4.0  # For loose B2C units in B2B shipment
LOOSE_CASE_8KG = 8.0  # For loose B2C units in B2B shipment

# ============================================================================
# RATE CARDS
# ============================================================================

B2C_RATE_CARD = {
    'Bluedart Surface': {
        'Local': {'0-500': 30.0, 'add_500': 24.0, '2kg': 96.0, 'add_1kg_2-5': 46.0, '5kg': 227.0, 'add_1kg_5-10': 45.0, '10kg': 449.0, 'add_1kg_10+': 44.0},
        'Within State': {'0-500': 36.0, 'add_500': 26.0, '2kg': 104.0, 'add_1kg_2-5': 49.0, '5kg': 250.0, 'add_1kg_5-10': 47.2, '10kg': 477.0, 'add_1kg_10+': 47.0},
        'Metro to Metro': {'0-500': 42.0, 'add_500': 33.0, '2kg': 134.0, 'add_1kg_2-5': 63.0, '5kg': 312.0, 'add_1kg_5-10': 61.0, '10kg': 617.0, 'add_1kg_10+': 61.0},
        'Rest of India': {'0-500': 47.0, 'add_500': 38.0, '2kg': 153.0, 'add_1kg_2-5': 72.0, '5kg': 355.0, 'add_1kg_5-10': 69.0, '10kg': 700.0, 'add_1kg_10+': 69.0},
        'Special Zone': {'0-500': 56.0, 'add_500': 50.0, '2kg': 202.0, 'add_1kg_2-5': 95.0, '5kg': 469.0, 'add_1kg_5-10': 92.0, '10kg': 924.0, 'add_1kg_10+': 91.0},
    },
    'Delhivery Surface': {
        'Local': {'0-500': 21.0, 'add_500': 17.0, '2kg': 71.0, 'add_1kg_2-5': 27.0, '5kg': 145.0, 'add_1kg_5-10': 23.0, '10kg': 238.0, 'add_1kg_10+': 14.0},
        'Within State': {'0-500': 25.0, 'add_500': 21.0, '2kg': 83.0, 'add_1kg_2-5': 32.0, '5kg': 150.0, 'add_1kg_5-10': 24.0, '10kg': 260.0, 'add_1kg_10+': 17.0},
        'Metro to Metro': {'0-500': 31.0, 'add_500': 24.0, '2kg': 90.0, 'add_1kg_2-5': 35.0, '5kg': 178.0, 'add_1kg_5-10': 24.0, '10kg': 281.0, 'add_1kg_10+': 17.0},
        'Rest of India': {'0-500': 34.0, 'add_500': 23.0, '2kg': 97.0, 'add_1kg_2-5': 37.0, '5kg': 199.0, 'add_1kg_5-10': 25.0, '10kg': 299.0, 'add_1kg_10+': 18.0},
        'Special Zone': {'0-500': 39.0, 'add_500': 25.0, '2kg': 109.0, 'add_1kg_2-5': 39.0, '5kg': 239.0, 'add_1kg_5-10': 35.0, '10kg': 387.0, 'add_1kg_10+': 22.0},
    }
}

B2B_BASE_RATES = {
    'West-2 to North-1': 8.64, 'West-2 to North-2': 10.8, 'West-2 to East': 10.8,
    'West-2 to North-East': 16.2, 'West-2 to West-1': 6.48, 'West-2 to West-2': 6.48,
    'West-2 to South-1': 7.56, 'West-2 to South-2': 6.48, 'West-2 to Central': 7.56
}

B2B_ZONE_MAP = {
    'North-1': ['DELHI', 'UTTAR PRADESH', 'HARYANA', 'RAJASTHAN', 'UP', 'DL', 'HR', 'RJ'],
    'North-2': ['CHANDIGARH', 'PUNJAB', 'HIMACHAL PRADESH', 'UTTARAKHAND', 'JAMMU', 'KASHMIR', 'LADAKH', 'PB', 'HP', 'UK', 'JK', 'J&K'],
    'East': ['WEST BENGAL', 'ODISHA', 'BIHAR', 'JHARKHAND', 'CHHATTISGARH', 'WB', 'OR', 'BR', 'JH', 'CG'],
    'North-East': ['ASSAM', 'MEGHALAYA', 'TRIPURA', 'ARUNACHAL PRADESH', 'MIZORAM', 'MANIPUR', 'NAGALAND', 'SIKKIM'],
    'West-1': ['GUJARAT', 'DAMAN', 'DIU', 'DADRA', 'GJ', 'DN', 'DD'],
    'West-2': ['MAHARASHTRA', 'GOA', 'MH', 'GA'],
    'South-1': ['ANDHRA PRADESH', 'TELANGANA', 'KARNATAKA', 'TAMIL NADU', 'TAMILNADU', 'PUDUCHERRY', 'AP', 'TG', 'KA', 'TN', 'PY'],
    'South-2': ['KERALA', 'KL'],
    'Central': ['MADHYA PRADESH', 'MP']
}

B2B_DOCKET_CHARGE = 100
B2B_FOV_RATE = 0.001
B2B_FOV_MIN = 100
B2B_FSC_RATE = 0.20

# ============================================================================
# ZONE DETERMINATION
# ============================================================================

def determine_zone(origin_city, dest_city, dest_state, origin_state=None):
    """Determine B2C shipping zone - EXACT LOGIC FROM REFERENCE"""
    origin_city = str(origin_city).strip().title() if pd.notna(origin_city) else ""
    dest_city = str(dest_city).strip().title() if pd.notna(dest_city) else ""
    dest_state = str(dest_state).strip().upper() if pd.notna(dest_state) else ""
    origin_state = str(origin_state).strip().upper() if pd.notna(origin_state) and origin_state else "MAHARASHTRA"
    
    state_mapping = {
        'MH': 'MAHARASHTRA', 'DL': 'DELHI', 'KA': 'KARNATAKA', 'TN': 'TAMIL NADU', 'TAMILNADU': 'TAMIL NADU',
        'WB': 'WEST BENGAL', 'GJ': 'GUJARAT', 'UP': 'UTTAR PRADESH', 'RJ': 'RAJASTHAN', 'HR': 'HARYANA',
        'PB': 'PUNJAB', 'AP': 'ANDHRA PRADESH', 'TG': 'TELANGANA', 'KL': 'KERALA', 'OR': 'ODISHA',
        'BR': 'BIHAR', 'JH': 'JHARKHAND', 'CG': 'CHHATTISGARH', 'MP': 'MADHYA PRADESH', 'AS': 'ASSAM',
        'HP': 'HIMACHAL PRADESH', 'J&K': 'JAMMU AND KASHMIR', 'JK': 'JAMMU AND KASHMIR', 'UT': 'UTTARAKHAND'
    }
    
    for code, full_name in state_mapping.items():
        if code in origin_state:
            origin_state = full_name
            break
    for code, full_name in state_mapping.items():
        if code in dest_state:
            dest_state = full_name
            break
    
    special_zone_states = ['JAMMU AND KASHMIR', 'HIMACHAL PRADESH', 'KERALA', 'ANDAMAN', 'LAKSHADWEEP',
                           'ARUNACHAL PRADESH', 'ASSAM', 'MANIPUR', 'MEGHALAYA', 'MIZORAM', 'NAGALAND', 'TRIPURA', 'SIKKIM']
    special_zone_keywords = ['ANDAMAN', 'LAKSHADWEEP', 'LEH', 'LADAKH']
    
    for sz in special_zone_states:
        if sz in dest_state:
            return 'Special Zone'
    for kw in special_zone_keywords:
        if kw in dest_state.upper() or kw in dest_city.upper():
            return 'Special Zone'
    
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
        if any(c in origin_city.upper() for c in cities) and any(c in dest_city.upper() for c in cities):
            return 'Local'
    
    metro_cities = ['MUMBAI', 'NAVI MUMBAI', 'DELHI', 'NEW DELHI', 'BANGALORE', 'BENGALURU', 'CHENNAI', 'KOLKATA', 'HYDERABAD', 'PUNE']
    origin_metro = any(m in origin_city.upper() for m in metro_cities)
    dest_metro = any(m in dest_city.upper() for m in metro_cities)
    
    if origin_metro and dest_metro:
        same_metro = False
        for metro, cities in local_city_groups.items():
            if any(c in origin_city.upper() for c in cities) and any(c in dest_city.upper() for c in cities):
                same_metro = True
                break
        if not same_metro:
            return 'Metro to Metro'
    
    if origin_state == dest_state:
        return 'Within State'
    
    return 'Rest of India'

def determine_b2b_zone(dest_state):
    """Determine B2B zone for Safexpress"""
    dest_state_upper = str(dest_state).strip().upper()
    
    state_mapping = {'MH': 'MAHARASHTRA', 'DL': 'DELHI', 'KA': 'KARNATAKA', 'TN': 'TAMIL NADU', 'TAMILNADU': 'TAMIL NADU'}
    for code, full_name in state_mapping.items():
        if code in dest_state_upper:
            dest_state_upper = full_name
            break
    
    for zone, states in B2B_ZONE_MAP.items():
        for state in states:
            if state in dest_state_upper:
                return zone
    return 'Central'

# ============================================================================
# COST CALCULATION
# ============================================================================

def calculate_freight_cost(weight_kg, zone, courier):
    """Calculate B2C freight cost - EXACT ROUNDING LOGIC"""
    if courier not in B2C_RATE_CARD or zone not in B2C_RATE_CARD[courier]:
        return 0, "Rate not found"
    
    rates = B2C_RATE_CARD[courier][zone]
    weight_grams = weight_kg * 1000
    
    if 'Air' in courier:
        if weight_grams <= 500:
            return rates['0-500'], "Base (0-500g)"
        additional_slabs = (weight_grams - 500) / 500
        if additional_slabs != int(additional_slabs):
            additional_slabs = int(additional_slabs) + 1
        else:
            additional_slabs = int(additional_slabs)
        return rates['0-500'] + (additional_slabs * rates['add_500']), f"Base + {additional_slabs}×500g"
    
    if weight_kg <= 0.5:
        return rates['0-500'], "Base (0-500g)"
    elif weight_kg <= 2.0:
        additional_slabs = (weight_grams - 500) / 500
        if additional_slabs != int(additional_slabs):
            additional_slabs = int(additional_slabs) + 1
        else:
            additional_slabs = int(additional_slabs)
        return rates['0-500'] + (additional_slabs * rates['add_500']), f"Base + {additional_slabs}×500g"
    elif weight_kg <= 5.0:
        additional_kg = weight_kg - 2.0
        if additional_kg != int(additional_kg):
            additional_kg = int(additional_kg) + 1
        else:
            additional_kg = int(additional_kg)
        return rates['2kg'] + (additional_kg * rates['add_1kg_2-5']), f"2kg + {additional_kg}×1kg"
    elif weight_kg <= 10.0:
        additional_kg = weight_kg - 5.0
        if additional_kg != int(additional_kg):
            additional_kg = int(additional_kg) + 1
        else:
            additional_kg = int(additional_kg)
        return rates['5kg'] + (additional_kg * rates['add_1kg_5-10']), f"5kg + {additional_kg}×1kg"
    else:
        additional_kg = weight_kg - 10.0
        if additional_kg != int(additional_kg):
            additional_kg = int(additional_kg) + 1
        else:
            additional_kg = int(additional_kg)
        return rates['10kg'] + (additional_kg * rates['add_1kg_10+']), f"10kg + {additional_kg}×1kg"

def calculate_b2b_cost(weight_kg, dest_zone, invoice_value=0):
    """Calculate B2B cost with Safexpress logic"""
    zone_key = f"{ORIGIN_B2B_ZONE} to {dest_zone}"
    base_rate = B2B_BASE_RATES.get(zone_key, 8.64)
    
    chargeable_weight = max(weight_kg, B2B_MIN_WEIGHT)
    base_freight = max(chargeable_weight * base_rate, B2B_MIN_FREIGHT)
    fsc = base_freight * B2B_FSC_RATE
    fov = max(invoice_value * B2B_FOV_RATE, B2B_FOV_MIN)
    
    total = base_freight + fsc + fov + B2B_DOCKET_CHARGE
    
    return total, {
        'base_freight': base_freight,
        'fsc': fsc,
        'fov': fov,
        'docket': B2B_DOCKET_CHARGE,
        'total': total,
        'zone': zone_key
    }

# ============================================================================
# MAIN CALCULATION - WITH B2B CASE PACK SUPPORT
# ============================================================================

def calculate_invoice_shipping_costs(invoices, item_master, customers):
    """
    Calculate shipping with B2B CASE PACK support
    
    Item types:
    - B2C: Uses dead_weight_kg, volumetric_weight_kg
    - B2B: Uses case_pack_qty, case_weight_kg
    """
    results = {}
    invoice_ids = list(set(inv.get('invoice_id') or inv.get('invoice_number') for inv in invoices))
    
    for inv_id in invoice_ids:
        invoice_items = [inv for inv in invoices if inv.get('invoice_id') == inv_id or inv.get('invoice_number') == inv_id]
        if not invoice_items:
            continue
        
        customer_name = invoice_items[0].get('customer_name', '')
        customer = customers.get(customer_name, {})
        customer_type = customer.get('type', 'B2C')
        is_marketplace = customer.get('is_marketplace', False)
        
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
        
        dest_city = invoice_items[0].get('dest_city', '')
        dest_state = invoice_items[0].get('dest_state', '')
        total_invoice_value = sum(item.get('item_total', 0) for item in invoice_items)
        
        line_calculations = []
        total_shipping = 0
        
        # For B2B customers with mixed items
        total_case_weight = 0
        total_loose_volumetric = 0
        
        for item in invoice_items:
            sku = item.get('sku', '')
            quantity = item.get('quantity', 1)
            product = item_master.get(sku, {})
            item_type = product.get('item_type', 'B2C')
            
            if item_type == 'B2B':
                # B2B Case Pack Logic
                case_pack_qty = product.get('case_pack_qty', 75)
                case_weight = product.get('case_weight_kg', 15.0)
                num_cases = math.ceil(quantity / case_pack_qty)
                total_weight = num_cases * case_weight
                
                if customer_type == 'B2B':
                    total_case_weight += total_weight
                
                line_calculations.append({
                    'sku': sku,
                    'item_name': item.get('item_name', ''),
                    'quantity': quantity,
                    'item_type': 'B2B',
                    'case_pack_qty': case_pack_qty,
                    'case_weight': case_weight,
                    'num_cases': num_cases,
                    'total_weight': total_weight,
                    'cost': 0,  # Calculated at invoice level for B2B
                    'breakdown': f"{quantity} units = {num_cases} cases × {case_weight}kg"
                })
            
            else:  # B2C
                dead_weight = product.get('dead_weight_kg', 0.5)
                vol_weight = product.get('volumetric_weight_kg', 0.5)
                chargeable_per_unit = max(dead_weight, vol_weight)
                total_weight = chargeable_per_unit * quantity
                
                if customer_type == 'B2B':
                    # B2C items in B2B shipment go into loose cases
                    total_loose_volumetric += vol_weight * quantity
                else:
                    # Pure B2C shipment
                    zone = determine_zone(DEFAULT_ORIGIN_CITY, dest_city, dest_state)
                    cost, breakdown = calculate_freight_cost(total_weight, zone, 'Delhivery Surface')
                    total_shipping += cost
                
                line_calculations.append({
                    'sku': sku,
                    'item_name': item.get('item_name', ''),
                    'quantity': quantity,
                    'item_type': 'B2C',
                    'dead_weight': dead_weight,
                    'vol_weight': vol_weight,
                    'chargeable_weight': chargeable_per_unit,
                    'total_weight': total_weight,
                    'zone': zone if customer_type == 'B2C' else 'N/A',
                    'cost': cost if customer_type == 'B2C' else 0,
                    'breakdown': breakdown if customer_type == 'B2C' else 'Packed in loose case'
                })
        
        # For B2B customers, calculate total shipping
        if customer_type == 'B2B':
            # Handle loose B2C units in B2B shipment
            loose_case_weight = 0
            if total_loose_volumetric > 0:
                if total_loose_volumetric <= LOOSE_CASE_4KG:
                    loose_case_weight = LOOSE_CASE_4KG
                elif total_loose_volumetric <= LOOSE_CASE_8KG:
                    loose_case_weight = LOOSE_CASE_8KG
                else:
                    num_loose_cases = math.ceil(total_loose_volumetric / LOOSE_CASE_8KG)
                    loose_case_weight = num_loose_cases * LOOSE_CASE_8KG
            
            # Total B2B weight
            total_b2b_weight = total_case_weight + loose_case_weight
            
            # Calculate B2B shipping
            dest_zone = determine_b2b_zone(dest_state)
            cost, breakdown = calculate_b2b_cost(total_b2b_weight, dest_zone, total_invoice_value)
            total_shipping = cost
            
            # Update line items with B2B info
            for line in line_calculations:
                line['b2b_total_weight'] = total_b2b_weight
                line['b2b_breakdown'] = breakdown
        
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
