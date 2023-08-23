"""Collection of Noodles Objects

Follows the specification in the cddl document, and
implements strict validation
"""

from __future__ import annotations

import logging
from typing import Optional, Any, Callable, List, Tuple, NamedTuple
from enum import Enum
from math import pi

from pydantic import ConfigDict, BaseModel, model_validator, field_validator
from pydantic_extra_types.color import Color


class InjectedMethod(object):
    """Class for representing injected method in delegate

    The context is automatically set when invoked. This object is callable and is what is actually called when the
    injected method is called.

    Attributes:
        method (Callable): method to be called
        injected (bool): attribute marking method as injected, useful for clearing out old injected methods
    """

    def __init__(self, method_obj) -> None:
        self.method = method_obj
        self.injected = True

    def __call__(self, *args, **kwargs):
        self.method(*args, **kwargs)


class LinkedMethod(object):
    """Class linking target delegate and method's delegate

    Make a cleaner function call in injected method, it's like setting the context automatically
    This is what actually gets called for the injected method

    Attributes:
        _obj_delegate (Delegate):
            delegate method is being linked to
        _method_delegate (MethodDelegate):
            the method's delegate
    """

    def __init__(self, object_delegate: Delegate, method_delegate: Method):
        self._obj_delegate = object_delegate
        self._method_delegate = method_delegate

    def __call__(self, *args, **kwargs):
        callback = kwargs.pop("callback", None)
        self._method_delegate.invoke(self._obj_delegate, list(args), callback=callback)


def inject_methods(delegate: Delegate, methods: List[MethodID]):
    """Inject methods into a delegate class

    Idea is to inject a method that is from the server to put into a delegate.
    Now it looks like the delegate has an instance method that actually calls what
    is on the server. Context, is automatically taken care of. This should mostly be
    called on_new or on_update for delegates that have methods. This method clears out any
    old injected methods if present.

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

    Idea is to inject a signal that is from the server to put into a delegate. These signals are stored in a dict
    that can be used to map the signal name to a callable response that handles the signal and its args.

    Args:
        delegate (Delegate):
            delegate object to be injected
        signals (list):
            list of signal id's to be injected
    """

    for signal_id in signals:
        signal = delegate.client.state[signal_id]  # refactored state
        delegate.signals[signal.name] = None


def get_context(delegate: Delegate):
    """Helper to get context from delegate

    Args:
        delegate (Delegate): delegate to get context for, can be Entity, Table, or Plot

    Returns:
        context (dict): context for delegate, None if not found indicating document

    """

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
    """Base class for all ID's

    Each ID is composed of a slot and a generation, resulting in a tuple like id ex. (0, 0). Both are positive
    integers that are filled in increasing order. Slots are taken first, but once the slot is freed, it can be used
    with a new generation. For example, a method is created -> (0, 0), then another is created -> (1, 0), then method
    (0, 0) is deleted. Now, the next method created will be (0, 1).

    Attributes:
        slot (int): Slot of the ID
        gen (int): Generation of the ID
    """

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
    """ID specific to methods"""
    pass


class SignalID(ID):
    """ID specific to signals"""
    pass


class EntityID(ID):
    """ID specific to entities"""
    pass


class PlotID(ID):
    """ID specific to plots"""
    pass


class BufferID(ID):
    """ID specific to buffers"""
    pass


class BufferViewID(ID):
    """ID specific to buffer views"""
    pass


class MaterialID(ID):
    """ID specific to materials"""
    pass


class ImageID(ID):
    """ID specific to images"""
    pass


class TextureID(ID):
    """ID specific to textures"""
    pass


class SamplerID(ID):
    """ID specific to samplers"""
    pass


class LightID(ID):
    """ID specific to lights"""
    pass


class GeometryID(ID):
    """ID specific to geometries"""
    pass


class TableID(ID):
    """ID specific to tables"""
    pass


""" ====================== Generic Parent Class ====================== """


