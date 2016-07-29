#+
# Python-3 binding for (parts of) HarfBuzz.
#-

import ctypes as ct
from weakref import \
    WeakValueDictionary
try :
    import freetype2 as freetype
except ImportError :
    freetype = None
#end try

hb = ct.cdll.LoadLibrary("libharfbuzz.so.0")

def seq_to_ct(seq, ct_type, conv = None) :
    "extracts the elements of a Python sequence value into a ctypes array" \
    " of type ct_type, optionally applying the conv function to each value.\n" \
    "\n" \
    "Why doesn’t ctypes make this easy?"
    if conv == None :
        conv = lambda x : x
    #end if
    nr_elts = len(seq)
    result = (nr_elts * ct_type)()
    for i in range(nr_elts) :
        result[i] = conv(seq[i])
    #end for
    return \
        result
#end seq_to_ct

class HARFBUZZ :
    "useful definitions adapted from harfbuzz/*.h. You will need to use the constants" \
    " and “macro” functions, but apart from that, see the more Pythonic wrappers" \
    " defined outside this class in preference to accessing low-level structures directly."

    # General ctypes gotcha: when passing addresses of ctypes-constructed objects
    # to routine calls, do not construct the objects directly in the call. Otherwise
    # the refcount goes to 0 before the routine is actually entered, and the object
    # can get prematurely disposed. Always store the object reference into a local
    # variable, and pass the value of the variable instead.

    # from hb-common.h:

    bool_t = ct.c_int
    codepoint_t = ct.c_uint
    position_t = ct.c_int # fixed 16.6?
    mask_t = ct.c_uint

    to_position_t = lambda x : round(x * 64)
    from_position_t = lambda x : x / 64

    class var_int_t(ct.Union) :
        _fields_ = \
            [
                ("u32", ct.c_uint),
                ("i32", ct.c_int),
                ("u16", ct.c_ushort),
                ("i16", ct.c_short),
                ("u8", ct.c_ubyte),
                ("i8", ct.c_byte),
            ]
    #end var_int_t

    tag_t = ct.c_uint

    def TAG(c1, c2, c3, c4) :
        "creates a tag_t from four byte values."
        return \
            c1 << 24 | c2 << 16 | c3 << 8 | c4
    #end TAG

    def UNTAG(tag) :
        "decomposes a tag_t into a tuple of four byte values."
        return \
            (tag >> 24 & 255, tag >> 16 & 255, tag >> 8 & 255, tag & 255)
    #end UNTAG

    TAG_NONE = TAG(0, 0, 0, 0)
    TAG_MAX = TAG(0xff, 0xff, 0xff, 0xff)
    TAG_MAX_SIGNED = TAG(0x7f, 0xff, 0xff, 0xff)
    # more TAG_xxx values todo

    direction_t = ct.c_uint
    DIRECTION_INVALID = 0
    DIRECTION_LTR = 4
    DIRECTION_RTL = 5
    DIRECTION_TTB = 6
    DIRECTION_BTT = 7

    script_t = ct.c_uint
    # SCRIPT_xxx values todo
    SCRIPT_INVALID = TAG_NONE

    destroy_func_t = ct.CFUNCTYPE(None, ct.c_void_p)

    # from hb-blob.h:

    memory_mode = ct.c_uint
    MEMORY_MODE_DUPLICATE = 0
    MEMORY_MODE_READONLY = 1
    MEMORY_MODE_WRITABLE = 2
    MEMORY_MODE_READONLY_MAY_MAKE_WRITABLE = 3

    # from hb-buffer.h:

    buffer_content_type_t = ct.c_uint
    BUFFER_CONTENT_TYPE_INVALID = 0
    BUFFER_CONTENT_TYPE_UNICODE = 1
    BUFFER_CONTENT_TYPE_GLYPHS = 2

    buffer_flags_t = ct.c_uint
    BUFFER_FLAG_DEFAULT = 0x00000000
    BUFFER_FLAG_BOT = 0x00000001 # Beginning-of-text
    BUFFER_FLAG_EOT = 0x00000002 # End-of-text
    BUFFER_FLAG_PRESERVE_DEFAULT_IGNORABLES = 0x00000004

    buffer_cluster_level_t = ct.c_uint
    BUFFER_CLUSTER_LEVEL_MONOTONE_GRAPHEMES = 0
    BUFFER_CLUSTER_LEVEL_MONOTONE_CHARACTERS = 1
    BUFFER_CLUSTER_LEVEL_CHARACTERS = 2
    BUFFER_CLUSTER_LEVEL_DEFAULT = BUFFER_CLUSTER_LEVEL_MONOTONE_GRAPHEMES

    # The default code point for replacing invalid characters in a given encoding
    BUFFER_REPLACEMENT_CODEPOINT_DEFAULT = 0xFFFD

    class segment_properties_t(ct.Structure) :
        pass
    segment_properties_t._fields_ = \
        [
            ("direction", direction_t),
            ("script", script_t),
            ("language", ct.c_void_p), # language_t
            # private
            ("reserved1", ct.c_void_p),
            ("reserved2", ct.c_void_p),
        ]
    #end segment_properties_t

    SEGMENT_PROPERTIES_DEFAULT = \
        segment_properties_t \
          (
            DIRECTION_INVALID,
            SCRIPT_INVALID,
            None, # Language.INVALID
            None,
            None,
          )

    class glyph_info_t(ct.Structure) :
        pass
    glyph_info_t._fields_ = \
        [
            ("codepoint", codepoint_t),
            ("mask", mask_t),
            ("cluster", ct.c_uint),
            # private
            ("var1", var_int_t),
            ("var2", var_int_t),
        ]
    #end glyph_info_t

    class glyph_position_t(ct.Structure) :
        pass
    glyph_position_t._fields_ = \
        [
            ("x_advance", position_t),
            ("y_advance", position_t),
            ("x_offset", position_t),
            ("y_offset", position_t),
            # private
            ("var", var_int_t),
        ]
    #end glyph_position_t

    # from hb-font.h:

    class font_extents_t(ct.Structure) :
        pass
    # Note that typically ascender is positive and descender negative in
    # coordinate systems that grow up.
    font_extents_t._fields_ = \
        [
            ("ascender", position_t), # typographic ascender.
            ("descender", position_t), # typographic descender.
            ("line_gap", position_t), # suggested line spacing gap.
            # private
            ("reserved9", position_t),
            ("reserved8", position_t),
            ("reserved7", position_t),
            ("reserved6", position_t),
            ("reserved5", position_t),
            ("reserved4", position_t),
            ("reserved3", position_t),
            ("reserved2", position_t),
            ("reserved1", position_t),
        ]
    #end font_extents_t

    class glyph_extents_t(ct.Structure) :
        pass
    glyph_extents_t._fields_ = \
        [
            ("x_bearing", position_t), # left side of glyph from origin.
            ("y_bearing", position_t), # top side of glyph from origin.
            ("width", position_t), # distance from left to right side.
            ("height", position_t), # distance from top to bottom side.
        ]
    #end glyph_extents_t

    # hb_xxx_func_t types todo

    # from hb-shape.h:

    class feature_t(ct.Structure) :
        pass
    feature_t._fields_ = \
        [
            ("tag", tag_t),
            ("value", ct.c_uint),
            ("start", ct.c_uint),
            ("end", ct.c_uint),
        ]
    #end feature_t

    # more TBD

