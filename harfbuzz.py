#+
# Python-3 binding for HarfBuzz.
#
# Additional recommended libraries:
#     python_freetype <https://github.com/ldo/python_freetype> -- binding for FreeType
#     Qahirah <https://github.com/ldo/qahirah> -- binding for Cairo
#     PyBidi <https://github.com/ldo/pybidi> -- binding for FriBidi
#
# Python adaptation copyright © 2016, 2017 Lawrence D'Oliveiro,
# based on C original by Behdad Esfahbod and others.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library, in a file named COPYING; if not, write to the
# Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
# Boston, MA 02110-1301, USA
#-

import ctypes as ct
import array
import sys
from weakref import \
    WeakValueDictionary
import atexit
try :
    import freetype2 as freetype
except ImportError :
    freetype = None
#end try
try :
    import qahirah
except ImportError :
    qahirah = None
#end try

if sys.platform == "win32":
    _dll = "libharfbuzz-0.dll"
elif sys.platform == "darwin":
    _dll = "libharfbuzz.0.dylib"
else:
    _dll = "libharfbuzz.so.0"
hb = ct.cdll.LoadLibrary(_dll)

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

    def TAG(*args) :
        "creates a tag_t from four byte values or a bytes value of length 4."
        if len(args) == 4 :
            c1, c2, c3, c4 = args
        elif len(args) == 1 :
            c1, c2, c3, c4 = tuple(args[0])
        else :
            raise TypeError("wrong nr of TAG args")
        #end if
        return \
            c1 << 24 | c2 << 16 | c3 << 8 | c4
    #end TAG

    def UNTAG(tag, printable = False) :
        "decomposes a tag_t into a tuple or bytes object of four byte values."
        result = (tag >> 24 & 255, tag >> 16 & 255, tag >> 8 & 255, tag & 255)
        if printable :
            result = bytes(result)
        #end if
        return \
            result
    #end UNTAG

    TAG_NONE = TAG(0, 0, 0, 0)
    TAG_MAX = TAG(0xff, 0xff, 0xff, 0xff)
    TAG_MAX_SIGNED = TAG(0x7f, 0xff, 0xff, 0xff)

    direction_t = ct.c_uint
    DIRECTION_INVALID = 0
    DIRECTION_LTR = 4
    DIRECTION_RTL = 5
    DIRECTION_TTB = 6
    DIRECTION_BTT = 7

    def DIRECTION_IS_VALID(dirn) :
        return \
            dirn & ~3 == 4
    #end DIRECTION_IS_VALID

    # Direction must be valid for the following

    def DIRECTION_IS_HORIZONTAL(dirn) :
        return \
            dirn & ~1 == 4
    #end DIRECTION_IS_HORIZONTAL

    def DIRECTION_IS_VERTICAL(dirn) :
        return \
            dirn & ~1 == 6
    #end DIRECTION_IS_VERTICAL

    def DIRECTION_IS_FORWARD(dirn) :
        return \
            dirn & ~2 == 4
    #end DIRECTION_IS_FORWARD

    def DIRECTION_IS_BACKWARD(dirn) :
        return \
            dirn & ~2 == 5
    #end DIRECTION_IS_BACKWARD

    def DIRECTION_REVERSE(dirn) :
        return \
            dirn ^ 1
    #end DIRECTION_REVERSE

    script_t = ct.c_uint
    # http://unicode.org/iso15924/
    # http://goo.gl/x9ilM
    # Unicode Character Database property: Script (sc)
    # 1.1
    SCRIPT_COMMON = TAG(b'Zyyy')
    SCRIPT_INHERITED = TAG(b'Zinh')
    # 5.0
    SCRIPT_UNKNOWN = TAG(b'Zzzz')

    # 1.1
    SCRIPT_ARABIC = TAG(b'Arab')
    SCRIPT_ARMENIAN = TAG(b'Armn')
    SCRIPT_BENGALI = TAG(b'Beng')
    SCRIPT_CYRILLIC = TAG(b'Cyrl')
    SCRIPT_DEVANAGARI = TAG(b'Deva')
    SCRIPT_GEORGIAN = TAG(b'Geor')
    SCRIPT_GREEK = TAG(b'Grek')
    SCRIPT_GUJARATI = TAG(b'Gujr')
    SCRIPT_GURMUKHI = TAG(b'Guru')
    SCRIPT_HANGUL = TAG(b'Hang')
    SCRIPT_HAN = TAG(b'Hani')
    SCRIPT_HEBREW = TAG(b'Hebr')
    SCRIPT_HIRAGANA = TAG(b'Hira')
    SCRIPT_KANNADA = TAG(b'Knda')
    SCRIPT_KATAKANA = TAG(b'Kana')
    SCRIPT_LAO = TAG(b'Laoo')
    SCRIPT_LATIN = TAG(b'Latn')
    SCRIPT_MALAYALAM = TAG(b'Mlym')
    SCRIPT_ORIYA = TAG(b'Orya')
    SCRIPT_TAMIL = TAG(b'Taml')
    SCRIPT_TELUGU = TAG(b'Telu')
    SCRIPT_THAI = TAG(b'Thai')

    # 2.0
    SCRIPT_TIBETAN = TAG(b'Tibt')

    # 3.0
    SCRIPT_BOPOMOFO = TAG(b'Bopo')
    SCRIPT_BRAILLE = TAG(b'Brai')
    SCRIPT_CANADIAN_SYLLABICS = TAG(b'Cans')
    SCRIPT_CHEROKEE = TAG(b'Cher')
    SCRIPT_ETHIOPIC = TAG(b'Ethi')
    SCRIPT_KHMER = TAG(b'Khmr')
    SCRIPT_MONGOLIAN = TAG(b'Mong')
    SCRIPT_MYANMAR = TAG(b'Mymr')
    SCRIPT_OGHAM = TAG(b'Ogam')
    SCRIPT_RUNIC = TAG(b'Runr')
    SCRIPT_SINHALA = TAG(b'Sinh')
    SCRIPT_SYRIAC = TAG(b'Syrc')
    SCRIPT_THAANA = TAG(b'Thaa')
    SCRIPT_YI = TAG(b'Yiii')

    # 3.1
    SCRIPT_DESERET = TAG(b'Dsrt')
    SCRIPT_GOTHIC = TAG(b'Goth')
    SCRIPT_OLD_ITALIC = TAG(b'Ital')

    # 3.2
    SCRIPT_BUHID = TAG(b'Buhd')
    SCRIPT_HANUNOO = TAG(b'Hano')
    SCRIPT_TAGALOG = TAG(b'Tglg')
    SCRIPT_TAGBANWA = TAG(b'Tagb')

    # 4.0
    SCRIPT_CYPRIOT = TAG(b'Cprt')
    SCRIPT_LIMBU = TAG(b'Limb')
    SCRIPT_LINEAR_B = TAG(b'Linb')
    SCRIPT_OSMANYA = TAG(b'Osma')
    SCRIPT_SHAVIAN = TAG(b'Shaw')
    SCRIPT_TAI_LE = TAG(b'Tale')
    SCRIPT_UGARITIC = TAG(b'Ugar')

    # 4.1
    SCRIPT_BUGINESE = TAG(b'Bugi')
    SCRIPT_COPTIC = TAG(b'Copt')
    SCRIPT_GLAGOLITIC = TAG(b'Glag')
    SCRIPT_KHAROSHTHI = TAG(b'Khar')
    SCRIPT_NEW_TAI_LUE = TAG(b'Talu')
    SCRIPT_OLD_PERSIAN = TAG(b'Xpeo')
    SCRIPT_SYLOTI_NAGRI = TAG(b'Sylo')
    SCRIPT_TIFINAGH = TAG(b'Tfng')

    # 5.0
    SCRIPT_BALINESE = TAG(b'Bali')
    SCRIPT_CUNEIFORM = TAG(b'Xsux')
    SCRIPT_NKO = TAG(b'Nkoo')
    SCRIPT_PHAGS_PA = TAG(b'Phag')
    SCRIPT_PHOENICIAN = TAG(b'Phnx')

    # 5.1
    SCRIPT_CARIAN = TAG(b'Cari')
    SCRIPT_CHAM = TAG(b'Cham')
    SCRIPT_KAYAH_LI = TAG(b'Kali')
    SCRIPT_LEPCHA = TAG(b'Lepc')
    SCRIPT_LYCIAN = TAG(b'Lyci')
    SCRIPT_LYDIAN = TAG(b'Lydi')
    SCRIPT_OL_CHIKI = TAG(b'Olck')
    SCRIPT_REJANG = TAG(b'Rjng')
    SCRIPT_SAURASHTRA = TAG(b'Saur')
    SCRIPT_SUNDANESE = TAG(b'Sund')
    SCRIPT_VAI = TAG(b'Vaii')

    # 5.2
    SCRIPT_AVESTAN = TAG(b'Avst')
    SCRIPT_BAMUM = TAG(b'Bamu')
    SCRIPT_EGYPTIAN_HIEROGLYPHS = TAG(b'Egyp')
    SCRIPT_IMPERIAL_ARAMAIC = TAG(b'Armi')
    SCRIPT_INSCRIPTIONAL_PAHLAVI = TAG(b'Phli')
    SCRIPT_INSCRIPTIONAL_PARTHIAN = TAG(b'Prti')
    SCRIPT_JAVANESE = TAG(b'Java')
    SCRIPT_KAITHI = TAG(b'Kthi')
    SCRIPT_LISU = TAG(b'Lisu')
    SCRIPT_MEETEI_MAYEK = TAG(b'Mtei')
    SCRIPT_OLD_SOUTH_ARABIAN = TAG(b'Sarb')
    SCRIPT_OLD_TURKIC = TAG(b'Orkh')
    SCRIPT_SAMARITAN = TAG(b'Samr')
    SCRIPT_TAI_THAM = TAG(b'Lana')
    SCRIPT_TAI_VIET = TAG(b'Tavt')

    # 6.0
    SCRIPT_BATAK = TAG(b'Batk')
    SCRIPT_BRAHMI = TAG(b'Brah')
    SCRIPT_MANDAIC = TAG(b'Mand')

    # 6.1
    SCRIPT_CHAKMA = TAG(b'Cakm')
    SCRIPT_MEROITIC_CURSIVE = TAG(b'Merc')
    SCRIPT_MEROITIC_HIEROGLYPHS = TAG(b'Mero')
    SCRIPT_MIAO = TAG(b'Plrd')
    SCRIPT_SHARADA = TAG(b'Shrd')
    SCRIPT_SORA_SOMPENG = TAG(b'Sora')
    SCRIPT_TAKRI = TAG(b'Takr')

    # Since: 0.9.30
    # 7.0
    SCRIPT_BASSA_VAH = TAG(b'Bass')
    SCRIPT_CAUCASIAN_ALBANIAN = TAG(b'Aghb')
    SCRIPT_DUPLOYAN = TAG(b'Dupl')
    SCRIPT_ELBASAN = TAG(b'Elba')
    SCRIPT_GRANTHA = TAG(b'Gran')
    SCRIPT_KHOJKI = TAG(b'Khoj')
    SCRIPT_KHUDAWADI = TAG(b'Sind')
    SCRIPT_LINEAR_A = TAG(b'Lina')
    SCRIPT_MAHAJANI = TAG(b'Mahj')
    SCRIPT_MANICHAEAN = TAG(b'Mani')
    SCRIPT_MENDE_KIKAKUI = TAG(b'Mend')
    SCRIPT_MODI = TAG(b'Modi')
    SCRIPT_MRO = TAG(b'Mroo')
    SCRIPT_NABATAEAN = TAG(b'Nbat')
    SCRIPT_OLD_NORTH_ARABIAN = TAG(b'Narb')
    SCRIPT_OLD_PERMIC = TAG(b'Perm')
    SCRIPT_PAHAWH_HMONG = TAG(b'Hmng')
    SCRIPT_PALMYRENE = TAG(b'Palm')
    SCRIPT_PAU_CIN_HAU = TAG(b'Pauc')
    SCRIPT_PSALTER_PAHLAVI = TAG(b'Phlp')
    SCRIPT_SIDDHAM = TAG(b'Sidd')
    SCRIPT_TIRHUTA = TAG(b'Tirh')
    SCRIPT_WARANG_CITI = TAG(b'Wara')

    # 8.0
    SCRIPT_AHOM = TAG(b'Ahom')
    SCRIPT_ANATOLIAN_HIEROGLYPHS = TAG(b'Hluw')
    SCRIPT_HATRAN = TAG(b'Hatr')
    SCRIPT_MULTANI = TAG(b'Mult')
    SCRIPT_OLD_HUNGARIAN = TAG(b'Hung')
    SCRIPT_SIGNWRITING = TAG(b'Sgnw')

    # No script set.
    SCRIPT_INVALID = TAG_NONE

    destroy_func_t = ct.CFUNCTYPE(None, ct.c_void_p)

    # from hb-unicode.h:

    unicode_general_category_t = ct.c_uint
    UNICODE_GENERAL_CATEGORY_CONTROL = 0 #  Cc
    UNICODE_GENERAL_CATEGORY_FORMAT = 1 #  Cf
    UNICODE_GENERAL_CATEGORY_UNASSIGNED = 2 #  Cn
    UNICODE_GENERAL_CATEGORY_PRIVATE_USE = 3 #  Co
    UNICODE_GENERAL_CATEGORY_SURROGATE = 4 #  Cs
    UNICODE_GENERAL_CATEGORY_LOWERCASE_LETTER = 5 #  Ll
    UNICODE_GENERAL_CATEGORY_MODIFIER_LETTER = 6 #  Lm
    UNICODE_GENERAL_CATEGORY_OTHER_LETTER = 7 #  Lo
    UNICODE_GENERAL_CATEGORY_TITLECASE_LETTER = 8 #  Lt
    UNICODE_GENERAL_CATEGORY_UPPERCASE_LETTER = 9 #  Lu
    UNICODE_GENERAL_CATEGORY_SPACING_MARK = 10 # Mc
    UNICODE_GENERAL_CATEGORY_ENCLOSING_MARK = 11 # Me
    UNICODE_GENERAL_CATEGORY_NON_SPACING_MARK = 12 # Mn
    UNICODE_GENERAL_CATEGORY_DECIMAL_NUMBER = 13 # Nd
    UNICODE_GENERAL_CATEGORY_LETTER_NUMBER = 14 # Nl
    UNICODE_GENERAL_CATEGORY_OTHER_NUMBER = 15 # No
    UNICODE_GENERAL_CATEGORY_CONNECT_PUNCTUATION = 16 # Pc
    UNICODE_GENERAL_CATEGORY_DASH_PUNCTUATION = 17 # Pd
    UNICODE_GENERAL_CATEGORY_CLOSE_PUNCTUATION = 18 # Pe
    UNICODE_GENERAL_CATEGORY_FINAL_PUNCTUATION = 19 # Pf
    UNICODE_GENERAL_CATEGORY_INITIAL_PUNCTUATION = 20 # Pi
    UNICODE_GENERAL_CATEGORY_OTHER_PUNCTUATION = 21 # Po
    UNICODE_GENERAL_CATEGORY_OPEN_PUNCTUATION = 22 # Ps
    UNICODE_GENERAL_CATEGORY_CURRENCY_SYMBOL = 23 # Sc
    UNICODE_GENERAL_CATEGORY_MODIFIER_SYMBOL = 24 # Sk
    UNICODE_GENERAL_CATEGORY_MATH_SYMBOL = 25 # Sm
    UNICODE_GENERAL_CATEGORY_OTHER_SYMBOL = 26 # So
    UNICODE_GENERAL_CATEGORY_LINE_SEPARATOR = 27 # Zl
    UNICODE_GENERAL_CATEGORY_PARAGRAPH_SEPARATOR = 28 # Zp
    UNICODE_GENERAL_CATEGORY_SPACE_SEPARATOR = 29 # Zs

    # hb_unicode_combining_class_t

    # Note: newer versions of Unicode may add new values.  Clients should be ready to handle
    # any value in the 0..254 range being returned from hb_unicode_combining_class().

    # Unicode Character Database property: Canonical_Combining_Class (ccc)
    unicode_combining_class_t = ct.c_uint
    UNICODE_COMBINING_CLASS_NOT_REORDERED = 0
    UNICODE_COMBINING_CLASS_OVERLAY = 1
    UNICODE_COMBINING_CLASS_NUKTA = 7
    UNICODE_COMBINING_CLASS_KANA_VOICING = 8
    UNICODE_COMBINING_CLASS_VIRAMA = 9

    # Hebrew
    UNICODE_COMBINING_CLASS_CCC10 = 10
    UNICODE_COMBINING_CLASS_CCC11 = 11
    UNICODE_COMBINING_CLASS_CCC12 = 12
    UNICODE_COMBINING_CLASS_CCC13 = 13
    UNICODE_COMBINING_CLASS_CCC14 = 14
    UNICODE_COMBINING_CLASS_CCC15 = 15
    UNICODE_COMBINING_CLASS_CCC16 = 16
    UNICODE_COMBINING_CLASS_CCC17 = 17
    UNICODE_COMBINING_CLASS_CCC18 = 18
    UNICODE_COMBINING_CLASS_CCC19 = 19
    UNICODE_COMBINING_CLASS_CCC20 = 20
    UNICODE_COMBINING_CLASS_CCC21 = 21
    UNICODE_COMBINING_CLASS_CCC22 = 22
    UNICODE_COMBINING_CLASS_CCC23 = 23
    UNICODE_COMBINING_CLASS_CCC24 = 24
    UNICODE_COMBINING_CLASS_CCC25 = 25
    UNICODE_COMBINING_CLASS_CCC26 = 26

    # Arabic
    UNICODE_COMBINING_CLASS_CCC27 = 27
    UNICODE_COMBINING_CLASS_CCC28 = 28
    UNICODE_COMBINING_CLASS_CCC29 = 29
    UNICODE_COMBINING_CLASS_CCC30 = 30
    UNICODE_COMBINING_CLASS_CCC31 = 31
    UNICODE_COMBINING_CLASS_CCC32 = 32
    UNICODE_COMBINING_CLASS_CCC33 = 33
    UNICODE_COMBINING_CLASS_CCC34 = 34
    UNICODE_COMBINING_CLASS_CCC35 = 35

    # Syriac
    UNICODE_COMBINING_CLASS_CCC36 = 36

    # Telugu
    UNICODE_COMBINING_CLASS_CCC84 = 84
    UNICODE_COMBINING_CLASS_CCC91 = 91

    # Thai
    UNICODE_COMBINING_CLASS_CCC103 = 103
    UNICODE_COMBINING_CLASS_CCC107 = 107

    # Lao
    UNICODE_COMBINING_CLASS_CCC118 = 118
    UNICODE_COMBINING_CLASS_CCC122 = 122

    # Tibetan
    UNICODE_COMBINING_CLASS_CCC129 = 129
    UNICODE_COMBINING_CLASS_CCC130 = 130
    UNICODE_COMBINING_CLASS_CCC133 = 132

    UNICODE_COMBINING_CLASS_ATTACHED_BELOW_LEFT = 200
    UNICODE_COMBINING_CLASS_ATTACHED_BELOW = 202
    UNICODE_COMBINING_CLASS_ATTACHED_ABOVE = 214
    UNICODE_COMBINING_CLASS_ATTACHED_ABOVE_RIGHT = 216
    UNICODE_COMBINING_CLASS_BELOW_LEFT = 218
    UNICODE_COMBINING_CLASS_BELOW = 220
    UNICODE_COMBINING_CLASS_BELOW_RIGHT = 222
    UNICODE_COMBINING_CLASS_LEFT = 224
    UNICODE_COMBINING_CLASS_RIGHT = 226
    UNICODE_COMBINING_CLASS_ABOVE_LEFT = 228
    UNICODE_COMBINING_CLASS_ABOVE = 230
    UNICODE_COMBINING_CLASS_ABOVE_RIGHT = 232
    UNICODE_COMBINING_CLASS_DOUBLE_BELOW = 233
    UNICODE_COMBINING_CLASS_DOUBLE_ABOVE = 234

    UNICODE_COMBINING_CLASS_IOTA_SUBSCRIPT = 240

    UNICODE_COMBINING_CLASS_INVALID = 255

    unicode_combining_class_func_t = \
        ct.CFUNCTYPE(unicode_combining_class_t, ct.c_void_p, codepoint_t, ct.c_void_p)
    unicode_eastasian_width_func_t = \
        ct.CFUNCTYPE(ct.c_uint, ct.c_void_p, codepoint_t, ct.c_void_p)
    unicode_general_category_func_t = \
        ct.CFUNCTYPE(unicode_general_category_t, ct.c_void_p, codepoint_t, ct.c_void_p)
    unicode_mirroring_func_t = \
        ct.CFUNCTYPE(codepoint_t, ct.c_void_p, codepoint_t, ct.c_void_p)
    unicode_script_func_t = \
        ct.CFUNCTYPE(script_t, ct.c_void_p, codepoint_t, ct.c_void_p)
    unicode_compose_func_t = \
        ct.CFUNCTYPE(bool_t, ct.c_void_p, codepoint_t, codepoint_t, ct.POINTER(codepoint_t), ct.c_void_p)
    unicode_decompose_func_t = \
        ct.CFUNCTYPE(bool_t, ct.c_void_p, codepoint_t, ct.POINTER(codepoint_t), ct.POINTER(codepoint_t), ct.c_void_p)
    unicode_decompose_compatibility_func_t = \
        ct.CFUNCTYPE(ct.c_uint, ct.c_void_p, codepoint_t, ct.POINTER(codepoint_t), ct.c_void_p)

    UNICODE_MAX_DECOMPOSITION_LEN = 18 + 1 # codepoints

    # from hb-blob.h:

    memory_mode = ct.c_uint
    MEMORY_MODE_DUPLICATE = 0
      # blob is to get its own copy of data; its mode becomes MEMORY_MODE_WRITABLE
    MEMORY_MODE_READONLY = 1
      # passed data area is to be assumed to be read-only, so any
      # attempt to get writable access will cause it to be copied
      # to a new area and the mode changed to MEMORY_MODE_WRITABLE
    MEMORY_MODE_WRITABLE = 2 # passed data area is to be assumed to be writable
    MEMORY_MODE_READONLY_MAY_MAKE_WRITABLE = 3
       # passed data area is to be assumed to be initially read-only, but
       # may be made writable in-place

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

    buffer_message_func_t = ct.CFUNCTYPE(bool_t, ct.c_void_p, ct.c_void_p, ct.c_char_p, ct.c_void_p)

    BUFFER_SERIALIZE_FLAG_DEFAULT = 0x00000000
    BUFFER_SERIALIZE_FLAG_NO_CLUSTERS = 0x00000001
    BUFFER_SERIALIZE_FLAG_NO_POSITIONS = 0x00000002
    BUFFER_SERIALIZE_FLAG_NO_GLYPH_NAMES = 0x00000004
    BUFFER_SERIALIZE_FLAG_GLYPH_EXTENTS = 0x00000008

    BUFFER_SERIALIZE_FORMAT_TEXT = TAG(b'TEXT')
    BUFFER_SERIALIZE_FORMAT_JSON = TAG(b'JSON')
    BUFFER_SERIALIZE_FORMAT_INVALID = TAG_NONE

    # from hb-face.h:

    reference_table_func_t = ct.CFUNCTYPE(ct.c_void_p, ct.c_void_p, tag_t, ct.c_void_p)

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

    # Note that height is negative in coordinate systems that grow up.
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

    font_get_font_extents_func_t = ct.CFUNCTYPE(bool_t, ct.c_void_p, ct.c_void_p, ct.POINTER(font_extents_t), ct.c_void_p)
    font_get_font_h_extents_func_t = font_get_font_extents_func_t
    font_get_font_v_extents_func_t = font_get_font_extents_func_t
    font_get_nominal_glyph_func_t = ct.CFUNCTYPE(bool_t, ct.c_void_p, ct.c_void_p, codepoint_t, ct.POINTER(codepoint_t), ct.c_void_p)
    font_get_variation_glyph_func_t = ct.CFUNCTYPE(bool_t, ct.c_void_p, ct.c_void_p, codepoint_t, codepoint_t, ct.POINTER(codepoint_t), ct.c_void_p)
    font_get_glyph_advance_func_t = ct.CFUNCTYPE(position_t, ct.c_void_p, ct.c_void_p, codepoint_t, ct.c_void_p)
    font_get_glyph_h_advance_func_t = font_get_glyph_advance_func_t
    font_get_glyph_v_advance_func_t = font_get_glyph_advance_func_t
    font_get_glyph_origin_func_t = ct.CFUNCTYPE(bool_t, ct.c_void_p, ct.c_void_p, codepoint_t, ct.POINTER(position_t), ct.POINTER(position_t), ct.c_void_p)
    font_get_glyph_h_origin_func_t = font_get_glyph_origin_func_t
    font_get_glyph_v_origin_func_t = font_get_glyph_origin_func_t
    font_get_glyph_kerning_func_t = ct.CFUNCTYPE(position_t, ct.c_void_p, ct.c_void_p, codepoint_t, codepoint_t, ct.c_void_p)
    font_get_glyph_h_kerning_func_t = font_get_glyph_kerning_func_t
    font_get_glyph_v_kerning_func_t = font_get_glyph_kerning_func_t
    font_get_glyph_extents_func_t = ct.CFUNCTYPE(bool_t, ct.c_void_p, ct.c_void_p, codepoint_t, ct.POINTER(glyph_extents_t), ct.c_void_p)
    font_get_glyph_contour_point_func_t = ct.CFUNCTYPE(bool_t, ct.c_void_p, ct.c_void_p, codepoint_t, ct.c_uint, ct.POINTER(position_t), ct.POINTER(position_t), ct.c_void_p)
    font_get_glyph_name_func_t = ct.CFUNCTYPE(bool_t, ct.c_void_p, ct.c_void_p, codepoint_t, ct.POINTER(ct.c_char), ct.c_uint, ct.c_void_p)
    font_get_glyph_from_name_func_t = ct.CFUNCTYPE(bool_t, ct.c_void_p, ct.c_void_p, ct.POINTER(ct.c_char), ct.c_int, ct.POINTER(codepoint_t), ct.c_void_p)

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

    # from hb-set.h:

    SET_VALUE_INVALID = 0xffffffff

    # from hb-ot-tag.h:

    OT_TAG_DEFAULT_SCRIPT = TAG(b'DFLT')
    OT_TAG_DEFAULT_LANGUAGE = TAG(b'dflt')

    # from hb-ot-layout.h:

    OT_TAG_GDEF = TAG(b'GDEF')
    OT_TAG_GSUB = TAG(b'GSUB')
    OT_TAG_GPOS = TAG(b'GPOS')
    OT_TAG_JSTF = TAG(b'JSTF')

    ot_layout_glyph_class_t = ct.c_uint
    OT_LAYOUT_GLYPH_CLASS_UNCLASSIFIED = 0
    OT_LAYOUT_GLYPH_CLASS_BASE_GLYPH = 1
    OT_LAYOUT_GLYPH_CLASS_LIGATURE = 2
    OT_LAYOUT_GLYPH_CLASS_MARK = 3
    OT_LAYOUT_GLYPH_CLASS_COMPONENT = 4

    OT_LAYOUT_NO_SCRIPT_INDEX = 0xFFFF
    OT_LAYOUT_NO_FEATURE_INDEX = 0xFFFF
    OT_LAYOUT_DEFAULT_LANGUAGE_INDEX = 0xFFFF