class NoodleObject(BaseModel):
    """Parent Class for all noodle objects"""
    model_config = ConfigDict(arbitrary_types_allowed=True, use_enum_values=True, extra="allow", frozen=False)


class Delegate(NoodleObject):
    """Parent class for all delegates
    
    Defines general methods that should be available for all delegates
    
    Attributes:
        client (Client): Client delegate is attached to
        id (ID): Unique identifier for delegate
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

Vec3 = List[float]  # Length 3
Vec4 = List[float]  # Length 4
Mat3 = List[float]  # Length 9
Mat4 = List[float]  # Length 16


class AttributeSemantic(Enum):
    """String indicating type of attribute, used in Attribute inside of geometry patch

    Takes value of either POSITION, NORMAL, TANGENT, TEXTURE, or COLOR
    """
    position = "POSITION"
    normal = "NORMAL"
    tangent = "TANGENT"
    texture = "TEXTURE"
    color = "COLOR"


class Format(Enum):
    """String indicating format of byte data for an attribute

    Used in Attribute inside of geometry patch. Takes value of either U8, U16, U32, U8VEC4, U16VEC2,
    VEC2, VEC3, VEC4, MAT3, or MAT4
    """

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
    """String indicating format of byte data for an index

   Used in Index inside of geometry patch. Takes value of either U8, U16, or U32
   """
    u8 = "U8"
    u16 = "U16"
    u32 = "U32"


class PrimitiveType(Enum):
    """String indicating type of primitive used in a geometry patch

    Takes value of either POINTS, LINES, LINE_LOOP, LINE_STRIP, TRIANGLES, or TRIANGLE_STRIP
    """
    points = "POINTS"
    lines = "LINES"
    line_loop = "LINE_LOOP"
    line_strip = "LINE_STRIP"
    triangles = "TRIANGLES"
    triangle_strip = "TRIANGLE_STRIP"


class ColumnType(str, Enum):
    """String indicating type of data stored in a column in a table

    Used in TableColumnInfo inside TableInitData. Takes value of either TEXT, REAL, or INTEGER
    """
    text = "TEXT"
    real = "REAL"
    integer = "INTEGER"


class BufferType(str, Enum):
    """String indicating type of data stored in a buffer

    Used in BufferView. Takes value of either UNK, GEOMETRY, or IMAGE
    """
    unknown = "UNK"
    geometry = "GEOMETRY"
    image = "IMAGE"


class SamplerMode(Enum):
    """String options for sampler mode

    Used in Sampler. Takes value of either CLAMP_TO_EDGE, MIRRORED_REPEAT, or REPEAT
    """
    clamp_to_edge = "CLAMP_TO_EDGE"
    mirrored_repeat = "MIRRORED_REPEAT"
    repeat = "REPEAT"


class MagFilterTypes(Enum):
    """Options for magnification filter type

    Used in Sampler. Takes value of either NEAREST or LINEAR
    """
    nearest = "NEAREST"
    linear = "LINEAR"


class MinFilterTypes(Enum):
    """Options for minification filter type

    Used in Sampler. Takes value of either NEAREST, LINEAR, or LINEAR_MIPMAP_LINEAR
    """
    nearest = "NEAREST"
    linear = "LINEAR"
    linear_mipmap_linear = "LINEAR_MIPMAP_LINEAR"


class SelectionRange(NoodleObject):
    """Range of rows to select in a table

    Attributes:
        key_from_inclusive (int): First row to select
        key_to_exclusive (int): Where to end selection, exclusive
    """
    key_from_inclusive: int
    key_to_exclusive: int


class Selection(NoodleObject):
    """Selection of rows in a table

    Attributes:
        name (str): Name of selection
        rows (List[int]): List of rows to select
        row_ranges (List[SelectionRange]): List of ranges of rows to select
    """
    name: str
    rows: Optional[List[int]] = None
    row_ranges: Optional[List[SelectionRange]] = None


class MethodArg(NoodleObject):
    """Argument for a method

    Attributes:
        name (str): Name of argument
        doc (str): Documentation for argument
        editor_hint (str): Hint for editor, refer to message spec for hint options
    """
    name: str
    doc: Optional[str] = None
    editor_hint: Optional[str] = None


class BoundingBox(NoodleObject):
    """Axis-aligned bounding box

    Attributes:
        min (Vec3): Minimum point of bounding box
        max (Vec3): Maximum point of bounding box
    """
    min: Vec3
    max: Vec3


class TextRepresentation(NoodleObject):
    """Text representation for an entity

    Attributes:
        txt (str): Text to display
        font (str): Font to use
        height (Optional[float]): Height of text
        width (Optional[float]): Width of text
    """
    txt: str
    font: Optional[str] = "Arial"
    height: Optional[float] = .25
    width: Optional[float] = -1.0


class WebRepresentation(NoodleObject):
    """Web page with a given URL rendered as a plane

    Attributes:
        source (str): URL for entity
        height (Optional[float]): Height of plane
        width (Optional[float]): Width of plane
    """
    source: str
    height: Optional[float] = .5
    width: Optional[float] = .5


class InstanceSource(NoodleObject):
    """Source of instances for a geometry patch

    Attributes:
        view (BufferViewID): View of mat4
        stride (int): Stride for buffer, defaults to tightly packed
        bb (BoundingBox): Bounding box of instances
    """
    view: BufferViewID
    stride: Optional[int] = 0
    bb: Optional[BoundingBox] = None


class RenderRepresentation(NoodleObject):
    """Render representation for an entity

   Attributes:
       mesh (GeometryID): Mesh to render
       instances (Optional[InstanceSource]): Source of instances for mesh
   """
    mesh: GeometryID
    instances: Optional[InstanceSource] = None


class TextureRef(NoodleObject):
    """Reference to a texture

    Attributes:
        texture (TextureID): Texture to reference
        transform (Optional[Mat3]): Transform to apply to texture
        texture_coord_slot (Optional[int]): Texture coordinate slot to use
    """
    texture: TextureID
    transform: Optional[Mat3] = [1.0, 0.0, 0.0,
                                 0.0, 1.0, 0.0,
                                 0.0, 0.0, 1.0]
    texture_coord_slot: Optional[int] = 0.0


class PBRInfo(NoodleObject):
    """Physically based rendering information for a material

   Attributes:
       base_color (Optional[RGBA]): Base color of material
       base_color_texture (Optional[TextureRef]): Texture to use for base color
       metallic (Optional[float]): Metallic value of material
       roughness (Optional[float]): Roughness value of material
       metal_rough_texture (Optional[TextureRef]): Texture to use for metallic and roughness
   """
    base_color: Optional[Color] = Color('white')
    base_color_texture: Optional[TextureRef] = None  # assume SRGB, no premult alpha

    metallic: Optional[float] = 1.0
    roughness: Optional[float] = 1.0
    metal_rough_texture: Optional[TextureRef] = None  # assume linear, ONLY RG used

    @field_validator("base_color", mode='before')
    def check_color_rgba(cls, value):

        # Raise warning if format is wrong from server
        if len(value) != 4:
            logging.warning(f"Base Color is Wrong Color Format: {value}")
        return value


class PointLight(NoodleObject):
    """Point light information for a light delegate

    Attributes:
        range (float): Range of light, -1 defaults to infinite
    """
    range: float = -1.0


class SpotLight(NoodleObject):
    """Spotlight information for a light delegate

    Attributes:
        range (float): Range of light, -1 defaults to infinite
        inner_cone_angle_rad (float): Inner cone angle of light
        outer_cone_angle_rad (float): Outer cone angle of light
    """
    range: float = -1.0
    inner_cone_angle_rad: float = 0.0
    outer_cone_angle_rad: float = pi/4


class DirectionalLight(NoodleObject):
    """Directional light information for a light delegate

    Attributes:
        range (float): Range of light, -1 defaults to infinite
    """
    range: float = -1.0


class Attribute(NoodleObject):
    """Attribute for a geometry patch

    Each attribute is a view into a buffer that corresponds to a specific element of the mesh
    (e.g. position, normal, etc.). Attributes allow information for the vertices to be extracted from buffers

    Attributes:
        view (BufferViewID): View of the buffer storing the data
        semantic (AttributeSemantic): String describing the type of attribute
        channel (Optional[int]): Channel of attribute, if applicable
        offset (Optional[int]): Offset into buffer
        stride (Optional[int]): Distance, in bytes, between data for two vertices in the buffer
        format (Format): How many bytes per element, how to decode the bytes
        minimum_value (Optional[List[float]]): Minimum value for attribute data
        maximum_value (Optional[List[float]]): Maximum value for attribute data
        normalized (Optional[bool]): Whether to normalize the attribute data
    """
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
    """Index for a geometry patch

    The index is a view into a buffer that corresponds to the indices of the mesh. The index allows the mesh to
    connect vertices and render triangles, lines, or points.

    Attributes:
        view (BufferViewID): View of the buffer storing the data
        count (int): Number of indices
        offset (Optional[int]): Offset into buffer
        stride (Optional[int]): Distance, in bytes, between data for two elements in the buffer
        format (IndexFormat): How many bytes per element, how to decode the bytes
    """
    view: BufferViewID
    count: int
    offset: Optional[int] = 0
    stride: Optional[int] = 0
    format: IndexFormat


class GeometryPatch(NoodleObject):
    """Geometry patch for a mesh

   Principle object used in geometry delegates. A geometry patch combines vertex data from attributes and index data
   from indices.

   Attributes:
       attributes (List[Attribute]): List of attributes storing vertex data for the mesh
       vertex_count (int): Number of vertices in the mesh
       indices (Optional[Index]): Indices for the mesh
       type (PrimitiveType): Type of primitive to render
       material (MaterialID): Material to use for rendering
   """
    attributes: List[Attribute]
    vertex_count: int
    indices: Optional[Index] = None
    type: PrimitiveType
    material: MaterialID  # Material ID


class InvokeIDType(NoodleObject):
    """Context for invoking a signal

    Attributes:
        entity (Optional[EntityID]): Entity to invoke signal on
        table (Optional[TableID]): Table to invoke signal on
        plot (Optional[PlotID]): Plot to invoke signal on
    """
    entity: Optional[EntityID] = None
    table: Optional[TableID] = None
    plot: Optional[PlotID] = None

    @model_validator(mode="after")
    def one_of_three(cls, model):
        num_set = bool(model.entity) + bool(model.table) + bool(model.plot)
        if num_set != 1:
            raise ValueError("Must set exactly one of entity, table, or plot")
        return model


class TableColumnInfo(NoodleObject):
    """Information about a column in a table

    Attributes:
        name (str): Name of column
        type (ColumnType): Type data in the column
    """
    name: str
    type: ColumnType


class TableInitData(NoodleObject):
    """Init data to create a table

    Attributes:
        columns (List[TableColumnInfo]): List of column information
        keys (List[int]): List of column indices that are keys
        data (List[List[Any]]): List of rows of data
        selections (Optional[List[Selection]]): List of selections to apply to table
    """
    columns: List[TableColumnInfo]
    keys: List[int]
    data: List[List[Any]]  # Originally tried union, but currently order is used to coerce by pydantic
    selections: Optional[List[Selection]] = None

    # too much overhead? - strict mode
    @model_validator(mode="after")
    def types_match(cls, model):
        for row in model.data:
            for col, i in zip(model.columns, range(len(row))):
                text_mismatch = isinstance(row[i], str) and col.type != "TEXT"
                real_mismatch = isinstance(row[i], float) and col.type != "REAL"
                int_mismatch = isinstance(row[i], int) and col.type != "INTEGER"
                if text_mismatch or real_mismatch or int_mismatch:
                    raise ValueError(f"Column Info doesn't match type in data: {col, row[i]}")
        return model


""" ====================== NOODLE COMPONENTS ====================== """


class Method(Delegate):
    """A method that clients can request the server to call.

    Attributes:
        id: ID for the method
        name: Name of the method
        doc: Documentation for the method
        return_doc: Documentation for the return value
        arg_doc: Documentation for the arguments
    """

    id: MethodID
    name: str
    doc: Optional[str] = None
    return_doc: Optional[str] = None
    arg_doc: List[MethodArg] = []

    def invoke(self, on_delegate: Delegate, args=None, callback=None):
        """Invoke this delegate's method

        Args:
            on_delegate (Delegate):
                delegate method is being invoked on 
                used to get context
            args (list, optional):
                args for the method
            callback (function):
                function to be called when complete

        Raises:
            ValueError: Invalid delegate context
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
        self.client.invoke_method(self.id, args, context=context, callback=callback)

    def __str__(self) -> str:
        """Custom string representation for methods"""

        rep = f"{self.name}:\n\t{self.doc}\n\tReturns: {self.return_doc}\n\tArgs:"
        for arg in self.arg_doc:
            rep += f"\n\t\t{arg.name}: {arg.doc}"
        return rep


