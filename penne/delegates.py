"""Collection of Noodles Objects

Follows the specification in the cddl document, and
implements strict validation
"""

from __future__ import annotations

import logging
from typing import Optional, Any, Union, Callable, List, Tuple, NamedTuple
from enum import Enum
from math import pi

from pydantic import BaseModel, root_validator, Extra, validator, Field
from pydantic.color import Color


class InjectedMethod(object):
    """Class for representing injected method in delegate, context automatically set

    Attributes:
        method (method): method to be called
        injected (bool): attribute marking method as injected
    """

    def __init__(self, method_obj) -> None:
        self.method = method_obj
        self.injected = True

    def __call__(self, *args, **kwargs):
        self.method(*args, **kwargs)


class LinkedMethod(object):
    """Class linking target delegate and method's delegate

    make a cleaner function call in injected method, it's like setting the context automatically
    This is what actually gets called for the injected method

    Attributes:
        _obj_delegate (delegate):
            delegate method is being linked to
        _method_delegate (MethodDelegate):
            the method's delegate
    """

    def __init__(self, object_delegate: Delegate, method_delegate: Method):
        self._obj_delegate = object_delegate
        self._method_delegate = method_delegate

    def __call__(self, on_done=None, *arguments):
        self._method_delegate.invoke(self._obj_delegate, list(arguments), callback=on_done)


def inject_methods(delegate: Delegate, methods: List[MethodID]):
    """Inject methods into a delegate class

    Idea is to inject a method that is from the server to put int into a delegate.
    Now it looks like the delegate has an instance method that actually calls what
    is on the server. Context, is automatically taken care of by the linked method

    Args:
        delegate (Delegate):
            identifier for delegate to be modified
        methods (list):
            list of method id's to inject
    """

    # Clear out old injected methods
    to_remove = []
    for field, value in delegate:
        if hasattr(value, "injected"):
            logging.debug(f"Deleting: {field} in inject methods")
            to_remove.append(field)
    for field in to_remove:
        delattr(delegate, field)

    for method_id in methods:

        # Get method delegate and manipulate name to exclude noo::
        method = delegate.client.get_delegate(method_id)
        if "noo::" in method.name:
            name = method.name[5:]
        else:
            name = method.name

        # Create injected by linking delegates, and creating call method
        linked = LinkedMethod(delegate, method)
        injected = InjectedMethod(linked.__call__)

        setattr(delegate, name, injected)


def inject_signals(delegate: Delegate, signals: List[SignalID]):
    """Method to inject signals into delegate

    Args:
        delegate (delegate):
            delegate object to be injected
        signals (list):
            list of signal id's to be injected
    """

    for signal_id in signals:
        signal = delegate.client.state[signal_id]  # refactored state
        delegate.signals[signal.name] = None


def get_context(delegate):
    """Helper to get context from delegate"""

    if isinstance(delegate, Entity):
        return {"entity": delegate.id}
    elif isinstance(delegate, Table):
        return {"table": delegate.id}
    elif isinstance(delegate, Plot):
        return {"plot": delegate.id}
    else:
        return None


""" =============================== ID's ============================= """


class ID(NamedTuple):
    slot: int
    gen: int

    def compact_str(self):
        return f"|{self.slot}/{self.gen}|"

    def __str__(self):
        return f"{type(self).__name__}{self.compact_str()}"

    def __key(self):
        return type(self), self.slot, self.gen

    def __eq__(self, other: object) -> bool:
        if type(other) is type(self):
            return self.__key() == other.__key()
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.__key())


class MethodID(ID):
    pass


class SignalID(ID):
    pass


class EntityID(ID):
    pass


class PlotID(ID):
    pass


class BufferID(ID):
    pass


class BufferViewID(ID):
    pass


class MaterialID(ID):
    pass


class ImageID(ID):
    pass


class TextureID(ID):
    pass


class SamplerID(ID):
    pass


class LightID(ID):
    pass


class GeometryID(ID):
    pass


class TableID(ID):
    pass


""" ====================== Generic Parent Class ====================== """


class NoodleObject(BaseModel):
    """Parent Class for all noodle objects"""

    class Config:
        """Configuration for Validation"""

        arbitrary_types_allowed = True
        use_enum_values = True
        extra = Extra.allow  # Allow injected methods