#end HARFBUZZ
HB = HARFBUZZ # if you prefer

def def_struct_class(name, ctname, conv = None, extra = None) :
    # defines a class with attributes that are a straightforward mapping
    # of a ctypes struct. Optionally includes extra members from extra
    # if specified.

    ctstruct = getattr(HARFBUZZ, ctname)

    class result_class :

        __slots__ = tuple(field[0] for field in ctstruct._fields_) # to forestall typos

        def to_hb(self) :
            "returns a HarfBuzz representation of the structure."
            result = ctstruct()
            for name, cttype in ctstruct._fields_ :
                val = getattr(self, name)
                if val != None and conv != None and name in conv :
                    val = conv[name]["to"](val)
                #end if
                setattr(result, name, val)
            #end for
            return \
                result
        #end to_hb

        @staticmethod
        def from_hb(r) :
            "decodes the HarfBuzz representation of the structure."
            result = result_class()
            for name, cttype in ctstruct._fields_ :
                val = getattr(r, name)
                if val != None and conv != None and name in conv :
                    val = conv[name]["from"](val)
                #end if
                setattr(result, name, val)
            #end for
            return \
                result
        #end from_hb

        def __getitem__(self, i) :
            "allows the object to be coerced to a tuple."
            return \
                getattr(self, ctstruct._fields_[i][0])
        #end __getitem__

        def __repr__(self) :
            return \
                (
                    "%s(%s)"
                %
                    (
                        name,
                        ", ".join
                          (
                            "%s = %s" % (field[0], getattr(self, field[0]))
                            for field in ctstruct._fields_
                          ),
                    )
                )
        #end __repr__

    #end result_class

#begin def_struct_class
    result_class.__name__ = name
    result_class.__doc__ = \
        (
            "representation of a HarfBuzz %s structure. Fields are %s."
            "\nCreate by decoding the HarfBuzz form with the from_hb method;"
            " convert an instance to HarfBuzz form with the to_hb method."
        %
            (
                ctname,
                ", ".join(f[0] for f in ctstruct._fields_),
            )
        )
    if extra != None :
        for attr in dir(extra) :
            if not attr.startswith("__") :
                setattr(result_class, attr, getattr(extra, attr))
            #end if
        #end for
    #end if
    return \
        result_class
#end def_struct_class