class Signal(Delegate):
    """A signal that the server can send to update clients.

    Attributes:
        id: ID for the signal
        name: Name of the signal
        doc: Documentation for the signal
        arg_doc: Documentation for the arguments
    """
    id: SignalID
    name: str
    doc: Optional[str] = None
    arg_doc: List[MethodArg] = []


class Entity(Delegate):
    """Container for other entities, possibly renderable, has associated methods and signals

    Attributes:
        id: ID for the entity
        name: Name of the entity
        parent: Parent entity
        transform: Local transform for the entity
        text_rep: Text representation for the entity
        web_rep: Web representation for the entity
        render_rep: Render representation for the entity
        lights: List of lights attached to the entity
        tables: List of tables attached to the entity
        plots: List of plots attached to the entity
        tags: List of tags for the entity
        methods_list: List of methods attached to the entity
        signals_list: List of signals attached to the entity
        influence: Bounding box for the entity
    """
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

    # Injected methods
    set_position: Optional[InjectedMethod] = None
    set_rotation: Optional[InjectedMethod] = None
    set_scale: Optional[InjectedMethod] = None
    activate: Optional[InjectedMethod] = None
    get_activation_choices: Optional[InjectedMethod] = None
    get_var_keys: Optional[InjectedMethod] = None
    get_var_options: Optional[InjectedMethod] = None
    get_var_value: Optional[InjectedMethod] = None
    set_var_value: Optional[InjectedMethod] = None
    select_region: Optional[InjectedMethod] = None
    select_sphere: Optional[InjectedMethod] = None
    select_half_plane: Optional[InjectedMethod] = None
    select_hull: Optional[InjectedMethod] = None
    probe_at: Optional[InjectedMethod] = None

    def on_new(self, message: dict):

        # Inject methods and signals if applicable
        if self.methods_list:
            inject_methods(self, self.methods_list)
        if self.signals_list:
            inject_signals(self, self.signals_list)

    def on_update(self, message: dict):

        # Inject methods and signals if applicable
        if self.methods_list:
            inject_methods(self, self.methods_list)
        if self.signals_list:
            inject_signals(self, self.signals_list)

    def request_set_position(self, position: Vec3):
        """Request to set the position of the entity

        Args:
            position (Vec3): Position to set
        """
        self.set_position(position)

    def request_set_rotation(self, rotation: Vec4):
        """Request to set the rotation of the entity

        Args:
            rotation (Vec4): Rotation to set
        """
        self.set_rotation(rotation)

    def request_set_scale(self, scale: Vec3):
        """Request to set the scale of the entity

        Args:
            scale (Vec3): Scale to set
        """
        self.set_scale(scale)

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
    """An abstract plot object.

    Attributes:
        id: ID for the plot
        name: Name of the plot
        table: Table to plot
        simple_plot: Simple plot to render
        url_plot: URL for plot to render
        methods_list: List of methods attached to the plot
        signals_list: List of signals attached to the plot
    """
    id: PlotID
    name: Optional[str] = "Unnamed Plot Delegate"

    table: Optional[TableID] = None

    simple_plot: Optional[str] = None
    url_plot: Optional[str] = None

    methods_list: Optional[List[MethodID]] = None
    signals_list: Optional[List[SignalID]] = None

    @model_validator(mode="after")
    def one_of(cls, model):
        if bool(model.simple_plot) != bool(model.url_plot):
            return model
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
    """A buffer of bytes containing data for an image or a mesh.

    Attributes:
        id: ID for the buffer
        name: Name of the buffer
        size: Size of the buffer in bytes
        inline_bytes: Bytes of the buffer
        uri_bytes: URI for the bytes
    """
    id: BufferID
    name: Optional[str] = "Unnamed Buffer Delegate"
    size: int

    inline_bytes: Optional[bytes] = None
    uri_bytes: Optional[str] = None

    @model_validator(mode="after")
    def one_of(cls, model):
        if bool(model.inline_bytes) != bool(model.uri_bytes):
            return model
        else:
            raise ValueError("One plot type must be specified")


