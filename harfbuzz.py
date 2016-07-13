#+
# Python-3 binding for (parts of) HarfBuzz.
#-

import ctypes as ct

harfbuzz = ct.cdll.LoadLibrary("libharfbuzz.so.0")

#+
# Routine arg/result types
#-

harfbuzz.hb_version.restype = None
harfbuzz.hb_version.argtypes = (ct.POINTER(ct.c_uint), ct.POINTER(ct.c_uint), ct.POINTER(ct.c_uint))
# more TBD

#+
# Higher-level stuff begins here
#-

def version() :
    "returns a 3-integer-tuple version (major, minor, micro)."
    major = ct.c_uint()
    minor = ct.c_uint()
    micro = ct.c_uint()
    harfbuzz.hb_version(ct.byref(major), ct.byref(minor), ct.byref(micro))
    return \
        major.value, minor.value, micro.value
#end version

# more TBD