#+
# Routine arg/result types
#-

hb.hb_version.restype = None
hb.hb_version.argtypes = (ct.POINTER(ct.c_uint), ct.POINTER(ct.c_uint), ct.POINTER(ct.c_uint))
hb.hb_version_atleast.restype = HB.bool_t
hb.hb_version_atleast.argtypes = (ct.c_uint, ct.c_uint, ct.c_uint)
hb.hb_version_string.restype = ct.c_char_p
hb.hb_version_string.argtypes = ()
hb.hb_language_from_string.restype = ct.c_void_p
hb.hb_language_from_string.argtypes = (ct.c_char_p, ct.c_int)
hb.hb_language_to_string.restype = ct.c_char_p
hb.hb_language_to_string.argtypes = (ct.c_void_p,)
hb.hb_language_get_default.restype = ct.c_void_p
hb.hb_language_get_default.argtypes = ()

hb.hb_blob_create.restype = ct.c_void_p
hb.hb_blob_create.argtypes = (ct.c_void_p, ct.c_uint, ct.c_uint, ct.c_void_p, ct.c_void_p)
hb.hb_blob_create_sub_blob.restype = ct.c_void_p
hb.hb_blob_create_sub_blob.argtypes = (ct.c_void_p, ct.c_uint, ct.c_uint)
hb.hb_blob_get_empty.restype = ct.c_void_p
hb.hb_blob_get_empty.argtypes = ()
hb.hb_blob_destroy.restype = None
hb.hb_blob_destroy.argtypes = (ct.c_void_p,)
hb.hb_blob_make_immutable.restype = None
hb.hb_blob_make_immutable.argtypes = (ct.c_void_p,)
hb.hb_blob_is_immutable.restype = HB.bool_t
hb.hb_blob_is_immutable.argtypes = (ct.c_void_p,)
hb.hb_blob_get_length.restype = ct.c_uint
hb.hb_blob_get_length.argtypes = (ct.c_void_p,)
hb.hb_blob_get_data.restype = ct.c_void_p
hb.hb_blob_get_data.argtypes = (ct.c_void_p, ct.POINTER(ct.c_uint))
hb.hb_blob_get_data_writable.restype = ct.c_void_p
hb.hb_blob_get_data_writable.argtypes = (ct.c_void_p, ct.POINTER(ct.c_uint))