#end HARFBUZZ
HB = HARFBUZZ # if you prefer

#+
# Internal class-construction helpers
#-

def def_struct_class(name, ctname, conv = None, extra = None) :
    # defines a class with attributes that are a straightforward mapping
    # of a ctypes struct. Optionally includes extra members from extra
    # if specified.

    ctstruct = getattr(HARFBUZZ, ctname)

    class result_class :

        __slots__ = tuple(field[0] for field in ctstruct._fields_) # to forestall typos

        def __init__(self, *args, **kwargs) :
            for field in self.__slots__ :
                if field in kwargs :
                    setattr(self, field, kwargs[field])
                    del kwargs[field]
                #end if
            #end for
            unrecognized = ", ".join(k for k in kwargs)
            if len(unrecognized) != 0 :
                raise TypeError("unrecognized fields for %s: %s" % (name, unrecognized))
            #end if
        #end __init__

        def to_hb(self, autoscale = None) :
            "returns a HarfBuzz representation of the structure."
            result = ctstruct()
            for name, cttype in ctstruct._fields_ :
                val = getattr(self, name, None)
                if val != None :
                    if conv != None and name in conv :
                        conv_to = conv[name]["to"]
                        if conv_to is HB.to_position_t :
                            if autoscale == None :
                                raise TypeError \
                                  (
                                        "missing autoscale arg in %s.to_hb conversion"
                                    %
                                        type(self).__name__
                                  )
                            #end if
                            if not autoscale :
                                conv_to = round
                            #end if
                        #end if
                        val = conv_to(val)
                    #end if
                    setattr(result, name, val)
                #end if
            #end for
            return \
                result
        #end to_hb

        @classmethod
        def from_hb(celf, r, autoscale = None) :
            "decodes the HarfBuzz representation of the structure."
            result = celf()
            for name, cttype in ctstruct._fields_ :
                val = getattr(r, name)
                if val != None and conv != None and name in conv :
                    conv_from = conv[name]["from"]
                    if conv_from is HB.from_position_t :
                        if autoscale == None :
                            raise TypeError \
                              (
                                "missing autoscale arg in %s.from_hb conversion" % celf.__name__
                              )
                        #end if
                        if not autoscale :
                            conv_from = None
                        #end if
                    #end if
                    if conv_from != None :
                        val = conv_from(val)
                    #end if
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
                            if hasattr(self, field[0])
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

def def_callback_wrapper(celf, method_name, docstring, callback_field_name, destroy_field_name, def_wrap_callback_func, hb_proc) :
    # Common routine for defining a set-callback method. These all have the same form,
    # where the caller specifies
    #  * the callback function
    #  * an additional user_data pointer (meaning is up the caller)
    #  * an optional destroy callback which is passed the user_data pointer
    #    when the containing object is destroyed.
    # The only variation is in the arguments and result type of the callback.

    def set_callback(self, callback_func, user_data, destroy) :
        # This becomes the actual set-callback method.
        wrap_callback_func = def_wrap_callback_func(self, callback_func, user_data)
        if destroy != None :
            @HB.destroy_func_t
            def wrap_destroy(c_user_data) :
                destroy(user_data)
            #end wrap_destroy
        else :
            wrap_destroy = None
        #end if
        setattr(self, callback_field_name, wrap_callback_func)
        setattr(self, destroy_field_name, wrap_destroy)
        getattr(hb, hb_proc)(self._hbobj, wrap_callback_func, None, wrap_destroy)
    #end set_callback

#begin def_callback_wrapper
    set_callback.__name__ = method_name
    set_callback.__doc__ = docstring
    setattr(celf, method_name, set_callback)
#end def_callback_wrapper

def def_immutable(celf, hb_query, hb_set) :

    def get_immutable(self) :
        return \
            getattr(hb, hb_query)(self._hbobj) != 0
    #end set_immutable

    def set_immutable(self, immut) :
        if not isinstance(immut, bool) :
            raise TypeError("new setting must be a bool")
        elif not immut :
            raise ValueError("cannot clear immutable setting")
        #end if
        getattr(hb, hb_set)(self._hbobj)
    #end set_immutable

#begin def_immutable
    class_name = celf.__name__
    get_immutable.__name__ = "immutable"
    get_immutable.__doc__ = "is the %s immutable." % class_name
    set_immutable.__name__ = "immutable"
    set_immutable.__doc__ = "makes the %s immutable." % class_name
    immutable = property(get_immutable)
    immutable = immutable.setter(set_immutable)
    setattr(celf, "immutable", immutable)
#end def_immutable

#+
# Useful stuff
#-

def seq_to_ct(seq, ct_type, conv = None, zeroterm = False) :
    "extracts the elements of a Python sequence value into a ctypes array" \
    " of type ct_type, optionally applying the conv function to each value."
    if conv == None :
        conv = lambda x : x
    #end if
    nr_elts = len(seq) + int(zeroterm)
    result = (nr_elts * ct_type)()
    for i in range(nr_elts) :
        result[i] = conv(seq[i])
    #end for
    if zeroterm :
        result[nr_elts] = conv(0)
    #end if
    return \
        result
#end seq_to_ct

def shaper_list_to_hb(shaper_list) :
    "converts a list of strings to a null-terminated ctypes array of" \
    " pointers to char. Returns a tuple of 3 items: the number of shaper" \
    " strings (excluding the terminating null entry), the ctypes array, and" \
    " a separate Python list of the ctypes char pointers. I’m not sure if" \
    " the last one is really necessary to ensure the allocated strings don’t" \
    " unexpectedly disappear, so I include it, just in case.\n" \
    "\n" \
    "The shaper_list can be null, in which case 0 and null values are returned."
    if shaper_list != None :
        nr_shapers = len(shaper_list)
        c_shaper_list = ((nr_shapers + 1) * ct.c_char_p)()
        c_strs = []
        for i, s in enumerate(shaper_list) :
            c_str = ct.c_char_p(s.encode())
            c_strs.append(c_str)
            c_shaper_list[i] = c_str
        #end for
        c_shaper_list[nr_shapers] = None # marks end of list
    else :
        nr_shapers = 0
        c_shaper_list = None
        c_strs = None
    #end if
    return \
        nr_shapers, c_shaper_list, c_strs
#end shaper_list_to_hb

#+
# Routine arg/result types
#-

hb.hb_version.restype = None
hb.hb_version.argtypes = (ct.POINTER(ct.c_uint), ct.POINTER(ct.c_uint), ct.POINTER(ct.c_uint))
hb.hb_version_atleast.restype = HB.bool_t
hb.hb_version_atleast.argtypes = (ct.c_uint, ct.c_uint, ct.c_uint)
hb.hb_version_string.restype = ct.c_char_p
hb.hb_version_string.argtypes = ()
hb.hb_direction_from_string.restype = HB.direction_t
hb.hb_direction_from_string.argtypes = (ct.c_void_p, ct.c_int)
hb.hb_direction_to_string.restype = ct.c_char_p
hb.hb_direction_to_string.argtypes = (HB.direction_t,)
hb.hb_language_from_string.restype = ct.c_void_p
hb.hb_language_from_string.argtypes = (ct.c_char_p, ct.c_int)
hb.hb_language_to_string.restype = ct.c_char_p
hb.hb_language_to_string.argtypes = (ct.c_void_p,)
hb.hb_language_get_default.restype = ct.c_void_p
hb.hb_language_get_default.argtypes = ()
hb.hb_tag_from_string.restype = HB.tag_t
hb.hb_tag_from_string.argtypes = (ct.c_void_p, ct.c_int)
hb.hb_tag_to_string.restype = None
hb.hb_tag_to_string.argtypes = (HB.tag_t, ct.c_void_p)
hb.hb_script_from_iso15924_tag.restype = HB.script_t
hb.hb_script_from_iso15924_tag.argtypes = (HB.tag_t,)
hb.hb_script_from_string.restype = HB.script_t
hb.hb_script_from_string.argtypes = (ct.c_void_p, ct.c_int)
hb.hb_script_to_iso15924_tag.restype = HB.tag_t
hb.hb_script_to_iso15924_tag.argtypes = (HB.script_t,)
hb.hb_script_get_horizontal_direction.restype = HB.direction_t
hb.hb_script_get_horizontal_direction.argtypes = (HB.script_t,)

hb.hb_unicode_funcs_get_default.restype = ct.c_void_p
hb.hb_unicode_funcs_get_default.argtypes = ()
hb.hb_unicode_funcs_create.restype = ct.c_void_p
hb.hb_unicode_funcs_create.argtypes = (ct.c_void_p,)
hb.hb_unicode_funcs_get_empty.restype = ct.c_void_p
hb.hb_unicode_funcs_get_empty.argtypes = ()
hb.hb_unicode_funcs_reference.restype = ct.c_void_p
hb.hb_unicode_funcs_reference.argtypes = (ct.c_void_p,)
hb.hb_unicode_funcs_destroy.restype = None
hb.hb_unicode_funcs_destroy.argtypes = (ct.c_void_p,)
hb.hb_unicode_funcs_make_immutable.restype = None
hb.hb_unicode_funcs_make_immutable.argtypes = (ct.c_void_p,)
hb.hb_unicode_funcs_is_immutable.restype = HB.bool_t
hb.hb_unicode_funcs_is_immutable.argtypes = (ct.c_void_p,)
hb.hb_unicode_funcs_get_parent.restype = ct.c_void_p
hb.hb_unicode_funcs_get_parent.argtypes = (ct.c_void_p,)
hb.hb_unicode_funcs_set_combining_class_func.restype = None
hb.hb_unicode_funcs_set_combining_class_func.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p)
hb.hb_unicode_funcs_set_combining_class_func.restype = None
hb.hb_unicode_funcs_set_combining_class_func.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p)
hb.hb_unicode_funcs_set_eastasian_width_func.restype = None
hb.hb_unicode_funcs_set_eastasian_width_func.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p)
hb.hb_unicode_funcs_set_general_category_func.restype = None
hb.hb_unicode_funcs_set_general_category_func.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p)
hb.hb_unicode_funcs_set_mirroring_func.restype = None
hb.hb_unicode_funcs_set_mirroring_func.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p)
hb.hb_unicode_funcs_set_script_func.restype = None
hb.hb_unicode_funcs_set_script_func.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p)
hb.hb_unicode_funcs_set_compose_func.restype = None
hb.hb_unicode_funcs_set_compose_func.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p)
hb.hb_unicode_funcs_set_decompose_func.restype = None
hb.hb_unicode_funcs_set_decompose_func.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p)
hb.hb_unicode_funcs_set_decompose_compatibility_func.restype = None
hb.hb_unicode_funcs_set_decompose_compatibility_func.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p)
hb.hb_unicode_combining_class.restype = HB.unicode_combining_class_t
hb.hb_unicode_combining_class.argtypes = (ct.c_void_p, HB.codepoint_t)
hb.hb_unicode_eastasian_width.restype = ct.c_uint
hb.hb_unicode_eastasian_width.argtypes = (ct.c_void_p, HB.codepoint_t)
hb.hb_unicode_general_category.restype = HB.unicode_general_category_t
hb.hb_unicode_general_category.argtypes = (ct.c_void_p, HB.codepoint_t)
hb.hb_unicode_mirroring.restype = HB.codepoint_t
hb.hb_unicode_mirroring.argtypes = (ct.c_void_p, HB.codepoint_t)
hb.hb_unicode_script.restype = HB.script_t
hb.hb_unicode_script.argtypes = (ct.c_void_p, HB.codepoint_t)
hb.hb_unicode_compose.restype = HB.bool_t
hb.hb_unicode_compose.argtypes = (ct.c_void_p, HB.codepoint_t, HB.codepoint_t, ct.POINTER(HB.codepoint_t))
hb.hb_unicode_decompose.restype = HB.bool_t
hb.hb_unicode_decompose.argtypes = (ct.c_void_p, HB.codepoint_t, ct.POINTER(HB.codepoint_t), ct.POINTER(HB.codepoint_t))
hb.hb_unicode_decompose_compatibility.restype = ct.c_uint
hb.hb_unicode_decompose_compatibility.argtypes = (ct.c_void_p, HB.codepoint_t, ct.POINTER(HB.codepoint_t))

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
hb.hb_blob_reference.restype = ct.c_void_p
hb.hb_blob_reference.argtypes = (ct.c_void_p,)

