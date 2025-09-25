from sde_loader import SdeLoader
from esi_manager import EsiManager
from dependency_calculator import DependencyCalculator
import math
from collections import defaultdict, deque

class IndustrialScheduler:
    def __init__(self):
        print("Initializing EVE Online Industrial Scheduler...")
        self.sde = SdeLoader()
        self.esi = EsiManager()
        self.dep_calc = DependencyCalculator(self.sde)

        self.inventory_by_name = {}
        self.mfg_slots = 0
        self.react_slots = 0
        
    def run(self):
        if not self.esi.authenticate():
            print("Authentication failed. Exiting.")
            return
        
        self._get_user_input()
        self._fetch_inventory()
        
        # This pre-calculation is necessary to populate the dependency calculator's internal state
        # with all possible components in the tree for the target product.
        print("\nPre-calculating full dependency tree...")
        self.dep_calc.get_total_requirements(self.target_product, self.target_quantity)

        self._plan_production_run()
        self._display_action_plan()

    def _get_user_input(self):
        self.target_product = input("\nEnter the final product you want to build (e.g., Eris): ")
        try:
            self.target_quantity = int(input(f"How many {self.target_product} do you want to build? [Default: 1]: ") or 1)
        except ValueError:
            self.target_quantity = 1
        
        try:
            self.mfg_slots = int(input(f"Enter available manufacturing slots [Default: 9]: ") or 9)
            self.react_slots = int(input(f"Enter available reaction slots [Default: 5]: ") or 5)
        except ValueError:
            self.mfg_slots, self.react_slots = 9, 5

    def _fetch_inventory(self):
        print("Fetching current inventory...")
        inventory_by_id = self.esi.get_inventory()
        self.inventory_by_name = {self.sde.get_type_name(tid): qty for tid, qty in inventory_by_id.items()}

    def _is_raw_material(self, component_name):
        """Checks if a component is a raw material (minerals, PI, reactions, etc.)."""
        # A component is raw if it's in our predefined list or has no blueprint.
        if component_name in self.dep_calc.raw_materials:
            return True
        
        # Check if a blueprint exists. If not, it's a raw material (like PI goods).
        product_id = self.sde.get_type_id(component_name)
        if not product_id or self.sde.get_blueprint_for_product(product_id) is None:
            return True
            
        return False

    def _plan_production_run(self):
        """Plans the production run using a Breadth-First Search (BFS) algorithm."""
        print("Planning buildable jobs using BFS...")
        
        self.recommended_jobs = []
        self.shopping_list = defaultdict(float)
        
        queue = deque([self.target_product])
        visited = {self.target_product}
        SECONDS_IN_A_DAY = 86400

        while queue:
            current_comp_name = queue.popleft()

            # We don't build raw materials
            if self._is_raw_material(current_comp_name):
                continue

            # Calculate batch size for ~24h
            comp_details = self.dep_calc.total_components.get(current_comp_name)
            if not comp_details: continue # Should not happen if pre-calc worked
            
            time_per_run = comp_details.get('time_per_run', 0)
            runs_for_batch = max(1, round(SECONDS_IN_A_DAY / time_per_run)) if time_per_run > 0 else 1

            # Get direct materials and categorize them
            direct_materials = self.dep_calc.get_direct_materials_for_product_name(current_comp_name)
            producable_inputs = {}
            raw_inputs = {}
            for mat, qty in direct_materials.items():
                if self._is_raw_material(mat):
                    raw_inputs[mat] = qty
                else:
                    producable_inputs[mat] = qty

            # Check if all producable inputs are available for the batch
            can_build = True
            for sub_comp, qty_per in producable_inputs.items():
                needed_for_batch = qty_per * runs_for_batch
                if self.inventory_by_name.get(sub_comp, 0) < needed_for_batch:
                    can_build = False
                    # Add missing sub-component to queue if not already visited
                    if sub_comp not in visited:
                        queue.append(sub_comp)
                        visited.add(sub_comp)

            if can_build:
                # Add this job to recommendations
                job_info = {
                    'name': current_comp_name,
                    'runs': runs_for_batch,
                    'activity_id': comp_details['activity_id']
                }
                self.recommended_jobs.append(job_info)

                # Check for and add missing raw materials to shopping list
                for raw_mat, qty_per in raw_inputs.items():
                    needed_for_batch = qty_per * runs_for_batch
                    if self.inventory_by_name.get(raw_mat, 0) < needed_for_batch:
                        self.shopping_list[raw_mat] += needed_for_batch - self.inventory_by_name.get(raw_mat, 0)

    def _display_action_plan(self):
        mfg_to_start = [j for j in self.recommended_jobs if j['activity_id'] == 1][:self.mfg_slots]
        react_to_start = [j for j in self.recommended_jobs if j['activity_id'] == 11][:self.react_slots]

        print("\n" + "="*20 + " ACTION PLAN " + "="*20)

        print(f"\n--- Recommended Manufacturing Jobs ({len(mfg_to_start)}/{self.mfg_slots} slots) ---")
        if not mfg_to_start: print("  - None")
        for job in mfg_to_start:
            print(f"\n  - Start {job['runs']} run(s) of: {job['name']}")
            # Sanity Check
            direct_mats = self.dep_calc.get_direct_materials_for_product_name(job['name'])
            for mat, needed_per in direct_mats.items():
                needed_total = needed_per * job['runs']
                have = self.inventory_by_name.get(mat, 0)
                print(f"    - Req: {mat} ({math.ceil(needed_total)}), Have: {have}")

        print(f"\n--- Recommended Reaction Jobs ({len(react_to_start)}/{self.react_slots} slots) ---")
        if not react_to_start: print("  - None")
        for job in react_to_start:
            print(f"\n  - Start {job['runs']} run(s) of: {job['name']}")
            # Sanity Check
            direct_mats = self.dep_calc.get_direct_materials_for_product_name(job['name'])
            for mat, needed_per in direct_mats.items():
                needed_total = needed_per * job['runs']
                have = self.inventory_by_name.get(mat, 0)
                print(f"    - Req: {mat} ({math.ceil(needed_total)}), Have: {have}")
        
        if self.shopping_list:
            print("\n--- Shopping List (for recommended jobs) ---")
            for item, qty in sorted(self.shopping_list.items()):
                print(f"{item} {math.ceil(qty)}")
        else:
            print("\n--- Shopping List ---")
            print("  - No items need to be purchased for the recommended jobs.")

        print("\n" + "="*53)


if __name__ == '__main__':
    scheduler = IndustrialScheduler()
    scheduler.run()
