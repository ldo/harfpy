#+
# Python-3 binding for (parts of) HarfBuzz.
#
# Additional recommended libraries:
#     python_freetype <https://github.com/ldo/python_freetype> -- binding for FreeType
#     Qahirah <https://github.com/ldo/qahirah> -- binding for Cairo
#     PyBidi <https://github.com/ldo/pybidi> -- binding for FriBidi
#
# Python adaptation copyright © 2016 Lawrence D'Oliveiro,
# based on C original by Behdad Esfahbod, Owen Taylor, David Turner,
# Werner Lemberg and Ryan Lortie, with copyrights by Red Hat, Google and Codethink, 2009-2014.
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
from weakref import \
    WeakValueDictionary
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

hb = ct.cdll.LoadLibrary("libharfbuzz.so.0")

def seq_to_ct(seq, ct_type, conv = None, zeroterm = False) :
    "extracts the elements of a Python sequence value into a ctypes array" \
    " of type ct_type, optionally applying the conv function to each value.\n" \
    "\n" \
    "Why doesn’t ctypes make this easy?"
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

    def HB_DIRECTION_IS_VALID(dirn) :
        return \
            dirn & ~3 == 4
    #end HB_DIRECTION_IS_VALID

    # Direction must be valid for the following

    def HB_DIRECTION_IS_HORIZONTAL(dirn) :
        return \
            dirn & ~1 == 4
    #end HB_DIRECTION_IS_HORIZONTAL

    def HB_DIRECTION_IS_VERTICAL(dirn) :
        return \
            dirn & ~1 == 6
    #end HB_DIRECTION_IS_VERTICAL

    def HB_DIRECTION_IS_FORWARD(dirn) :
        return \
            dirn & ~2 == 4
    #end HB_DIRECTION_IS_FORWARD

    def HB_DIRECTION_IS_BACKWARD(dirn) :
        return \
            dirn & ~2 == 5
    #end HB_DIRECTION_IS_BACKWARD

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
    font_get_glyph_name_func_t = ct.CFUNCTYPE(bool_t, ct.c_void_p, ct.c_void_p, codepoint_t, ct.c_void_p, ct.c_uint, ct.c_void_p)
    font_get_glyph_from_name_func_t = ct.CFUNCTYPE(bool_t, ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_int, ct.POINTER(codepoint_t), ct.c_void_p)

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
hb.hb_buffer_create.restype = ct.c_void_p
hb.hb_buffer_create.argtypes = ()
hb.hb_buffer_reference.restype = ct.c_void_p
hb.hb_buffer_reference.argtypes = (ct.c_void_p,)
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
hb.hb_face_create_for_tables.restype = ct.c_void_p
hb.hb_face_create_for_tables.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p)
hb.hb_face_destroy.restype = None
hb.hb_face_destroy.argtypes = (ct.c_void_p,)
hb.hb_face_reference.restype = ct.c_void_p
hb.hb_face_reference.argtypes = (ct.c_void_p,)
hb.hb_face_get_empty.restype = ct.c_void_p
hb.hb_face_get_empty.argtypes = ()

hb.hb_font_create.restype = ct.c_void_p
hb.hb_font_create.argtypes = (ct.c_void_p,)
hb.hb_font_create_sub_font.restype = ct.c_void_p
hb.hb_font_create_sub_font.argtypes = (ct.c_void_p,)
hb.hb_font_destroy.restype = None
hb.hb_font_destroy.argtypes = (ct.c_void_p,)

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
hb.hb_ot_layout_language_get_feature_indexes.argtypes = (ct.c_void_p, HB.tag_t, ct.c_uint, ct.c_uint, ct.c_uint, ct.POINTER(ct.c_uint), ct.POINTER(ct.c_uint))
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
hb.hb_shape_plan_create.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_uint, ct.c_void_p)
hb.hb_shape_plan_create_cached.restype = ct.c_void_p
hb.hb_shape_plan_create_cached.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_uint, ct.c_void_p)
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
        bool(hb.hb_version_atleast(major, minor, micro))
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