hb.hb_buffer_destroy.restype = None
hb.hb_buffer_destroy.argtypes = (ct.c_void_p,)
hb.hb_buffer_create.restype = ct.c_void_p
hb.hb_buffer_create.argtypes = ()
hb.hb_buffer_reference.restype = ct.c_void_p
hb.hb_buffer_reference.argtypes = (ct.c_void_p,)
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
hb.hb_buffer_set_unicode_funcs.restype = None
hb.hb_buffer_set_unicode_funcs.argtypes = (ct.c_void_p, ct.c_void_p)
hb.hb_buffer_get_unicode_funcs.restype = ct.c_void_p
hb.hb_buffer_get_unicode_funcs.argtypes = (ct.c_void_p,)
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
hb.hb_buffer_set_segment_properties.argtypes = (ct.c_void_p, ct.POINTER(HB.segment_properties_t))
hb.hb_buffer_get_segment_properties.restype = None
hb.hb_buffer_get_segment_properties.argtypes = (ct.c_void_p, ct.POINTER(HB.segment_properties_t))
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
hb.hb_buffer_set_message_func.restype = None
hb.hb_buffer_set_message_func.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p)
hb.hb_buffer_serialize_format_from_string.restype = HB.tag_t
hb.hb_buffer_serialize_format_from_string.argtypes = (ct.c_char_p, ct.c_int)
hb.hb_buffer_serialize_format_to_string.restype = ct.c_char_p
hb.hb_buffer_serialize_format_to_string.argtypes = (HB.tag_t,)
hb.hb_buffer_serialize_list_formats.restype = ct.POINTER(ct.c_char_p)
hb.hb_buffer_serialize_list_formats.argtypes = ()
hb.hb_buffer_serialize_glyphs.restype = ct.c_uint
hb.hb_buffer_serialize_glyphs.argtypes = (ct.c_void_p, ct.c_uint, ct.c_uint, ct.c_void_p, ct.c_uint, ct.POINTER(ct.c_uint), ct.c_void_p, HB.tag_t, ct.c_uint)
hb.hb_buffer_deserialize_glyphs.restype = HB.bool_t
hb.hb_buffer_deserialize_glyphs.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_int, ct.c_void_p, ct.c_void_p, HB.tag_t)

hb.hb_segment_properties_equal.restype = HB.bool_t
hb.hb_segment_properties_equal.argtypes = (ct.c_void_p, ct.c_void_p)
hb.hb_segment_properties_hash.restype = ct.c_uint
hb.hb_segment_properties_hash.argtypes = (ct.c_void_p,)

hb.hb_face_create.restype = ct.c_void_p
hb.hb_face_create.argtypes = (ct.c_void_p, ct.c_uint)
hb.hb_face_create_for_tables.restype = ct.c_void_p
hb.hb_face_create_for_tables.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p)
hb.hb_face_destroy.restype = None
hb.hb_face_destroy.argtypes = (ct.c_void_p,)
hb.hb_face_reference.restype = ct.c_void_p
hb.hb_face_reference.argtypes = (ct.c_void_p,)
hb.hb_face_get_empty.restype = ct.c_void_p
hb.hb_face_get_empty.argtypes = ()
hb.hb_face_is_immutable.restype = HB.bool_t
hb.hb_face_is_immutable.argtypes = (ct.c_void_p,)
hb.hb_face_make_immutable.restype = None
hb.hb_face_make_immutable.argtypes = (ct.c_void_p,)
hb.hb_face_reference_table.restype = ct.c_void_p
hb.hb_face_reference_table.argtypes = (ct.c_void_p, HB.tag_t)
hb.hb_face_reference_blob.restype = ct.c_void_p
hb.hb_face_reference_blob.argtypes = (ct.c_void_p,)
hb.hb_face_reference_table.restype = ct.c_void_p
hb.hb_face_reference_table.argtypes = (ct.c_void_p, HB.tag_t)
hb.hb_face_reference_blob.restype = ct.c_void_p
hb.hb_face_reference_blob.argtypes = (ct.c_void_p,)
hb.hb_face_set_index.restype = None
hb.hb_face_set_index.argtypes = (ct.c_void_p, ct.c_uint)
hb.hb_face_get_index.restype = ct.c_uint
hb.hb_face_get_index.argtypes = (ct.c_void_p,)
hb.hb_face_set_upem.restype = None
hb.hb_face_set_upem.argtypes = (ct.c_void_p, ct.c_uint)
hb.hb_face_get_upem.restype = ct.c_uint
hb.hb_face_get_upem.argtypes = (ct.c_void_p,)
hb.hb_face_set_glyph_count.restype = None
hb.hb_face_set_glyph_count.argtypes = (ct.c_void_p, ct.c_uint)
hb.hb_face_get_glyph_count.restype = ct.c_uint
hb.hb_face_get_glyph_count.argtypes = (ct.c_void_p,)

hb.hb_font_create.restype = ct.c_void_p
hb.hb_font_create.argtypes = (ct.c_void_p,)
hb.hb_font_create_sub_font.restype = ct.c_void_p
hb.hb_font_create_sub_font.argtypes = (ct.c_void_p,)
hb.hb_font_destroy.restype = None
hb.hb_font_destroy.argtypes = (ct.c_void_p,)
hb.hb_font_reference.restype = ct.c_void_p
hb.hb_font_reference.argtypes = (ct.c_void_p,)
hb.hb_font_is_immutable.restype = HB.bool_t
hb.hb_font_is_immutable.argtypes = (ct.c_void_p,)
hb.hb_font_make_immutable.restype = None
hb.hb_font_make_immutable.argtypes = (ct.c_void_p,)
hb.hb_font_set_funcs.restype = None
hb.hb_font_set_funcs.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p)
hb.hb_font_set_funcs_data.restype = None
hb.hb_font_set_funcs_data.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p)
hb.hb_font_set_parent.restype = None
hb.hb_font_set_parent.argtypes = (ct.c_void_p, ct.c_void_p)
hb.hb_font_get_parent.restype = ct.c_void_p
hb.hb_font_get_parent.argtypes = (ct.c_void_p,)
hb.hb_font_get_face.restype = ct.c_void_p
hb.hb_font_get_face.argtypes = (ct.c_void_p,)
hb.hb_font_set_scale.restype = None
hb.hb_font_set_scale.argtypes = (ct.c_void_p, ct.c_int, ct.c_int)
hb.hb_font_get_scale.restype = None
hb.hb_font_get_scale.argtypes = (ct.c_void_p, ct.POINTER(ct.c_int), ct.POINTER(ct.c_int))
hb.hb_font_set_ppem.restype = None
hb.hb_font_set_ppem.argtypes = (ct.c_void_p, ct.c_uint, ct.c_uint)
hb.hb_font_get_ppem.restype = None
hb.hb_font_get_ppem.argtypes = (ct.c_void_p, ct.POINTER(ct.c_uint), ct.POINTER(ct.c_uint))
hb.hb_font_get_h_extents.restype = HB.bool_t
hb.hb_font_get_h_extents.argtypes = (ct.c_void_p, ct.POINTER(HB.font_extents_t))
hb.hb_font_get_v_extents.restype = HB.bool_t
hb.hb_font_get_v_extents.argtypes = (ct.c_void_p, ct.POINTER(HB.font_extents_t))
hb.hb_font_get_nominal_glyph.restype = HB.bool_t
hb.hb_font_get_nominal_glyph.argtypes = (ct.c_void_p, HB.codepoint_t, ct.POINTER(HB.codepoint_t))
hb.hb_font_get_variation_glyph.restype = HB.bool_t
hb.hb_font_get_variation_glyph.argtypes = (ct.c_void_p, HB.codepoint_t, HB.codepoint_t, ct.POINTER(HB.codepoint_t))
hb.hb_font_get_glyph_h_advance.restype = HB.position_t
hb.hb_font_get_glyph_h_advance.argtypes = (ct.c_void_p, HB.codepoint_t)
hb.hb_font_get_glyph_v_advance.restype = HB.position_t
hb.hb_font_get_glyph_v_advance.argtypes = (ct.c_void_p, HB.codepoint_t)
hb.hb_font_get_glyph_h_origin.restype = HB.bool_t
hb.hb_font_get_glyph_h_origin.argtypes = (ct.c_void_p, HB.codepoint_t, ct.POINTER(HB.position_t), ct.POINTER(HB.position_t))
hb.hb_font_get_glyph_v_origin.restype = HB.bool_t
hb.hb_font_get_glyph_v_origin.argtypes = (ct.c_void_p, HB.codepoint_t, ct.POINTER(HB.position_t), ct.POINTER(HB.position_t))
hb.hb_font_get_glyph_h_kerning.restype = HB.position_t
hb.hb_font_get_glyph_h_kerning.argtypes = (ct.c_void_p, HB.codepoint_t, HB.codepoint_t)
hb.hb_font_get_glyph_v_kerning.restype = HB.position_t
hb.hb_font_get_glyph_v_kerning.argtypes = (ct.c_void_p, HB.codepoint_t, HB.codepoint_t)
hb.hb_font_get_glyph_extents.restype = HB.bool_t
hb.hb_font_get_glyph_extents.argtypes = (ct.c_void_p, HB.codepoint_t, ct.POINTER(HB.glyph_extents_t))
hb.hb_font_get_glyph_contour_point.restype = HB.bool_t
hb.hb_font_get_glyph_contour_point.argtypes = (ct.c_void_p, HB.codepoint_t, ct.c_uint, ct.POINTER(HB.position_t), ct.POINTER(HB.position_t))
hb.hb_font_get_glyph_name.restype = HB.bool_t
hb.hb_font_get_glyph_name.argtypes = (ct.c_void_p, HB.codepoint_t, ct.c_char_p, ct.c_uint)
hb.hb_font_get_glyph_from_name.restype = HB.bool_t
hb.hb_font_get_glyph_from_name.argtypes = (ct.c_void_p, ct.c_char_p, ct.c_int, ct.POINTER(HB.codepoint_t))
hb.hb_font_get_glyph.restype = HB.bool_t
hb.hb_font_get_glyph.argtypes = (ct.c_void_p, HB.codepoint_t, HB.codepoint_t, ct.POINTER(HB.codepoint_t))
hb.hb_font_get_extents_for_direction.restype = None
hb.hb_font_get_extents_for_direction.argtypes = (ct.c_void_p, HB.direction_t, ct.POINTER(HB.font_extents_t))
hb.hb_font_get_glyph_advance_for_direction.restype = None
hb.hb_font_get_glyph_advance_for_direction.argtypes = (ct.c_void_p, HB.codepoint_t, HB.direction_t, ct.POINTER(HB.position_t), ct.POINTER(HB.position_t))
hb.hb_font_get_glyph_origin_for_direction.restype = None
hb.hb_font_get_glyph_origin_for_direction.argtypes = (ct.c_void_p, HB.codepoint_t, HB.direction_t, ct.POINTER(HB.position_t), ct.POINTER(HB.position_t))
hb.hb_font_add_glyph_origin_for_direction.restype = None
hb.hb_font_add_glyph_origin_for_direction.argtypes = (ct.c_void_p, HB.codepoint_t, HB.direction_t, ct.POINTER(HB.position_t), ct.POINTER(HB.position_t))
hb.hb_font_subtract_glyph_origin_for_direction.restype = None
hb.hb_font_subtract_glyph_origin_for_direction.argtypes = (ct.c_void_p, HB.codepoint_t, HB.direction_t, ct.POINTER(HB.position_t), ct.POINTER(HB.position_t))
hb.hb_font_get_glyph_kerning_for_direction.restype = None
hb.hb_font_get_glyph_kerning_for_direction.argtypes = (ct.c_void_p, HB.codepoint_t, HB.codepoint_t, HB.direction_t, ct.POINTER(HB.position_t), ct.POINTER(HB.position_t))
hb.hb_font_get_glyph_extents_for_origin.restype = HB.bool_t
hb.hb_font_get_glyph_extents_for_origin.argtypes = (ct.c_void_p, HB.codepoint_t, HB.direction_t, ct.POINTER(HB.glyph_extents_t))
hb.hb_font_get_glyph_contour_point_for_origin.restype = HB.bool_t
hb.hb_font_get_glyph_contour_point_for_origin.argtypes = (ct.c_void_p, HB.codepoint_t, ct.c_uint, HB.direction_t, ct.POINTER(HB.position_t), ct.POINTER(HB.position_t))
hb.hb_font_glyph_to_string.restype = None
hb.hb_font_glyph_to_string.argtypes = (ct.c_void_p, HB.codepoint_t, ct.c_char_p, ct.c_uint)
hb.hb_font_glyph_from_string.restype = HB.bool_t
hb.hb_font_glyph_from_string.argtypes = (ct.c_void_p, ct.c_char_p, ct.c_int, ct.POINTER(HB.codepoint_t))

hb.hb_font_funcs_create.restype = ct.c_void_p
hb.hb_font_funcs_create.argtypes = ()
hb.hb_font_funcs_get_empty.restype = ct.c_void_p
hb.hb_font_funcs_get_empty.argtypes = ()
hb.hb_font_funcs_destroy.restype = None
hb.hb_font_funcs_destroy.argtypes = (ct.c_void_p,)
hb.hb_font_funcs_make_immutable.restype = None
hb.hb_font_funcs_make_immutable.argtypes = (ct.c_void_p,)
hb.hb_font_funcs_is_immutable.restype = HB.bool_t
hb.hb_font_funcs_is_immutable.argtypes = (ct.c_void_p,)
hb.hb_font_funcs_reference.restype = ct.c_void_p
hb.hb_font_funcs_reference.argtypes = (ct.c_void_p,)
hb.hb_font_funcs_set_font_h_extents_func.restype = None
hb.hb_font_funcs_set_font_h_extents_func.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p)
hb.hb_font_funcs_set_font_v_extents_func.restype = None
hb.hb_font_funcs_set_font_v_extents_func.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p)
hb.hb_font_funcs_set_nominal_glyph_func.restype = None
hb.hb_font_funcs_set_nominal_glyph_func.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p)
hb.hb_font_funcs_set_variation_glyph_func.restype = None
hb.hb_font_funcs_set_variation_glyph_func.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p)
hb.hb_font_funcs_set_glyph_h_advance_func.restype = None
hb.hb_font_funcs_set_glyph_h_advance_func.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p)
hb.hb_font_funcs_set_glyph_v_advance_func.restype = None
hb.hb_font_funcs_set_glyph_v_advance_func.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p)
hb.hb_font_funcs_set_glyph_h_origin_func.restype = None
hb.hb_font_funcs_set_glyph_h_origin_func.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p)
hb.hb_font_funcs_set_glyph_v_origin_func.restype = None
hb.hb_font_funcs_set_glyph_v_origin_func.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p)
hb.hb_font_funcs_set_glyph_h_kerning_func.restype = None
hb.hb_font_funcs_set_glyph_h_kerning_func.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p)
hb.hb_font_funcs_set_glyph_v_kerning_func.restype = None
hb.hb_font_funcs_set_glyph_v_kerning_func.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p)
hb.hb_font_funcs_set_glyph_extents_func.restype = None
hb.hb_font_funcs_set_glyph_extents_func.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p)
hb.hb_font_funcs_set_glyph_contour_point_func.restype = None
hb.hb_font_funcs_set_glyph_contour_point_func.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p)
hb.hb_font_funcs_set_glyph_name_func.restype = None
hb.hb_font_funcs_set_glyph_name_func.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p)
hb.hb_font_funcs_set_glyph_from_name_func.restype = None
hb.hb_font_funcs_set_glyph_from_name_func.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p)

if freetype != None : # might as well skip these if I’m not using them
    hb.hb_ft_face_create_referenced.restype = ct.c_void_p
    hb.hb_ft_face_create_referenced.argtypes = (ct.c_void_p,)
    hb.hb_ft_font_create_referenced.restype = ct.c_void_p
    hb.hb_ft_font_create_referenced.argtypes = (ct.c_void_p,)
    hb.hb_ft_font_get_face.restype = ct.c_void_p
    hb.hb_ft_font_get_face.argtypes = (ct.c_void_p,)
    hb.hb_ft_font_set_load_flags.restype = None
    hb.hb_ft_font_set_load_flags.argtypes = (ct.c_void_p, ct.c_int)
    hb.hb_ft_font_get_load_flags.restype = ct.c_int
    hb.hb_ft_font_get_load_flags.argtypes = (ct.c_void_p,)
    hb.hb_ft_font_set_funcs.restype = None
    hb.hb_ft_font_set_funcs.argtypes = (ct.c_void_p,)
#end if

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

hb.hb_set_create.restype = ct.c_void_p
hb.hb_set_create.argtypes = ()
hb.hb_set_destroy.restype = None
hb.hb_set_destroy.argtypes = (ct.c_void_p,)
hb.hb_set_get_empty.restype = ct.c_void_p
hb.hb_set_get_empty.argtypes = ()
hb.hb_set_add.restype = None
hb.hb_set_add.argtypes = (ct.c_void_p, HB.codepoint_t)
hb.hb_set_add_range.restype = None
hb.hb_set_add_range.argtypes = (ct.c_void_p, HB.codepoint_t, HB.codepoint_t)
hb.hb_set_allocation_successful.restype = HB.bool_t
hb.hb_set_allocation_successful.argtypes = (ct.c_void_p,)
hb.hb_set_next.restype = HB.bool_t
hb.hb_set_next.argtypes = (ct.c_void_p, ct.c_void_p)
hb.hb_set_next_range.restype = HB.bool_t
hb.hb_set_next_range.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p)