hb.hb_buffer_destroy.restype = None
hb.hb_buffer_create.restype = ct.c_void_p
hb.hb_buffer_create.argtypes = ()
hb.hb_buffer_destroy.restype = None
hb.hb_buffer_destroy.argtypes = (ct.c_void_p,)
hb.hb_buffer_get_empty.restype = ct.c_void_p
hb.hb_buffer_get_empty.argtypes = ()
hb.hb_buffer_reset.restype = None
hb.hb_buffer_reset.argtypes = (ct.c_void_p,)
hb.hb_buffer_clear_contents.restype = None
hb.hb_buffer_clear_contents.argtypes = (ct.c_void_p,)
hb.hb_buffer_pre_allocate.restype = HB.bool_t
hb.hb_buffer_pre_allocate.arg_types = (ct.c_void_p, ct.c_uint)
hb.hb_buffer_allocation_successful.restype = HB.bool_t
hb.hb_buffer_allocation_successful.argtypes = (ct.c_void_p,)
hb.hb_buffer_add.restype = None
hb.hb_buffer_add.argtypes = (ct.c_void_p, HB.codepoint_t, ct.c_uint)
hb.hb_buffer_add_codepoints.restype = None
hb.hb_buffer_add_codepoints.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_int, ct.c_uint, ct.c_int)
hb.hb_buffer_set_content_type.restype = None
hb.hb_buffer_set_content_type.argtypes = (ct.c_void_p, HB.buffer_content_type_t)
hb.hb_buffer_get_content_type.restype = HB.buffer_content_type_t
hb.hb_buffer_get_content_type.argtypes = (ct.c_void_p,)
hb.hb_buffer_set_direction.restype = None
hb.hb_buffer_set_direction.argtypes = (ct.c_void_p, HB.direction_t)
hb.hb_buffer_get_direction.restype = HB.direction_t
hb.hb_buffer_get_direction.argtypes = (ct.c_void_p,)
hb.hb_buffer_set_script.restype = None
hb.hb_buffer_set_script.argtypes = (ct.c_void_p, HB.script_t)
hb.hb_buffer_get_script.restype = HB.script_t
hb.hb_buffer_get_script.argtypes = (ct.c_void_p,)
hb.hb_buffer_set_language.restype = None
hb.hb_buffer_set_language.argtypes = (ct.c_void_p, ct.c_void_p)
hb.hb_buffer_get_language.restype = ct.c_void_p
hb.hb_buffer_get_language.argtypes = (ct.c_void_p,)
hb.hb_buffer_set_flags.restype = None
hb.hb_buffer_set_flags.argtypes = (ct.c_void_p, HB.buffer_flags_t)
hb.hb_buffer_get_flags.restype = HB.buffer_flags_t
hb.hb_buffer_get_flags.argtypes = (ct.c_void_p,)
hb.hb_buffer_set_cluster_level.restype = None
hb.hb_buffer_set_cluster_level.argtypes = (ct.c_void_p, HB.buffer_cluster_level_t)
hb.hb_buffer_get_cluster_level.restype = HB.buffer_cluster_level_t
hb.hb_buffer_get_cluster_level.argtypes = (ct.c_void_p,)
hb.hb_buffer_set_length.restype = None
hb.hb_buffer_set_length.argtypes = (ct.c_void_p, ct.c_uint)
hb.hb_buffer_get_length.restype = ct.c_uint
hb.hb_buffer_get_length.argtypes = (ct.c_void_p,)
hb.hb_buffer_set_segment_properties.restype = None
hb.hb_buffer_set_segment_properties.argtypes = (ct.c_void_p, ct.c_void_p)
hb.hb_buffer_get_segment_properties.restype = None
hb.hb_buffer_get_segment_properties.argtypes = (ct.c_void_p, ct.c_void_p)
hb.hb_buffer_guess_segment_properties.restype = None
hb.hb_buffer_guess_segment_properties.argtypes = (ct.c_void_p,)
hb.hb_buffer_get_glyph_infos.restype = ct.c_void_p
hb.hb_buffer_get_glyph_infos.argtypes = (ct.c_void_p, ct.POINTER(ct.c_uint))
hb.hb_buffer_get_glyph_positions.restype = ct.c_void_p
hb.hb_buffer_get_glyph_positions.argtypes = (ct.c_void_p, ct.POINTER(ct.c_uint))
hb.hb_buffer_normalize_glyphs.restype = ct.c_void_p
hb.hb_buffer_normalize_glyphs.argtypes = (ct.c_void_p,)
hb.hb_buffer_reverse.restype = ct.c_void_p
hb.hb_buffer_reverse.argtypes = (ct.c_void_p,)
hb.hb_buffer_reverse_range.restype = ct.c_void_p
hb.hb_buffer_reverse_range.argtypes = (ct.c_void_p, ct.c_uint, ct.c_uint)
hb.hb_buffer_reverse_clusters.restype = ct.c_void_p
hb.hb_buffer_reverse_clusters.argtypes = (ct.c_void_p,)
hb.hb_buffer_set_replacement_codepoint.restype = None
hb.hb_buffer_set_replacement_codepoint.argtypes = (ct.c_void_p, HB.codepoint_t)
hb.hb_buffer_get_replacement_codepoint.restype = HB.codepoint_t
hb.hb_buffer_get_replacement_codepoint.argtypes = (ct.c_void_p,)

hb.hb_face_create.restype = ct.c_void_p
hb.hb_face_create.argtypes = (ct.c_void_p, ct.c_uint)
hb.hb_face_destroy.restype = None
hb.hb_face_destroy.argtypes = (ct.c_void_p,)
hb.hb_face_get_empty.restype = ct.c_void_p
hb.hb_face_get_empty.argtypes = ()

hb.hb_font_destroy.restype = None
hb.hb_font_destroy.argtypes = (ct.c_void_p,)

hb.hb_ft_face_create_referenced.restype = ct.c_void_p
hb.hb_ft_face_create_referenced.argtypes = (ct.c_void_p,)
hb.hb_ft_font_create_referenced.restype = ct.c_void_p
hb.hb_ft_font_create_referenced.argtypes = (ct.c_void_p,)
hb.hb_ft_font_set_load_flags.restype = None
hb.hb_ft_font_set_load_flags.argtypes = (ct.c_void_p, ct.c_int)
hb.hb_ft_font_get_load_flags.restype = ct.c_int
hb.hb_ft_font_get_load_flags.argtypes = (ct.c_void_p,)

hb.hb_feature_from_string.restype = HB.bool_t
hb.hb_feature_from_string.argtypes = (ct.c_void_p, ct.c_int, ct.c_void_p)
hb.hb_feature_to_string.restype = None
hb.hb_feature_to_string.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_uint)
hb.hb_shape.restype = None
hb.hb_shape.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_uint)
hb.hb_shape_full.restype = HB.bool_t
hb.hb_shape_full.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_uint, ct.c_void_p)
hb.hb_shape_list_shapers.restype = ct.c_void_p
hb.hb_shape_list_shapers.argtypes = ()
# more TBD

#+
# Higher-level stuff begins here
#-

# from hb-version.h:

def version() :
    "returns a 3-integer-tuple version (major, minor, micro)."
    major = ct.c_uint()
    minor = ct.c_uint()
    micro = ct.c_uint()
    hb.hb_version(ct.byref(major), ct.byref(minor), ct.byref(micro))
    return \
        major.value, minor.value, micro.value
