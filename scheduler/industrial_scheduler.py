from sde_loader import SdeLoader
from esi_manager import EsiManager
from dependency_calculator import DependencyCalculator
import math
from collections import defaultdict

def main():
    """
    Main execution function for the industrial scheduler.
    """
    print("Initializing EVE Online Industrial Scheduler...")
    sde = SdeLoader()
    esi = EsiManager()
    
    if not esi.authenticate():
        print("Authentication failed. Exiting.")
        return

    dep_calc = DependencyCalculator(sde)

    # --- User Input ---
    target_product = input("\nEnter the final product you want to build (e.g., Eris): ")
    try:
        target_quantity = int(input(f"How many {target_product} do you want to build? [Default: 1]: ") or 1)
    except ValueError:
        print("Invalid quantity. Defaulting to 1.")
        target_quantity = 1
    
    try:
        mfg_slots = int(input(f"Enter available manufacturing slots [Default: 9]: ") or 9)
        react_slots = int(input(f"Enter available reaction slots [Default: 5]: ") or 5)
    except ValueError:
        print("Invalid slot count. Using defaults.")
        mfg_slots, react_slots = 9, 5

    # --- Calculation & Analysis ---
    print("\nCalculating total requirements...")
    total_raw_mats, total_components = dep_calc.get_total_requirements(target_product, target_quantity)

    print("Fetching current inventory...")
    inventory_by_id = esi.get_inventory()
    inventory_by_name = {sde.get_type_name(tid): qty for tid, qty in inventory_by_id.items()}

    # --- Calculate TOTAL Project Shopping List ---
    total_project_shopping_list = defaultdict(float)
    for mat, needed in total_raw_mats.items():
        have = inventory_by_name.get(mat, 0)
        if have < needed:
            total_project_shopping_list[mat] = needed - have

    # --- Job Prioritization ---
    job_priorities = []
    for comp, details in total_components.items():
        have = inventory_by_name.get(comp, 0)
        needed = details['needed']
        ratio = have / needed if needed > 0 else 1.0 
        job_priorities.append({'name': comp, 'ratio': ratio, 'activity_id': details['activity_id']})
    
    job_priorities.sort(key=lambda x: x['ratio'])
    
    # --- Intelligent Job Recommendation ---
    recommended_mfg = []
    recommended_react = []
    immediate_shopping_list = defaultdict(float)

    for job in job_priorities:
        # Check if we have room for this job type
        if job['activity_id'] == 1 and len(recommended_mfg) >= mfg_slots:
            continue
        if job['activity_id'] == 11 and len(recommended_react) >= react_slots:
            continue
        
        direct_materials = dep_calc.get_direct_materials_for_product_name(job['name'])
        is_buildable = True
        missing_raws_for_this_job = defaultdict(float)

        for mat, needed_per in direct_materials.items():
            have = inventory_by_name.get(mat, 0)
            if have < needed_per:
                # Is the missing material a raw mineral/item or a sub-component?
                if mat in dep_calc.raw_materials:
                    missing_raws_for_this_job[mat] += needed_per - have
                else: # Missing a sub-component, can't build this job right now.
                    is_buildable = False
                    break 
        
        if is_buildable:
            if job['activity_id'] == 1:
                recommended_mfg.append(job['name'])
            else:
                recommended_react.append(job['name'])
            
            # Add any missing raws for this buildable job to the immediate shopping list
            for item, qty in missing_raws_for_this_job.items():
                immediate_shopping_list[item] += qty

    # --- Display Actionable Plan ---
    print("\n" + "="*20 + " ACTION PLAN " + "="*20)
    
    print(f"\n--- Recommended Manufacturing Jobs ({len(recommended_mfg)}/{mfg_slots} slots) ---")
    if not recommended_mfg:
        print("  - None")
    else:
        for job_name in recommended_mfg:
            print(f"  - Start 1 run of: {job_name}")

    print(f"\n--- Recommended Reaction Jobs ({len(recommended_react)}/{react_slots} slots) ---")
    if not recommended_react:
        print("  - None")
    else:
        for job_name in recommended_react:
            print(f"  - Start 1 run of: {job_name}")

    if immediate_shopping_list:
        print("\n--- Shopping List (for IMMEDIATE jobs) ---")
        for item, qty in sorted(immediate_shopping_list.items()):
            print(f"{item} {math.ceil(qty)}")

    if total_project_shopping_list:
        print("\n--- TOTAL Project Shopping List ---")
        for item, qty in sorted(total_project_shopping_list.items()):
            print(f"{item} {math.ceil(qty)}")
    else:
        print("\n--- TOTAL Project Shopping List ---")
        print("  - All required raw materials are already in your structures.")


    print("\n" + "="*53)

if __name__ == '__main__':
    main()