hb.hb_ot_layout_has_glyph_classes.restype = HB.bool_t
hb.hb_ot_layout_has_glyph_classes.argtypes = (ct.c_void_p,)
hb.hb_ot_layout_get_glyph_class.restype = HB.ot_layout_glyph_class_t
hb.hb_ot_layout_get_glyph_class.argtypes = (ct.c_void_p, HB.codepoint_t)
hb.hb_ot_layout_get_glyphs_in_class.restype = None
hb.hb_ot_layout_get_glyphs_in_class.argtypes = (ct.c_void_p, HB.ot_layout_glyph_class_t, ct.c_void_p)
hb.hb_ot_layout_get_attach_points.restype = ct.c_uint
hb.hb_ot_layout_get_attach_points.argtypes = (ct.c_void_p, HB.codepoint_t, ct.c_uint, ct.POINTER(ct.c_uint), ct.POINTER(ct.c_uint))
hb.hb_ot_layout_get_ligature_carets.restype = ct.c_uint
hb.hb_ot_layout_get_ligature_carets.argtypes = (ct.c_void_p, HB.direction_t, HB.codepoint_t, ct.c_uint, ct.POINTER(ct.c_uint), ct.POINTER(HB.position_t))
hb.hb_ot_layout_table_get_script_tags.restype = ct.c_uint
hb.hb_ot_layout_table_get_script_tags.argtypes = (ct.c_void_p, HB.tag_t, ct.c_uint, ct.POINTER(ct.c_uint), ct.POINTER(HB.tag_t))
hb.hb_ot_layout_table_find_script.restype = HB.bool_t
hb.hb_ot_layout_table_find_script.argtypes = (ct.c_void_p, HB.tag_t, HB.tag_t, ct.POINTER(ct.c_uint))
hb.hb_ot_layout_table_choose_script.restype = HB.bool_t
hb.hb_ot_layout_table_choose_script.argtypes = (ct.c_void_p, HB.tag_t, ct.POINTER(HB.tag_t), ct.POINTER(ct.c_uint), ct.POINTER(HB.tag_t))
hb.hb_ot_layout_table_get_feature_tags.restype = ct.c_uint
hb.hb_ot_layout_table_get_feature_tags.argtypes = (ct.c_void_p, HB.tag_t, ct.c_uint, ct.POINTER(ct.c_uint), ct.POINTER(HB.tag_t))
hb.hb_ot_layout_script_get_language_tags.restype = ct.c_uint
hb.hb_ot_layout_script_get_language_tags.argtypes = (ct.c_void_p, HB.tag_t, ct.c_uint, ct.c_uint, ct.POINTER(ct.c_uint), ct.POINTER(HB.tag_t))
hb.hb_ot_layout_script_find_language.restype = HB.bool_t
hb.hb_ot_layout_script_find_language.argtypes = (ct.c_void_p, HB.tag_t, ct.c_uint, HB.tag_t, ct.POINTER(ct.c_uint))
hb.hb_ot_layout_language_get_required_feature_index.restype = HB.bool_t
hb.hb_ot_layout_language_get_required_feature_index.argtypes = (ct.c_void_p, HB.tag_t, ct.c_uint, ct.c_uint, ct.POINTER(ct.c_uint))
hb.hb_ot_layout_language_get_required_feature.restype = HB.bool_t
hb.hb_ot_layout_language_get_required_feature.argtypes = (ct.c_void_p, HB.tag_t, ct.c_uint, ct.c_uint, ct.POINTER(ct.c_uint), ct.POINTER(HB.tag_t))
hb.hb_ot_layout_language_get_feature_indexes.restype = ct.c_uint
hb.hb_ot_layout_language_get_feature_indexes.argtypes = (ct.c_void_p, HB.tag_t, ct.c_uint, ct.c_uint, ct.c_uint, ct.POINTER(ct.c_uint), ct.POINTER(HB.tag_t))
hb.hb_ot_layout_language_get_feature_tags.restype = ct.c_uint
hb.hb_ot_layout_language_get_feature_tags.argtypes = (ct.c_void_p, HB.tag_t, ct.c_uint, ct.c_uint, ct.c_uint, ct.POINTER(ct.c_uint), ct.POINTER(HB.tag_t))
hb.hb_ot_layout_language_find_feature.restype = HB.bool_t
hb.hb_ot_layout_language_find_feature.argtypes = (ct.c_void_p, HB.tag_t, ct.c_uint, ct.c_uint, HB.tag_t, ct.POINTER(ct.c_uint))
hb.hb_ot_layout_feature_get_lookups.restype = ct.c_uint
hb.hb_ot_layout_feature_get_lookups.argtypes = (ct.c_void_p, HB.tag_t, ct.c_uint, ct.c_uint, ct.POINTER(ct.c_uint), ct.POINTER(ct.c_uint))
hb.hb_ot_layout_table_get_lookup_count.restype = ct.c_uint
hb.hb_ot_layout_table_get_lookup_count.argtypes = (ct.c_void_p, HB.tag_t)
hb.hb_ot_layout_collect_lookups.restype = None
hb.hb_ot_layout_collect_lookups.argtypes = (ct.c_void_p, HB.tag_t, ct.POINTER(HB.tag_t), ct.POINTER(HB.tag_t), ct.POINTER(HB.tag_t), ct.c_void_p)
hb.hb_ot_layout_lookup_collect_glyphs.restype = None
hb.hb_ot_layout_lookup_collect_glyphs.argtypes = (ct.c_void_p, HB.tag_t, ct.c_uint, ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p)
hb.hb_ot_layout_has_substitution.restype = HB.bool_t
hb.hb_ot_layout_has_substitution.argtypes = (ct.c_void_p,)
hb.hb_ot_layout_lookup_would_substitute.restype = HB.bool_t
hb.hb_ot_layout_lookup_would_substitute.argtypes = (ct.c_void_p, ct.c_uint, ct.POINTER(HB.codepoint_t), ct.c_uint, HB.bool_t)
hb.hb_ot_layout_lookup_substitute_closure.restype = None
hb.hb_ot_layout_lookup_substitute_closure.argtypes = (ct.c_void_p, ct.c_uint, ct.c_void_p)
hb.hb_ot_layout_has_positioning.restype = HB.bool_t
hb.hb_ot_layout_has_positioning.argtypes = (ct.c_void_p,)
hb.hb_ot_layout_get_size_params.restype = HB.bool_t
hb.hb_ot_layout_get_size_params.argtypes = (ct.c_void_p, ct.POINTER(ct.c_uint), ct.POINTER(ct.c_uint), ct.POINTER(ct.c_uint), ct.POINTER(ct.c_uint), ct.POINTER(ct.c_uint))

hb.hb_ot_tags_from_script.restype = None
hb.hb_ot_tags_from_script.argtypes = (HB.script_t, ct.POINTER(HB.tag_t), ct.POINTER(HB.tag_t))
hb.hb_ot_tag_to_script.restype = HB.script_t
hb.hb_ot_tag_to_script.argtypes = (HB.tag_t,)
hb.hb_ot_tag_from_language.restype = HB.tag_t
hb.hb_ot_tag_from_language.argtypes = (ct.c_void_p,)
hb.hb_ot_tag_to_language.restype = ct.c_void_p
hb.hb_ot_tag_to_language.argtypes = (HB.tag_t,)

hb.hb_ot_font_set_funcs.restype = None
hb.hb_ot_font_set_funcs.argtypes = (ct.c_void_p,)

hb.hb_ot_shape_glyphs_closure.restype = None
hb.hb_ot_shape_glyphs_closure.argtyes = (ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_uint, ct.c_void_p)
hb.hb_ot_shape_plan_collect_lookups.restype = None
hb.hb_ot_shape_plan_collect_lookups.argtypes = (ct.c_void_p, HB.tag_t, ct.c_void_p)

hb.hb_shape_plan_create.restype = ct.c_void_p
hb.hb_shape_plan_create.argtypes = (ct.c_void_p, ct.POINTER(HB.segment_properties_t), ct.c_void_p, ct.c_uint, ct.c_void_p)
hb.hb_shape_plan_create_cached.restype = ct.c_void_p
hb.hb_shape_plan_create_cached.argtypes = (ct.c_void_p, ct.POINTER(HB.segment_properties_t), ct.c_void_p, ct.c_uint, ct.c_void_p)
hb.hb_shape_plan_destroy.restype = None
hb.hb_shape_plan_destroy.argtypes = (ct.c_void_p,)
hb.hb_shape_plan_execute.restype = HB.bool_t
hb.hb_shape_plan_execute.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_uint)
hb.hb_shape_plan_get_empty.restype = ct.c_void_p
hb.hb_shape_plan_get_empty.argtypes = ()
hb.hb_shape_plan_get_shaper.restype = ct.c_char_p
hb.hb_shape_plan_get_shaper.argtypes = (ct.c_void_p,)
hb.hb_shape_plan_reference.restype = ct.c_void_p
hb.hb_shape_plan_reference.argtypes = (ct.c_void_p,)

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
        hb.hb_version_atleast(major, minor, micro) != 0
#end version_atleast

def version_string() :
    "returns the version string."
    return \
        hb.hb_version_string().decode() # automatically stops at NUL?
#end version_string

# from hb-common.h:

def direction_from_string(s) :
    sb = s.encode()
    return \
        hb.hb_direction_from_string(sb, len(sb))
#end direction_from_string

def direction_to_string(direction) :
    return \
        hb.hb_direction_to_string(direction).decode() # automatically stops at NUL?
#end direction_to_string

#+
# Notes on object design:
#
# Python objects which wrap HarfBuzz objects store address of latter
# in _hbobj attribute. Object constructors are reserved for internal
# use.
#
# Round-trip object identity: when one HarfBuzz object is set as an
# attribute of another (e.g. a Buffer.unicode_funcs is set to a
# UnicodeFuncs) and then retrieved again, it is nice if the caller
# gets back the same Python wrapper object. I do this by maintaining a
# WeakValueDictionary in each of the relevant (base) classes, which is
# updated by the constructors.
#
# Fixme: there is still a hole in the interaction of the above with
# the handling of dependency references ("_arr" and "_face" attributes
# to keep referenced objects from unexpectedly disappearing), namely that
# such references will not be recovered when the Python object has to be
# recreated. Should I worry about this?
#-

class UserDataDict(dict) :
    "a subclass of dict that allows weakrefs."

    __slots__ = ("__weakref__",)

    def __init__(self, *args, **kwargs) :
        super().__init__(*args, **kwargs)
    #end __init__

#end UserDataDict

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
        "returns the currently-configured default Language."
        return \
            Language(hb.hb_language_get_default())
    #end default

    @classmethod
    def from_string(celf, s) :
        "returns the Language object for the specified language string, e.g. “en-nz”."
        sb = s.encode()
        result = hb.hb_language_from_string(sb, len(sb))
        if result == None :
            raise ValueError("invalid language “%s”" % s)
        #end if
        return \
            Language(result)
    #end from_string

    def to_string(self) :
        "returns the language string for this Language object, e.g. “en-nz”."
        return \
            hb.hb_language_to_string(self._hbobj).decode() # automatically stops at NUL?
    #end to_string

    def __repr__(self) :
        return \
            "<Language>(%s)" % self.to_string()
    #end __repr__

#end Language

def tag_from_bytes(b) :
    "constructs a tag from a four-byte bytes value."
    return \
        hb.hb_tag_from_string(b, len(b))
#end tag_from_string

def tag_to_bytes(tag) :
    "converts a tag to a four-byte bytes value."
    buf = (4 * ct.c_ubyte)()
    hb.hb_tag_to_string(tag, ct.byref(buf))
    return \
        bytes(buf)
#end tag_to_bytes

def tag_from_string(s) :
    "constructs a tag from a four-character string."
    sb = s.encode()
    return \
        hb.hb_tag_from_string(sb, len(sb))
#end tag_from_string

def tag_to_string(tag) :
    "converts a tag to a four-character string."
    buf = (4 * ct.c_ubyte)()
    hb.hb_tag_to_string(tag, ct.byref(buf))
    return \
        bytes(buf).decode()
#end tag_to_string

def script_from_iso15924_tag(tag) :
    return \
        hb.hb_script_from_iso15924_tag(tag)
#end script_from_iso15924_tag

def script_from_string(s) :
    sb = s.encode()
    return \
        hb.hb_script_from_string(sb, len(sb))
#end script_from_string

def script_to_iso15924_tag(script) :
    return \
        hb.hb_script_to_iso15924_tag(script)
#end script_to_iso15924_tag

def script_get_horizontal_direction(script) :
    return \
        hb.hb_script_get_horizontal_direction(script)
#end script_get_horizontal_direction

# from hb-unicode.h:

class UnicodeFuncs :
    "wrapper around hb_unicode_funcs_t objects. Do not instantiate directly; use" \
    " the create, get_default and get_empty methods."

    __slots__ = \
        ( # to forestall typos
            "_hbobj",
            "_user_data",
            "__weakref__",
            # need to keep references to ctypes-wrapped functions
            # so they don't disappear prematurely:
            "_wrap_combining_class_func",
            "_wrap_combining_class_destroy",
            "_wrap_eastasian_width_func",
            "_wrap_eastasian_width_destroy",
            "_wrap_general_category_func",
            "_wrap_general_category_destroy",
            "_wrap_mirroring_func",
            "_wrap_mirroring_destroy",
            "_wrap_script_func",
            "_wrap_script_destroy",
            "_wrap_compose_func",
            "_wrap_compose_destroy",
            "_wrap_decompose_func",
            "_wrap_decompose_destroy",
            "_wrap_decompose_compatibility_func",
            "_wrap_decompose_compatibility_destroy",
        )

    _instances = WeakValueDictionary()
    _ud_refs = WeakValueDictionary()

    def __new__(celf, _hbobj) :
        self = celf._instances.get(_hbobj)
        if self == None :
            self = super().__new__(celf)
            self._wrap_combining_class_func = None
            self._wrap_combining_class_destroy = None
            self._wrap_eastasian_width_func = None
            self._wrap_eastasian_width_destroy = None
            self._wrap_general_category_func = None
            self._wrap_general_category_destroy = None
            self._wrap_mirroring_func = None
            self._wrap_mirroring_destroy = None
            self._wrap_script_func = None
            self._wrap_script_destroy = None
            self._wrap_compose_func = None
            self._wrap_compose_destroy = None
            self._wrap_decompose_func = None
            self._wrap_decompose_destroy = None
            self._wrap_decompose_compatibility_func = None
            self._wrap_decompose_compatibility_destroy = None
            self._hbobj = _hbobj
            user_data = celf._ud_refs.get(_hbobj)
            if user_data == None :
                user_data = UserDataDict()
                celf._ud_refs[_hbobj] = user_data
            #end if
            self._user_data = user_data
            celf._instances[_hbobj] = self
        else :
            hb.hb_unicode_funcs_destroy(self._hbobj)
              # lose extra reference created by caller
        #end if
        return \
            self
    #end __new__

    def __del__(self) :
        if hb != None and self._hbobj != None :
            hb.hb_unicode_funcs_destroy(self._hbobj)
            self._hbobj = None
        #end if
    #end __del__

    @staticmethod
    def get_default() :
        return \
            UnicodeFuncs(hb.hb_unicode_funcs_reference(hb.hb_unicode_funcs_get_default()))
    #end get_default

    @staticmethod
    def create(parent = None) :
        if parent != None and not isinstance(parent, UnicodeFuncs) :
            raise TypeError("parent must be None or a UnicodeFuncs")
        #end if
        return \
            UnicodeFuncs \
              (
                hb.hb_unicode_funcs_create
                  (
                    (lambda : None, lambda : parent._hbobj)[parent != None]()
                  )
              )
    #end create

    @staticmethod
    def get_empty() :
        "returns the (unique) “empty” UnicodeFuncs object. Its functions behave as" \
        " follows:\n" \
        "\n" \
        "    combining_class always returns HB.UNICODE_COMBINING_CLASS_NOT_REORDERED\n" \
        "    eastasian_width always returns 1\n" \
        "    general_category always returns HB.UNICODE_GENERAL_CATEGORY_OTHER_LETTER\n" \
        "    unicode_mirroring always returns the passed character\n" \
        "    unicode_script always returns HB.SCRIPT_UNKNOWN\n" \
        "    unicode_compose always returns None\n" \
        "    unicode_decompose always returns None\n" \
        "    unicode_decompose_compatibility always returns an empty sequence."
        return \
            UnicodeFuncs(hb.hb_unicode_funcs_reference(hb.hb_unicode_funcs_get_empty()))
    #end get_empty

    # immutable defined below

    @property
    def user_data(self) :
        "a dict, initially empty, which may be used by caller for any purpose."
        return \
            self._user_data
    #end user_data

    # HarfBuzz user_data calls not exposed to caller, probably not useful

    @property
    def parent(self) :
        return \
            UnicodeFuncs(hb.hb_unicode_funcs_reference(hb.hb_unicode_funcs_get_parent(self._hbobj)))
    #end parent

    # set_combining_class_func
    # set_eastasian_width_func
    # set_general_category_func
    # set_mirroring_func
    # set_script_func
    # set_compose_func
    # set_decompose_func
    # set_decompose_compatibility_func
    # all defined below

    def combining_class(self, unicode) :
        "invokes the combining_class_func."
        return \
            hb.hb_unicode_combining_class(self._hbobj, unicode)
    #end combining_class

    def eastasian_width(self, unicode) :
        "invokes the eastasian_width_func."
        return \
            hb.hb_unicode_eastasian_width(self._hbobj, unicode)
    #end eastasian_width

    def general_category(self, unicode) :
        "invokes the general_category_func."
        return \
            hb.hb_unicode_general_category(self._hbobj, unicode)
    #end general_category

    def mirroring(self, unicode) :
        "invokes the mirroring_func."
        return \
            hb.hb_unicode_mirroring(self._hbobj, unicode)
    #end mirroring

    def script(self, unicode) :
        "invokes the script_func."
        return \
            hb.hb_unicode_script(self._hbobj, unicode)
    #end script

    def compose(self, a, b) :
        "invokes the compose_func."
        ab = HB.codepoint_t()
        if hb.hb_unicode_compose(self._hbobj, a, b, ct.byref(ab)) != 0 :
            result = ab.value
        else :
            result = None
        #end if
        return \
            result
    #end compose

    def decompose(self, ab) :
        "invokes the decompose_func."
        a = HB.codepoint_t()
        b = HB.codepoint_t()
        if hb.hb_unicode_decompose(self._hbobj, ab, ct.byref(a), ct.byref(b)) != 0 :
            result = (a.value, b.value)
        else :
            result = None
        #end if
        return \
            result
    #end decompose

    def decompose_compatibility(self, u) :
        "invokes the decompose_compatibility_func."
        decomposed = (HB.codepoint_t * HB.UNICODE_MAX_DECOMPOSITION_LEN)()
        decomposed_len = hb.hb_unicode_decompose_compatibility(self._hbobj, u, decomposed)
        return \
            decomposed[:decomposed_len]
    #end decompose_compatibility

#end UnicodeFuncs
def_immutable \
  (
    celf = UnicodeFuncs,
    hb_query = "hb_unicode_funcs_is_immutable",
    hb_set = "hb_unicode_funcs_make_immutable",
  )
def def_unicodefuncs_extra() :

    def def_wrap_combining_class_func(self, combining_class_func, user_data) :

        @HB.unicode_combining_class_func_t
        def wrap_combining_class_func(c_funcs, unicode, c_user_data) :
            return \
                combining_class_func(self, unicode, user_data)
        #end wrap_combining_class_func

    #begin def_wrap_combining_class_func
        return \
            wrap_combining_class_func
    #end def_wrap_combining_class_func

    def def_wrap_eastasian_width_func(self, eastasian_width_func, user_data) :

        @HB.unicode_eastasian_width_func_t
        def wrap_eastasian_width_func(c_funcs, unicode, c_user_data) :
            return \
                eastasian_width_func(self, unicode, user_data)
        #end wrap_eastasian_width_func

    #begin def_wrap_eastasian_width_func
        return \
            wrap_eastasian_width_func
    #end def_wrap_eastasian_width_func

    def def_wrap_general_category_func(self, general_category_func, user_data) :

        @HB.unicode_general_category_func_t
        def wrap_general_category_func(c_funcs, unicode, c_user_data) :
            return \
                general_category_func(self, unicode, user_data)
        #end wrap_general_category_func

    #begin def_wrap_general_category_func
        return \
            wrap_general_category_func
    #end def_wrap_general_category_func

    def def_wrap_mirroring_func(self, mirroring_func, user_data) :

        @HB.unicode_mirroring_func_t
        def wrap_mirroring_func(c_funcs, unicode, c_user_data) :
            return \
                mirroring_func(self, unicode, user_data)
        #end wrap_mirroring_func

    #begin def_wrap_mirroring_func
        return \
            wrap_mirroring_func
    #end def_wrap_mirroring_func

    def def_wrap_script_func(self, script_func, user_data) :

        @HB.unicode_script_func_t
        def wrap_script_func(c_funcs, unicode, c_user_data) :
            return \
                script_func(self, unicode, user_data)
        #end wrap_script_func

    #begin def_wrap_script_func
        return \
            wrap_script_func
    #end def_wrap_script_func

    def def_wrap_compose_func(self, compose_func, user_data) :

        @HB.unicode_compose_func_t
        def wrap_compose_func(c_funcs, a, b, c_ab, c_user_data) :
            result = compose_func(self, a, b, user_data)
            if result != None :
                c_ab[0] = result
            else :
                c_ab[0] = 0 # ?
            #end if
            return \
                result != None
        #end wrap_compose_func

    #begin def_wrap_compose_func
        return \
            wrap_compose_func
    #end def_wrap_compose_func

    def def_wrap_decompose_func(self, decompose_func, user_data) :

        @HB.unicode_decompose_func_t
        def wrap_decompose_func(c_funcs, ab, c_a, c_b, c_user_data) :
            result = decompose_func(self, ab, user_data)
            if result != None :
                c_a[0], c_b[0] = result
            else :
                c_a[0], c_b[0] = (0, 0)
            #end if
            return \
                result != None
        #end wrap_decompose_func

    #begin def_wrap_decompose_func
        return \
            wrap_decompose_func
    #end def_wrap_decompose_func

    def def_wrap_decompose_compatibility_func(self, decompose_compatibility_func, user_data) :

        @HB.unicode_decompose_compatibility_func_t
        def wrap_decompose_compatibility_func(c_funcs, u, c_decomposed, c_user_data) :
            result = decompose_compatibility_func(self, u, user_data)
            if result == None :
                result = ()
            #end if
            if len(result) > HB.UNICODE_MAX_DECOMPOSITION_LEN :
                raise IndexError \
                  (
                        "decompose_compatibility result len %d exceeds %d"
                    %
                        (len(result), HB.UNICODE_MAX_DECOMPOSITION_LEN)
                  )
            #end if
            for i in range(len(result)) :
                c_decomposed[i] = result[i]
            #end for
            return \
                len(result)
        #end wrap_decompose_compatibility_func

    #begin def_wrap_decompose_compatibility_func
        return \
            wrap_decompose_compatibility_func
    #end def_wrap_decompose_compatibility_func

