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


class TableDelegate(object):

    def __init__(self, client):
        self._client = client
        self.dataframe = None

    def on_table_init(self, init_info):
        print("Initializing table...")
        print(init_info)
        table_data = pd.DataFrame({col: data for col, data in zip(
            init_info['columns'], init_info['data'])}, index=init_info['keys'])
        self.dataframe = pd.DataFrame(table_data)

    def reset_table(self):
        pass
    def remove_rows(self, key_list):
        pass
    def update_rows(self, key_list, column_list):
        pass
    def selection_changed(self, name, selection_obj):
        pass
    def get_selection(self, name):
        pass
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
        messages.IDGroup(*table_id)
        self._client.invoke_method(4, [], context=messages.InvokeIDType(table=table_id), callback=self.on_table_init)


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