class Delegate(NoodleObject):
    """Parent class for all delegates
    
    Defines general methods that should be available for all delegates
    
    Attributes:
        client (Client): Client delegate is attached to
        id: (ID): Unique identifier for delegate
        name (str): Name of delegate
        signals (dict): Signals that can be called on delegate, method name to callable
    """

    client: object = None
    id: ID = None
    name: Optional[str] = "No-Name"
    signals: Optional[dict] = {}

    def __str__(self):
        return f"{self.name} - {type(self).__name__} - {self.id.compact_str()}"

    # For all except Document Delegate
    def on_new(self, message: dict):
        pass

    # For Document, Table, Entity, Plot, Material, Light Delegates
    def on_update(self, message: dict):
        pass

    # For all except Document Delegate
    def on_remove(self, message: dict):
        pass


""" ====================== Common Definitions ====================== """

Vec3 = Tuple[float, float, float]
Vec4 = Tuple[float, float, float, float]
Mat3 = Tuple[float, float, float,
             float, float, float,
             float, float, float]
Mat4 = Tuple[float, float, float, float,
             float, float, float, float,
             float, float, float, float,
             float, float, float, float]


class AttributeSemantic(Enum):
    position = "POSITION"
    normal = "NORMAL"
    tangent = "TANGENT"
    texture = "TEXTURE"
    color = "COLOR"


class Format(Enum):
    u8 = "U8"
    u16 = "U16"
    u32 = "U32"
    u8vec4 = "U8VEC4"
    u16vec2 = "U16VEC2"
    vec2 = "VEC2"
    vec3 = "VEC3"
    vec4 = "VEC4"
    mat3 = "MAT3"
    mat4 = "MAT4"


class IndexFormat(str, Enum):
    u8 = "U8"
    u16 = "U16"
    u32 = "U32"


class PrimitiveType(Enum):
    points = "POINTS"
    lines = "LINES"
    line_loop = "LINE_LOOP"
    line_strip = "LINE_STRIP"
    triangles = "TRIANGLES"
    triangle_strip = "TRIANGLE_STRIP"


class ColumnType(str, Enum):
    text = "TEXT"
    real = "REAL"
    integer = "INTEGER"


class BufferType(str, Enum):
    unknown = "UNK"
    geometry = "GEOMETRY"
    image = "IMAGE"


class SamplerMode(Enum):
    clamp_to_edge = "CLAMP_TO_EDGE"
    mirrored_repeat = "MIRRORED_REPEAT"
    repeat = "REPEAT"


class MagFilterTypes(Enum):
    nearest = "NEAREST"
    linear = "LINEAR"


class MinFilterTypes(Enum):
    nearest = "NEAREST"
    linear = "LINEAR"
    linear_mipmap_linear = "LINEAR_MIPMAP_LINEAR"


class SelectionRange(NoodleObject):
    key_from_inclusive: int
    key_to_exclusive: int


class Selection(NoodleObject):
    name: str
    rows: Optional[List[int]] = None
    row_ranges: Optional[List[SelectionRange]] = None


class MethodArg(NoodleObject):
    name: str
    doc: Optional[str] = None
    editor_hint: Optional[str] = None


class BoundingBox(NoodleObject):
    min: Vec3
    max: Vec3


class TextRepresentation(NoodleObject):
    txt: str
    font: Optional[str] = "Arial"
    height: Optional[float] = .25
    width: Optional[float] = -1.0


class WebRepresentation(NoodleObject):
    source: str
    height: Optional[float] = .5
    width: Optional[float] = .5


class InstanceSource(NoodleObject):
    view: BufferViewID  # view of mat4
    stride: int
    bb: Optional[BoundingBox] = None


class RenderRepresentation(NoodleObject):
    mesh: GeometryID
    instances: Optional[InstanceSource] = None


class TextureRef(NoodleObject):
    texture: TextureID
    transform: Optional[Mat3] = [1.0, 0.0, 0.0,
                                 0.0, 1.0, 0.0,
                                 0.0, 0.0, 1.0]
    texture_coord_slot: Optional[int] = 0.0


class PBRInfo(NoodleObject):
    base_color: Optional[Color] = Color('white')
    base_color_texture: Optional[TextureRef] = None  # assume SRGB, no premult alpha

    metallic: Optional[float] = 1.0
    roughness: Optional[float] = 1.0
    metal_rough_texture: Optional[TextureRef] = None  # assume linear, ONLY RG used

    @validator("base_color", pre=True, allow_reuse=True)
    def check_color_rgba(cls, value):

        # Raise warning if format is wrong from server
        if len(value) != 4:
            logging.warning(f"Base Color is Wrong Color Format: {value}")
        return value


