from select import select
import pandas as pd
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


class SelectionRange(tuple):

    def __new__(cls, key_from, key_to):
        return super().__new__(SelectionRange, (key_from, key_to))


class Selection(object):

    def __init__(self, name: str, rows: list[int] = None, row_ranges: list[SelectionRange] = None) -> None:
        self.name = name
        self.rows = rows
        self.row_ranges = row_ranges

    def __repr__(self) -> str:
        return f"Selection Object({self.__dict__})"

    def __getitem__(self, attribute):
        return getattr(self, attribute)


class TableDelegate(object):

    # SelectionRange = ( key_from_inclusive : int, key_to_exclusive : int )

    # Selection = {
    #     name : text,
    #     ? rows : [* int],
    #     ? row_ranges : [* SelectionRange]
    # }

    def __init__(self, client):
        self._client = client
        self.dataframe = None
        self.selections = {}
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
        print(f"Removed Rows: {key_list}...\n", self.dataframe)

    def update_rows(self, keys: list, cols: list):
        headers = self.dataframe.columns.values
        new_df = pd.DataFrame({col: data for col, data in zip(
            headers, cols)}, index=keys)
        new_df_filled = new_df.combine_first(self.dataframe) # changes order of columns - problem?
        self.dataframe = new_df_filled
    
        print(f"Updated Rows...{keys}\n", self.dataframe)
        
    def update_rows2(self, new_rows: dict):
        headers = self.dataframe.columns.values
        new_df = pd.DataFrame(new_rows, index=headers).transpose()
        new_df.combine_first(self.dataframe) 
        print("transposed row input:")
        print(new_df)
        self.dataframe.update(new_df)
        print(f"Updated Rows...{new_rows.keys()}\n", self.dataframe)

    def update_cols(self, new_cols: dict):
        # Expects a dict mapping col name to new values
        new_df = pd.DataFrame(new_cols)
        self.dataframe.update(new_df)
        print(f"Updated Cols {new_cols.keys()}...\n", self.dataframe)

    def make_selection(self, selection_obj: Selection):
        # Change selection in state
        self.selections[selection_obj.name] = selection_obj
        print(f"Made selection {selection_obj.name} = {selection_obj}")
        
    def get_selection(self, name):
        
        # Try to retrieve selection object from instance
        try:
            sel_obj = self.selections[name]
        except:
            return pd.DataFrame(columns=self.dataframe.columns)

        frames = []

        # Get rows already in that selection
        if sel_obj.rows:
            frames.append(self.dataframe.loc[sel_obj["rows"]])

        # Uses ranges in object to get other rows
        if sel_obj.row_ranges:
            ranges = sel_obj["row_ranges"]
            for r in ranges:
                frames.append(self.dataframe.loc[r[0]:r[1]-1])

        # Return frames concatenated
        df = pd.concat(frames)
        print(f"Got selection for {sel_obj}\n{df}")
        return df

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
