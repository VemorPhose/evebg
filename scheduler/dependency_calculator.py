import math
from collections import defaultdict

class DependencyCalculator:
    """
    Calculates the entire dependency tree for a final product,
    breaking it down into raw materials and intermediate components.
    """
    def __init__(self, sde_loader):
        self.sde = sde_loader
        self.raw_materials = {
            'Tritanium', 'Pyerite', 'Mexallon', 'Isogen',
            'Nocxium', 'Zydrine', 'Megacyte', 'Morphite',
            'R.A.M.- Starship Tech', 'Oxygen Fuel Block', 'Hydrogen Fuel Block', 
            'Helium Fuel Block', 'Nitrogen Fuel Block', 'Catalyst'
        }

    def get_total_requirements(self, final_product_name, quantity=1):
        """
        Calculates all raw materials and intermediate build components for a target product.
        
        Returns three dictionaries:
        1. Total raw materials required.
        2. Total intermediate components to be built.
        3. Direct materials needed for one run of the final product.
        """
        final_product_id = self.sde.get_type_id(final_product_name)
        if not final_product_id:
            print(f"Error: Final product '{final_product_name}' not found.")
            return {}, {}, {}

        total_raws = defaultdict(float)
        total_components = defaultdict(float)
        
        # Memoization to avoid re-calculating branches
        memo = {}

        def process_component(product_id, required_quantity):
            if product_id in memo and memo[product_id] >= required_quantity:
                return
            memo[product_id] = required_quantity

            product_name = self.sde.get_type_name(product_id)
            blueprint_info = self.sde.get_blueprint_for_product(product_id)

            if product_name in self.raw_materials or blueprint_info is None:
                total_raws[product_name] += required_quantity
                return

            # It's an intermediate component, add to the list
            total_components[product_name] += required_quantity
            
            blueprint_id = blueprint_info['typeID']
            products_per_run = blueprint_info['quantity']
            activity_id = blueprint_info['activityID']
            
            materials = self.sde.get_materials(blueprint_id, activity_id)
            for _, material in materials.iterrows():
                mat_id = material['materialTypeID']
                qty_per_run = material['quantity']
                # Quantity of sub-component needed for the requested parent quantity
                total_material_needed = (required_quantity / products_per_run) * qty_per_run
                process_component(mat_id, total_material_needed)

        # Start the recursive calculation
        process_component(final_product_id, quantity)
        
        # Separately calculate direct materials for the final product
        final_product_direct_materials = {}
        final_bp_info = self.sde.get_blueprint_for_product(final_product_id)
        if final_bp_info is not None:
            final_bp_id = final_bp_info['typeID']
            final_activity_id = final_bp_info['activityID']
            materials = self.sde.get_materials(final_bp_id, final_activity_id)
            for _, material in materials.iterrows():
                mat_name = self.sde.get_type_name(material['materialTypeID'])
                final_product_direct_materials[mat_name] = material['quantity']

        return dict(total_raws), dict(total_components), final_product_direct_materials

