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
        
        Returns two dictionaries:
        1. Total raw materials required.
        2. Total intermediate components, with details on quantity and activity type.
        """
        final_product_id = self.sde.get_type_id(final_product_name)
        if not final_product_id:
            print(f"Error: Final product '{final_product_name}' not found.")
            return {}, {}

        total_raws = defaultdict(float)
        # The structure of total_components is now {name: {'needed': float, 'activity_id': int}}
        total_components = defaultdict(lambda: {'needed': 0, 'activity_id': 0})
        
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

            activity_id = blueprint_info['activityID']
            total_components[product_name]['needed'] += required_quantity
            total_components[product_name]['activity_id'] = activity_id
            
            blueprint_id = blueprint_info['typeID']
            products_per_run = blueprint_info['quantity']
            
            materials = self.sde.get_materials(blueprint_id, activity_id)
            for _, material in materials.iterrows():
                mat_id = material['materialTypeID']
                qty_per_run = material['quantity']
                total_material_needed = (required_quantity / products_per_run) * qty_per_run
                process_component(mat_id, total_material_needed)

        process_component(final_product_id, quantity)
        return dict(total_raws), dict(total_components)

    def get_direct_materials_for_product_name(self, product_name):
        """
        Returns a dictionary of direct material requirements for a single run of a product.
        {material_name: quantity}
        """
        product_id = self.sde.get_type_id(product_name)
        if not product_id:
            return {}

        bp_info = self.sde.get_blueprint_for_product(product_id)
        if bp_info is None:
            return {}
            
        materials_df = self.sde.get_materials(bp_info['typeID'], bp_info['activityID'])
        direct_materials = {}
        for _, material in materials_df.iterrows():
            mat_name = self.sde.get_type_name(material['materialTypeID'])
            direct_materials[mat_name] = material['quantity']
        
        return direct_materials