class BufferView(Delegate):
    """A view into a buffer, specifying a subset of the buffer and how to interpret it.

    Attributes:
        id: ID for the buffer view
        name: Name of the buffer view
        source_buffer: Buffer that the view is referring to
        type: Type of the buffer view
        offset: Offset into the buffer in bytes
        length: Length of the buffer view in bytes
    """
    id: BufferViewID
    name: Optional[str] = "Unnamed Buffer-View Delegate"
    source_buffer: BufferID

    type: BufferType = BufferType.unknown
    offset: int
    length: int

    @field_validator("type", mode='before')
    def coerce_type(cls, value):
        if value in ["UNK", "GEOMETRY", "IMAGE"]:
            return value

        if "GEOMETRY" in value.upper():
            logging.warning(f"Buffer View Type does not meet the specification: {value} coerced to 'GEOMETRY'")
            return "GEOMETRY"
        elif "IMAGE" in value.upper():
            logging.warning(f"Buffer View Type does not meet the specification: {value} coerced to 'IMAGE'")
            return "IMAGE"
        else:
            logging.warning(f"Buffer View Type does not meet the specification: {value} coerced to 'UNK'")
            return "UNK"


class Material(Delegate):
    """A material that can be applied to a mesh.

    Attributes:
        id: ID for the material
        name: Name of the material
        pbr_info: Information for physically based rendering
        normal_texture: Texture for normals
        occlusion_texture: Texture for occlusion
        occlusion_texture_factor: Factor for occlusion
        emissive_texture: Texture for emissive
        emissive_factor: Factor for emissive
        use_alpha: Whether to use alpha
        alpha_cutoff: Alpha cutoff
        double_sided: Whether the material is double-sided
    """
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
    """An image, can be used for a texture

    Attributes:
        id: ID for the image
        name: Name of the image
        buffer_source: Buffer that the image is stored in
        uri_source: URI for the bytes if they are hosted externally
    """
    id: ImageID
    name: Optional[str] = "Unnamed Image Delegate"

    buffer_source: Optional[BufferID] = None
    uri_source: Optional[str] = None

    @model_validator(mode="after")
    def one_of(cls, model):
        if bool(model.buffer_source) != bool(model.uri_source):
            return model
        else:
            raise ValueError("One plot type must be specified")


