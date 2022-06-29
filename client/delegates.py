import pandas as pd

"""
Default Delegates for Python Client
"""

class MethodDelegate(object):

    def _link(self, client, id):
        self._client = client
        self._id = id

    def on_new(self, data):
        pass 

    def on_remove(self, data): 
        pass


class SignalDelegate(object):
    
    def _link(self, client, id):
        self._client = client
        self._id = id

    def on_new(self, data):
        pass 

    def on_remove(self, data): 
        pass


class TableDelegate(object):

    def __init__(self):
        self.dataframe = None
    
    def _link(self, client, id):
        self._client = client
        self._id = id

    def on_table_init(self, table_data):
        print("Initializing table...")
        print(table_data)
        table_data = {col : data for col, data in zip()}
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

    def subscribe(self):
        self._client.invoke_method(4, [], context = None, callback=self.on_table_init)


class DocumentDelegate(object):
    
    def _link(self, client, id):
        self._client = client
        self._id = id

    def on_update(self, data):
        pass

    def on_reset(self, data): 
        pass

class EntityDelegate(object):

    def _link(self, client, id):
        self._client = client
        self._id = id

    def on_new(self, data):
        pass

    def on_update(self, data):
        pass

    def on_remove(self, data): 
        pass

class PlotDelegate(object):

    def _link(self, client, id):
        self._client = client
        self._id = id

    def on_new(self, data):
        pass

    def on_update(self, data):
        pass

    def on_remove(self, data): 
        pass

class MaterialDelegate(object):

    def _link(self, client, id):
        self._client = client
        self._id = id

    def on_new(self, data):
        pass

    def on_update(self, data):
        pass

    def on_remove(self, data): 
        pass

class GeometryDelegate(object):

    def _link(self, client, id):
        self._client = client
        self._id = id

    def on_new(self, data):
        pass

    def on_update(self, data):
        pass

    def on_remove(self, data): 
        pass

class LightDelegate(object):

    def _link(self, client, id):
        self._client = client
        self._id = id

    def on_new(self, data):
        pass

    def on_update(self, data):
        pass

    def on_remove(self, data): 
        pass

class ImageDelegate(object):

    def _link(self, client, id):
        self._client = client
        self._id = id

    def on_new(self, data):
        pass

    def on_update(self, data):
        pass

    def on_remove(self, data): 
        pass

class TextureDelegate(object):

    def _link(self, client, id):
        self._client = client
        self._id = id

    def on_new(self, data):
        pass

    def on_update(self, data):
        pass

    def on_remove(self, data): 
        pass

class SamplerDelegate(object):

    def _link(self, client, id):
        self._client = client
        self._id = id

    def on_new(self, data):
        pass

    def on_update(self, data):
        pass

    def on_remove(self, data): 
        pass

class BufferDelegate(object):

    def _link(self, client, id):
        self._client = client
        self._id = id

    def on_new(self, data):
        pass

    def on_update(self, data):
        pass

    def on_remove(self, data): 
        pass

class BufferViewDelegate(object):

    def _link(self, client, id):
        self._client = client
        self._id = id

    def on_new(self, data):
        pass

    def on_update(self, data):
        pass

    def on_remove(self, data): 
        pass