def tag_from_string(s) :
    sb = s.encode()
    return \
        hb.hb_tag_from_string(sb, len(sb))
#end tag_from_string

def tag_to_string(tag) :
    buf = (4 * ct.c_ubyte)()
    hb.hb_tag_to_string(tag, ct.byref(buf))
    return \
        HB.TAG(*tuple(buf[i] for i in range(4)))
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
            "__weakref__",
        )

    _instances = WeakValueDictionary()

    def __new__(celf, _hbobj) :
        self = celf._instances.get(_hbobj)
        if self == None :
            self = super().__new__(celf)
            self._hbobj = _hbobj
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
            hb.hb_blob_destroy(self._hbobj)
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
        return \
            UnicodeFuncs(hb.hb_unicode_funcs_reference(hb.hb_unicode_funcs_get_empty()))
    #end get_empty

    # TODO: user_data?

    @property
    def immutable(self) :
        "is the UnicodeFuncs immutable."
        return \
            hb.hb_unicode_funcs_is_immutable(self._hbobj) != 0
    #end immutable

    @immutable.setter
    def immutable(self, immut) :
        "blocks further changes."
        if not isinstance(immut, bool) :
            raise TypeError("new setting must be a bool")
        elif not immut :
            raise ValueError("cannot clear immutable setting")
        #end if
        hb.hb_unicode_funcs_make_immutable(self._hbobj)
    #end immutable

    @property
    def parent(self) :
        return \
            UnicodeFuncs(hb.hb_unicode_funcs_reference(hb.hb_unicode_funcs_get_parent(self._hbobj)))
    #end parent

    # TODO: set the actual funcs

#end UnicodeFuncs

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
        " Child inherits parent’s memory mode, but Parent is made immutable."
        return \
            Blob(hb.hb_blob_create_sub_blob(self._hbobj, offset, length))
    #end create_sub

    @staticmethod
    def get_empty() :
        "returns the empty Blob."
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

    @property
    def immutable(self) :
        "is the Blob immutable."
        return \
            hb.hb_blob_is_immutable(self._hbobj) != 0
    #end immutable

    @immutable.setter
    def immutable(self, immut) :
        "blocks further access to the memory area for writes."
        if not isinstance(immut, bool) :
            raise TypeError("new setting must be a bool")
        elif not immut :
            raise ValueError("cannot clear immutable setting")
        #end if
        hb.hb_blob_make_immutable(self._hbobj)
    #end immutable

    # TODO: destroy_func
    # TODO: user_data?