class Texture(Delegate):
    """A texture, can be used for a material

    Attributes:
        id: ID for the texture
        name: Name of the texture
        image: Image to use for the texture
        sampler: Sampler to use for the texture
    """
    id: TextureID
    name: Optional[str] = "Unnamed Texture Delegate"
    image: ImageID
    sampler: Optional[SamplerID] = None


class Sampler(Delegate):
    """A sampler to use for a texture

   Attributes:
       id: ID for the sampler
       name: Name of the sampler
       mag_filter: Magnification filter
       min_filter: Minification filter
       wrap_s: Wrap mode for S
       wrap_t: Wrap mode for T
   """
    id: SamplerID
    name: Optional[str] = "Unnamed Sampler Delegate"

    mag_filter: Optional[MagFilterTypes] = MagFilterTypes.linear
    min_filter: Optional[MinFilterTypes] = MinFilterTypes.linear_mipmap_linear

    wrap_s: Optional[SamplerMode] = "REPEAT"
    wrap_t: Optional[SamplerMode] = "REPEAT"


class Light(Delegate):
    """Represents a light in the scene

    Attributes:
        id: ID for the light
        name: Name of the light
        color: Color of the light
        intensity: Intensity of the light
        point: Point light information
        spot: Spotlight information
        directional: Directional light information
    """
    id: LightID
    name: Optional[str] = "Unnamed Light Delegate"

    color: Optional[Color] = Color('white')
    intensity: Optional[float] = 1.0

    point: Optional[PointLight] = None
    spot: Optional[SpotLight] = None
    directional: Optional[DirectionalLight] = None

    @field_validator("color", mode='before')
    def check_color_rgb(cls, value):

        # Raise warning if format is wrong
        if len(value) != 3:
            logging.warning(f"Color is not RGB in Light: {value}")
        return value

    @model_validator(mode="after")
    def one_of(cls, model):
        num_selected = bool(model.point) + bool(model.spot) + bool(model.directional)
        if num_selected > 1:
            raise ValueError("Only one light type can be selected")
        elif num_selected == 0:
            raise ValueError("No light type selected")
        else:
            return model