#end version

def version_atleast(major, minor, micro) :
    "is the HarfBuzz version at least that specified."
    return \
        bool(hb.hb_version_atleast(major, minor, micro))
#end version_atleast

def version_string() :
    "returns the version string."
    return \
        hb.hb_version_string().decode()
#end version_string

# from hb-common.h:

class Language :
    "wraps the hb_language_t opaque type. Do not instantiate directly; use" \
    " the from_string() and default() methods."

    __slots__ = \
        ( # to forestall typos
            "_hbobj",
            "__weakref__",
        )

    _instances = WeakValueDictionary()

    INVALID = None # use to indicate invalid Language

    def __new__(celf, _hbobj) :
        self = celf._instances.get(_hbobj)
        if self == None :
            self = super().__new__(celf)
            self._hbobj = _hbobj
            celf._instances[_hbobj] = self
        #end if
        return \
            self
    #end __new__

    # no __del__ -- these objects are never freed

    @classmethod
    def default(celf) :
        return \
            Language(hb.hb_language_get_default())
    #end default

    @classmethod
    def from_string(celf, s) :
        sb = s.encode()
        result = hb.hb_language_from_string(sb, len(sb))
        if result == None :
            raise ValueError("invalid language “%s”" % s)
        #end if
        return \
            Language(result)
    #end from_string

    def to_string(self) :
        return \
            hb.hb_language_to_string(self._hbobj).decode() # automatically stops at NUL?
    #end to_string

    def __repr__(self) :
        return \
            "<Language>(%s)" % self.to_string()
    #end __repr__

#end Language

# from hb-blob.h:

class Blob :
    "wraps the hb_blob_t opaque type. Do not instantiate directly; use" \
    " the create and get_empty methods."

    __slots__ = \
        ( # to forestall typos
            "_hbobj",
            "__weakref__",
        )

    _instances = WeakValueDictionary()

    def __new__(celf, _hbobj) :
        self = celf._instances.get(_hbobj)
        if self == None :
            self = super().__new__(celf)
            self._hbobj = _hbobj
            celf._instances[_hbobj] = self
        #end if
        return \
            self
    #end __new__

    def __del__(self) :
        if self._hbobj != None :
            hb.hb_blob_destroy(self._hbobj)
            self._hbobj = None
        #end if
    #end __del__

    @staticmethod
    def create_for_array(arr, mode, destroy) :
        "creates a Blob that wraps the storage for the specified array.array object." \
        " mode is one of the MEMORY_MODE_XXX values."
        if destroy != None :
            raise NotImplementedError("no destroy arg for now")
        #end if
        bufinfo = arr.buffer_info()
        return \
            Blob(hb.hb_blob_create(bufinfo[0], bufinfo[1], mode, None, None))
    #end create_for_array

    def create_sub(self, offset, length) :
        "creates a sub-Blob spanning the specified range of bytes in the parent." \
        " parent mode is set to immutable, while new blob seems to inherit" \
        " previous parent mutability setting?"
        return \
            Blob(hb.hb_blob_create_sub_blob(self._hbobj, offset, length))
    #end create_sub

    @staticmethod
    def get_empty() :
        "returns the empty Blob."
        return \
            Blob(hb.hb_blob_get_empty())
    #end get_empty

    def __len__(self) :
        "the length of the Blob data."
        return \
            hb.hb_get_length(self._hbobj)
    #end __len__

    def data(self, writable) :
        "returns a tuple (addr, length) of the Blob."
        length = ct.c_uint()
        addr = (hb.hb_blob_get_data, hb.hb_blob_get_data_writable)[writable] \
            (self._hbobj, ct.byref(length))
        if addr == None :
            raise ValueError("failed to get blob data")
        #end if
        return \
            addr, length.value
    #end data

    @property
    def immutable(self) :
        "is the Blob immutable."
        return \
            hb.hb_blob_is_immutable(self._hbobj) != 0
    #end immutable

    @immutable.setter
    def immutable(self, immut) :
        "makes the Blob immutable."
        if not isinstance(immut, bool) :
            raise TypeError("new setting must be a bool")
        elif not immut :
            raise ValueError("cannot clear immutable setting")
        #end if
        hb.hb_blob_make_immutable(self._hbobj)
    #end immutable

    # TODO: user_data, destroy_func

#end Blob

# from hb-buffer.h:

GlyphInfo = def_struct_class \
  (
    name = "GlyphInfo",
    ctname = "glyph_info_t"
  )
GlyphPosition = def_struct_class \
  (
    name = "GlyphPosition",
    ctname = "glyph_position_t",
    conv =
        {
            "x_advance" : {"from" : HB.from_position_t, "to" : HB.to_position_t},
            "y_advance" : {"from" : HB.from_position_t, "to" : HB.to_position_t},
            "x_offset" : {"from" : HB.from_position_t, "to" : HB.to_position_t},
            "y_offset" : {"from" : HB.from_position_t, "to" : HB.to_position_t},
        }
  )