#end Blob

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
        "returns the empty Buffer instance."
        return \
            Buffer(hb.hb_buffer_reference(hb.hb_buffer_get_empty()))
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
        hb.hb_buffer_set_unicode_funcs(self._hbobj, new_funcs)
    #end unicode_funcs

    # TODO: user_data?

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
            # need to keep references to ctypes-wrapped functions
            # so they don't disappear prematurely:
            "_wrap_reference_table",
            "_wrap_destroy",
        )

    _instances = WeakValueDictionary()

    def __new__(celf, _hbobj) :
        self = celf._instances.get(_hbobj)
        if self == None :
            self = super().__new__(celf)
            self._hbobj = _hbobj
            self._wrap_reference_table = None
            self._wrap_destroy = None
            celf._instances[_hbobj] = self
        else :
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
    def create(blob, index) :
        if not isinstance(blob, Blob) :
            raise TypeError("blob must be a Blob")
        #end if
        return \
            Face(hb.hb_face_create(blob._hbobj, index))
    #end create

    @staticmethod
    def create_for_tables(reference_table, user_data, destroy) :
        "creates a Face which calls the specified reference_table action to access" \
        " the font tables. This should be declared as\n" \
        "\n" \
        "    def reference_table(face, tag, user_data)\n" \
        "\n" \
        "where face is the Face instance, tag is the integer tag identifying the" \
        " table, and must return a Blob. The interpretation of user_data is up to you." \
        " The destroy action may be None, but if not, it should be declared as\n" \
        "\n" \
        "     def destroy(user_data)\n" \
        "\n" \
        "and will be called when the Face is destroyed."

        @HB.reference_table_func_t
        def wrap_reference_table(c_face, c_tag, c_user_data) :
            result = reference_table(Face(hb.hb_face_reference(c_face)), c_tag.value, user_data)
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

        result = Face(hb.hb_face_create_for_tables(wrap_reference_table, None, wrap_destroy))
        result._wrap_reference_table = wrap_reference_table
        result._wrap_destroy = wrap_destroy
        return \
            result
    #end create_for_tables

    @staticmethod
    def get_empty() :
        "returns the (unique) empty Face."
        return \
            Face(hb.hb_face_reference(hb.hb_face_get_empty()))
    #end get_empty

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

    # TODO: get/set glyph_count, index, upem, user_data, immutable,
    # reference_blob? reference_table?

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
                tuple(point_array[i].value for i in range(nr_attach_points))
        #end get_attach_points

        # GSUB/GPOS feature query and enumeration interface

        def layout_table_get_script_tags(self, table_tag) :
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
                tuple(script_tags[i].value for i in range(nr_script_tags))
        #end layout_table_get_script_tags

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
                tuple(feature_tags[i].value for i in range(nr_feature_tags))
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
                tuple(language_tags[i].value for i in range(nr_language_tags))
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
                tuple(feature_indexes[i].value for i in range(nr_feature_indexes))
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
                tuple(feature_tags[i].value for i in range(nr_feature_tags))
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
                tuple(lookup_indexes[i].value for i in range(nr_lookups))
        #end feature_get_lookups

        def table_get_lookup_count(self, table_tag) :
            return \
                hb_ot_layout_table_get_lookup_count(self._hbobj, table_tag)
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
            hb.hb_ot_layout_lookup_collect_glyphs(self._hbobj, lookup_index, glyphs_before._hbobj, glyphs_input._hbobj, glyphs_after._hbobj, glyphs_output._hbobj)
            return \
                (glyphs_before.from_hb(), glyphs_input.from_hb(), glyphs_after.from_hb(), glyphs_output.from_hb())
        #end lookup_collect_glyphs

        # GSUB

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

        def has_positioning(self) :
            return \
                hb.hb_ot_layout_has_positioning(self._hbobj) != 0
        #end has_positioning

        def get_size_params(self) :
            # Optical 'size' feature info.  Returns true if found.
            # http://www.microsoft.com/typography/otspec/features_pt.htm#size
            design_size = ct.c_uint()
            subfamily_id = ct.c_uint()
            subfamily_name_id = ct.c_uint()
            range_start = ct.c_uint()
            range_end = ct.c_uint()
            hb.hb_ot_layout_get_size_params \
              (
                self._hbobj,
                ct.byref(design_size),
                ct.byref(subfamily_id),
                ct.byref(subfamily_name_id),
                ct.byref(range_start),
                ct.byref(range_end)
              )
            return \
                (design_size.value, subfamily_id.value, subfamily_name_id.value, range_start.value, range_end.value)
        #end get_size_params

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

# from hb-font.h:

class Font :
    "wrapper around hb_font_t objects. Do not instantiate directly; use" \
    " create methods."

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
        else :
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
        if not isinstance(face, Face) :
            raise TypeError("face must be a Face")
        #end if
        return \
            Font(hb.hb_font_create(face._hbobj))
    #end create

    def create_sub_font(self) :
        return \
            Font(hb.hb_font_create_sub_font(self._hbobj))
    #end create_sub_font

    # TODO: get/set immutable, ppem, scale, parent

    # TODO: get/set glyph_contour_point_func, glyph_extents_func, glyph_from_name_func,
    # glyph_func, glyph_kerning_func, h_advance_func, h_kerning_func, h_origin_func,
    # glyph_name_func, v_advance_func, v_kerning_func, v_origin_func,
    # font_h/v_extents_func, font_extents_func
    # TODO: set_funcs, set_funcs_data

    # TODO: getting corresponding information computed by above functions

    # TODO: glyph to/from string, subtract_glyph_origin_for_direction,
    # get_extents_for_direction

    # TODO: user data?

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

        # Note: cannot implement get_face because that requires
        # reconstructing a freetype.Face wrapper object, which
        # cannot safely be done without the associated library
        # for disposal purposes.

        # TODO: set_funcs

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
                tuple(caret_array[i].value for i in range(nr_carets))
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

class FontFuncs :
    "wrapper around hb_font_funcs_t objects. Do not instantiate directly; use" \
    " create and get_empty methods."

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
        else :
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
    def create() :
        return \
            FontFuncs(hb.hb_font_funcs_create())
    #end create

    @staticmethod
    def get_empty() :
        return \
            FontFuncs(hb.hb_font_funcs_reference(hb.hb_font_funcs_get_empty()))
    #end get_empty

    # TODO: user_data?

    @property
    def immutable(self) :
        return \
            hb.hb_font_funcs_is_immutable(self._hbobj) != 0
    #end immutable

    @immutable.setter
    def immutable(self, immut) :
        if not isinstance(immut, bool) :
            raise TypeError("new setting must be a bool")
        elif not immut :
            raise ValueError("cannot clear immutable setting")
        #end if
        hb.hb_font_funcs_make_immutable(self._hbobj)
    #end immutable

    # TBD: actual funcs

#end FontFuncs

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
    nr_shapers, c_shaper_list, c_strs = shaper_list_to_hb(shaper_list)
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
            while True :
                if hb.hb_set_next_range(self._hbobj, ct.byref(first), ct.byref(last)) == 0 :
                    break
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
    hb_ot_shape_glyphs_closure(font._hbobj, buffer._hbobj, c_features, nr_features, c_glyphs._hbobj)
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
            "__weakref__",
        )

    # Not sure if I need the ability to map hb_shape_plan_t objects back to
    # Python objects, but, just in case...
    _instances = WeakValueDictionary()

    def __new__(celf, _hbobj) :
        self = celf._instances.get(_hbobj)
        if self == None :
            self = super().__new__(celf)
            self._hbobj = _hbobj
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
                    hb_shape_plan_create,
                    hb_shape_plan_create_cached,
                )[cached]
                (face._hbobj, c_props, c_user_features, nr_user_features, c_shaper_list)
              )
    #end create

    def execute(self, font, buffer, features) :
        if not isinstance(font, Font) or not isinstance(buffer, Buffer) :
            raise TypeError("font must be a Font and buffer must be a Buffer")
        #end if
        if user_features != None :
            c_user_features = seq_to_ct(user_features, HB.feature_t, lambda f : f.to_hb())
            nr_user_features = len(user_features)
        else :
            c_user_features = None
            nr_user_features = 0
        #end if
        return \
            hb.hb_shape_plan_execute(self._hbobj, font._hbobj, buffer._hbobj, c_user_features, nr_user_features) != 0
    #end execute

    @staticmethod
    def get_empty() :
        return \
            ShapePlan(hb.hb_shape_plan_reference(hb.hb_shape_plan_get_empty()))
    #end get_empty

    @property
    def shaper(self) :
        return \
            hb.hb_shape_plan_get_shaper(self._hbobj).decode() # automatically stops at NUL?
    #end shaper

    # TODO: user_data?

    # from hb-ot-shape.h:

    def ot_collect_lookups(table_tag) :
        hb_set = Set.to_hb()
        hb.hb_ot_shape_plan_collect_lookups(self._hbobj, table_tag, hb_set._hbobj)
        return \
            hb_set.from_hb()
    #end ot_collect_lookups

#end ShapePlan

del def_struct_class # my work is done
