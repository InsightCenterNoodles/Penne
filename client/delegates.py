import pandas as pd
import numpy as np
from . import messages

"""
Default Delegates for Python Client
"""

class MethodDelegate(object):

    def __init__(self, client):
        self._client = client

    def on_new(self, data):
        pass 

    def on_remove(self, data): 
        pass


class SignalDelegate(object):
    
    def __init__(self, client):
        self._client = client

    def on_new(self, data):
        pass 

    def on_remove(self, data): 
        pass


class TableDelegate(object):

    def __init__(self, client):
        self._client = client
        self.dataframe = None
        self.selections = None
        self.signals = {
            "tbl_reset" : self.reset_table,
            "tbl_rows_removed" : self.remove_rows,
            "tbl_updated" : self.update_rows,
            "tbl_selection_updated" : self.make_selection
        }

    def on_table_init(self, init_info):
        print("Initializing table...")
        # had to set column as just the name - lost type info - ok?
        data_dict = {getattr(col, "name"): data for col, data in zip(getattr(init_info, "columns"), getattr(init_info, "data"))}
        table_data = pd.DataFrame(data_dict, index=getattr(init_info, "keys"))
        self.dataframe = pd.DataFrame(table_data)
        print(self.dataframe)

    def reset_table(self):
        self.dataframe = pd.DataFrame()
        self.selections = {}
        print("Table Reset...", self.dataframe)

    def remove_rows(self, key_list):
        self.dataframe.drop(index=key_list, inplace=True)
        print("Rows Removed...", self.dataframe)

    def update_rows(self, key_list, column_list):
        headers = self.dataframe.columns.values
        new_df = pd.DataFrame({col: data for col, data in zip(
            headers, column_list)}, index=key_list)
        new_df_filled = self.dataframe.combine_first(new_df)
        self.dataframe = new_df_filled.update(new_df)

    def make_selection(self, name, selection_obj):
        self.selections[name] = selection_obj
        print("Selection made / changed...", name, selection_obj)
        
    def get_selection(self, name):
        
        # Create selection object
        try:
            sel_obj = self.selections[name]
        except:
            return pd.DataFrame(columns=self.dataframe.columns)

        frames = []

        # Get rows already in that selection
        if "rows" in sel_obj:
            frames += [self.dataframe.loc[sel_obj["rows"]]]

        # Uses ranges in object to get other rows
        if "row_ranges" in sel_obj:
            ranges = np.array(sel_obj["row_ranges"]).reshape(-1, 2)
            for r in ranges:
                frames += [
                    self.dataframe.loc[r[0]:r[1]-1]
                ]
        return pd.concat(frames)

    def relink_signals(self):
        pass


    def on_new(self, data):
        print("New table message:")
        print(data)

    def on_update(self, data):
        pass
    def on_remove(self, data): 
        pass

    def subscribe(self, table_id):
        # what type is table_id, and where to convert?
        invoke_id = messages.InvokeIDType(table=table_id)
        #invoke_id = messages.InvokeIDType.generate({"table": table_id})
        self._client.invoke_method(4, [], context=invoke_id, callback=self.on_table_init)


class DocumentDelegate(object):
    
    def __init__(self, client):
        self._client = client

    def on_update(self, data):
        pass

    def on_reset(self, data): 
        pass

class EntityDelegate(object):

    def __init__(self, client):
        self._client = client

    def on_new(self, data):
        pass

    def on_update(self, data):
        pass

    def on_remove(self, data): 
        pass

class PlotDelegate(object):

    def __init__(self, client):
        self._client = client

    def on_new(self, data):
        pass

    def on_update(self, data):
        pass

    def on_remove(self, data): 
        pass

class MaterialDelegate(object):

    def __init__(self, client):
        self._client = client

    def on_new(self, data):
        pass

    def on_update(self, data):
        pass

    def on_remove(self, data): 
        pass

class GeometryDelegate(object):

    def __init__(self, client):
        self._client = client

    def on_new(self, data):
        pass

    def on_update(self, data):
        pass

    def on_remove(self, data): 
        pass

class LightDelegate(object):

    def __init__(self, client):
        self._client = client

    def on_new(self, data):
        pass

    def on_update(self, data):
        pass

    def on_remove(self, data): 
        pass

class ImageDelegate(object):

    def __init__(self, client):
        self._client = client

    def on_new(self, data):
        pass

    def on_update(self, data):
        pass

    def on_remove(self, data): 
        pass

class TextureDelegate(object):

    def __init__(self, client):
        self._client = client

    def on_new(self, data):
        pass

    def on_update(self, data):
        pass

    def on_remove(self, data): 
        pass

class SamplerDelegate(object):

    def __init__(self, client):
        self._client = client

    def on_new(self, data):
        pass

    def on_update(self, data):
        pass

    def on_remove(self, data): 
        pass

class BufferDelegate(object):

    def __init__(self, client):
        self._client = client

    def on_new(self, data):
        pass

    def on_update(self, data):
        pass

    def on_remove(self, data): 
        pass

class BufferViewDelegate(object):

    def __init__(self, client):
        self._client = client

    def on_new(self, data):
        pass

    def on_update(self, data):
        pass

    def on_remove(self, data): 
        pass