#begin def_unicodefuncs_extra
    for basename, def_func, protostr, resultstr in \
        (
            ("combining_class", def_wrap_combining_class_func, "combining_class_func(self, unicode, user_data)", "n integer combining class code"),
            ("eastasian_width", def_wrap_eastasian_width_func, "eastasian_width_func(self, unicode, user_data)", "n integer"),
            ("general_category", def_wrap_general_category_func, "general_category_func(self, unicode, user_data)", "n integer general category code"),
            ("mirroring", def_wrap_mirroring_func, "mirroring_func(self, unicode, user_data)", " unicode code point"),
            ("script", def_wrap_script_func, "script_func(self, unicode, user_data)", "n integer script code"),
            ("compose", def_wrap_compose_func, "compose_func(self, a, b, user_data)", " unicode code point or None"),
            ("decompose", def_wrap_decompose_func, "decompose_func(self, ab, user_data)", " 2-tuple of Unicode code points or None"),
            ("decompose_compatibility", def_wrap_decompose_compatibility_func, "decompose_compatibility_func(self, u, user_data)", " tuple of Unicode code points or None"),
        ) \
    :
        def_callback_wrapper \
          (
            celf = UnicodeFuncs,
            method_name = "set_%s_func" % basename,
            docstring =
                    "sets the %(name)s_func callback, along with an optional destroy"
                    " callback for the user_data. The callback_func should be declared"
                    " as follows:\n"
                    "\n"
                    "    def %(proto)s\n"
                    "\n"
                    " where self is the UnicodeFuncs instance, and return a%(result)s."
                %
                    {"name" : basename, "proto" : protostr, "result" : resultstr},
            callback_field_name = "_wrap_%s_func" % basename,
            destroy_field_name = "_wrap_%s_destroy" % basename,
            def_wrap_callback_func = def_func,
            hb_proc = "hb_unicode_funcs_set_%s_func" % basename,
          )
    #end for
#end def_unicodefuncs_extra
def_unicodefuncs_extra()
del def_unicodefuncs_extra

# from hb-blob.h:

class Blob :
    "wraps the hb_blob_t opaque type. This is used to manage storage for Face objects." \
    " Do not instantiate directly; use the create and get_empty methods."

    __slots__ = \
        ( # to forestall typos
            "_hbobj",
            "_user_data",
            "__weakref__",
            "_arr",
            # need to keep references to ctypes-wrapped functions
            # so they don't disappear prematurely:
            "_wrap_destroy",
        )

    _instances = WeakValueDictionary()
    _ud_refs = WeakValueDictionary()

    def __new__(celf, _hbobj) :
        self = celf._instances.get(_hbobj)
        if self == None :
            self = super().__new__(celf)
            self._hbobj = _hbobj
            self._arr = None
            self._wrap_destroy = None
            user_data = celf._ud_refs.get(_hbobj)
            if user_data == None :
                user_data = UserDataDict()
                celf._ud_refs[_hbobj] = user_data
            #end if
            self._user_data = user_data
            celf._instances[_hbobj] = self
        else :
            hb.hb_blob_destroy(self._hbobj)
              # lose extra reference created by caller
        #end if
        return \
            self
    #end __new__

    def __del__(self) :
        if hb != None and self._hbobj != None :
            hb.hb_blob_destroy(self._hbobj)
            self._hbobj = None
        #end if
    #end __del__

    @classmethod
    def create(celf, data, length, mode, user_data, destroy) :
        "low-level Blob create routine: data is address of storage and length" \
        " is its length in bytes."
        if destroy != None :
            @HB.destroy_func_t
            def wrap_destroy(c_user_data) :
                destroy(user_data)
            #end wrap_destroy
        else :
            wrap_destroy = None
        #end if
        result = celf(hb.hb_blob_create(data, length, mode, None, wrap_destroy))
        result._wrap_destroy = wrap_destroy
        return \
            result
    #end create

    @classmethod
    def create_for_array(celf, arr, mode) :
        "creates a Blob that wraps the storage for the specified bytes, bytearray or" \
        " array.array object. mode is one of the MEMORY_MODE_XXX values."
        if isinstance(arr, bytes) :
            baseadr = ct.cast(arr, ct.c_void_p).value
            size = len(arr)
        elif isinstance(arr, bytearray) :
            size = len(arr)
            baseadr = ct.addressof((ct.c_char * size).from_buffer(arr))
        elif isinstance(arr, array.array) and arr.typecode == "B" :
            baseadr, size = arr.buffer_info()
        else :
            raise TypeError("data is not bytes, bytearray or array.array of bytes")
        #end if
        result = celf.create(baseadr, size, mode, None, None)
        result._arr = arr # keep a reference to ensure it doesn’t disappear prematurely
        return \
            result
    #end create_for_array

    def create_sub(self, offset, length) :
        "creates a sub-Blob spanning the specified range of bytes in the parent." \
        " Child inherits parent’s memory mode, but Parent is made immutable."
        return \
            Blob(hb.hb_blob_create_sub_blob(self._hbobj, offset, length))
    #end create_sub

    @staticmethod
    def get_empty() :
        "returns the (unique) empty Blob. This has a null data pointer, zero length," \
        " and its memory mode is readonly."
        return \
            Blob(hb.hb_blob_reference(hb.hb_blob_get_empty()))
    #end get_empty

    def __len__(self) :
        "the length of the Blob data."
        return \
            hb.hb_blob_get_length(self._hbobj)
    #end __len__

    def data(self, writable) :
        "returns a tuple (addr, length) of the Blob for read-only or read/write" \
        " access, depending on writable."
        length = ct.c_uint()
        addr = (hb.hb_blob_get_data, hb.hb_blob_get_data_writable)[writable] \
            (self._hbobj, ct.byref(length))
        if addr == None :
            raise ValueError("failed to get blob data")
        #end if
        return \
            addr, length.value
    #end data

    # immutable defined below

    @property
    def user_data(self) :
        "a dict, initially empty, which may be used by caller for any purpose."
        return \
            self._user_data
    #end user_data

    # HarfBuzz user_data calls not exposed to caller, probably not useful

#end Blob
def_immutable \
  (
    celf = Blob,
    hb_query = "hb_blob_is_immutable",
    hb_set = "hb_blob_make_immutable",
  )

# from hb-buffer.h:

GlyphInfo = def_struct_class \
  (
    name = "GlyphInfo",
    ctname = "glyph_info_t"
  )
class GlyphPositionExtra :
    # extra members for GlyphPosition class.

    if qahirah != None :

        @property
        def advance(self) :
            "returns the x- and y-advance of the glyph position as a qahirah.Vector."
            return \
                qahirah.Vector(self.x_advance, self.y_advance)
        #end advance

        @property
        def offset(self) :
            "returns the x- and y-offset of the glyph position as a qahirah.Vector."
            return \
                qahirah.Vector(self.x_offset, self.y_offset)
        #end offset

    #end if
#end GlyphPositionExtra
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
        },
    extra = GlyphPositionExtra
  )
del GlyphPositionExtra
FontExtents = def_struct_class \
  (
    name = "FontExtents",
    ctname = "font_extents_t",
    conv =
        {
            "ascender" : {"from" : HB.from_position_t, "to" : HB.to_position_t},
            "descender" : {"from" : HB.from_position_t, "to" : HB.to_position_t},
            "line_gap" : {"from" : HB.from_position_t, "to" : HB.to_position_t},
        }
  )
GlyphExtents = def_struct_class \
  (
    name = "GlyphExtents",
    ctname = "glyph_extents_t",
    conv =
        {
            "x_bearing" : {"from" : HB.from_position_t, "to" : HB.to_position_t},
            "y_bearing" : {"from" : HB.from_position_t, "to" : HB.to_position_t},
            "width" : {"from" : HB.from_position_t, "to" : HB.to_position_t},
            "height" : {"from" : HB.from_position_t, "to" : HB.to_position_t},
        }
  )

SegmentProperties = None # forward
class SegmentPropertiesExtra :
    # extra members for SegmentProperties class.

    def __eq__(s1, s2) :
        if isinstance(s2, SegmentProperties) :
            result = hb.hb_segment_properties_equal(s1,_hbobj, s2._hbobj) != 0
        else :
            result = NotImplemented
        #end if
        return \
            result
    #end __eq__

    def __hash__(self) :
        return \
            hb.hb_segment_properties_hash(self._hbobj)
    #end __hash__

#end SegmentPropertiesExtra
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
                },
            "script" :
                {
                    "to" : HB.TAG,
                    "from" : lambda t : HB.UNTAG(t, True),
                },
        },
    extra = SegmentPropertiesExtra
  )
del SegmentPropertiesExtra

class Buffer :
    "a HarfBuzz buffer. This is where the text shaping is actually done." \
    " Note that a Buffer can only manage a single run of text (language, script," \
    " direction = “segment”) at once."
    " Do not instantiate directly; call the create or get_empty methods."

    __slots__ = \
        ( # to forestall typos
            "_hbobj",
            "_user_data",
            "__weakref__",
            "autoscale", # setting from last font passed to a shape operation
            "_unicode_funcs", # last set UnicodeFuncs, just to keep it from going away prematurely
            # need to keep references to ctypes-wrapped functions
            # so they don't disappear prematurely:
            "_wrap_message_func",
            "_wrap_message_destroy",
        )

    _instances = WeakValueDictionary()
    _ud_refs = WeakValueDictionary()

    def __new__(celf, _hbobj) :
        self = celf._instances.get(_hbobj)
        if self == None :
            self = super().__new__(celf)
            self._hbobj = _hbobj
            self.autoscale = False # to begin with
            self._unicode_funcs = None
            self._wrap_message_func = None
            self._wrap_message_destroy = None
            user_data = celf._ud_refs.get(_hbobj)
            if user_data == None :
                user_data = UserDataDict()
                celf._ud_refs[_hbobj] = user_data
            #end if
            self._user_data = user_data
            celf._instances[_hbobj] = self
        else :
            hb.hb_buffer_destroy(self._hbobj)
              # lose extra reference created by caller
        #end if
        return \
            self
    #end __new__

    def __del__(self) :
        if hb != None and self._hbobj != None :
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
        "returns the (unique) empty Buffer instance."
        return \
            Buffer(hb.hb_buffer_reference(hb.hb_buffer_get_empty()))
    #end get_empty

    def reset(self) :
        "resets the buffer state as though it were newly created."
        hb.hb_buffer_reset(self._hbobj)
        self.autoscale = False # to begin with
    #end reset

    def clear_contents(self) :
        "similar to reset, but does not clear the Unicode functions" \
        " or the replacement code point."
        hb.hb_buffer_clear_contents(self._hbobj)
        self.autoscale = False # to begin with
    #end clear_contents

    def pre_allocate(self, size) :
        if hb.hb_buffer_pre_allocate(self._hbobj, size) == 0 :
            raise RuntimeError("pre_allocate failed")
        #end if
    #end pre_allocate

    def allocation_successful(self) :
        return \
            hb.hb_buffer_allocation_successful(self._hbobj) != 0
    #end allocation_successful

    def check_alloc(self) :
        "checks that the last buffer allocation was successful."
        if hb.hb_buffer_allocation_successful(self._hbobj) == 0 :
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

    def add_str(self, text, item_offset = None, item_length = None) :
        if item_offset == None :
            item_offset = 0
        #end if
        if item_length == None :
            item_length = len(text)
        #end if
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
        if hb.hb_buffer_set_length(self._hbobj, length) == 0 :
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

    @property
    def unicode_funcs(self) :
        return \
            UnicodeFuncs(hb.hb_unicode_funcs_reference(hb.hb_buffer_get_unicode_funcs(self._hbobj)))
    #end unicode_funcs

    @unicode_funcs.setter
    def unicode_funcs(self, funcs) :
        if funcs == None :
            new_funcs = None
        elif isinstance(funcs, UnicodeFuncs) :
            new_funcs = funcs._hbobj
        else :
            raise TypeError("funcs must be None or UnicodeFuncs")
        #end if
        self._unicode_funcs = funcs
        hb.hb_buffer_set_unicode_funcs(self._hbobj, new_funcs)
    #end unicode_funcs

    @property
    def user_data(self) :
        "a dict, initially empty, which may be used by caller for any purpose."
        return \
            self._user_data
    #end user_data

    # HarfBuzz user_data calls not exposed to caller, probably not useful

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
            tuple(GlyphPosition.from_hb(arr[i], self.autoscale) for i in range(nr_glyphs.value))
    #end glyph_positions

    if qahirah != None :

        def get_glyphs(self, origin = None) :
            "returns a a tuple of two items, a list of qahirah.Glyph objects," \
            " and the Vector origin for the following glyph run. All positions can" \
            " be optionally offset by the specified Vector origin. The signs of the" \
            " y-coordinates are flipped to correspond to the usual Cairo convention" \
            " of increasing downwards."
            glyph_infos = self.glyph_infos
            glyph_positions = self.glyph_positions
            result = []
            if origin != None :
                pos = origin
            else :
                pos = qahirah.Vector(0, 0)
            #end if
            for i in range(len(glyph_infos)) :
                result.append \
                  (
                    qahirah.Glyph(glyph_infos[i].codepoint, pos + qahirah.Vector(1, -1) * glyph_positions[i].offset)
                  )
                pos += qahirah.Vector(1, -1) * glyph_positions[i].advance
            #end for
            return \
                (result, pos)
        #end get_glyphs

    #end if

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

    def serialize_glyphs(self, font, format, flags) :
        "returns a bytes value."
        if font != None and not isinstance(font, Font) :
            raise TypeError("font must be None or a Font")
        #end if
        format = SerializeFormat.make_serialize(format)
        pos = 0
        end = len(self)
        tempbuf = array.array("B", (0,) * 512)
        nr_items = 0
        buf_consumed = ct.c_uint()
        result = b""
        while pos != end :
            seg_items = hb.hb_buffer_serialize_glyphs(self._hbobj, pos, end, tempbuf.buffer_info()[0], tempbuf.buffer_info()[1], ct.byref(buf_consumed), (lambda : None, lambda : font._hbobj)[font != None](), format._tag, flags)
            result += bytes(tempbuf[:buf_consumed.value])
            pos += seg_items
        #end while
        return \
            result
    #end serialize_glyphs

    def deserialize_glyphs(self, b, font, format) :
        if font != None and not isinstance(font, Font) :
            raise TypeError("font must be None or a Font")
        #end if
        format = SerializeFormat.make_serialize(format)
        tempbuf = array.array("B", b)
        end_ptr = ct.c_void_p()
        if (
                hb.hb_buffer_deserialize_glyphs
                  (
                    self._hbobj,
                    tempbuf.buffer_info()[0],
                    tempbuf.buffer_info()[1],
                    ct.byref(end_ptr),
                    (lambda : None, lambda : font._hbobj)[font != None](),
                    format._tag
                  )
            ==
                0
        ) :
            raise RuntimeError \
              (
                    "hb.hb_buffer_deserialize_glyphs failed at %d of %d bytes processed"
                %
                    (end_ptr.value - tempbuf.buffer_info()[0], len(b))
              )
    #end deserialize_glyphs

    # segment properties methods are in SegmentPropertiesExtra (above)

    # set_message_func defined below

#end Buffer
def def_buffer_extra() :

    def def_wrap_message_func(self, message_func, user_data) :

        @HB.buffer_message_func_t
        def wrap_message_func(c_buffer, c_font, message, c_user_data) :
            return \
                message_func \
                  (
                    self,
                    Font(hb.hb_font_reference(c_font), None),
                    message.decode(),
                    user_data
                  )
        #end wrap_message_func

    #begin def_wrap_message_func
        return \
            wrap_message_func
    #end def_wrap_message_func

#begin def_buffer_extra
    def_callback_wrapper \
      (
        celf = Buffer,
        method_name = "set_message_func",
        docstring = None,
        callback_field_name = "_wrap_message_func",
        destroy_field_name = "_wrap_message_destroy",
        def_wrap_callback_func = def_wrap_message_func,
        hb_proc = "hb_buffer_set_message_func",
      )
#end def_buffer_extra
def_buffer_extra()
del def_buffer_extra

class SerializeFormat :
    "a high-level encapsulation of hb_buffer_serialize_format_t values." \
    " Do not instantiate directly; use from_string and get_list methods."

    __slots__ = \
        ( # to forestall typos
            "_tag",
            "__weakref__",
        )

    _instances = WeakValueDictionary()

    def __new__(celf, _tag) :
        self = celf._instances.get(_tag)
        if self == None :
            self = super().__new__(celf)
            self._tag = _tag
            celf._instances[_tag] = self
        #end if
        return \
            self
    #end __new__

    # no __del__ -- these objects are never freed

    @classmethod
    def make_serialize(celf, t) :
        if isinstance(t, SerializeFormat) :
            result = t
        elif isinstance(t, int) :
            result = celf(t)
        elif isinstance(t, bytes) :
            result = celf(HB.TAG(t))
        else :
            raise TypeError("bad SerializeFormat")
        #end if
        return \
            result
    #end make_serialize

    @classmethod
    def from_string(celf, s) :
        sb = s.encode()
        return \
            celf(hb.hb_buffer_serialize_format_from_string(sb, len(sb)))
    #end from_string

    def to_string(self) :
        return \
            hb.hb_buffer_serialize_format_to_string(self._tag).decode()
    #end to_string

    @classmethod
    def get_list(celf) :
        result = []
        formats = hb.hb_buffer_serialize_list_formats()
        i = 0
        while bool(formats[i]) :
            result.append(celf.from_string(formats[i].decode()))
            i += 1
        #end while
        return \
            tuple(result)
    #end get_list

    def __repr__(self) :
        return \
            "%s(%s)" % (type(self).__name__, HB.UNTAG(self._tag, True))
    #end __repr__

#end SerializeFormat

# from hb-face.h:

