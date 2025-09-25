from sde_loader import SdeLoader
from esi_manager import EsiManager
from dependency_calculator import DependencyCalculator

def main():
    """
    Main execution function for the industrial scheduler.
    """
    print("Initializing EVE Online Industrial Scheduler...")

    # --- Phase 1: Initialization ---
    sde = SdeLoader()
    esi = EsiManager()
    dep_calc = DependencyCalculator(sde)

    # --- User Input ---
    target_product = input("Enter the final product you want to build (e.g., Eris): ")
    try:
        target_quantity = int(input(f"How many {target_product} do you want to build? [Default: 1]: ") or 1)
    except ValueError:
        print("Invalid quantity. Defaulting to 1.")
        target_quantity = 1
    
    # --- Phase 1: Calculate Total Needs & Get Current Inventory ---
    # This calculates the ideal "bill of materials" as if we had nothing.
    total_raw_mats, total_components = dep_calc.get_total_requirements(target_product, target_quantity)

    # This gets our current inventory from the specified structure.
    current_inventory = esi.get_inventory() # Currently returns sample data

    # --- Phase 2: Core Logic (To Be Implemented) ---
    print("\n--- Next Steps (Phase 2) ---")
    print("1. Implement full ESI OAuth2 authentication in EsiManager.")
    print("2. Implement inventory fetching from the ESI API.")
    print("3. Calculate material/component deficits by comparing total needs with current inventory.")
    print("4. Implement the job prioritization and queuing logic based on your notes.")
    print("5. Display the final, actionable list of jobs to start.")
    
    # Example of what the data looks like at this stage:
    print("\n--- Example Data (End of Phase 1) ---")
    print("\nTotal Raw Materials Required:")
    for mat, qty in sorted(total_raw_mats.items()):
        print(f"  {mat}: {math.ceil(qty)}")
        
    print("\nTotal Intermediate Components to Build:")
    for comp, qty in sorted(total_components.items()):
        print(f"  {comp}: {math.ceil(qty)}")

if __name__ == '__main__':
    import math
    main()