class Geometry(Delegate):
    """Represents geometry in the scene and can be used for meshes

    Attributes:
        id: ID for the geometry
        name: Name of the geometry
        patches: Patches that make up the geometry
    """
    id: GeometryID
    name: Optional[str] = "Unnamed Geometry Delegate"
    patches: List[GeometryPatch]


class Table(Delegate):
    """Object to store tabular data.

    Attributes:
        id: ID for the table
        name: Name of the table
        meta: Metadata for the table
        methods_list: List of methods for the table
        signals_list: List of signals for the table
        tbl_subscribe: Injected method to subscribe to the table
        tbl_insert: Injected method to insert rows into the table
        tbl_update: Injected method to update rows in the table
        tbl_remove: Injected method to remove rows from the table
        tbl_clear: Injected method to clear the table
        tbl_update_selection: Injected method to update the selection
    """
    id: TableID
    name: Optional[str] = f"Unnamed Table Delegate"

    meta: Optional[str] = None
    methods_list: Optional[List[MethodID]] = None
    signals_list: Optional[List[SignalID]] = None

    tbl_subscribe: Optional[InjectedMethod] = None
    tbl_insert: Optional[InjectedMethod] = None
    tbl_update: Optional[InjectedMethod] = None
    tbl_remove: Optional[InjectedMethod] = None
    tbl_clear: Optional[InjectedMethod] = None
    tbl_update_selection: Optional[InjectedMethod] = None

    def __init__(self, **kwargs):
        """Override init to link default values with methods"""
        super().__init__(**kwargs)
        self.signals = {
            "noo::tbl_reset": self._reset_table,
            "noo::tbl_rows_removed": self._remove_rows,
            "noo::tbl_updated": self._update_rows,
            "noo::tbl_selection_updated": self._update_selection
        }

    def _on_table_init(self, init_info: dict, callback=None):
        """Creates table from server response info

        Args:
            init_info (Message Obj): 
                Server response to subscribe which has columns, keys, data, 
                and possibly selections
        """

        init = TableInitData(**init_info)
        logging.info(f"Table Initialized with cols: {init.columns} and row data: {init.data}")
        if callback:
            callback()

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

        Injecting signals adds them as keys which map to None. The signals must be relinked after injecting.
        These should always be linked, along with whatever is injected.
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

        # Check contents
        methods = self.methods_list
        signals = self.signals_list

        # Inject methods and signals if applicable
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

        # Inject methods and signals if applicable
        if self.methods_list:
            inject_methods(self, self.methods_list)
        if self.signals_list:
            inject_signals(self, self.signals_list)
        self.relink_signals()

    def subscribe(self, callback: Callable = None):
        """Subscribe to this delegate's table

        Calls on_table_init as callback

        Args:
              callback (Callable): function to be called after table is subscribed to and initialized

        Raises:
            Exception: Could not subscribe to table
        """

        try:
            # Allow for callback after table init
            self.tbl_subscribe(callback=lambda data: self._on_table_init(data, callback))
        except Exception as e:
            raise Exception(f"Could not subscribe to table {self.id}...{e}")

    def request_insert(self, row_list: List[List[int]], callback=None):
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
            callback (function, optional): callback function
        """

        self.tbl_insert(row_list, callback=callback)

    def request_update(self, keys: List[int], rows: List[List[int]], callback=None):
        """Update the table using a DataFrame

        User endpoint for interacting with table and invoking method

        Args:
            keys (list[int]):
                list of keys to update
            rows (list[list[int]]):
                list of new rows to update with
            callback (function, optional):
                callback function called when complete
        """

        self.tbl_update(keys, rows, callback=callback)

    def request_remove(self, keys: List[int], callback=None):
        """Remove rows from table by their keys

        User endpoint for interacting with table and invoking method

        Args:
            keys (list):
                list of keys for rows to be removed
            callback (function, optional):
                callback function called when complete
        """

        self.tbl_remove(keys, callback=callback)

    def request_clear(self, callback=None):
        """Clear the table

        User endpoint for interacting with table and invoking method

        Args:
            callback (function, optional): callback function called when complete
        """
        self.tbl_clear(callback=callback)

    def request_update_selection(self, name: str, keys: List[int], callback=None):
        """Update a selection object in the table

        User endpoint for interacting with table and invoking method

        Args:
            name (str):
                name of the selection object to be updated
            keys (list):
                list of keys to be in new selection
            callback (function, optional):
                callback function called when complete
        """
        selection = Selection(name=name, rows=keys)
        self.tbl_update_selection(selection.model_dump(), callback=callback)

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
    """Delegate for document

    Attributes:
        name (str): name will be "Document"
        methods_list (list[MethodID]): list of methods available on the document
        signals_list (list[SignalID]): list of signals available on the document
    """

    name: str = "Document"

    methods_list: List[MethodID] = []  # Server usually sends as an update
    signals_list: List[SignalID] = []

    client_view: Optional[InjectedMethod] = None

    def on_update(self, message: dict):
        """Handler when update message is received

        Should update methods_list and signals_list

        Args:
            message (Message): update message with the new document's info
        """
        if "methods_list" in message:
            self.methods_list = [MethodID(*element) for element in message["methods_list"]]
            inject_methods(self, self.methods_list)
        if "signals_list" in message:
            self.signals_list = [SignalID(*element) for element in message["signals_list"]]

    def reset(self):
        """Reset the document

        Called when document reset message is received. Will reset state, and clear methods and signals on document
        """
        self.client.state = {"document": self}
        self.methods_list = []
        self.signals_list = []

    def update_client_view(self, direction: Vec3, angle: float):
        """Notify the server of an area of interest for the client"""

        self.client_view(direction, angle)

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
    """Exception raised when invoking a method

    Will be sent as part of a reply message

    Attributes:
        code (int): error code
        message (str): error message
        data (Any): data associated with the error
    """
    code: int
    message: Optional[str] = None
    data: Optional[Any] = None


class Reply(NoodleObject):
    """Reply message sent from server in response to method invocation

    Will either contain resulting data, or an exception

    Attributes:
        invoke_id (str): id of the invoke message that this is a reply to
        result (Any): result of the method invocation
        method_exception (MethodException): exception raised when invoking method
    """
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