class PointLight(NoodleObject):
    range: float = -1.0


class SpotLight(NoodleObject):
    range: float = -1.0
    inner_cone_angle_rad: float = 0.0
    outer_cone_angle_rad: float = pi/4


class DirectionalLight(NoodleObject):
    range: float = -1.0


class Attribute(NoodleObject):
    view: BufferViewID
    semantic: AttributeSemantic
    channel: Optional[int] = None
    offset: Optional[int] = 0
    stride: Optional[int] = 0
    format: Format
    minimum_value: Optional[List[float]] = None
    maximum_value: Optional[List[float]] = None
    normalized: Optional[bool] = False


class Index(NoodleObject):
    view: BufferViewID
    count: int
    offset: Optional[int] = 0
    stride: Optional[int] = 0
    format: IndexFormat


class GeometryPatch(NoodleObject):
    attributes: List[Attribute]
    vertex_count: int
    indices: Optional[Index] = None
    type: PrimitiveType
    material: MaterialID  # Material ID


class InvokeIDType(NoodleObject):
    entity: Optional[EntityID] = None
    table: Optional[TableID] = None
    plot: Optional[PlotID] = None

    @root_validator
    def one_of_three(cls, values):
        already_found = False
        for field in values:
            if values[field] and already_found:
                raise ValueError("More than one field entered")
            elif values[field]:
                already_found = True

        if not already_found:
            raise ValueError("No field provided")
        else:
            return values


class TableColumnInfo(NoodleObject):
    name: str
    type: ColumnType


class TableInitData(NoodleObject):
    columns: List[TableColumnInfo]
    keys: List[int]
    data: List[List[Any]]  # Originally tried union, but currently order is used to coerce by pydantic
    selections: Optional[List[Selection]] = None

    # too much overhead? - strict mode
    @root_validator
    def types_match(cls, values):
        for row in values['data']:
            for col, i in zip(values['columns'], range(len(row))):
                text_mismatch = isinstance(row[i], str) and col.type != "TEXT"
                real_mismatch = isinstance(row[i], float) and col.type != "REAL"
                int_mismatch = isinstance(row[i], int) and col.type != "INTEGER"
                if text_mismatch or real_mismatch or int_mismatch:
                    raise ValueError(f"Column Info doesn't match type in data: {col, row[i]}")
        return values


""" ====================== NOODLE COMPONENTS ====================== """


class Method(Delegate):
    id: MethodID
    name: str
    doc: Optional[str] = None
    return_doc: Optional[str] = None
    arg_doc: List[MethodArg] = []

    def invoke(self, on_delegate: Delegate, args=None, callback=None):
        """Invoke this delegate's method

        Args:
            on_delegate (delegate):
                delegate method is being invoked on 
                used to get context
            args (list, optional):
                args for the method
            callback (function):
                function to be called when complete
        """

        if isinstance(on_delegate, Table):
            kind = "table"
        elif isinstance(on_delegate, Plot):
            kind = "plot"
        elif isinstance(on_delegate, Entity):
            kind = "entity"
        else:
            raise ValueError("Invalid delegate context")

        context = {kind: on_delegate.id}
        self.client.invoke_method(self.id, args, context=context, on_done=callback)

    def __str__(self) -> str:
        """Custom string representation for methods"""

        rep = f"{self.name}:\n\t{self.doc}\n\tReturns: {self.return_doc}\n\tArgs:"
        for arg in self.arg_doc:
            rep += f"\n\t\t{arg.name}: {arg.doc}"
        return rep


class Signal(Delegate):
    id: SignalID
    name: str
    doc: Optional[str] = None
    arg_doc: List[MethodArg] = None


class Entity(Delegate):
    id: EntityID
    name: Optional[str] = "Unnamed Entity Delegate"

    parent: Optional[EntityID] = None
    transform: Optional[Mat4] = None

    null_rep: Optional[Any] = None
    text_rep: Optional[TextRepresentation] = None
    web_rep: Optional[WebRepresentation] = None
    render_rep: Optional[RenderRepresentation] = None

    lights: Optional[List[LightID]] = None
    tables: Optional[List[TableID]] = None
    plots: Optional[List[PlotID]] = None
    tags: Optional[List[str]] = None
    methods_list: Optional[List[MethodID]] = None
    signals_list: Optional[List[SignalID]] = None

    influence: Optional[BoundingBox] = None

    def show_methods(self):
        """Show methods available on the entity"""

        if self.methods_list is None:
            message = "No methods available"
        else:
            message = f"-- Methods on {self.name} --\n--------------------------------------\n"
            for method_id in self.methods_list:
                method = self.client.get_delegate(method_id)
                message += f">> {method}"

        print(message)
        return message


