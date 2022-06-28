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
    
    def _link(self, client, id):
        self._client = client
        self._id = id

    def on_new(self, data):
        pass 
    def on_update(self, data):
        pass

    def on_remove(self, data): 
        pass


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
