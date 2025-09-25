import pandas as pd

class SdeLoader:
    """
    Handles loading and providing access to the EVE Online Static Data Export (SDE) files.
    """
    def __init__(self, data_path='../static_data'):
        """Load data from the EVE Online SDE files."""
        try:
            self.industry_activity = pd.read_csv(f'{data_path}/industryActivity.csv')
            self.activity_materials = pd.read_csv(f'{data_path}/industryActivityMaterials.csv')
            self.activity_products = pd.read_csv(f'{data_path}/industryActivityProducts.csv')
            self.inv_types = pd.read_csv(f'{data_path}/invTypes.csv')
            self.inv_types.set_index('typeID', inplace=True)
            print("SDE data loaded successfully.")
        except FileNotFoundError as e:
            print(f"Error loading SDE data: {e}. Make sure the 'static_data' directory is correct.")
            exit()

    def get_type_id(self, type_name):
        """Get typeID from typeName."""
        result = self.inv_types[self.inv_types['typeName'] == type_name]
        return result.index[0] if not result.empty else None

    def get_type_name(self, type_id):
        """Get typeName from typeID."""
        try:
            return self.inv_types.loc[type_id, 'typeName']
        except KeyError:
            return f"Unknown TypeID: {type_id}"

    def get_blueprint_for_product(self, product_type_id):
        """
        Find the blueprint/formula that produces a given product.
        Prioritizes manufacturing (1) over reactions (11).
        """
        for activity_id in [1, 11]:
            blueprint = self.activity_products[
                (self.activity_products['productTypeID'] == product_type_id) & 
                (self.activity_products['activityID'] == activity_id)
            ]
            if not blueprint.empty:
                return blueprint.iloc[0]
        return None

    def get_materials(self, blueprint_type_id, activity_id):
        """Get materials required for a specific blueprint and activity."""
        return self.activity_materials[
            (self.activity_materials['typeID'] == blueprint_type_id) & 
            (self.activity_materials['activityID'] == activity_id)
        ]
        
    def get_production_time(self, blueprint_type_id, activity_id):
        """Get the production time for a specific blueprint and activity."""
        time_info = self.industry_activity[
            (self.industry_activity['typeID'] == blueprint_type_id) & 
            (self.industry_activity['activityID'] == activity_id)
        ]
        return time_info.iloc[0]['time'] if not time_info.empty else 0

