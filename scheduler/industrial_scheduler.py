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

    # --- Two-Tiered Job Prioritization ---
    needed_jobs = []
    filler_jobs = []
    
    for comp, details in total_components.items():
        have = inventory_by_name.get(comp, 0)
        needed = details['needed']
        ratio = have / needed if needed > 0 else 1.0 
        
        job_info = {
            'name': comp, 
            'ratio': ratio, 
            'activity_id': details['activity_id'],
            'time_per_run': details['time_per_run']
        }
        
        if have < needed:
            needed_jobs.append(job_info)
        else:
            filler_jobs.append(job_info)

    # Sort both lists by completion ratio
    needed_jobs.sort(key=lambda x: x['ratio'])
    filler_jobs.sort(key=lambda x: x['ratio'])
    
    # --- Intelligent Job Recommendation ---
    buildable_mfg = []
    buildable_react = []
    blocked_jobs = []
    immediate_shopping_list = defaultdict(float)
    
    SECONDS_IN_A_DAY = 86400

    def recommend_jobs(job_list, is_filler=False):
        """Helper function to process a list of jobs and find buildable ones."""
        for job in job_list:
            # Stop if slots are full
            if job['activity_id'] == 1 and len(buildable_mfg) >= mfg_slots: continue
            if job['activity_id'] == 11 and len(buildable_react) >= react_slots: continue
            
            time_per_run = job.get('time_per_run', 0)
            runs_for_batch = 1
            if time_per_run > 0:
                runs_for_batch = max(1, round(SECONDS_IN_A_DAY / time_per_run))
            
            direct_materials = dep_calc.get_direct_materials_for_product_name(job['name'])
            is_blocked = False
            missing_raws_for_this_job = defaultdict(float)

            for mat, needed_per_run in direct_materials.items():
                needed_for_batch = needed_per_run * runs_for_batch
                have = inventory_by_name.get(mat, 0)

                if have < needed_for_batch:
                    if mat in dep_calc.raw_materials:
                        missing_raws_for_this_job[mat] += needed_for_batch - have
                    else:
                        is_blocked = True
                        break 
            
            job_details = {'name': job['name'], 'runs': runs_for_batch, 'is_filler': is_filler}
            
            if is_blocked:
                blocked_jobs.append(job_details)
            else:
                if job['activity_id'] == 1 and len(buildable_mfg) < mfg_slots:
                    buildable_mfg.append(job_details)
                    for item, qty in missing_raws_for_this_job.items():
                        immediate_shopping_list[item] += qty
                elif job['activity_id'] == 11 and len(buildable_react) < react_slots:
                    buildable_react.append(job_details)
                    for item, qty in missing_raws_for_this_job.items():
                        immediate_shopping_list[item] += qty

    # 1. Process CRITICAL jobs first
    recommend_jobs(needed_jobs)
    # 2. Process FILLER jobs only if slots are still empty
    recommend_jobs(filler_jobs, is_filler=True)

    # --- Fill remaining slots with blocked jobs for visibility ---
    unfilled_mfg = mfg_slots - len(buildable_mfg)
    unfilled_react = react_slots - len(buildable_react)
    recommended_blocked_mfg = [j for j in blocked_jobs if total_components[j['name']]['activity_id'] == 1][:unfilled_mfg]
    recommended_blocked_react = [j for j in blocked_jobs if total_components[j['name']]['activity_id'] == 11][:unfilled_react]

    # --- Display Actionable Plan ---
    print("\n" + "="*20 + " ACTION PLAN " + "="*20)
    
    print(f"\n--- Start These Jobs Now ({len(buildable_mfg)}/{mfg_slots} Mfg, {len(buildable_react)}/{react_slots} React) ---")
    if not buildable_mfg and not buildable_react:
        print("  - No jobs are ready to start. Check shopping list and blocked jobs.")
    
    for job in buildable_mfg:
        tag = "(Filler)" if job['is_filler'] else ""
        print(f"  [Mfg] Start {job['runs']} run(s) of: {job['name']} {tag}")
    for job in buildable_react:
        tag = "(Filler)" if job['is_filler'] else ""
        print(f"  [React] Start {job['runs']} run(s) of: {job['name']} {tag}")

    if recommended_blocked_mfg or recommended_blocked_react:
        print(f"\n--- Blocked Jobs (Prepare for These Next) ---")
        for job in recommended_blocked_mfg:
            print(f"  [Mfg] BLOCKED: {job['name']} (Waiting for components)")
        for job in recommended_blocked_react:
            print(f"  [React] BLOCKED: {job['name']} (Waiting for components)")

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