class Plot(Delegate):
    id: PlotID
    name: Optional[str] = "Unnamed Plot Delegate"

    table: Optional[TableID] = None

    simple_plot: Optional[str] = None
    url_plot: Optional[str] = None

    methods_list: Optional[List[MethodID]] = None
    signals_list: Optional[List[SignalID]] = None

    @root_validator
    def one_of(cls, values):
        if bool(values['simple_plot']) != bool(values['url_plot']):
            return values
        else:
            raise ValueError("One plot type must be specified")

    def show_methods(self):
        """Show methods available on the entity"""

        if self.methods_list is None:
            message = "No methods available"
        else:
            message = f"-- Methods on {self.name} --\n--------------------------------------\n"
            for method_id in self.methods_list:
                method = self.client.get_delegate(method_id)
                message += f">> {method}"

        print(message)
        return message


class Buffer(Delegate):
    id: BufferID
    name: Optional[str] = "Unnamed Buffer Delegate"
    size: int = None

    inline_bytes: bytes = None
    uri_bytes: str = None

    @root_validator
    def one_of(cls, values):
        if bool(values['inline_bytes']) != bool(values['uri_bytes']):
            return values
        else:
            raise ValueError("One plot type must be specified")


class BufferView(Delegate):
    id: BufferViewID
    name: Optional[str] = "Unnamed Buffer-View Delegate"
    source_buffer: BufferID

    type: BufferType = BufferType.unknown
    offset: int
    length: int

    @validator("type", pre=True)
    def coerce_type(cls, value):
        if value in ["UNK", "GEOMETRY", "IMAGE"]:
            return value

        logging.warning(f"Buffer View Type does not meet the specification: {value} coerced to 'UNK'")
        if "GEOMETRY" in value.upper():
            return "GEOMETRY"
        elif "IMAGE" in value.upper():
            return "IMAGE"
        else:
            return "UNK"


class Material(Delegate):
    id: MaterialID
    name: Optional[str] = "Unnamed Material Delegate"

    pbr_info: Optional[PBRInfo] = PBRInfo()
    normal_texture: Optional[TextureRef] = None

    occlusion_texture: Optional[TextureRef] = None  # assumed to be linear, ONLY R used
    occlusion_texture_factor: Optional[float] = 1.0

    emissive_texture: Optional[TextureRef] = None  # assumed to be SRGB, ignore A
    emissive_factor: Optional[Vec3] = [1.0, 1.0, 1.0]

    use_alpha: Optional[bool] = False
    alpha_cutoff: Optional[float] = .5

    double_sided: Optional[bool] = False


class Image(Delegate):
    id: ImageID
    name: Optional[str] = "Unnamed Image Delegate"

    buffer_source: BufferID = None
    uri_source: str = None

    @root_validator
    def one_of(cls, values):
        if bool(values['buffer_source']) != bool(values['uri_source']):
            return values
        else:
            raise ValueError("One plot type must be specified")


class Texture(Delegate):
    id: TextureID
    name: Optional[str] = "Unnamed Texture Delegate"
    image: ImageID
    sampler: Optional[SamplerID] = None


class Sampler(Delegate):
    id: SamplerID
    name: Optional[str] = "Unnamed Sampler Delegate"

    mag_filter: Optional[MagFilterTypes] = MagFilterTypes.linear
    min_filter: Optional[MinFilterTypes] = MinFilterTypes.linear_mipmap_linear

    wrap_s: Optional[SamplerMode] = "REPEAT"
    wrap_t: Optional[SamplerMode] = "REPEAT"


class Light(Delegate):
    id: LightID
    name: Optional[str] = "Unnamed Light Delegate"

    color: Optional[Color] = Color('white')
    intensity: Optional[float] = 1.0

    point: PointLight = None
    spot: SpotLight = None
    directional: DirectionalLight = None

    @validator("color", pre=True, allow_reuse=True)
    def check_color_rgb(cls, value):

        # Raise warning if format is wrong
        if len(value) != 3:
            logging.warning(f"Color is not RGB in Light: {value}")

        return value

    @root_validator
    def one_of(cls, values):
        already_found = False
        for field in ['point', 'spot', 'directional']:
            if values[field] and already_found:
                raise ValueError("More than one field entered")
            elif values[field]:
                already_found = True

        if not already_found:
            raise ValueError("No field provided")
        else:
            return values