class Face :
    "wrapper around hb_face_t objects, analogous to Cairo’s font_face_t objects." \
    " Do not instantiate directly; use create or get_empty methods."

    __slots__ = \
        ( # to forestall typos
            "autoscale",
            "_hbobj",
            "_user_data",
            "__weakref__",
            "_arr", # from parent Blob, if any
            # need to keep references to ctypes-wrapped functions
            # so they don't disappear prematurely:
            "_wrap_reference_table",
            "_wrap_destroy",
        )

    _instances = WeakValueDictionary()
    _ud_refs = WeakValueDictionary()

    def __new__(celf, _hbobj, autoscale) :
        self = celf._instances.get(_hbobj)
        if self == None :
            self = super().__new__(celf)
            assert autoscale != None, "missing autoscale flag"
            self.autoscale = autoscale
            self._hbobj = _hbobj
            self._arr = None # to begin with
            self._wrap_reference_table = None
            self._wrap_destroy = None
            user_data = celf._ud_refs.get(_hbobj)
            if user_data == None :
                user_data = UserDataDict()
                celf._ud_refs[_hbobj] = user_data
            #end if
            self._user_data = user_data
            celf._instances[_hbobj] = self
        else :
            assert autoscale == None or autoscale == self.autoscale, "inconsistent autoscale settings"
            hb.hb_face_destroy(self._hbobj)
              # lose extra reference created by caller
        #end if
        return \
            self
    #end __new__

    def __del__(self) :
        if hb != None and self._hbobj != None :
            hb.hb_face_destroy(self._hbobj)
            self._hbobj = None
        #end if
    #end __del__

    @staticmethod
    def create(blob, index, autoscale) :
        "creates a Face that gets its data from the specified Blob."
        if not isinstance(blob, Blob) :
            raise TypeError("blob must be a Blob")
        #end if
        result = Face(hb.hb_face_create(blob._hbobj, index), autoscale)
        result._arr = blob._arr # in case Blob goes away
        return \
            result
    #end create

    @staticmethod
    def create_for_tables(reference_table, user_data, destroy, autoscale) :
        "creates a Face which calls the specified reference_table action to access" \
        " the font tables. This should be declared as\n" \
        "\n" \
        "    def reference_table(face, tag, user_data)\n" \
        "\n" \
        "where face is the Face instance, tag is the integer tag identifying the" \
        " table, and must return either None or a Blob, which should remain valid" \
        " for as long as the Face is referenced. The interpretation of user_data" \
        " is up to you. The destroy action may be None, but if not, it should be" \
        " declared as\n" \
        "\n" \
        "     def destroy(user_data)\n" \
        "\n" \
        "and will be called when the Face is destroyed."

        @HB.reference_table_func_t
        def wrap_reference_table(c_face, c_tag, c_user_data) :
            result = reference_table(Face(hb.hb_face_reference(c_face), autoscale), c_tag, user_data)
            if isinstance(result, Blob) :
                c_result = hb.hb_blob_reference(result._hbobj)
            elif result == None :
                c_result = None
            else :
                raise TypeError("reference_table must return a Blob or None")
            #end if
            return \
                c_result
        #end wrap_reference_table

        if destroy != None :
            @HB.destroy_func_t
            def wrap_destroy(c_user_data) :
                destroy(user_data)
            #end wrap_destroy
        else :
            wrap_destroy = None
        #end if

        result = Face(hb.hb_face_create_for_tables(wrap_reference_table, None, wrap_destroy), autoscale)
        # note I cannot save any references to Blob._arr -- user will have to
        # ensure these do not vanish prematurely
        result._wrap_reference_table = wrap_reference_table
        result._wrap_destroy = wrap_destroy
        return \
            result
    #end create_for_tables

    @staticmethod
    def get_empty() :
        "returns the (unique) empty Face. This has no glyphs and is immutable."
        return \
            Face(hb.hb_face_reference(hb.hb_face_get_empty()), False)
    #end get_empty

    if freetype != None :

        # from hb-ft.h:

        @staticmethod
        def ft_create(ft_face) :
            "creates a Face from a freetype.Face."
            if not isinstance(ft_face, freetype.Face) :
                raise TypeError("ft_face must be a freetype.Face")
            #end if
            return \
                Face(hb.hb_ft_face_create_referenced(ft_face._ftobj), True)
        #end ft_create

    #end if

    # immutable defined below

    # get/set glyph_count, index, upem defined below

    def reference_table(self, tag) :
        "returns a Blob for the specified table, or the empty Blob if it cannot be found."
        return \
            Blob(hb.hb_face_reference_table(self._hbobj, tag))
    #end reference_table

    def reference_blob(self) :
        "returns the Blob with which the Face was created, or the empty Blob if it" \
        " doesn’t have one."
        return \
            Blob(hb.hb_face_reference_blob(self._hbobj))
    #end reference_blob

    @property
    def user_data(self) :
        "a dict, initially empty, which may be used by caller for any purpose."
        return \
            self._user_data
    #end user_data

    # HarfBuzz user_data calls not exposed to caller, probably not useful

    # from hb-ot-layout.h:

    class OTLayout :
        "namespace wrapper for ot_layout functions on Face objects." \
        " Do not instantiate directly; get from Face.ot_layout property."

        __slots__ = \
            ( # to forestall typos
                "_hbobj",
            )

        def __init__(self, _hbobj) :
            # note I’m not calling hb_face_reference,
            # assuming parent Face doesn’t go away!
            self._hbobj = _hbobj
        #end __init__

        @property
        def has_glyph_classes(self) :
            return \
                hb.hb_ot_layout_has_glyph_classes(self._hbobj) != 0
        #end has_glyph_classes

        def get_glyph_class(self, glyph) :
            return \
                hb.hb_ot_layout_get_glyph_class(self._hbobj, glyph)
        #end get_glyph_class

        def get_glyphs_in_class(self, klass) :
            result = Set.to_hb()
            hb.hb_ot_layout_get_glyphs_in_class(self._hbobj, klass, result._hbobj)
            return \
                result.from_hb()
        #end get_glyphs_in_class

        def get_attach_points(self, glyph) :
            point_count = None
            point_array = None
            while True :
                # just get the length on the first pass
                nr_attach_points = hb.hb_ot_layout_get_attach_points \
                    (self._hbobj, glyph, 0, point_count, point_array)
                if point_array != None :
                    break
                # allocate space, now I know how much I need
                point_count = ct.c_uint(nr_attach_points)
                point_array = (nr_attach_points * ct.c_uint)()
            #end while
            return \
                tuple(point_array[i] for i in range(nr_attach_points))
        #end get_attach_points

        # GSUB/GPOS feature query and enumeration interface

        def table_get_script_tags(self, table_tag) :
            script_count = None
            script_tags = None
            while True :
                # just get the length on the first pass
                nr_script_tags = hb.hb_ot_layout_table_get_script_tags \
                    (self._hbobj, table_tag, 0, script_count, script_tags)
                if script_tags != None :
                    break
                # allocate space, now I know how much I need
                script_count = ct.c_uint(nr_script_tags)
                script_tags = (nr_script_tags * ct.c_uint)()
            #end while
            return \
                tuple(script_tags[i] for i in range(nr_script_tags))
        #end table_get_script_tags

        def find_script(self, table_tag, script_tag) :
            script_index = ct.c_uint()
            if hb.hb_ot_layout_table_find_script(self._hbobj, table_tag, script_tag, script_index) != 0 :
                result = script_index.value
            else :
                result = None
            #end if
            return \
                result
        #end find_script

        def choose_script(self, table_tag, script_tags) :
            "Like find_script, but takes sequence of scripts to test."
            c_script_tags = seq_to_ct(script_tags, HB.tag_t, zeroterm = True)
            script_index = ct.c_uint()
            chosen_script = HB.tag_t()
            success = hb.hb_ot_layout_table_choose_script(self._hbobj, table_tag, c_script_tags, script_index, chosen_script) != 0
            return \
                (success, script_index.value, chosen_script.value)
        #end choose_script

        def table_get_feature_tags(self, table_tag) :
            feature_count = None
            feature_tags = None
            while True :
                # just get the length on the first pass
                nr_feature_tags = hb.hb_ot_layout_table_get_feature_tags \
                    (self._hbobj, table_tag, 0, feature_count, feature_tags)
                if feature_tags != None :
                    break
                # allocate space, now I know how much I need
                feature_count = ct.c_uint(nr_feature_tags)
                feature_tags = (nr_feature_tags * ct.c_uint)()
            #end while
            return \
                tuple(feature_tags[i] for i in range(nr_feature_tags))
        #end table_get_feature_tags

        def script_get_language_tags(self, table_tag, script_index) :
            language_count = None
            language_tags = None
            while True :
                # just get the length on the first pass
                nr_language_tags = hb.hb_ot_layout_script_get_language_tags \
                    (self._hbobj, table_tag, script_index, 0, language_count, language_tags)
                if language_tags != None :
                    break
                # allocate space, now I know how much I need
                language_count = ct.c_uint(nr_language_tags)
                language_tags = (nr_language_tags * ct.c_uint)()
            #end while
            return \
                tuple(language_tags[i] for i in range(nr_language_tags))
        #end script_get_language_tags

        def script_find_language(self, table_tag, script_index, language_tag) :
            language_index = ct.c_uint()
            success = hb.hb_ot_layout_script_find_language(self._hbobj, table_tag, script_index, language_tag, language_index) != 0
            return \
                (success, language_index.value)
        #end script_find_language

        # don’t bother implementing language_get_required_feature_index,
        # use language_get_required_feature instead

        def language_get_required_feature(self, table_tag, script_index, language_index) :
            feature_index = ct.c_uint()
            feature_tag = HB.tag_t()
            success = hb.hb_ot_layout_language_get_required_feature(self._hbobj, table_tag, script_index, language_index, feature_index, feature_tag) != 0
            return \
                (success, feature_index.value, feature_tag.value)
        #end language_get_required_feature

        def language_get_feature_indexes(self, table_tag, script_index, language_index) :
            feature_count = None
            feature_indexes = None
            while True :
                # just get the length on the first pass
                nr_feature_indexes = hb.hb_ot_layout_language_get_feature_indexes \
                    (self._hbobj, table_tag, script_index, language_index, 0, feature_count, feature_indexes)
                if feature_indexes != None :
                    break
                # allocate space, now I know how much I need
                feature_count = ct.c_uint(nr_feature_indexes)
                feature_indexes = (nr_feature_indexes * ct.c_uint)()
            #end while
            return \
                tuple(feature_indexes[i] for i in range(nr_feature_indexes))
        #end language_get_feature_indexes

        def language_get_feature_tags(self, table_tag, script_index, language_index) :
            feature_count = None
            feature_tags = None
            while True :
                # just get the length on the first pass
                nr_feature_tags = hb.hb_ot_layout_language_get_feature_tags \
                    (self._hbobj, table_tag, script_index, language_index, 0, feature_count, feature_tags)
                if feature_tags != None :
                    break
                # allocate space, now I know how much I need
                feature_count = ct.c_uint(nr_feature_tags)
                feature_tags = (nr_feature_tags * ct.c_uint)()
            #end while
            return \
                tuple(feature_tags[i] for i in range(nr_feature_tags))
        #end language_get_feature_tags

        def language_find_feature(self, table_tag, script_index, language_index, feature_tag) :
            feature_index = ct.c_uint()
            success = hb.hb_ot_layout_language_find_feature(self._hbobj, table_tag, script_index, language_index, feature_tag, feature_index) != 0
            return \
                (success, feature_index.value)
        #end language_find_feature

        def feature_get_lookups(self, table_tag, feature_index) :
            lookup_count = None
            lookup_indexes = None
            while True :
                # just get the length on the first pass
                nr_lookups = hb.hb_ot_layout_feature_get_lookups \
                    (self._hbobj, table_tag, feature_index, 0, lookup_count, lookup_indexes)
                if lookup_indexes != None :
                    break
                # allocate space, now I know how much I need
                lookup_count = ct.c_uint(nr_lookups)
                lookup_indexes = (nr_lookups * ct.c_uint)()
            #end while
            return \
                tuple(lookup_indexes[i] for i in range(nr_lookups))
        #end feature_get_lookups

        def table_get_lookup_count(self, table_tag) :
            return \
                hb.hb_ot_layout_table_get_lookup_count(self._hbobj, table_tag)
        #end table_get_lookup_count

        def collect_lookups(self, table_tag, scripts, languages, features) :
            if scripts != None :
                c_scripts = seq_to_ct(scripts, HB.tag_t, zeroterm = True)
            else :
                c_scripts = None
            #end if
            if languages != None :
                c_languages = seq_to_ct(languages, HB.tag_t, zeroterm = True)
            else :
                c_languages = None
            #end if
            if features != None :
                c_features = seq_to_ct(features, HB.tag_t, zeroterm = True)
            else :
                c_features = None
            #end if
            lookup_indexes = Set.to_hb()
            hb.hb_ot_layout_collect_lookups(self._hbobj, table_tag, c_scripts, c_languages, cC_features, lookup_indexes._hbobj)
            return \
                lookup_indexes.from_hb()
        #end collect_lookups

        def lookup_collect_glyphs(self, table_tag, lookup_index, want_glyphs_before, want_glyphs_input, want_glyphs_after, want_glyphs_output) :
            glyphs_before = (Set.NULL, Set.to_hb)[want_glyphs_before]()
            glyphs_input = (Set.NULL, Set.to_hb)[want_glyphs_input]()
            glyphs_after = (Set.NULL, Set.to_hb)[want_glyphs_after]()
            glyphs_output = (Set.NULL, Set.to_hb)[want_glyphs_output]()
            hb.hb_ot_layout_lookup_collect_glyphs(self._hbobj, table_tag, lookup_index, glyphs_before._hbobj, glyphs_input._hbobj, glyphs_after._hbobj, glyphs_output._hbobj)
            return \
                (glyphs_before.from_hb(), glyphs_input.from_hb(), glyphs_after.from_hb(), glyphs_output.from_hb())
        #end lookup_collect_glyphs

        # GSUB

        @property
        def has_substitution(self) :
            return \
                hb.hb_ot_layout_has_substitution(self._hbobj) != 0
        #end has_substitution

        def lookup_would_substitute(self, lookup_index, glyphs, zero_context) :
            c_glyphs = seq_to_ct(glyphs, HB.codepoint_t)
            return \
                (
                    hb.hb_ot_layout_lookup_would_substitute
                        (self._hbobj, lookup_index, c_glyphs, len(glyphs, zero_context))
                !=
                    0
                )
        #end lookup_would_substitute

        def lookup_substitute_closure(self, lookup_index) :
            glyphs = Set.to_hb()
            hb.hb_ot_layout_lookup_substitute_closure(self._hbobj, lookup_index. glyphs._hbobj)
            return \
                glyphs.from_hb()
        #end lookup_substitute_closure

        # GPOS

        @property
        def has_positioning(self) :
            return \
                hb.hb_ot_layout_has_positioning(self._hbobj) != 0
        #end has_positioning

        @property
        def size_params(self) :
            # Optical 'size' feature info. Returns 5-tuple of values if found,
            # else None.
            # http://www.microsoft.com/typography/otspec/features_pt.htm#size
            design_size = ct.c_uint()
            subfamily_id = ct.c_uint()
            subfamily_name_id = ct.c_uint()
            range_start = ct.c_uint()
            range_end = ct.c_uint()
            if (
                    hb.hb_ot_layout_get_size_params \
                      (
                        self._hbobj,
                        ct.byref(design_size),
                        ct.byref(subfamily_id),
                        ct.byref(subfamily_name_id),
                        ct.byref(range_start),
                        ct.byref(range_end),
                      )
                !=
                    0
            ) :
                result = \
                    (
                        design_size.value,
                        subfamily_id.value,
                        subfamily_name_id.value,
                        range_start.value,
                        range_end.value,
                    )
            else :
                result = None
            #end if
            return \
                result
        #end size_params

    #end OTLayout

    @property
    def ot_layout(self) :
        "returns an object which can be used to invoke ot_layout_xxx functions" \
        " relevant to Face objects."
        # Should this be a property or an attribute set up directly in __init__?
        # Latter case would cause reference circularity, unless I use weak refs,
        # which further complicates things. Seems simpler to just make this
        # a property.
        return \
            self.OTLayout(self._hbobj)
    #end ot_layout

#end Face
def_immutable \
  (
    celf = Face,
    hb_query = "hb_face_is_immutable",
    hb_set = "hb_face_make_immutable",
  )
def def_face_props(celf) :
    # get/set index, upem and glyph_count all have the same form:
    # all these properties are unsigned integers.

    def def_face_prop(propname) :
        # need separate inner function so each method gets
        # correct values for hb_getter and hb_setter
        hb_getter = "hb_face_get_%s" % propname
        hb_setter = "hb_face_set_%s" % propname

        def getter(self) :
            return \
                getattr(hb, hb_getter)(self._hbobj)
        #end getter

        def setter(self, newval) :
            getattr(hb, hb_setter)(self._hbobj, newval)
        #end setter

        getter.__name__ = propname
        getter.__doc__ = "the %s property." % propname
        setter.__name__ = propname
        setter.__doc__ = "sets the %s property." % propname
        propmethod = property(getter)
        propmethod = propmethod.setter(setter)
        setattr(celf, propname, propmethod)
    #end def_face_prop

#begin def_face_props
    for propname in ("index", "upem", "glyph_count") :
        def_face_prop(propname)
    #end for
#end def_face_props
def_face_props(Face)
del def_face_props

# from hb-font.h:

