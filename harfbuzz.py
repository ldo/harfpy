#+
# Python-3 binding for (parts of) HarfBuzz.
#-

import ctypes as ct

harfbuzz = ct.cdll.LoadLibrary("libharfbuzz.so.0")

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

    # more TBD

#end HARFBUZZ

#+
# Routine arg/result types
#-

harfbuzz.hb_version.restype = None
harfbuzz.hb_version.argtypes = (ct.POINTER(ct.c_uint), ct.POINTER(ct.c_uint), ct.POINTER(ct.c_uint))
harfbuzz.hb_version_atleast.restype = HARFBUZZ.bool_t
harfbuzz.hb_version_atleast.argtypes = (ct.c_uint, ct.c_uint, ct.c_uint)
harfbuzz.hb_version_string.restype = ct.c_char_p
harfbuzz.hb_version_string.argtypes = ()
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
    harfbuzz.hb_version(ct.byref(major), ct.byref(minor), ct.byref(micro))
    return \
        major.value, minor.value, micro.value
#end version

def version_atleast(major, minor, micro) :
    "is the HarfBuzz version at least that specified."
    return \
        bool(harfbuzz.hb_version_atleast(major, minor, micro))
#end version_atleast

def version_string() :
    "returns the version string."
    return \
        harfbuzz.hb_version_string().decode()
#end version_string

# more TBD
