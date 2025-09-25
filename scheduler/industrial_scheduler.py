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

    # --- Phase 1: Initialization & Authentication ---
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
    
    # --- Phase 2: Calculation & Analysis ---
    print("\nCalculating total requirements...")
    total_raw_mats, total_components, final_prod_mats = dep_calc.get_total_requirements(target_product, target_quantity)

    print("Fetching current inventory...")
    inventory_by_id = esi.get_inventory()
    inventory_by_name = {sde.get_type_name(tid): qty for tid, qty in inventory_by_id.items()}

    # --- Deficit Calculation ---
    component_deficits = defaultdict(float)
    for comp, needed in total_components.items():
        have = inventory_by_name.get(comp, 0)
        if have < needed:
            component_deficits[comp] = needed - have

    # --- Job Prioritization ---
    job_priorities = []
    for comp, needed in total_components.items():
        have = inventory_by_name.get(comp, 0)
        # Ratio of completion. Lower is higher priority.
        ratio = have / needed if needed > 0 else 1.0 
        job_priorities.append({'name': comp, 'ratio': ratio})
    
    # Sort jobs by completion ratio, lowest first
    job_priorities.sort(key=lambda x: x['ratio'])
    
    # --- Determine Case 1 vs Case 2 ---
    can_build_final_product = True
    print("\n--- Pre-flight Check ---")
    for mat, needed_per_run in final_prod_mats.items():
        needed_total = needed_per_run * target_quantity
        have = inventory_by_name.get(mat, 0)
        if have < needed_total:
            can_build_final_product = False
            print(f"[-] Missing material for {target_product}: Need {math.ceil(needed_total)} {mat}, Have {have}.")
    
    if can_build_final_product:
        print(f"[+] All direct materials for {target_quantity}x {target_product} are available.")
    
    # --- Display Actionable Plan ---
    print("\n" + "="*20 + " ACTION PLAN " + "="*20)
    
    if can_build_final_product:
        # --- CASE 1: Enough components for final runs ---
        print(f"Start Manufacturing: {target_quantity}x {target_product}")
        print("\nFill unused production slots with the following components (highest priority first):")
        
        # Filter out the final product itself from the component list
        priority_components = [job for job in job_priorities if job['name'] != target_product]
        
        if not priority_components:
            print("  - All components are already built. Nothing to do.")
        else:
            for job in priority_components[:10]: # Show top 10 priorities
                print(f"  - Build {job['name']} (Completion: {job['ratio']:.2%})")

    else:
        # --- CASE 2: Not enough components for final runs ---
        print("Cannot start final assembly. Focus on building missing components.")
        print("Build the following (highest priority first):")
        
        # We only need to show components we actually have a deficit in
        priority_deficits = [job for job in job_priorities if job['name'] in component_deficits]
        
        if not priority_deficits:
             print("  - No component deficits found, but pre-flight check failed. Check raw materials.")
        else:
            for job in priority_deficits[:10]: # Show top 10 priorities
                print(f"  - Build {job['name']} (Completion: {job['ratio']:.2%})")

    print("\n" + "="*53)


if __name__ == '__main__':
    main()

