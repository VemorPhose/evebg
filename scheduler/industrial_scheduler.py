from sde_loader import SdeLoader
from esi_manager import EsiManager
from dependency_calculator import DependencyCalculator
import math
from collections import defaultdict

class IndustrialScheduler:
    def __init__(self):
        print("Initializing EVE Online Industrial Scheduler...")
        self.sde = SdeLoader()
        self.esi = EsiManager()
        self.dep_calc = DependencyCalculator(self.sde)

        self.inventory_by_name = {}
        self.mfg_slots = 0
        self.react_slots = 0
        
        self.recommended_jobs = []
        self.shopping_list = defaultdict(float)
        self.memoization = {} # To avoid re-calculating components

    def run(self):
        if not self.esi.authenticate():
            print("Authentication failed. Exiting.")
            return
        
        self._get_user_input()
        self._fetch_inventory()
        
        print("\nPlanning production chain...")
        self._plan_for_target()
        self._plan_filler_reactions()
        
        self._display_action_plan()

    def _get_user_input(self):
        self.target_product = input("\nEnter the final product you want to build (e.g., Eris): ")
        try:
            self.target_quantity = int(input(f"How many {self.target_product} do you want to build? [Default: 1]: ") or 1)
        except ValueError:
            print("Invalid quantity. Defaulting to 1.")
            self.target_quantity = 1
        
        try:
            self.mfg_slots = int(input(f"Enter available manufacturing slots [Default: 9]: ") or 9)
            self.react_slots = int(input(f"Enter available reaction slots [Default: 5]: ") or 5)
        except ValueError:
            print("Invalid slot count. Using defaults.")
            self.mfg_slots, self.react_slots = 9, 5

    def _fetch_inventory(self):
        print("Fetching current inventory...")
        inventory_by_id = self.esi.get_inventory()
        self.inventory_by_name = {self.sde.get_type_name(tid): qty for tid, qty in inventory_by_id.items()}

    def _plan_for_target(self):
        needed_for_target = self.dep_calc.get_direct_materials_for_product_name(self.target_product)
        # We start by "needing" the final product itself
        self._recursive_plan(self.target_product, self.target_quantity)

    def _recursive_plan(self, component_name, needed_qty):
        """
        Recursively checks if a component can be built and adds it to the recommendation list if so.
        Returns True if the component is available or can be built/bought, False otherwise.
        """
        if component_name in self.memoization:
            return self.memoization[component_name]

        have = self.inventory_by_name.get(component_name, 0)
        if have >= needed_qty:
            self.memoization[component_name] = True
            return True

        # If it's a raw material, we just need to buy it.
        if component_name in self.dep_calc.raw_materials:
            self.shopping_list[component_name] += needed_qty - have
            self.memoization[component_name] = True # Treat as "available" after buying
            return True

        # It's a buildable component and we need more.
        # Check if we have slots available for this type of job.
        activity_id = self.dep_calc.total_components.get(component_name, {}).get('activity_id')
        if not activity_id: return False # Should not happen if data is consistent

        current_mfg_jobs = sum(1 for job in self.recommended_jobs if job['activity_id'] == 1)
        current_react_jobs = sum(1 for job in self.recommended_jobs if job['activity_id'] == 11)

        if (activity_id == 1 and current_mfg_jobs >= self.mfg_slots) or \
           (activity_id == 11 and current_react_jobs >= self.react_slots):
            self.memoization[component_name] = False # No slots, can't build it now.
            return False

        # Check sub-components recursively
        sub_components_available = True
        direct_materials = self.dep_calc.get_direct_materials_for_product_name(component_name)

        for sub_comp, qty_per_run in direct_materials.items():
            if not self._recursive_plan(sub_comp, qty_per_run): # Assume we check for 1 run for simplicity
                sub_components_available = False
        
        # After checking all children, decide if we can queue this job.
        if sub_components_available:
            # All sub-components are either present or can be made/bought.
            # We can recommend this job.
            time_per_run = self.dep_calc.total_components.get(component_name, {}).get('time_per_run', 0)
            runs = max(1, round(86400 / time_per_run)) if time_per_run > 0 else 1

            job_info = {'name': component_name, 'runs': runs, 'activity_id': activity_id}
            self.recommended_jobs.append(job_info)
            
            # Update shopping list for this job's raw materials if needed
            for mat, needed_per in direct_materials.items():
                if mat in self.dep_calc.raw_materials:
                    needed_for_batch = needed_per * runs
                    have_mat = self.inventory_by_name.get(mat, 0)
                    if have_mat < needed_for_batch:
                        self.shopping_list[mat] += needed_for_batch - have_mat
            
            self.memoization[component_name] = True
            return True

        self.memoization[component_name] = False
        return False

    def _plan_filler_reactions(self):
        """If reaction slots are free, find simple reactions to run."""
        current_react_jobs = sum(1 for job in self.recommended_jobs if job['activity_id'] == 11)
        while current_react_jobs < self.react_slots:
            found_filler = False
            for reaction_name, details in self.dep_calc.total_components.items():
                if details['activity_id'] == 11 and reaction_name not in [j['name'] for j in self.recommended_jobs]:
                    inputs = self.dep_calc.get_direct_materials_for_product_name(reaction_name)
                    if all(mat in self.dep_calc.raw_materials for mat in inputs):
                        # This is a simple reaction, add it as a filler
                        time_per_run = details.get('time_per_run', 0)
                        runs = max(1, round(86400 / time_per_run)) if time_per_run > 0 else 1
                        job_info = {'name': reaction_name, 'runs': runs, 'activity_id': 11, 'is_filler': True}
                        self.recommended_jobs.append(job_info)
                        
                        # Add its materials to the shopping list
                        for mat, needed_per in inputs.items():
                            needed_for_batch = needed_per * runs
                            have_mat = self.inventory_by_name.get(mat, 0)
                            if have_mat < needed_for_batch:
                                self.shopping_list[mat] += needed_for_batch - have_mat

                        current_react_jobs += 1
                        found_filler = True
                        break # Move to the next slot
            if not found_filler:
                break # No more simple reactions to add

    def _display_action_plan(self):
        print("\n" + "="*20 + " ACTION PLAN " + "="*20)

        mfg_jobs = [j for j in self.recommended_jobs if j['activity_id'] == 1]
        react_jobs = [j for j in self.recommended_jobs if j['activity_id'] == 11]

        print(f"\n--- Recommended Manufacturing Jobs ({len(mfg_jobs)}/{self.mfg_slots} slots) ---")
        if not mfg_jobs: print("  - None")
        for job in mfg_jobs:
            print(f"  - Start {job['runs']} run(s) of: {job['name']}")

        print(f"\n--- Recommended Reaction Jobs ({len(react_jobs)}/{self.react_slots} slots) ---")
        if not react_jobs: print("  - None")
        for job in react_jobs:
            tag = "(Filler)" if job.get('is_filler') else ""
            print(f"  - Start {job['runs']} run(s) of: {job['name']} {tag}")

        if self.shopping_list:
            print("\n--- Shopping List ---")
            for item, qty in sorted(self.shopping_list.items()):
                print(f"{item} {math.ceil(qty)}")
        else:
            print("\n--- Shopping List ---")
            print("  - No items need to be purchased.")
            
        print("\n" + "="*53)


if __name__ == '__main__':
    # Initial calculation is needed to populate the dependency calculator's internal state
    # This feels a bit clunky but is necessary for the recursive logic to have access to the full tree
    temp_dep_calc = DependencyCalculator(SdeLoader())
    print("Pre-calculating full dependency tree for performance...")
    # We need a representative T2 product to build the full component tree
    temp_dep_calc.get_total_requirements("Eris", 1) 
    
    # Now run the main scheduler
    scheduler = IndustrialScheduler()
    # Pass the pre-warmed dependency calculator to the main instance
    scheduler.dep_calc = temp_dep_calc
    scheduler.run()

