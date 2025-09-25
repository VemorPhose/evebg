import math
from collections import defaultdict

class DependencyCalculator:
    """
    Calculates the total, ideal material and component requirements for a
    target build, ignoring any existing inventory.
    """
    def __init__(self, sde_loader):
        self.sde = sde_loader
        # A list of items to always treat as raw materials
        self.force_raw_materials = {
            'Tritanium', 'Pyerite', 'Mexallon', 'Isogen',
            'Nocxium', 'Zydrine', 'Megacyte', 'Morphite',
            'R.A.M.- Starship Tech', 'Oxygen Fuel Block', 'Hydrogen Fuel Block', 
            'Helium Fuel Block', 'Nitrogen Fuel Block'
        }

    def get_total_requirements(self, product_name, quantity=1):
        """
        Performs a full recursive calculation for all materials and intermediate
        components required to build a final product.

        Returns two dictionaries:
        - bill_of_materials: {type_name: quantity} for raw materials.
        - component_jobs: {type_name: quantity} for intermediate components to be built.
        """
        print(f"Calculating total requirements for {quantity}x {product_name}...")
        product_id = self.sde.get_type_id(product_name)
        if not product_id:
            print(f"Error: Could not find '{product_name}' in SDE.")
            return {}, {}

        bill_of_materials = defaultdict(float)
        component_jobs = defaultdict(float)
        
        def process_component(p_id, p_qty):
            p_name = self.sde.get_type_name(p_id)
            blueprint = self.sde.get_blueprint_for_product(p_id)

            if p_name in self.force_raw_materials or blueprint is None:
                bill_of_materials[p_name] += p_qty
                return

            # This is an intermediate component we need to build
            if p_id != product_id: # Don't add the final product itself
                 component_jobs[p_name] += p_qty

            bp_id = blueprint['typeID']
            activity_id = blueprint['activityID']
            products_per_run = blueprint['quantity']
            runs_needed = p_qty / products_per_run

            materials = self.sde.get_materials_for_blueprint(bp_id, activity_id)
            for _, material in materials.iterrows():
                mat_id = material['materialTypeID']
                qty_per_run = material['quantity']
                total_material_needed = runs_needed * qty_per_run
                process_component(mat_id, total_material_needed)

        process_component(product_id, quantity)

        # Convert defaultdicts to regular dicts for clean output
        return dict(bill_of_materials), dict(component_jobs)
