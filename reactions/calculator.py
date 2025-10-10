import pandas as pd
import requests
import time
import os
import json

# --- CONFIGURATION ---
SDE_FOLDER = '../static_data'
OUTPUT_CSV = 'reaction_profits.csv'
JITA_REGION_ID = '10000002'  # The region ID for The Forge, which contains Jita
CACHE_FILE = 'price_cache.json'
CACHE_EXPIRATION_HOURS = 1  # How long to keep price cache before refreshing

# Fees - adjust these if your skills/standings are different
BROKER_FEE = 0.035  # 3.5%
SALES_TAX = 0.025  # 2.5%

# --- END OF CONFIGURATION ---


def get_market_prices():
    """
    Fetches market prices from ESI. Uses a cache to avoid excessive API calls.
    """
    # Check if cache exists, is recent, and is not empty
    if os.path.exists(CACHE_FILE):
        cache_mod_time = os.path.getmtime(CACHE_FILE)
        if (time.time() - cache_mod_time) / 3600 < CACHE_EXPIRATION_HOURS:
            try:
                print("Loading prices from cache...")
                with open(CACHE_FILE, 'r') as f:
                    cached_data = json.load(f)
                    # FIX: Only return cached data if it's not empty
                    if cached_data:
                        print("Cache successfully loaded.")
                        return cached_data
                    else:
                        print("Cache file is empty. Fetching new data.")
            except (json.JSONDecodeError, FileNotFoundError):
                print("Cache file is corrupted or missing. Fetching new data.")

    print("Fetching live market prices from ESI (this may take a few minutes)...")
    prices = {}
    # Corrected URL to use region_id
    url = f"https://esi.evetech.net/latest/markets/{JITA_REGION_ID}/orders/"
    
    # We need prices for all items, so we fetch all pages.
    page = 1
    # Add a User-Agent header, which is good practice for ESI
    headers = {'User-Agent': 'EVEProfitabilityCalculator/1.0'}

    while True:
        try:
            params = {'order_type': 'all', 'page': page}
            # Pass the headers with the request
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status() # Raises an exception for bad status codes
            
            data = response.json()
            if not data:
                break # No more data, exit loop
            
            for order in data:
                # We only care about Jita IV Moon 4 (Caldari Navy Assembly Plant), stationID 60003760
                if order.get('location_id') != 60003760:
                    continue

                type_id = str(order['type_id'])
                if type_id not in prices:
                    prices[type_id] = {'buy': 0, 'sell': float('inf')}
                
                if order['is_buy_order']:
                    prices[type_id]['buy'] = max(prices[type_id]['buy'], order['price'])
                else:
                    prices[type_id]['sell'] = min(prices[type_id]['sell'], order['price'])

            # Show progress
            if page % 20 == 0:
                print(f"  ... fetched page {page}")

            page += 1
            time.sleep(0.1) # Be gentle with the API

        except requests.exceptions.RequestException as e:
            print(f"Error fetching page {page}: {e}")
            break
            
    # Clean up prices where sell might still be infinity
    for type_id in prices:
        if prices[type_id]['sell'] == float('inf'):
            prices[type_id]['sell'] = 0

    print(f"Fetched prices for {len(prices)} unique item types in Jita.")

    # FIX: Only save the cache if we actually fetched some price data
    if prices:
        print("Saving prices to cache...")
        with open(CACHE_FILE, 'w') as f:
            json.dump(prices, f)
    else:
        print("No prices fetched. Cache will not be updated.")

    return prices