SegmentProperties = def_struct_class \
  (
    name = "SegmentProperties",
    ctname = "segment_properties_t",
    conv =
        {
            "language" :
                {
                    "to" : lambda l : l._hbobj,
                    "from" : Language,
                }
        }
  )

class Buffer :
    "a HarfBuzz buffer. Do not instantiate directly; call the create or get_empty methods."

    __slots__ = \
        ( # to forestall typos
            "_hbobj",
            "__weakref__",
        )

    _instances = WeakValueDictionary()

    def __new__(celf, _hbobj) :
        self = celf._instances.get(_hbobj)
        if self == None :
            self = super().__new__(celf)
            self._hbobj = _hbobj
            celf._instances[_hbobj] = self
        #end if
        return \
            self
    #end __new__

    def __del__(self) :
        if self._hbobj != None :
            hb.hb_buffer_destroy(self._hbobj)
            self._hbobj = None
        #end if
    #end __del__

    @staticmethod
    def create() :
        "creates a new Buffer."
        return \
            Buffer(hb.hb_buffer_create())
    #end create

    @staticmethod
    def get_empty() :
        "returns the empty Buffer instance."
        return \
            Buffer(hb.hb_buffer_get_empty())
    #end get_empty

    def reset(self) :
        "resets the buffer state as though it were newly created."
        hb.hb_buffer_reset(self._hbobj)
    #end reset

    def clear_contents(self) :
        "similar to reset, but does not clear the Unicode functions" \
        " or the replacement code point."
        hb.hb_clear_contents(self._hbobj)
    #end clear_contents

    def pre_allocate(self, size) :
        if not hb.hb_buffer_pre_allocate(self._hbobj, size) :
            raise RuntimeError("pre_allocate failed")
        #end if
    #end pre_allocate

    def allocation_successful(self) :
        return \
            hb.hb_buffer_allocation_successful(self._hbobj) != 0
    #end allocation_successful

    def check_alloc(self) :
        "checks that the last buffer allocation was successful."
        if not hb.hb_buffer_allocation_successful(self._hbobj) :
            raise RuntimeError("allocation failure")
        #end if
    #end check_alloc

    def add(self, codepoint, cluster) :
        "adds a single codepoint to the buffer, with the specified cluster index."
        hb.hb_buffer_add(self._hbobj, codepoint, cluster)
        self.check_alloc()
    #end add

    def add_codepoints(self, text, text_length, item_offset, item_length) :
        "adds a list or tuple of codepoints to the buffer."
        c_text = seq_to_ct(text, HB.codepoint_t)
        hb.hb_buffer_add_codepoints(self._hbobj, c_text, text_length, item_offset, item_length)
        self.check_alloc()
    #end add_codepoints

    def add_str(self, text, item_offset, item_length) :
        self.add_codepoints \
          (
            text = tuple(ord(c) for c in text),
            text_length = len(text),
            item_offset = item_offset,
            item_length = item_length
          )
    #end add_str

    @property
    def content_type(self) :
        return \
            hb.hb_buffer_get_content_type(self._hbobj)
    #end content_type

    @content_type.setter
    def content_type(self, content_type) :
        hb.hb_buffer_set_content_type(self._hbobj, content_type)
    #end content_type

    @property
    def direction(self) :
        "returns the buffer direction as a DIRECTION_XXX value."
        return \
            hb.hb_buffer_get_direction(self._hbobj)
    #end direction

    @direction.setter
    def direction(self, direction) :
        "sets the buffer direction as a DIRECTION_XXX value."
        hb.hb_buffer_set_direction(self._hbobj, direction)
    #end direction

    @property
    def script(self) :
        "returns the script as a SCRIPT_XXX value."
        return \
            hb.hb_buffer_get_script(self._hbobj)
    #end script

    @script.setter
    def script(self, script) :
        "sets the script as a SCRIPT_XXX value."
        hb.hb_buffer_set_script(self._hbobj, script)
    #end script

    @property
    def language(self) :
        "returns the language as a Language instance."
        result = hb.hb_buffer_get_language(self._hbobj)
        if result != None :
            result = Language(result)
        #end if
        return \
            result
    #end language

    @language.setter
    def language(self, language) :
        "sets a new language from a Language instance."
        if language != None and not isinstance(language, Language) :
            raise TypeError("language must be a Language")
        #end if
        if language != None :
            hb.hb_buffer_set_language(self._hbobj, language._hbobj)
        else :
            hb.hb_buffer_set_language(self._hbobj, None)
        #end if
    #end language

    @property
    def flags(self) :
        "returns the flags as a mask of BUFFER_FLAG_XXX bits."
        return \
            hb.hb_buffer_get_flags(self._hbobj)
    #end flags

    @flags.setter
    def flags(self, flags) :
        "sets new flags as a mask of BUFFER_FLAG_XXX bits."
        hb.hb_buffer_set_flags(self._hbobj, flags)
    #end flags

    @property
    def cluster_level(self) :
        "returns the cluster level as a BUFFER_CLUSTER_LEVEL_XXX value."
        return \
            hb.hb_buffer_get_cluster_level(self._hbobj)
    #end cluster_level

    @cluster_level.setter
    def cluster_level(self, cluster_level) :
        "sets the cluster level as a BUFFER_CLUSTER_LEVEL_XXX value."
        hb.hb_buffer_set_cluster_level(self._hbobj, cluster_level)
    #end cluster_level

    def __len__(self) :
        "the number of items in the buffer."
        return \
            hb.hb_buffer_get_length(self._hbobj)
    #end __len__

    @property
    def length(self) :
        "the number of items in the buffer."
        return \
            len(self)
    #end length

    @length.setter
    def length(self, length) :
        if not hb.hb_buffer_set_length(self._hbobj, length) :
            raise RuntimeError("set_length failed")
        #end if
    #end length

    @property
    def segment_properties(self) :
        "convenience accessor for getting direction, script and language all at once."
        result = HB.segment_properties_t()
        hb.hb_buffer_get_segment_properties(self._hbobj, ct.byref(result))
        return \
            SegmentProperties.from_hb(result)
    #end segment_properties

    @segment_properties.setter
    def segment_properties(self, segment_properties) :
        "convenience accessor for setting direction, script and language all at once."
        if not isinstance(segment_properties, SegmentProperties) :
            raise TypeError("segment_properties must be a SegmentProperties")
        #end if
        hb.hb_buffer_set_segment_properties(self._hbobj, segment_properties.to_hb())
    #end segment_properties

    def guess_segment_properties(self) :
        "guesses what the segment properties should be, based on the buffer contents."
        hb.hb_buffer_guess_segment_properties(self._hbobj)
    #end guess_segment_properties

    # TODO: unicode_funcs, user_data

    @property
    def glyph_infos(self) :
        nr_glyphs = ct.c_uint()
        arr = ct.cast \
          (
            hb.hb_buffer_get_glyph_infos(self._hbobj, ct.byref(nr_glyphs)),
            ct.POINTER(HB.glyph_info_t)
          )
        return \
            tuple(GlyphInfo.from_hb(arr[i]) for i in range(nr_glyphs.value))
    #end glyph_infos

    @property
    def glyph_positions(self) :
        nr_glyphs = ct.c_uint()
        arr = ct.cast \
          (
            hb.hb_buffer_get_glyph_positions(self._hbobj, ct.byref(nr_glyphs)),
            ct.POINTER(HB.glyph_position_t)
          )
        return \
            tuple(GlyphPosition.from_hb(arr[i]) for i in range(nr_glyphs.value))
    #end glyph_positions

    @property
    def replacement_codepoint(self) :
        return \
            hb.hb_buffer_get_replacement_codepoint(self._hbobj)
    #end replacement_codepoint

    @replacement_codepoint.setter
    def replacement_codepoint(self, replacement_codepoint) :
        hb.hb_buffer_set_replacement_codepoint(self._hbobj, replacement_codepoint)
    #end replacement_codepoint

    def normalize_glyphs(self) :
        hb.hb_buffer_normalize_glyphs(self._hbobj)
    #end normalize_glyphs

    def reverse(self) :
        hb.hb_buffer_reverse(self._hbobj)
    #end reverse

    def reverse_range(self, start, end) :
        hb.hb_buffer_reverse_range(self._hbobj, start, end)
    #end reverse_range

    def reverse_clusters(self) :
        hb.hb_buffer_reverse_clusters(self._hbobj)
    #end reverse_clusters

    # TODO: (de)serialize, segment properties, message_func