class Geometry(Delegate):
    id: GeometryID
    name: Optional[str] = "Unnamed Geometry Delegate"
    patches: List[GeometryPatch]


class Table(Delegate):
    id: TableID
    name: Optional[str] = f"Unnamed Table Delegate"

    meta: Optional[str] = None
    methods_list: Optional[List[MethodID]] = None
    signals_list: Optional[List[SignalID]] = None

    methods: List[str] = [
        "subscribe",
        "request_clear",
        "request_insert",
        "request_remove",
        "request_update",
        "request_update_selection",
        "plot"
    ]

    tbl_subscribe: InjectedMethod = None
    tbl_insert: InjectedMethod = None
    tbl_update: InjectedMethod = None
    tbl_remove: InjectedMethod = None
    tbl_clear: InjectedMethod = None
    tbl_update_selection: InjectedMethod = None

    def __init__(self, **kwargs):
        """Override init to link default values with methods"""
        super().__init__(**kwargs)
        self.signals = {
            "noo::tbl_reset": self._reset_table,
            "noo::tbl_rows_removed": self._remove_rows,
            "noo::tbl_updated": self._update_rows,
            "noo::tbl_selection_updated": self._update_selection
        }

    def _on_table_init(self, init_info: dict, on_done=None):
        """Creates table from server response info

        Args:
            init_info (Message Obj): 
                Server response to subscribe which has columns, keys, data, 
                and possibly selections
        """

        init = TableInitData(**init_info)
        logging.info(f"Table Initialized with cols: {init.columns} and row data: {init.data}")
        if on_done:
            on_done()

    def _reset_table(self, init_info: dict = None):
        """Reset dataframe and selections to blank objects

        Method is linked to 'tbl_reset' signal
        """

        self.selections = {}
        if init_info:
            init = TableInitData(**init_info)
            logging.info(f"Table Reset and Initialized with cols: {init.columns} and row data: {init.data}")

    def _remove_rows(self, keys: List[int]):
        """Removes rows from table

        Method is linked to 'tbl_rows_removed' signal

        Args:
            keys (list): list of keys corresponding to rows to be removed
        """

        logging.info(f"Removed Rows: {keys}...\n")

    def _update_rows(self, keys: List[int], rows: list):
        """Update rows in table

        Method is linked to 'tbl_updated' signal

        Args:
            keys (list): 
                list of keys to update
            rows (list):
                list of rows containing the values for each new row
        """

        logging.info(f"Updated Rows...{keys}\n")

    def _update_selection(self, selection: dict):
        """Change selection in delegate's state to new selection object

        Method is linked to 'tbl_selection_updated' signal

        Args:
            selection (Selection): 
                obj with new selections to replace obj with same name
        """

        self.selections.setdefault(selection["name"], selection)
        logging.info(f"Made selection {selection['name']} = {selection}")

    def relink_signals(self):
        """Relink the signals for built-in methods

        These should always be linked, along with whatever is injected,
        so relink on new and on update messages
        """

        self.signals["noo::tbl_reset"] = self._reset_table
        self.signals["noo::tbl_rows_removed"] = self._remove_rows
        self.signals["noo::tbl_updated"] = self._update_rows
        self.signals["noo::tbl_selection_updated"] = self._update_selection

    def on_new(self, message: dict):
        """Handler when create message is received

        Args:
            message (Message): create message with the table's info
        """

        # Set name
        methods = self.methods_list
        signals = self.signals_list

        # Inject methods and signals
        if methods:
            inject_methods(self, methods)
        if signals:
            inject_signals(self, signals)

        # Reset
        self._reset_table()
        self.relink_signals()

    def on_update(self, message: dict):
        """Handler when update message is received
        
        Args:
            message (Message): update message with the new table's info
        """

        self.relink_signals()

    def on_remove(self, message: dict):
        pass

    def subscribe(self, on_done: Callable = None):
        """Subscribe to this delegate's table

        Calls on_table_init as callback
        
        Raises:
            Exception: Could not subscribe to table
        """

        try:
            # Allow for callback after table init
            self.tbl_subscribe(on_done=lambda data: self._on_table_init(data, on_done))
        except Exception as e:
            raise Exception(f"Could not subscribe to table {self.id}...{e}")

    def request_insert(self, row_list: List[List[int]], on_done=None):
        """Add rows to end of table

        User endpoint for interacting with table and invoking method
        For input, row list is list of rows. Also note that tables have
        nine columns by default (x, y, z, r, g, b, sx, sy, sz).
        x, y, z -> coordinates
        r, g, b -> color values [0, 1]
        sx, sy, sz -> scaling factors, default size is 1 meter

        Row_list: [[1, 2, 3, 4, 5, 6, 7, 8, 9]]

        Args:
            row_list (list, optional): add rows using list of rows
            on_done (function, optional): callback function
        Raises:
            Invalid input for request insert exception
        """

        self.tbl_insert(on_done, row_list)

    def request_update(self, keys: List[int], rows: List[List[int]], on_done=None):
        """Update the table using a DataFrame

        User endpoint for interacting with table and invoking method

        Args:
            keys (list[int]):
                list of keys to update
            rows (list[list[int]])
                list of new rows to update with
            on_done (function, optional): 
                callback function called when complete
        """

        self.tbl_update(on_done, keys, rows)

    def request_remove(self, keys: List[int], on_done=None):
        """Remove rows from table by their keys

        User endpoint for interacting with table and invoking method

        Args:
            keys (list):
                list of keys for rows to be removed
            on_done (function, optional): 
                callback function called when complete
        """

        self.tbl_remove(on_done, keys)

    def request_clear(self, on_done=None):
        """Clear the table

        User endpoint for interacting with table and invoking method

        Args:
            on_done (function, optional): callback function called when complete
        """
        self.tbl_clear(on_done)

    def request_update_selection(self, name: str, keys: List[int], on_done=None):
        """Update a selection object in the table

        User endpoint for interacting with table and invoking method

        Args:
            name (str):
                name of the selection object to be updated
            keys (list):
                list of keys to be in new selection
            on_done (function, optional): 
                callback function called when complete
        """
        selection = Selection(name=name, rows=keys)
        self.tbl_update_selection(on_done, selection.dict())

    def show_methods(self):
        """Show methods available on the table"""

        if self.methods_list is None:
            message = "No methods available"
        else:
            message = f"-- Methods on {self.name} --\n--------------------------------------\n"
            for method_id in self.methods_list:
                method = self.client.get_delegate(method_id)
                message += f">> {method}"

        print(message)
        return message