class Font :
    "wrapper around hb_font_t objects, analogous to Cairo’s scaled_font_t objects." \
    " Do not instantiate directly; use create methods."

    __slots__ = \
        ( # to forestall typos
            "autoscale",
            "_hbobj",
            "_user_data",
            "__weakref__",
            "_font_funcs", # last set FontFuncs, just to keep it from going away prematurely
            "_font_data", # for the FontFuncs
            "_face", # harfbuzz.Face or freetype2.Face, just to keep it from going away prematurely
            # need to keep references to ctypes-wrapped functions
            # so they don't disappear prematurely:
            "_wrap_destroy",
        )

    _instances = WeakValueDictionary()
    _ud_refs = WeakValueDictionary()

    def __new__(celf, _hbobj, autoscale) :
        self = celf._instances.get(_hbobj)
        if self == None :
            self = super().__new__(celf)
            assert autoscale != None, "missing autoscale flag"
            self.autoscale = autoscale
            self._hbobj = _hbobj
            self._font_funcs = None
            self._font_data = None
            self._face = None # to begin with
            user_data = celf._ud_refs.get(_hbobj)
            if user_data == None :
                user_data = UserDataDict()
                celf._ud_refs[_hbobj] = user_data
            #end if
            self._user_data = user_data
            celf._instances[_hbobj] = self
        else :
            assert autoscale == None or autoscale == self.autoscale, "inconsistent autoscale settings"
            hb.hb_font_destroy(self._hbobj)
              # lose extra reference created by caller
        #end if
        return \
            self
    #end __new__

    def __del__(self) :
        if hb != None and self._hbobj != None :
            hb.hb_font_destroy(self._hbobj)
            self._hbobj = None
        #end if
    #end __del__

    @staticmethod
    def create(face) :
        "creates a Font from the specified Face."
        if not isinstance(face, Face) :
            raise TypeError("face must be a Face")
        #end if
        result = Font(hb.hb_font_create(face._hbobj), face.autoscale)
        result._face = face
        return \
            result
    #end create

    def create_sub_font(self) :
        result = Font(hb.hb_font_create_sub_font(self._hbobj), self.autoscale)
        result._face = self._face
        return \
            result
    #end create_sub_font

    # immutable defined below

    def get_h_extents(self) :
        c_extents = HB.font_extents_t()
        if hb.hb_font_get_h_extents(self._hbobj, ct.byref(c_extents)) != 0 :
            result = FontExtents.from_hb(c_extents, self.autoscale)
        else :
            result = None
        #end if
        return \
            result
    #end get_h_extents

    def get_v_extents(self) :
        c_extents = HB.font_extents_t()
        if hb.hb_font_get_v_extents(self._hbobj, ct.byref(c_extents)) != 0 :
            result = FontExtents.from_hb(c_extents, self.autoscale)
        else :
            result = None
        #end if
        return \
            result
    #end get_v_extents

    def get_nominal_glyph(self, unicode) :
        glyph = HB.codepoint_t()
        if hb.hb_font_get_nominal_glyph(self._hbobj, unicode, ct.byref(glyph)) != 0 :
            result = glyph.value
        else :
            result = None
        #end if
        return \
            result
    #end get_nominal_glyph

    def get_variation_glyph(self, unicode, variation_selector) :
        glyph = HB.codepoint_t()
        if hb.hb_font_get_variation_glyph(self._hbobj, unicode, variation_selector, ct.byref(glyph)) != 0 :
            result = glyph.value
        else :
            result = None
        #end if
        return \
            result
    #end get_variation_glyph

    def get_glyph_h_advance(self, glyph) :
        result = hb.hb_font_get_glyph_h_advance(self._hbobj, glyph)
        if self.autoscale :
            result = HB.from_position_t(result)
        #end if
        return \
            result
    #end get_glyph_h_advance

    def get_glyph_v_advance(self, glyph) :
        result = hb.hb_font_get_glyph_v_advance(self._hbobj, glyph)
        if self.autoscale :
            result = HB.from_position_t(result)
        #end if
        return \
            result
    #end get_glyph_v_advance

    def get_glyph_h_origin(self, glyph) :
        x = HB.position_t()
        y = HB.position_t()
        if hb.hb_font_get_glyph_h_origin(self._hbobj, glyph, ct.byref(x), ct.byref(y)) != 0 :
            if self.autoscale :
                result = (HB.from_position_t(x.value), HB.from_position_t(y.value))
            else :
                result = (x.value, y.value)
            #end if
        else :
            result = None
        #end if
        return \
            result
    #end get_glyph_h_origin

    def get_glyph_v_origin(self, glyph) :
        x = HB.position_t()
        y = HB.position_t()
        if hb.hb_font_get_glyph_v_origin(self._hbobj, glyph, ct.byref(x), ct.byref(y)) != 0 :
            if self.autoscale :
                result = (HB.from_position_t(x.value), HB.from_position_t(y.value))
            else :
                result = (x.value, y.value)
            #end if
        else :
            result = None
        #end if
        return \
            result
    #end get_glyph_v_origin

    def get_glyph_h_kerning(self, left_glyph, right_glyph) :
        result = hb.hb_font_get_glyph_h_kerning(self._hbobj, left_glyph, right_glyph)
        if self.autoscale :
            result = HB.from_position_t(result)
        #end if
        return \
            result
    #end get_glyph_h_kerning

    def get_glyph_v_kerning(self, top_glyph, bottom_glyph) :
        result = hb.hb_font_get_glyph_v_kerning(self._hbobj, top_glyph, bottom_glyph)
        if self.autoscale :
            result = HB.from_position_t(result)
        #end if
        return \
            result
    #end get_glyph_v_kerning

    def get_glyph_extents(self, glyph) :
        c_extents = HB.glyph_extents_t()
        if hb.hb_font_get_glyph_extents(self._hbobj, glyph, ct.byref(c_extents)) != 0 :
            result = GlyphExtents.from_hb(c_extents, self.autoscale)
        else :
            result = None
        #end if
        return \
            result
    #end get_glyph_extents

    def get_glyph_contour_point(self, glyph, point_index) :
        x = HB.position_t()
        y = HB.position_t()
        if hb.hb_font_get_glyph_contour_point(self._hbobj, glyph, point_index, ct.byref(x), ct.byref(y)) != 0 :
            if self.autoscale :
                result = (HB.from_position_t(x.value), HB.from_position_t(y.value))
            else :
                result = (x.value, y.value)
            #end if
        else :
            result = None
        #end if
        return \
            result
    #end get_glyph_contour_point

    def get_glyph_name(self, glyph) :
        bufsize = 128 # big enough?
        c_name = (ct.c_char * bufsize)()
        if hb.hb_font_get_glyph_name(self._hbobj, glyph, c_name, bufsize) != 0 :
            result = c_name.value.decode() # nul-terminated
        else :
            result = None
        #end if
        return \
            result
    #end wrap_get_glyph_name_func

    def get_glyph_from_name(self, name) :
        c_name = (ct.c_char * len(name))()
        c_name.value = name.encode()
        c_glyph = HB.codepoint_t()
        if hb.hb_font_get_glyph_from_name(self._hbobj, c_name, len(name), ct.byref(c_glyph)) != 0 :
            result = c_glyph.value
        else :
            result = None
        #end if
        return \
            result
    #end get_glyph_from_name

    def get_glyph(self, unicode, variation_selector) :
        glyph = HB.codepoint_t()
        if hb.hb_font_get_glyph(self._hbobj, unicode, variation_selector, ct.byref(glyph)) != 0 :
            result = glyph.value
        else :
            result = None
        #end if
        return \
            result
    #end get_glyph

    def get_extents_for_direction(self, glyph, direction) :
        extents = HB.font_extents_t()
        hb.hb_font_get_extents_for_direction(self._hbobj, glyph, direction, ct.byref(extents))
        return \
            FontExtents.from_hb(extents, self.autoscale)
    #end get_extents_for_direction

    def get_glyph_advance_for_direction(self, glyph, direction) :
        x = HB.position_t()
        y = HB.position_t()
        hb.hb_font_get_glyph_advance_for_direction(self._hbobj, glyph, direction, ct.byref(x), ct.byref(y))
        if self.autoscale :
            result = (HB.from_position_t(x.value), HB.from_position_t(y.value))
        else :
            result = (x.value, y.value)
        #end if
        return \
            result
    #end get_glyph_advance_for_direction

    def get_glyph_origin_for_direction(self, glyph, direction) :
        x = HB.position_t()
        y = HB.position_t()
        hb.hb_font_get_glyph_origin_for_direction(self._hbobj, glyph, direction, ct.byref(x), ct.byref(y))
        if self.autoscale :
            result = (HB.from_position_t(x.value), HB.from_position_t(y.value))
        else :
            result = (x.value, y.value)
        #end if
        return \
            result
    #end get_glyph_origin_for_direction

    def add_glyph_origin_for_direction(self, glyph, direction, origin) :
        origin = tuple(origin)
        if self.autoscale :
            x = HB.position_t(HB.to_position_t(origin[0]))
            y = HB.position_t(HB.to_position_t(origin[1]))
        else :
            x = HB.position_t(origin[0])
            y = HB.position_t(origin[1])
        #end if
        hb.hb_font_add_glyph_origin_for_direction(self._hbobj, glyph, direction, ct.byref(x), ct.byref(y))
        if self.autoscale :
            result = (HB.from_position_t(x.value), HB.from_position_t(y.value))
        else :
            result = (x.value, y.value)
        #end if
        return \
            result
    #end add_glyph_origin_for_direction

    def subtract_glyph_origin_for_direction(self, glyph, direction, origin) :
        origin = tuple(origin)
        if self.autoscale :
            x = HB.position_t(HB.to_position_t(origin[0]))
            y = HB.position_t(HB.to_position_t(origin[1]))
        else :
            x = HB.position_t(origin[0])
            y = HB.position_t(origin[1])
        #end if
        hb.hb_font_subtract_glyph_origin_for_direction(self._hbobj, glyph, direction, ct.byref(x), ct.byref(y))
        if self.autoscale :
            result = (HB.from_position_t(x.value), HB.from_position_t(y.value))
        else :
            result = (x.value, y.value)
        #end if
        return \
            result
    #end subtract_glyph_origin_for_direction

    def get_glyph_kerning_for_direction(self, first_glyph, second_glyph, direction) :
        x = HB.position_t()
        y = HB.position_t()
        hb.hb_font_get_glyph_kerning_for_direction(self._hbobj, first_glyph, second_glyph, direction, ct.byref(x), ct.byref(y))
        if self.autoscale :
            result = (HB.from_position_t(x.value), HB.from_position_t(y.value))
        else :
            result = (x.value, y.value)
        #end if
        return \
            result
    #end get_glyph_kerning_for_direction

    def get_glyph_extents_for_direction(self, glyph, direction) :
        extents = HB.glyph_extents_t()
        if hb.hb_font_get_glyph_extents_for_origin(self._hbobj, glyph, direction, ct.byref(extents)) != 0 :
            result = GlyphExtents.from_hb(extents, self.autoscale)
        else :
            result = None
        #end if
        return \
            result
    #end get_glyph_extents_for_direction

    def get_glyph_contour_point_for_direction(self, glyph, point_index, direction) :
        x = HB.position_t()
        y = HB.position_t()
        if hb.hb_font_get_glyph_contour_point_for_origin(self._hbobj, glyph, point_index, direction, ct.byref(x), ct.byref(y)) != 0 :
            if self.autoscale :
                result = (HB.from_position_t(x.value), HB.from_position_t(y.value))
            else :
                result = (x.value, y.value)
            #end if
        else :
            result = None
        #end if
        return \
            result
    #end get_glyph_contour_point_for_direction

    def glyph_to_string(self, glyph) :
        "generates gidDDD if glyph has no name."
        bufsize = 128 # big enough?
        c_name = (ct.c_char * bufsize)()
        hb.hb_font_glyph_to_string(self._hbobj, glyph, c_name, bufsize)
        return \
            c_name.value.decode() # nul-terminated
    #end glyph_to_string

    def glyph_from_string(self, name) :
        "parses gidDDD and uniUUUU strings automatically."
        c_name = (ct.c_char * len(name))()
        c_name.value = name.encode()
        c_glyph = HB.codepoint_t()
        if hb.hb_font_glyph_from_string(self._hbobj, c_name, len(name), ct.byref(c_glyph)) != 0 :
            result = c_glyph.value
        else :
            result = None
        #end if
        return \
            result
    #end glyph_from_string

    def set_funcs(self, funcs, font_data, destroy) :
        if funcs != None and not isinstance(funcs, FontFuncs) :
            raise TypeError("funcs must be None or a FontFuncs")
        #end if
        if destroy != None :
            @HB.destroy_func_t
            def wrap_destroy(c_font_data) :
                destroy(font_data)
            #end wrap_destroy
        else :
            wrap_destroy = None
        #end if
        self._font_funcs = funcs
        self._font_data = font_data
        self._wrap_destroy = wrap_destroy
        hb.hb_font_set_funcs \
          (self._hbobj, (lambda : None, lambda : funcs._hbobj)[funcs != None](), self._hbobj, wrap_destroy)
    #end set_funcs

    def set_funcs_data(self, font_data, destroy) :
        if destroy != None :
            @HB.destroy_func_t
            def wrap_destroy(c_font_data) :
                destroy(font_data)
            #end wrap_destroy
        else :
            wrap_destroy = None
        #end if
        self._font_data = font_data
        self._wrap_destroy = wrap_destroy
        hb.hb_font_set_funcs_data(self._hbobj, self._hbobj, wrap_destroy)
    #end set_funcs_data

    @property
    def parent(self) :
        return \
            Font(hb.hb_font_reference(hb.hb_font_get_parent(self._hbobj)), None)
    #end parent

    @parent.setter
    def parent(self, new_parent) :
        if new_parent != None and not isinstance(new_parent, Font) :
            raise TypeError("new_parent must be None or a Font")
        #end if
        hb.hb_font_set_parent \
            (self._hbobj, (lambda : None, lambda : new_parent._hbobj)[new_parent != None]())
    #end parent

    @property
    def face(self) :
        return \
            Face(hb.hb_face_reference(hb.hb_font_get_face(self._hbobj)), self.autoscale)
              # note this will not necessarily be the same Face that was passed to Font.create
    #end face

    # get/set ppem, scale defined below

    @property
    def user_data(self) :
        "a dict, initially empty, which may be used by caller for any purpose."
        return \
            self._user_data
    #end user_data

    # HarfBuzz user_data calls not exposed to caller, probably not useful

    if freetype != None :

        # from hb-ft.h:

        @staticmethod
        def ft_create(ft_face) :
            "creates a Font from a freetype.Face."
            if not isinstance(ft_face, freetype.Face) :
                raise TypeError("ft_face must be a freetype.Face")
            #end if
            result = Font(hb.hb_ft_font_create_referenced(ft_face._ftobj), True)
            result._face = ft_face
            return \
                result
        #end ft_create

        @property
        def ft_load_flags(self) :
            return \
                hb.hb_ft_font_get_load_flags(self._hbobj)
        #end ft_load_flags

        @ft_load_flags.setter
        def ft_load_flags(self, load_flags) :
            hb.hb_ft_font_set_load_flags(self._hbobj, load_flags)
        #end ft_load_flags

        @property
        def ft_face(self) :
            return \
                freetype.Face(None, hb.hb_ft_font_get_face(self._hbobj), None)
        #end ft_face

        def ft_set_funcs(self) :
            hb.hb_ft_font_set_funcs(self._hbobj)
        #end ft_set_funcs

    #end if

    # from hb-ot-font.h:

    def ot_set_funcs(self) :
        hb.hb_ot_font_set_funcs(self._hbobj)
    #end ot_set_funcs

    # from hb-ot-layout.h:

    class OTLayout :
        "namespace wrapper for ot_layout functions on Font objects." \
        " Do not instantiate directly; get from Font.ot_layout property."

        __slots__ = \
            ( # to forestall typos
                "_hbobj",
            )

        def __init__(self, _hbobj) :
            # note I’m not calling hb_font_reference,
            # assuming parent Font doesn’t go away!
            self._hbobj = _hbobj
        #end __init__

        def get_ligature_carets(self, direction, glyph) :
            caret_count = None
            caret_array = None
            while True :
                # just get the length on the first pass
                nr_carets = hb.hb_ot_layout_get_ligature_carets \
                    (self._hbobj, direction, glyph, 0, caret_count, caret_array)
                if caret_array != None :
                    break
                # allocate space, now I know how much I need
                caret_count = ct.c_uint(nr_carets)
                caret_array = (nr_carets * HB.position_t)()
            #end while
            return \
                tuple(caret_array[i] for i in range(nr_carets))
        #end get_ligature_carets

    #end OTLayout

    @property
    def ot_layout(self) :
        "returns an object which can be used to invoke ot_layout_xxx functions" \
        " relevant to Font objects."
        # Should this be a property or an attribute set up directly in __init__?
        # Latter case would cause reference circularity, unless I use weak refs,
        # which further complicates things. Seems simpler to just make this
        # a property.
        return \
            self.OTLayout(self._hbobj)
    #end ot_layout

#end Font
def_immutable \
  (
    celf = Font,
    hb_query = "hb_font_is_immutable",
    hb_set = "hb_font_make_immutable",
  )
def def_font_extra(celf) :

    def def_prop(propname, proptype, docextra, conv_to_hb, conv_from_hb) :
        # need separate inner function so each method gets
        # correct values for hb_getter and hb_setter
        hb_getter = "hb_font_get_%s" % propname
        hb_setter = "hb_font_set_%s" % propname

        assert (conv_to_hb == None) == (conv_from_hb == None)

        if conv_to_hb != None :
            assert conv_to_hb is HB.to_position_t and conv_from_hb is HB.from_position_t
              # the only case I need for now

            def getter(self) :
                x = proptype()
                y = proptype()
                getattr(hb, hb_getter)(self._hbobj, ct.byref(x), ct.byref(y))
                if self.autoscale :
                    result = (conv_from_hb(x.value), conv_from_hb(y.value))
                else :
                    result = (x.value, y.value)
                #end if
                return \
                    result
            #end getter

            def setter(self, new_xy) :
                if self.autoscale :
                    new_xy = (conv_to_hb(new_xy[0]), conv_to_hb(new_xy[1]))
                else :
                    new_xy = (round(new_xy[0]), round(new_xy[1]))
                #end if
                getattr(hb, hb_setter)(self._hbobj, new_xy[0], new_xy[1])
            #end setter

        else :

            def getter(self) :
                x = proptype()
                y = proptype()
                getattr(hb, hb_getter)(self._hbobj, ct.byref(x), ct.byref(y))
                return \
                    (x.value, y.value)
            #end getter

            def setter(self, new_xy) :
                getattr(hb, hb_setter)(self._hbobj, new_xy[0], new_xy[1])
            #end setter

        #end if

        getter.__name__ = propname
        getter.__doc__ = \
            (
                "the %(name)s property as an (x, y) tuple.%(extra)s"
            %
                {
                    "name" : propname,
                    "extra" : (lambda : "", lambda : " " + docextra)[docextra != None](),
                }
            )
        setter.__name__ = propname
        setter.__doc__ = "sets the %s property to a new (x, y) tuple." % propname
        propmethod = property(getter)
        propmethod = propmethod.setter(setter)
        setattr(celf, propname, propmethod)
    #end def_prop

#begin def_font_extra
    for propname, proptype, docextra, conv_to_hb, conv_from_hb in \
        (
            ("ppem", ct.c_uint, "A zero value means no hinting in that direction.", None, None),
            ("scale", ct.c_int, None, HB.to_position_t, HB.from_position_t),
        ) \
    :
        def_prop(propname, proptype, docextra, conv_to_hb, conv_from_hb)
    #end for
#end def_font_extra
def_font_extra(Font)
del def_font_extra

class FontFuncs :
    "wrapper around hb_font_funcs_t objects. Do not instantiate directly; use" \
    " create and get_empty methods. The autoscale attribute indicates whether" \
    " your callbacks return floating-point metrics that need to be multiplied by" \
    " 64 to convert to HarfBuzz position_t values."
    # Note that the font_data actually comes from the _font_data field
    # of the Font that these funcs are set for. This way, the caller
    # can pass any Python object for font_data.

    __slots__ = \
        ( # to forestall typos
            "autoscale",
            "_hbobj",
            "_user_data",
            "__weakref__",
            # need to keep references to ctypes-wrapped functions
            # so they don't disappear prematurely:
            "_wrap_font_h_extents_func",
            "_wrap_font_h_extents_destroy",
            "_wrap_font_v_extents_func",
            "_wrap_font_v_extents_destroy",
            "_wrap_nominal_glyph_func",
            "_wrap_nominal_glyph_destroy",
            "_wrap_variation_glyph_func",
            "_wrap_variation_glyph_destroy",
            "_wrap_glyph_h_advance_func",
            "_wrap_glyph_h_advance_destroy",
            "_wrap_glyph_v_advance_func",
            "_wrap_glyph_v_advance_destroy",
            "_wrap_glyph_h_origin_func",
            "_wrap_glyph_h_origin_destroy",
            "_wrap_glyph_v_origin_func",
            "_wrap_glyph_v_origin_destroy",
            "_wrap_glyph_h_kerning_func",
            "_wrap_glyph_h_kerning_destroy",
            "_wrap_glyph_v_kerning_func",
            "_wrap_glyph_v_kerning_destroy",
            "_wrap_glyph_extents_func",
            "_wrap_glyph_extents_destroy",
            "_wrap_glyph_contour_point_func",
            "_wrap_glyph_contour_point_destroy",
            "_wrap_glyph_name_func",
            "_wrap_glyph_name_destroy",
            "_wrap_glyph_from_name_func",
            "_wrap_glyph_from_name_destroy",
        )

    _instances = WeakValueDictionary()
    _ud_refs = WeakValueDictionary()

    def __new__(celf, _hbobj, autoscale) :
        self = celf._instances.get(_hbobj)
        if self == None :
            self = super().__new__(celf)
            assert autoscale != None, "missing autoscale flag"
            self.autoscale = autoscale
            self._hbobj = _hbobj
            self._wrap_font_h_extents_func = None
            self._wrap_font_h_extents_destroy = None
            self._wrap_font_v_extents_func = None
            self._wrap_font_v_extents_destroy = None
            self._wrap_nominal_glyph_func = None
            self._wrap_nominal_glyph_destroy = None
            self._wrap_variation_glyph_func = None
            self._wrap_variation_glyph_destroy = None
            self._wrap_glyph_h_advance_func = None
            self._wrap_glyph_h_advance_destroy = None
            self._wrap_glyph_v_advance_func = None
            self._wrap_glyph_v_advance_destroy = None
            self._wrap_glyph_h_origin_func = None
            self._wrap_glyph_h_origin_destroy = None
            self._wrap_glyph_v_origin_func = None
            self._wrap_glyph_v_origin_destroy = None
            self._wrap_glyph_h_kerning_func = None
            self._wrap_glyph_h_kerning_destroy = None
            self._wrap_glyph_v_kerning_func = None
            self._wrap_glyph_v_kerning_destroy = None
            self._wrap_glyph_extents_func = None
            self._wrap_glyph_extents_destroy = None
            self._wrap_glyph_contour_point_func = None
            self._wrap_glyph_contour_point_destroy = None
            self._wrap_glyph_name_func = None
            self._wrap_glyph_name_destroy = None
            self._wrap_glyph_from_name_func = None
            self._wrap_glyph_from_name_destroy = None
            user_data = celf._ud_refs.get(_hbobj)
            if user_data == None :
                user_data = UserDataDict()
                celf._ud_refs[_hbobj] = user_data
            #end if
            self._user_data = user_data
            celf._instances[_hbobj] = self
        else :
            assert autoscale == None or self.autoscale == autoscale, "inconsistent autoscale settings"
            hb.hb_font_funcs_destroy(self._hbobj)
              # lose extra reference created by caller
        #end if
        return \
            self
    #end __new__

    def __del__(self) :
        if hb != None and self._hbobj != None :
            hb.hb_font_funcs_destroy(self._hbobj)
            self._hbobj = None
        #end if
    #end __del__

    @staticmethod
    def create(autoscale) :
        return \
            FontFuncs(hb.hb_font_funcs_create(), autoscale)
    #end create

    @staticmethod
    def get_empty() :
        "returns the (unique) “empty” FontFuncs object. Its functions behave as" \
        " follows:\n" \
        "\n" \
        "    font_h_extents and font_v_extents are all zeroes\n" \
        "    nominal_glyph is always zero\n" \
        "    variation_glyph is always zero\n" \
        "    glyph_h_advance is always the font’s x_scale\n" \
        "    glyph_v_advance is always the font’s y_scale\n" \
        "    glyph_h_origin and glyph_v_origin are always zero\n" \
        "    glyph_h_kerning and glyph_v_kerning are always zero\n" \
        "    glyph_extents are all zeroes\n" \
        "    glyph_contour_point always returns (0, 0)\n" \
        "    glyph_name is always the empty string\n" \
        "    glyph_from_name is always zero."
        return \
            FontFuncs(hb.hb_font_funcs_reference(hb.hb_font_funcs_get_empty()), False)
    #end get_empty

    @property
    def user_data(self) :
        "a dict, initially empty, which may be used by caller for any purpose."
        return \
            self._user_data
    #end user_data

    # HarfBuzz user_data calls not exposed to caller, probably not useful

    # immutable
    # set_font_h_extents_func
    # set_font_v_extents_func
    # set_nominal_glyph_func
    # set_variation_glyph_func
    # set_glyph_h_advance_func
    # set_glyph_v_advance_func
    # set_glyph_h_origin_func
    # set_glyph_v_origin_func
    # set_glyph_h_kerning_func
    # set_glyph_v_kerning_func
    # set_glyph_extents_func
    # set_glyph_contour_point_func
    # set_glyph_name_func
    # set_glyph_from_name_func
    # all defined below

