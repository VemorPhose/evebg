import pandas as pd
import math
from collections import deque

class IndustryCalculator:
    # Map activity IDs to human-readable names
    ACTIVITY_IDS = {
        1: 'Manufacturing',
        11: 'Reactions'
    }
    
    # Add items here to treat them as raw materials, even if a blueprint exists
    FORCE_RAW_MATERIALS = {
        'R.A.M.- Starship Tech', 'Oxygen Fuel Block', 'Hydrogen Fuel Block', 'Helium Fuel Block',
        'Nitrogen Fuel Block'
    }

    def __init__(self, data_path='./static_data'):
        """Load data from the EVE Online SDE files."""
        self.industry_activity = pd.read_csv(f'{data_path}/industryActivity.csv')
        self.activity_materials = pd.read_csv(f'{data_path}/industryActivityMaterials.csv')
        self.activity_products = pd.read_csv(f'{data_path}/industryActivityProducts.csv')
        self.inv_types = pd.read_csv(f'{data_path}/invTypes.csv')
        self.inv_types.set_index('typeID', inplace=True)

    def get_type_id(self, type_name):
        """Get typeID from typeName."""
        result = self.inv_types[self.inv_types['typeName'] == type_name]
        return result.index[0] if not result.empty else None

    def get_type_name(self, type_id):
        """Get typeName from typeID."""
        try:
            return self.inv_types.loc[type_id, 'typeName']
        except KeyError:
            return f"Unknown TypeID: {type_id}"

    def get_blueprint_for_product(self, product_type_id):
        """
        Find the blueprint/formula that produces a given product.
        Prioritizes manufacturing over reactions if both exist.
        """
        # Check manufacturing first, then reactions
        for activity_id in [1, 11]:
            blueprint = self.activity_products[
                (self.activity_products['productTypeID'] == product_type_id) & 
                (self.activity_products['activityID'] == activity_id)
            ]
            if not blueprint.empty:
                return blueprint.iloc[0]
        return None

    def get_materials(self, blueprint_type_id, activity_id):
        """Get materials required for a specific blueprint and activity."""
        return self.activity_materials[
            (self.activity_materials['typeID'] == blueprint_type_id) & 
            (self.activity_materials['activityID'] == activity_id)
        ]

    def get_production_time(self, blueprint_type_id, activity_id):
        """Get the production time for a specific blueprint and activity."""
        time_info = self.industry_activity[
            (self.industry_activity['typeID'] == blueprint_type_id) & 
            (self.industry_activity['activityID'] == activity_id)
        ]
        return time_info.iloc[0]['time'] if not time_info.empty else 0
        
    def calculate_production_chain(self, final_product_name, concurrent_runs=1):
        """Recursively calculate the production chain across different activities."""
        final_product_id = self.get_type_id(final_product_name)
        if not final_product_id:
            print(f"Error: Final product '{final_product_name}' not found.")
            return

        print(f"\nCalculating production chain for {concurrent_runs} concurrent run(s) of {final_product_name}...")

        raw_materials_needed = {}
        production_jobs = {}
        
        # Memoization to avoid reprocessing nodes
        processed_components = set()

        def process_component(product_id, required_quantity):
            product_name = self.get_type_name(product_id)

            # Base case: Item is in the forced raw list or has no blueprint
            blueprint_info = self.get_blueprint_for_product(product_id)
            if product_name in self.FORCE_RAW_MATERIALS or blueprint_info is None:
                raw_materials_needed[product_name] = raw_materials_needed.get(product_name, 0) + required_quantity
                return
            
            blueprint_id = blueprint_info['typeID']
            activity_id = blueprint_info['activityID']
            products_per_run = blueprint_info['quantity']
            
            job_name = self.get_type_name(blueprint_id)

            if job_name not in production_jobs:
                prod_time = self.get_production_time(blueprint_id, activity_id)
                production_jobs[job_name] = {
                    'total_required': 0, 'time': prod_time, 'products_per_run': products_per_run,
                    'activity_id': activity_id, 'blueprint_id': blueprint_id, 'children': []
                }
            
            production_jobs[job_name]['total_required'] += required_quantity
            
            if blueprint_id in processed_components:
                return

            materials = self.get_materials(blueprint_id, activity_id)
            for _, material in materials.iterrows():
                mat_id = material['materialTypeID']
                qty_per_run = material['quantity']
                production_jobs[job_name]['children'].append({'id': mat_id, 'qty_per_run': qty_per_run})
                total_material_needed = (required_quantity / products_per_run) * qty_per_run
                process_component(mat_id, total_material_needed)
            
            processed_components.add(blueprint_id)


        process_component(final_product_id, concurrent_runs)

        final_blueprint_info = self.get_blueprint_for_product(final_product_id)
        if not final_blueprint_info.empty:
            final_job_name = self.get_type_name(final_blueprint_info['typeID'])
        else:
            print(f"Could not find a blueprint for {final_product_name}")
            return
            
        for job, details in production_jobs.items():
            details['fractional_runs'] = details['total_required'] / details['products_per_run']
            details['runs_needed'] = math.ceil(details['fractional_runs'])
            details['ratio'] = 0

        production_jobs[final_job_name]['ratio'] = float(concurrent_runs)
        
        q = deque([production_jobs[final_job_name]['blueprint_id']])
        visited_for_ratio = {production_jobs[final_job_name]['blueprint_id']}
        while q:
            parent_bp_id = q.popleft()
            parent_job_name = self.get_type_name(parent_bp_id)
            parent_details = production_jobs[parent_job_name]

            if parent_details['time'] == 0: continue
            
            for child in parent_details.get('children', []):
                child_id = child['id']
                child_bp_info = self.get_blueprint_for_product(child_id)
                
                if child_bp_info is not None:
                    child_bp_id = child_bp_info['typeID']
                    child_job_name = self.get_type_name(child_bp_id)
                    
                    if child_job_name in production_jobs:
                        child_details = production_jobs[child_job_name]
                        
                        if child_details['time'] > 0:
                            child_supply_rate = child_details['products_per_run'] / child_details['time']
                            demand_rate_from_parent = (child['qty_per_run'] / parent_details['time']) * parent_details['ratio']
                            child_details['ratio'] += demand_rate_from_parent / child_supply_rate

                            if child_bp_id not in visited_for_ratio:
                                q.append(child_bp_id)
                                visited_for_ratio.add(child_bp_id)

        # --- Find best whole number ratio multiplier using squared error from ceiling ---
        ratios_to_optimize = [details['ratio'] for details in production_jobs.values() if details['ratio'] > 0]
        best_multiplier = 1
        if ratios_to_optimize:
            lowest_cost = float('inf')
            # Iterate from 1 to 10 to find the multiplier with the lowest cost
            for m in range(1, 11):
                cost = sum((math.ceil(r * m) - (r * m))**2 for r in ratios_to_optimize)
                if cost < lowest_cost:
                    lowest_cost = cost
                    best_multiplier = m
        
        for details in production_jobs.values():
            details['closest_whole_ratio'] = details['ratio'] * best_multiplier
            details['rounded_up_ratio'] = math.ceil(details['closest_whole_ratio'])

        # --- Display Results ---
        print("\n--- Raw Materials Required (Multibuy Format) ---")
        if not raw_materials_needed:
            print("None")
        else:
            for name, qty in sorted(raw_materials_needed.items()):
                print(f"{name} {math.ceil(qty)}")

        for activity_id, activity_name in self.ACTIVITY_IDS.items():
            jobs_in_activity = {k: v for k, v in production_jobs.items() if v['activity_id'] == activity_id}
            if not jobs_in_activity: continue

            print(f"\n--- {activity_name} Jobs (Optimal Multiplier: {best_multiplier}) ---")
            header = (f"{'Blueprint':<40} | {'Runs Needed':<12} | {'Fractional Runs':<18} | "
                      f"{'Job Ratio':<15} | {'Near Whole Ratio':<20} | {'Rounded Ratio':<15}")
            print(header)
            print("-" * len(header))

            sorted_jobs = sorted(jobs_in_activity.items(), key=lambda item: item[1]['ratio'], reverse=True)

            for job, details in sorted_jobs:
                 line = (f"{job:<40} | {details['runs_needed']:<12} | {details['fractional_runs']:<18.4f} | "
                         f"{details['ratio']:<15.4f} | {details['closest_whole_ratio']:<20.4f} | {details['rounded_up_ratio']:<15}")
                 print(line)

if __name__ == '__main__':
    calculator = IndustryCalculator(data_path='./static_data')
    product_name = input("Enter the name of the final product (e.g., Eris, Dominix): ")
    
    concurrent_runs_input = input("Enter number of concurrent final product runs [Default: 1]: ")
    try:
        runs = int(concurrent_runs_input) if concurrent_runs_input else 1
    except ValueError:
        print("Invalid input. Using 1 run.")
        runs = 1
        
    calculator.calculate_production_chain(product_name, runs)