#end Buffer

# from hb-face.h:

class Face :
    "wrapper around hb_face_t objects. Do not instantiate directly; use" \
    " create or get_empty methods."

    __slots__ = \
        ( # to forestall typos
            "_hbobj",
            "__weakref__",
        )

    _instances = WeakValueDictionary()

    def __new__(celf, _hbobj) :
        self = celf._instances.get(_hbobj)
        if self == None :
            self = super().__new__(celf)
            self._hbobj = _hbobj
            celf._instances[_hbobj] = self
        #end if
        return \
            self
    #end __new__

    def __del__(self) :
        if self._hbobj != None :
            hb.hb_face_destroy(self._hbobj)
            self._hbobj = None
        #end if
    #end __del__

    @staticmethod
    def create(blob, index) :
        if not isinstance(blob, Blob) :
            raise TypeError("blob must be a Blob")
        #end if
        return \
            Face(hb.hb_face_create(blob._hbobj, index))
    #end create

    # TODO: create_for_tables

    if freetype != None :

        # from hb-ft.h:

        @staticmethod
        def ft_create(ft_face) :
            if not isinstance(ft_face, freetype.Face) :
                raise TypeError("ft_face must be a freetype.Face")
            #end if
            return \
                Face(hb.hb_ft_face_create_referenced(ft_face._ftobj))
        #end ft_create

    #end if

    @staticmethod
    def get_empty() :
        return \
            Face(hb.hb_face_get_empty())
    #end get_empty

    # TODO: get/set glyph_count, index, upem, user_data, immutable,
    # reference_blob? reference_table?

