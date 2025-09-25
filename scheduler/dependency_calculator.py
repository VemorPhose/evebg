from collections import defaultdict

class DependencyCalculator:
    def __init__(self, sde_loader):
        self.sde = sde_loader
        # This is the base list of minerals and blueprint components we always buy.
        self.raw_materials = {
            'Tritanium', 'Pyerite', 'Mexallon', 'Isogen',
            'Nocxium', 'Zydrine', 'Megacyte', 'Morphite',
            'R.A.M.- Starship Tech', 'Oxygen Fuel Block', 'Hydrogen Fuel Block', 
            'Helium Fuel Block', 'Nitrogen Fuel Block'
        }
        
        # This is the list of raw materials that come from reactions (moon mining).
        # Updated based on your provided list.
        reaction_inputs = {
            'Atmospheric Gases', 'Cadmium', 'Caesium', 'Chromium', 'Cobalt',
            'Dysprosium', 'Evaporite Deposits', 'Hafnium', 'Hydrocarbons',
            'Mercury', 'Neodymium', 'Platinum', 'Promethium', 'Scandium',
            'Silicates', 'Technetium', 'Thulium', 'Titanium', 'Tungsten', 'Vanadium'
        }
        # We add the reaction inputs to the main set of raw materials.
        self.raw_materials.update(reaction_inputs)
        
        self.total_components = {}
        self.processed_components_memo = set()

    def get_total_requirements(self, final_product_name, quantity=1):
        """Calculates the total raw materials and intermediate components needed for a final product."""
        self.total_components = {}
        self.processed_components_memo = set()
        
        final_product_id = self.sde.get_type_id(final_product_name)
        if not final_product_id:
            print(f"Error: Final product '{final_product_name}' not found.")
            return {}, {}

        # The main recursive call to build the dependency tree
        self._process_component(final_product_id, quantity)
        
        # Now, calculate total raw materials from the complete component list
        total_raws = defaultdict(float)
        for comp_name, details in self.total_components.items():
            materials = self.get_direct_materials_for_product_name(comp_name)
            for mat_name, qty_per_run in materials.items():
                if mat_name in self.raw_materials:
                    # Calculate how many runs of the component are needed
                    runs_needed = details['needed'] / details.get('products_per_run', 1)
                    total_raws[mat_name] += runs_needed * qty_per_run

        return dict(total_raws), self.total_components

    def _process_component(self, product_id, required_quantity):
        """Recursively builds a list of all required components and their quantities."""
        product_name = self.sde.get_type_name(product_id)

        if product_name in self.raw_materials:
            return

        blueprint_info = self.sde.get_blueprint_for_product(product_id)
        if blueprint_info is None:
            # If no blueprint, treat as a raw material. This adds PI goods etc. automatically.
            self.raw_materials.add(product_name)
            return

        blueprint_id = blueprint_info['typeID']
        activity_id = blueprint_info['activityID']
        products_per_run = blueprint_info['quantity']

        if product_name not in self.total_components:
            self.total_components[product_name] = {
                'needed': 0, 'products_per_run': products_per_run, 'activity_id': activity_id,
                'time_per_run': self.sde.get_production_time(blueprint_id, activity_id)
            }
        
        self.total_components[product_name]['needed'] += required_quantity
        
        if blueprint_id in self.processed_components_memo:
            return
        self.processed_components_memo.add(blueprint_id)

        materials = self.sde.get_materials(blueprint_id, activity_id)
        for _, material in materials.iterrows():
            total_material_needed = (required_quantity / products_per_run) * material['quantity']
            self._process_component(material['materialTypeID'], total_material_needed)
            
    def get_direct_materials_for_product_name(self, product_name):
        """Returns a dict of direct materials and quantities for one run of a product."""
        product_id = self.sde.get_type_id(product_name)
        if not product_id: return {}
        
        blueprint_info = self.sde.get_blueprint_for_product(product_id)
        if blueprint_info is None: return {}

        materials_df = self.sde.get_materials(blueprint_info['typeID'], blueprint_info['activityID'])
        
        materials_dict = {}
        for _, material in materials_df.iterrows():
            mat_name = self.sde.get_type_name(material['materialTypeID'])
            materials_dict[mat_name] = material['quantity']
        
        return materials_dict