def main():
    """Main function to load data, process, and save results."""
    print("--- Starting EVE Reaction Profitability Calculator ---")

    # 1. Load SDE files using pandas
    try:
        print("Loading SDE files...")
        inv_types = pd.read_csv(os.path.join(SDE_FOLDER, 'invTypes.csv'))
        industry_activity = pd.read_csv(os.path.join(SDE_FOLDER, 'industryActivity.csv'))
        activity_materials = pd.read_csv(os.path.join(SDE_FOLDER, 'industryActivityMaterials.csv'))
        activity_products = pd.read_csv(os.path.join(SDE_FOLDER, 'industryActivityProducts.csv'))
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please ensure the SDE files are in the correct directory.")
        return

    # 2. Filter for reactions
    # Activity ID for Reactions is 11
    all_reactions = industry_activity[industry_activity['activityID'] == 11]
    
    # NEW: Filter for Composite Reactions by name, excluding Boosters and Unrefined formulas
    # Merge with inv_types to get the reaction names for filtering
    reaction_details = pd.merge(all_reactions, inv_types[['typeID', 'typeName']], on='typeID')

    # Filter 1: Remove reactions with "Booster" in their name (case-insensitive)
    filtered_reactions_1 = reaction_details[~reaction_details['typeName'].str.contains("Booster", case=False, na=False)]
    
    # Filter 2: Remove reactions starting with "Unrefined"
    composite_reactions = filtered_reactions_1[~filtered_reactions_1['typeName'].str.startswith("Unrefined")]
    
    print(f"Found {len(composite_reactions)} composite reactions to process after filtering.")

    # 3. Create a TypeID -> TypeName mapping for easy lookups
    typeid_to_name = inv_types.set_index('typeID')['typeName'].to_dict()

    # 4. Get live market data
    market_prices = get_market_prices()

    # 5. Process each reaction
    print("Calculating profitability for each composite reaction...")
    results = []
    total_reactions = len(composite_reactions)
    for i, (_, reaction) in enumerate(composite_reactions.iterrows()):
        bp_type_id = reaction['typeID']
        
        # Skip if the blueprint name is not in our dictionary (unlikely, but safe)
        if bp_type_id not in typeid_to_name:
            continue
        
        reaction_name = typeid_to_name[bp_type_id]
        
        # --- Get Input Materials ---
        inputs = activity_materials[activity_materials['typeID'] == bp_type_id]
        input_cost_jita_sell = 0 # Cost if you buy instantly
        input_cost_jita_buy = 0  # Cost if you place buy orders
        input_details = []

        for _, mat in inputs.iterrows():
            mat_id = str(mat['materialTypeID'])
            qty = mat['quantity']
            mat_name = typeid_to_name.get(mat['materialTypeID'], 'Unknown Material')
            
            price_info = market_prices.get(mat_id, {'buy': 0, 'sell': 0})
            
            input_cost_jita_sell += price_info.get('sell', 0) * qty
            input_cost_jita_buy += price_info.get('buy', 0) * qty
            input_details.append(f"{mat_name} x{qty}")

        # --- Get Output Products ---
        products = activity_products[activity_products['typeID'] == bp_type_id]
        output_revenue_jita_buy = 0  # Revenue if you sell instantly
        output_revenue_jita_sell = 0 # Revenue if you place sell orders
        product_details = []

        for _, prod in products.iterrows():
            prod_id = str(prod['productTypeID'])
            qty = prod['quantity']
            prod_name = typeid_to_name.get(prod['productTypeID'], 'Unknown Product')
            
            price_info = market_prices.get(prod_id, {'buy': 0, 'sell': 0})
            
            output_revenue_jita_buy += price_info.get('buy', 0) * qty
            output_revenue_jita_sell += price_info.get('sell', 0) * qty
            product_details.append(f"{prod_name} x{qty}")

        # --- Calculate Profits ---
        # Scenario 1: Buy inputs instantly (Jita Sell), sell outputs instantly (Jita Buy)
        gross_profit_1 = output_revenue_jita_buy - input_cost_jita_sell
        net_profit_1 = output_revenue_jita_buy * (1 - BROKER_FEE - SALES_TAX) - input_cost_jita_sell

        # Scenario 2: Place buy orders for inputs, place sell orders for outputs
        gross_profit_2 = output_revenue_jita_sell - input_cost_jita_buy
        net_profit_2 = output_revenue_jita_sell * (1 - BROKER_FEE - SALES_TAX) - input_cost_jita_buy
        
        # NEW: Calculate profit percentages (ROI)
        profit_percent_1 = (net_profit_1 / input_cost_jita_sell * 100) if input_cost_jita_sell > 0 else 0
        profit_percent_2 = (net_profit_2 / input_cost_jita_buy * 100) if input_cost_jita_buy > 0 else 0

        # FINAL: Calculate weekly profit projection
        net_profit_per_week = net_profit_2 * 120

        # Avoid adding reactions with no market data
        if input_cost_jita_sell > 0 and output_revenue_jita_buy > 0:
            results.append({
                'Reaction Name': reaction_name,
                'Net Profit per Week': net_profit_per_week,
                'Net Profit (Instant Buy/Sell)': net_profit_1,
                'Profit % (Instant)': profit_percent_1,
                'Net Profit (Order-based)': net_profit_2,
                'Profit % (Order-based)': profit_percent_2,
                'Input Cost (Jita Sell)': input_cost_jita_sell,
                'Output Revenue (Jita Buy)': output_revenue_jita_buy,
                'Input Cost (Jita Buy)': input_cost_jita_buy,
                'Output Revenue (Jita Sell)': output_revenue_jita_sell,
                'Inputs': ", ".join(input_details),
                'Products': ", ".join(product_details),
            })
        
        if (i + 1) % 50 == 0:
            print(f"  ... processed {i+1}/{total_reactions} reactions")


    # 6. Sort and Save to CSV
    if not results:
        print("No profitable reactions found or market data was incomplete.")
        return

    print("Sorting results and saving to CSV...")
    results_df = pd.DataFrame(results)
    
    # Sort by the most optimistic profit scenario (order-based profit percentage)
    results_df_sorted = results_df.sort_values(by='Net Profit per Week', ascending=False)
    
    # Format columns for better readability
    for col in results_df_sorted.columns:
        if 'Cost' in col or 'Revenue' in col or col.startswith('Net Profit'):
            results_df_sorted[col] = results_df_sorted[col].apply(lambda x: f"{x:,.2f}")
        elif 'Profit %' in col:
            results_df_sorted[col] = results_df_sorted[col].apply(lambda x: f"{x:.2f}%")

    results_df_sorted.to_csv(OUTPUT_CSV, index=False)
    
    print(f"--- Process complete. Results saved to {OUTPUT_CSV} ---")


if __name__ == "__main__":
    main()