class Document(Delegate):
    name: str = "Document"

    methods_list: List[MethodID] = []  # Server usually sends as an update
    signals_list: List[SignalID] = []

    def on_update(self, message: dict):
        if "methods_list" in message:
            self.methods_list = [MethodID(*element) for element in message["methods_list"]]
        if "signals_list" in message:
            self.signals_list = [SignalID(*element) for element in message["signals_list"]]

    def reset(self):
        self.client.state = {"document": self}
        self.methods_list = []
        self.signals_list = []

    def show_methods(self):
        """Show methods available on the document"""

        if not self.methods_list:
            message = "No methods available"
        else:
            message = f"-- Methods on Document --\n--------------------------------------\n"
            for method_id in self.methods_list:
                method = self.client.get_delegate(method_id)
                message += f">> {method}"

        print(message)
        return message


""" ====================== Communication Objects ====================== """


class Invoke(NoodleObject):
    id: SignalID
    context: Optional[InvokeIDType] = None  # if empty - document
    signal_data: List[Any]


# Note: this isn't technically an exception
# for now this uses a model so that it can be validated / sent as message easier
class MethodException(NoodleObject):
    code: int
    message: Optional[str] = None
    data: Optional[Any] = None


class Reply(NoodleObject):
    invoke_id: str
    result: Optional[Any] = None
    method_exception: Optional[MethodException] = None


""" ====================== Miscellaneous Objects ====================== """

default_delegates = {
    Entity: Entity,
    Table: Table,
    Plot: Plot,
    Signal: Signal,
    Method: Method,
    Material: Material,
    Geometry: Geometry,
    Light: Light,
    Image: Image,
    Texture: Texture,
    Sampler: Sampler,
    Buffer: Buffer,
    BufferView: BufferView,
    Document: Document
}

id_map = {
    Method: MethodID,
    Signal: SignalID,
    Table: TableID,
    Plot: PlotID,
    Entity: EntityID,
    Material: MaterialID,
    Geometry: GeometryID,
    Light: LightID,
    Image: ImageID,
    Texture: TextureID,
    Sampler: SamplerID,
    Buffer: BufferID,
    BufferView: BufferViewID,
    Document: None
}