#end FontFuncs
def_immutable \
  (
    celf = FontFuncs,
    hb_query = "hb_font_funcs_is_immutable",
    hb_set = "hb_font_funcs_make_immutable",
  )
def def_fontfuncs_extra() :

    def get_font(c_font) :
        return \
            Font(hb.hb_font_reference(c_font), None)
    #end get_font

    def def_wrap_get_font_extents_func(self, get_font_extents, user_data) :

        @HB.font_get_font_extents_func_t
        def wrap_get_font_extents(c_font, c_font_data, c_metrics, c_user_data) :
            font = get_font(c_font)
            metrics = get_font_extents(font, font._font_data, user_data)
            if metrics != None :
                metrics = metrics.to_hb(self.autoscale)
                c_metrics[0] = metrics
            #end if
            return \
                metrics != None
        #end wrap_get_font_extents

    #begin def_wrap_get_font_extents_func
        return \
            wrap_get_font_extents
    #end def_wrap_get_font_extents_func

    def def_wrap_get_nominal_glyph_func(self, get_nominal_glyph, user_data) :

        @HB.font_get_nominal_glyph_func_t
        def wrap_get_nominal_glyph(c_font, c_font_data, unicode, c_glyph, c_user_data) :
            font = get_font(c_font)
            glyph = get_nominal_glyph(font, font._font_data, unicode, user_data)
            if glyph != None :
                c_glyph[0] = glyph
            #end if
            return \
                glyph != None
        #end wrap_get_nominal_glyph

    #begin def_wrap_get_nominal_glyph_func
        return \
            wrap_get_nominal_glyph
    #end def_wrap_get_nominal_glyph_func

    def def_wrap_get_variation_glyph_func(self, get_variation_glyph, user_data) :

        @HB.font_get_variation_glyph_func_t
        def wrap_get_variation_glyph(c_font, c_font_data, unicode, variation_selector, c_glyph, c_user_data) :
            font = get_font(c_font)
            glyph = get_variation_glyph(font, font._font_data, unicode, variation_selector, user_data)
            if glyph != None :
                c_glyph[0] = glyph
            #end if
            return \
                glyph != None
        #end wrap_get_variation_glyph

    #begin def_wrap_get_variation_glyph_func
        return \
            wrap_get_variation_glyph
    #end def_wrap_get_variation_glyph_func

    def def_wrap_get_glyph_advance_func(self, get_glyph_advance, user_data) :

        @HB.font_get_glyph_advance_func_t
        def wrap_get_glyph_advance(c_font, c_font_data, glyph, c_user_data) :
            font = get_font(c_font)
            result = get_glyph_advance(font, font._font_data, glyph, user_data)
            if self.autoscale :
                result = HB.to_position_t(result)
            else :
                result = round(result)
            #end if
            return \
                result
        #end wrap_get_glyph_advance

    #begin def_wrap_get_glyph_advance_func
        return \
            wrap_get_glyph_advance
    #end def_wrap_get_glyph_advance_func

    def def_wrap_get_glyph_origin_func(self, get_glyph_origin, user_data) :

        @HB.font_get_glyph_origin_func_t
        def wrap_get_glyph_origin(c_font, c_font_data, glyph, c_x, c_y, c_user_data) :
            font = get_font(c_font)
            pos = get_glyph_origin(font, font._font_data, glyph, user_data)
            if pos != None :
                if self.autoscale :
                    c_x[0] = HB.to_position_t(pos[0])
                    c_y[0] = HB.to_position_t(pos[1])
                else :
                    c_x[0] = round(pos[0])
                    c_y[0] = round(pos[1])
                #end if
            #end if
            return \
                pos != None
        #end wrap_get_glyph_origin

    #begin def_wrap_get_glyph_origin_func
        return \
            wrap_get_glyph_origin
    #end def_wrap_get_glyph_origin_func

    def def_wrap_get_glyph_kerning_func(self, get_glyph_kerning, user_data) :

        @HB.font_get_glyph_kerning_func_t
        def wrap_get_glyph_kerning(c_font, c_font_data, first_glyph, second_glyph, c_user_data) :
            font = get_font(c_font)
            result = get_glyph_kerning(font, font._font_data, first_glyph, second_glyph, user_data)
            if self.autoscale :
                result = HB.to_position_t(result)
            else :
                result = round(result)
            #end if
            return \
                result
        #end wrap_get_glyph_kerning

    #begin def_wrap_get_glyph_kerning_func
        return \
            wrap_get_glyph_kerning
    #end def_wrap_get_glyph_kerning_func

    def def_wrap_get_glyph_extents_func(self, get_glyph_extents, user_data) :

        @HB.font_get_glyph_extents_func_t
        def wrap_get_glyph_extents(c_font, c_font_data, glyph, c_extents, c_user_data) :
            font = get_font(c_font)
            extents = get_glyph_extents(font, font._font_data, glyph, user_data)
            if extents != None :
                extents = extents.to_hb(self.autoscale)
                c_extents[0].x_bearing = extents.x_bearing
                c_extents[0].y_bearing = extents.y_bearing
                c_extents[0].width = extents.width
                c_extents[0].height = extents.height
            #end if
            return \
                extents != None
        #end wrap_get_glyph_extents

    #begin def_wrap_get_glyph_extents_func
        return \
            wrap_get_glyph_extents
    #end def_wrap_get_glyph_extents_func

    def def_wrap_get_glyph_contour_point_func(self, get_glyph_contour_point, user_data) :

        @HB.font_get_glyph_contour_point_func_t
        def wrap_get_glyph_contour_point(c_font, c_font_data, glyph, point_index, c_x, c_y, c_user_data) :
            font = get_font(c_font)
            pos = get_glyph_contour_point(font, font._font_data, glyph, point_index, user_data)
            if pos != None :
                if self.autoscale :
                    c_x[0] = HB.to_position_t(pos[0])
                    c_y[0] = HB.to_position_t(pos[1])
                else :
                    c_x[0] = round(pos[0])
                    c_y[0] = round(pos[1])
                #end if
            #end if
            return \
                pos != None
        #end wrap_get_glyph_contour_point

    #begin def_wrap_get_glyph_contour_point_func
        return \
            wrap_get_glyph_contour_point
    #end def_wrap_get_glyph_contour_point_func

    def def_wrap_get_glyph_name_func(self, get_glyph_name, user_data) :

        @HB.font_get_glyph_name_func_t
        def wrap_get_glyph_name_func(c_font, c_font_data, glyph, c_name, size, c_user_data) :
            font = get_font(c_font)
            name = get_glyph_name(font, font._font_data, glyph, user_data)
            if size > 0 :
                if name != None :
                    enc_name = name.encode()[:size - 1] + b"\x00"
                    for i in range(len(enc_name)) :
                        c_name[i] = enc_name[i]
                    #end for
                else :
                    c_name[0] = 0
                #end if
            #end if
            return \
                name != None
        #end wrap_get_glyph_name_func

    #begin def_wrap_get_glyph_name_func
        return \
            wrap_get_glyph_name_func
    #end def_wrap_get_glyph_name_func

    def def_wrap_get_glyph_from_name_func(self, get_glyph_from_name, user_data) :

        @HB.font_get_glyph_from_name_func_t
        def wrap_get_glyph_from_name(c_font, c_font_data, c_name, c_len, c_glyph, c_user_data) :
            if c_len >= 0 :
                name = c_name[:c_len].decode()
            else :
                name = c_name.value.decode() # nul-terminated
            #end if
            font = get_font(c_font)
            glyph = get_glyph_from_name(font, font._font_data, name, user_data)
            if glyph != None :
                c_glyph[0] = glyph
            #end if
            return \
                glyph != None
        #end wrap_get_glyph_from_name

    #begin def_wrap_get_glyph_from_name_func
        return \
            wrap_get_glyph_from_name
    #end def_wrap_get_glyph_from_name_func

#begin def_fontfuncs_extra
    for basename, def_func, protostr, resultstr in \
        (
            ("font_h_extents", def_wrap_get_font_extents_func, "get_font_h_extents(font, font_data, user_data)", " FontExtents or None"),
            ("font_v_extents", def_wrap_get_font_extents_func, "get_font_v_extents(font, font_data, user_data)", " FontExtents or None"),
            ("nominal_glyph", def_wrap_get_nominal_glyph_func, "get_nominal_glyph(font, font_data, unicode, user_data)", "n integer glyph code or None"),
            ("variation_glyph", def_wrap_get_variation_glyph_func, "get_variation_glyph(font, font_data, unicode, variation_selector, user_data)", "n integer glyph code or None"),
            ("glyph_h_advance", def_wrap_get_glyph_advance_func, "get_glyph_h_advance(font, font_data, glyph, user_data)", " float"),
            ("glyph_v_advance", def_wrap_get_glyph_advance_func, "get_glyph_v_advance(font, font_data, glyph, user_data)", " float"),
            ("glyph_h_origin", def_wrap_get_glyph_origin_func, "get_glyph_h_origin(font, font_data, glyph, user_data)", " 2-tuple, qahirah.Vector or None"),
            ("glyph_v_origin", def_wrap_get_glyph_origin_func, "get_glyph_v_origin(font, font_data, glyph, user_data)", " 2-tuple, qahirah.Vector or None"),
            ("glyph_h_kerning", def_wrap_get_glyph_kerning_func, "get_glyph_h_kerning(font, font_data, first_glyph, second_glyph, user_data)", " float"),
            ("glyph_v_kerning", def_wrap_get_glyph_kerning_func, "get_glyph_v_kerning(font, font_data, first_glyph, second_glyph, user_data)", " float"),
            ("glyph_extents", def_wrap_get_glyph_extents_func, "get_glyph_extents(font, font_data, glyph, user_data)", " GlyphExtents or None"),
            ("glyph_contour_point", def_wrap_get_glyph_contour_point_func, "get_glyph_contour_point(font, font_data, glyph, point_index, user_data)", " 2-tuple, qahirah.Vector or None"),
            ("glyph_name", def_wrap_get_glyph_name_func, "get_glyph_name_func(font, font_data, glyph, user_data)", " string or None"),
            ("glyph_from_name", def_wrap_get_glyph_from_name_func, "get_glyph_from_name(font, font_data, name, user_data)", "n integer glyph code or None"),
        ) \
    :
        def_callback_wrapper \
          (
            celf = FontFuncs,
            method_name = "set_%s_func" % basename,
            docstring =
                    "sets the %(name)s_func callback, along with an optional destroy"
                    " callback for the user_data. The callback_func should be declared"
                    " as follows:\n"
                    "\n"
                    "    def %(proto)s\n"
                    "\n"
                    " where font is the Font instance and font_data was what was"
                    " passed to set_font_funcs for the Font, and return a%(result)s."
                %
                    {"name" : basename, "proto" : protostr, "result" : resultstr},
            callback_field_name = "_wrap_%s_func" % basename,
            destroy_field_name = "_wrap_%s_destroy" % basename,
            def_wrap_callback_func = def_func,
            hb_proc = "hb_font_funcs_set_%s_func" % basename,
          )
    #end for
#end def_fontfuncs_extra
def_fontfuncs_extra()
del def_fontfuncs_extra

# from hb-shape.h:

class FeatureExtra :
    # extra members for Feature class.

    @staticmethod
    def from_string(s) :
        "returns a Feature corresponding to the specified name string."
        sb = s.encode()
        result = HB.feature_t()
        if hb.hb_feature_from_string(sb, len(sb), ct.byref(result)) == 0 :
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
    buffer.autoscale = font.autoscale
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
    nr_shapers, c_shaper_list, c_strs = shaper_list_to_hb(shaper_list)
    result = hb.hb_shape_full(font._hbobj, buffer._hbobj, c_features, nr_features, c_shaper_list) != 0
    buffer.autoscale = font.autoscale
    return \
        result
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

# from hb-set.h:

class Set :
    "wrapper around hb_set_t objects. For internal use only: all relevant" \
    " functions will pass and return Python sets."

    __slots__ = \
        ( # to forestall typos
            "_hbobj",
        )

    def __init__(self, _hbobj) :
        self._hbobj = _hbobj
    #end __init__

    def __del__(self) :
        if hb != None and self._hbobj != None :
            hb.hb_set_destroy(self._hbobj)
            self._hbobj = None
        #end if
    #end __del__

    @staticmethod
    def to_hb(pyset = None) :
        hbobj = hb.hb_set_create()
        if pyset != None :
            for elt in pyset :
                if not isinstance(elt, int) or elt < 0 :
                    raise TypeError("set elements must be codepoints")
                #end if
                hb.hb_set_add(hbobj, elt)
                # figure out how to use set_add_range in future?
                if hb.hb_set_allocation_successful(hbobj) == 0 :
                    raise RuntimeError("insertion of set element failed")
                #end if
            #end for
        #end if
        return \
            Set(hbobj)
    #end to_hb

    @staticmethod
    def NULL() :
        return \
            Set(None)
    #end NULL

    def from_hb(self) :
        if self._hbobj != None :
            result = set()
            first = HB.codepoint_t()
            last = HB.codepoint_t()
            first.value = HB.SET_VALUE_INVALID
            while hb.hb_set_next_range(self._hbobj, ct.byref(first), ct.byref(last)) != 0 :
                result.update(range(first.value, last.value + 1))
            #end while
        else :
            result = None
        #end if
        return \
            result
    #end from_hb

#end Set

# from hb-ot-tag.h:

def ot_tags_from_script(script) :
    script_tag_1 = HB.tag_t()
    script_tag_2 = HB.tag_t()
    hb.hb_ot_tags_from_script(script, ct.byref(script_tag_1), ct.byref(script_tag_2))
    return \
        (script_tag_1.value, script_tag_2.value)
#end ot_tags_from_script

def ot_tag_to_script(tag) :
    return \
        hb.hb_ot_tag_to_script(tag).value
#end ot_tag_to_script

def ot_tag_from_language(language) :
    if not isinstance(language, Language) :
        raise TypeError("language must be a Language")
    #end if
    return \
        hb.hb_ot_tag_from_language(language._hbobj)
#end def

def ot_tag_to_language(tag) :
    return \
        Language(hb.hb_ot_tag_to_language(tag))
#end ot_tag_to_language

# from hb-ot-shape.h:

def ot_shape_glyphs_closure(font, buffer, features, glyphs = None) :
    # does HarfBuzz really allow an initial nonempty set of glyphs?
    if not isinstance(font, Font) or not isinstance(buffer, Buffer) :
        raise TypeError("font must be a Font and buffer must be a Buffer")
    #end if
    c_glyphs = Set.to_hb(glyphs)
    if features != None :
        c_features = seq_to_ct(features, HB.feature_t, lambda f : f.to_hb())
        nr_features = len(features)
    else :
        c_features = None
        nr_features = 0
    #end if
    hb.hb_ot_shape_glyphs_closure(font._hbobj, buffer._hbobj, c_features, nr_features, c_glyphs._hbobj)
    buffer.autoscale = font.autoscale
    return \
        c_glyphs.from_hb()
#end ot_shape_glyphs_closure

# ot_shape_plan_collect_lookups will be found as ShapePlan.ot_collect_lookups (below)

# from hb-shape-plan.h:

class ShapePlan :
    "wrapper around hb_shape_plan_t objects. Do not instantiate directly; use" \
    " create and get_empty methods."

    __slots__ = \
        ( # to forestall typos
            "_hbobj",
            "_user_data",
            "__weakref__",
        )

    # Not sure if I need the ability to map hb_shape_plan_t objects back to
    # Python objects, but, just in case...
    _instances = WeakValueDictionary()
    _ud_refs = WeakValueDictionary()

    def __new__(celf, _hbobj) :
        self = celf._instances.get(_hbobj)
        if self == None :
            self = super().__new__(celf)
            self._hbobj = _hbobj
            user_data = celf._ud_refs.get(_hbobj)
            if user_data == None :
                user_data = UserDataDict()
                celf._ud_refs[_hbobj] = user_data
            #end if
            self._user_data = user_data
            celf._instances[_hbobj] = self
        else :
            hb.hb_shape_plan_destroy(self._hbobj)
              # lose extra reference created by caller
        #end if
        return \
            self
    #end __new__

    def __del__(self) :
        if hb != None and self._hbobj != None :
            hb.hb_shape_plan_destroy(self._hbobj)
            self._hbobj = None
        #end if
    #end __del__

    @staticmethod
    def create(face, props, user_features, shaper_list, cached) :
        if not isinstance(face, Face) :
            raise TypeError("face must be a Face")
        #end if
        if not isinstance(props, SegmentProperties) :
            raise TypeError("props must be a SegmentProperties")
        #end if
        c_props = props.to_hb()
        if user_features != None :
            c_user_features = seq_to_ct(user_features, HB.feature_t, lambda f : f.to_hb())
            nr_user_features = len(user_features)
        else :
            nr_user_features = 0
            c_user_features = None
        #end if
        nr_shapers, c_shaper_list, c_strs = shaper_list_to_hb(shaper_list)
        return \
            ShapePlan \
              (
                (
                    hb.hb_shape_plan_create,
                    hb.hb_shape_plan_create_cached,
                )[cached]
                (face._hbobj, c_props, c_user_features, nr_user_features, c_shaper_list)
              )
    #end create

    def execute(self, font, buffer, features) :
        if not isinstance(font, Font) or not isinstance(buffer, Buffer) :
            raise TypeError("font must be a Font and buffer must be a Buffer")
        #end if
        if features != None :
            c_features = seq_to_ct(features, HB.feature_t, lambda f : f.to_hb())
            nr_features = len(features)
        else :
            c_features = None
            nr_features = 0
        #end if
        result = hb.hb_shape_plan_execute(self._hbobj, font._hbobj, buffer._hbobj, c_features, nr_features) != 0
        buffer.autoscale = font.autoscale
        return \
            result
    #end execute

    @staticmethod
    def get_empty() :
        return \
            ShapePlan(hb.hb_shape_plan_reference(hb.hb_shape_plan_get_empty()))
    #end get_empty

    @property
    def shaper(self) :
        result = hb.hb_shape_plan_get_shaper(self._hbobj)
        if bool(result) :
            result = result.decode() # automatically stops at NUL?
        #end if
        return \
            result
    #end shaper

    @property
    def user_data(self) :
        "a dict, initially empty, which may be used by caller for any purpose."
        return \
            self._user_data
    #end user_data

    # HarfBuzz user_data calls not exposed to caller, probably not useful

    # from hb-ot-shape.h:

    def ot_collect_lookups(self, table_tag) :
        hb_set = Set.to_hb()
        hb.hb_ot_shape_plan_collect_lookups(self._hbobj, table_tag, hb_set._hbobj)
        return \
            hb_set.from_hb()
    #end ot_collect_lookups

#end ShapePlan

def _atexit() :
    # disable all __del__ methods at process termination to avoid segfaults
    for cls in UnicodeFuncs, Blob, Buffer, Face, Font, FontFuncs, Set, ShapePlan :
        delattr(cls, "__del__")
    #end for
#end _atexit
atexit.register(_atexit)
del _atexit

del def_struct_class, def_callback_wrapper, def_immutable # my work is done