#end Face

# from hb-font.h:

class Font :
    "wrapper around hb_font_t objects. Do not instantiate directly; use" \
    " create methods."

    __slots__ = \
        ( # to forestall typos
            "_hbobj",
        )

    def __init__(self, _hbobj) :
        self._hbobj = _hbobj
    #end __init__

    def __del__(self) :
        if self._hbobj != None :
            hb.hb_font_destroy(self._hbobj)
            self._hbobj = None
        #end if
    #end __del__

    # no point implementing other create calls?

    if freetype != None :

        # from hb-ft.h:

        @staticmethod
        def ft_create(ft_face) :
            if not isinstance(ft_face, freetype.Face) :
                raise TypeError("ft_face must be a freetype.Face")
            #end if
            return \
                Font(hb.hb_ft_font_create_referenced(ft_face._ftobj))
        #end ft_create

        @property
        def load_flags(self) :
            return \
                hb.hb_ft_font_get_load_flags(self._hbobj)
        #end load_flags

        @load_flags.setter
        def load_flags(self, load_flags) :
            hb.hb_ft_font_set_load_flags(self._hbobj, load_flags)
        #end load_flags

    #end if

    # Note: cannot implement get_face because that requires
    # reconstructing a freetype.Face wrapper object, which
    # cannot safely be done without the associated library
    # for disposal purposes.

    # set_funcs todo

#end Font

# from hb-shape.h:

class FeatureExtra :
    # extra members for Feature class.

    @staticmethod
    def from_string(s) :
        "returns a Feature corresponding to the specified name string."
        sb = s.encode()
        result = HB.feature_t()
        if not hb.hb_feature_from_string(sb, len(sb), ct.byref(result)) :
            raise ValueError("failed to decode feature_from_string")
        #end if
        return \
            Feature.from_hb(result)
    #end from_string

    def to_string(self) :
        "returns the name string for the Feature."
        namebuf = (ct.c_char * 128)() # big enough according to docs
        hb_self = self.to_hb()
        hb.hb_feature_to_string(ct.byref(hb_self), namebuf, len(namebuf))
        return \
            namebuf.value.decode() # automatically stops at NUL
    #end to_string

#end FeatureExtra
Feature = def_struct_class \
  (
    name = "Feature",
    ctname = "feature_t",
    extra = FeatureExtra
  )
del FeatureExtra

def shape(font, buffer, features = None) :
    if not isinstance(font, Font) or not isinstance(buffer, Buffer) :
        raise TypeError("font must be a Font, buffer must be a Buffer")
    #end if
    if features != None :
        c_features = seq_to_ct(features, HB.feature_t, lambda f : f.to_hb())
        nr_features = len(features)
    else :
        c_features = None
        nr_features = 0
    #end if
    hb.hb_shape(font._hbobj, buffer._hbobj, c_features, nr_features)
#end shape

def shape_full(font, buffer, features = None, shaper_list = None) :
    if not isinstance(font, Font) or not isinstance(buffer, Buffer) :
        raise TypeError("font must be a Font, buffer must be a Buffer")
    #end if
    if features != None :
        c_features = seq_to_ct(features, HB.feature_t, lambda f : f.to_hb())
        nr_features = len(features)
    else :
        c_features = None
        nr_features = 0
    #end if
    if shaper_list != None :
        nr_shapers = len(shaper_list)
        c_shaper_list = ((nr_shapers + 1) * ct.c_char_p)()
        c_strs = []
        for s in shaper_list :
            c_str = ct.c_char_p(s.encode())
            c_strs.append(c_str)
            c_shaper_list.append(c_str)
        #end for
        c_shaper_list.append(None) # marks end of list
    else :
        c_shaper_list = None
    #end if
    return \
        hb.hb_shape_full(font._hbobj, buffer._hbobj, c_features, nr_features, c_shaper_list) != 0
#end shape_full

def shape_list_shapers() :
    c_shaper_list = ct.cast(hb.hb_shape_list_shapers(), ct.POINTER(ct.c_char_p))
    result = []
    i = 0
    while True :
        c_str = c_shaper_list[i]
        if not bool(c_str) :
            break
        result.append(c_str.decode())
        i += 1
    #end while
    return \
        tuple(result)
#end shape_list_shapers

# more TBD

# hb-set.h: probably not useful, might as well use Python sets instead

del def_struct_class # my work is done
