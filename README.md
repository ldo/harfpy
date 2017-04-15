HarfPy is a Python 3 binding for
[HarfBuzz](https://www.freedesktop.org/wiki/Software/HarfBuzz/). It is meant to be used in
conjunction with my Python wrappers for other major parts of the Linux typography stack:

* Qahirah ([GitLab](https://gitlab.com/ldo/qahirah),
  [GitHub](https://github.com/ldo/qahirah)) -- my binding for the
  [Cairo](https://www.cairographics.org/) graphics library
* python_freetype ([GitLab](https://gitlab.com/ldo/python_freetype),
  [GitHub](https://github.com/ldo/python_freetype)) -- my binding for
  [FreeType](https://www.freetype.org/)
* PyBidi ([GitLab](https://gitlab.com/ldo/pybidi),
  [GitHub](https://github.com/ldo/pybidi)) -- my binding for
  [FriBidi](https://fribidi.org/)

The basic steps in doing a piece of high-quality text rendering on Linux are:

* Make sure all text is encoded in Unicode. (This should go without saying...)
* Use FriBidi to reorder a string of unicode-encoded text from logical (reading) order to
  visual (rendering) order. (This step can be skipped in cases where you do not mix text
  of different directions.)
* Use FreeType to load a suitable font.
* Use HarfBuzz to choose and lay out suitable glyphs for the specified text, controlled by
  appropriate features selected from the specified font.
* Use Cairo to draw the actual glyphs, as laid out by HarfBuzz, with that font.


Installation
============

To install HarfPy on your system, type

    python3 setup.py install

This will install the Python module named “`harfbuzz`”.


Basic Usage
===========

All functionality comes from the one module:

    import harfbuzz

You will typically also want more direct access to constants and other definitions within
the `HARFBUZZ` class:

    from harfbuzz import \
        HARFBUZZ

Or you may want to abbreviate the names, for convenience:

    import harfbuzz as hb
    from harfbuzz import \
        HARFBUZZ as HB

Names in the module omit the “`hb_`” and "`HB_`” prefixes. For example, whereas in C you
might write

    hb_shape(font, buffer);

in Python this becomes (with the above import abbreviations):

    hb.shape(font, buffer)

And a constant like `HB_TAG_NONE` can be accessed (again with the above import
abbreviations) as `HB.TAG_NONE`.

Operations on specific HarfBuzz objects further lose the prefix parts of their names
associated with those objects, because they become methods defined within those objects.
Thus, instead of, in C,

    buf = hb_buffer_create();

in Python this becomes

    buf = hb.Buffer.create()

and

    hb_buffer_clear_contents(buf);

becomes

    buf.clear_contents()


Hello-HarfBuzz Example
======================

The HarfBuzz docs include [this
example](http://behdad.github.io/harfbuzz/hello-harfbuzz.html) on how to get started.
Let’s recreate that using HarfPy.

    import sys
    import qahirah as qah
    import harfbuzz as hb

We will need to load a font with FreeType. To use FreeType, you have to create a `Library`
instance. But Qahirah already has one, so it’s simpler to just use that:

    ft = qah.get_ft_lib()

(This also lets you use the same font instances for drawing the text.) Let’s make up a
simple line of right-to-left text:

    text_line = "\u0627\u0644\u0642\u0627\u0647\u0631\u0629" # “al-qahirah”

Create a `Buffer`:

    buf = hb.Buffer.create()

Put the text into the buffer:

    buf.add_str(text_line)

Let HarfBuzz figure out the run properties:

    buf.guess_segment_properties()

Load a suitable font:

    ft_face = ft.find_face("Scheherazade")

We need to set a font size, otherwise we won’t get any sensible metrics. A size of 1 will
do for measurement purposes:

    ft_face.set_char_size(size = 1, resolution = qah.base_dpi)

HarfBuzz wants us to wrap this in one of its own `Font` objects:

    hb_font = hb.Font.ft_create(ft_face)

Do the glyph selection and layout, based on the default font features:

    hb.shape(hb_font, buf)

And let’s see what we got:

    sys.stdout.write \
      (
            "buf.glyph_infos = %s\n glyph_positions = %s\n"
        %
            (buf.glyph_infos, buf.glyph_positions)
      )


Rendering Bidirectional Text
============================

How would you render a line containing a mixture of left-to-right and right-to-left text?
First of all, note that HarfBuzz can only do shaping on one run at a time. So you have to
break up your line into segments, put them through HarfBuzz shaping one at a time, and
collect all the glyphs together. Here is an example to walk you through the necessary
steps, using all the abovementioned Python modules. First, the necessary imports:

    import sys
    import os
    import math
    # import freetype2 as freetype # use Qahirah instance
    import qahirah as qah
    from qahirah import \
        CAIRO, \
        Colour, \
        Glyph, \
        Vector
    ft = qah.get_ft_lib()
    import fribidi as fb
    from fribidi import \
        FRIBIDI as FB
    import harfbuzz as hb

Next, the text we are going to render:

    book_title = \
        (
            "\u0627\u0644\u0643\u062a\u0627\u0628" # “al-kitab”
            " \u0627\u0644\u0645\u062e\u062a\u0635\u0631" # “al-mukhtasar”
            " \u0641\u064a" # “fi”
            " \u062d\u0633\u0627\u0628" # “hisab”
            " \u0627\u0644\u062c\u0628\u0631" # “al-jabr”
            " \u0648\u0627\u0644\u0645\u0642\u0627\u0628\u0644\u0629" # “wa’l-muqabala”
        )
    author = \
        (
            "\u0645\u062d\u0645\u062f" # “Muhammad’
            " \u0628\u0646" # “ibn”
            " \u0645\u0648\u0633\u0649" # “Musa”
            " \u0627\u0644\u062e\u0648\u0627\u0631\u0632\u0645\u06cc" # “al-Khwarizmi”
        )
    text_line = \
        (
            "The book “%(title)s” gives us the word “algebra”,"
            " its author’s name %(author)s gives us “algorithm”."
        %
            {"author" : author, "title" : book_title}
        )
    base_rtl = False

Initial font and buffer setup:

    text_size = 36
    buf = hb.Buffer.create()
    ft_face = ft.find_face("DejaVu Sans")
    ft_face.set_char_size(size = text_size, resolution = qah.base_dpi)
    hb_font = hb.Font.ft_create(ft_face)

Use FriBidi to reorder the line and define the embedding levels:

    bidi_types = fb.get_bidi_types(text_line)
    base_dir, embedding_levels = \
        fb.get_par_embedding_levels(bidi_types, (FB.PAR_LTR, FB.PAR_RTL)[base_rtl])[1:]
    vis_line, map = fb.reorder_line \
      (
        flags = FB.FLAGS_DEFAULT,
        bidi_types = bidi_types,
        line_offset = 0,
        base_dir = base_dir,
        embedding_levels = embedding_levels,
        logical_str = text_line,
        map = fb.Reordering.identity(text_line)
      )[1:]
    vis_bidi_types = map.apply(bidi_types)
    vis_embedding_levels = map.apply(embedding_levels)

Next, collect the glyphs for each segment/run into a list of Qahirah `Glyphs` objects.
Note the use of the `each_embedding_run` convenience routine provided by PyBidi, and the
`Buffer.get_glyphs` convenience method provided by HarfPy:

    glyphs = []
    glyph_pos = Vector(0, 0)
    for substr, pos1, pos2, level in fb.each_embedding_run(vis_line, vis_embedding_levels) :
        buf.reset()
        buf.add_str(substr)
        if FB.LEVEL_IS_RTL(level) :
            # HarfBuzz always wants to start with logical order, not display order,
            # so undo FriBidi reordering
            buf.reverse()
        #end if
        buf.guess_segment_properties()
        hb.shape(hb_font, buf)
        new_glyphs, end_glyph_pos = buf.get_glyphs(glyph_pos)
        glyph_pos = end_glyph_pos
        glyphs.extend(new_glyphs)
    #end for

Do the Cairo font setup, and figure out how big an `ImageSurface` we need:

    qah_face = qah.FontFace.create_for_ft_face(ft_face)
    glyph_extents = \
        (qah.Context.create_for_dummy()
            .set_font_face(qah_face)
            .set_font_size(text_size)
            .glyph_extents(glyphs)
        )
    figure_bounds = math.ceil(glyph_extents.bounds)
    pix = qah.ImageSurface.create \
      (
        format = CAIRO.FORMAT_RGB24,
        dimensions = figure_bounds.dimensions
      )

Actually render the glyphs into a Cairo context:

    (qah.Context.create(pix)
        .translate(- figure_bounds.topleft)
        .set_source_colour(Colour.grey(1))
        .paint()
        .set_source_colour(Colour.grey(0))
        .set_font_face(qah_face)
        .set_font_size(text_size)
        .show_glyphs(glyphs)
    )

And finally, save the `ImageSurface` contents to a PNG file for viewing:

    pix.flush().write_to_png("%s.png" % os.path.basename(sys.argv[0]))

For more complete example scripts, see my harfpy_examples
([GitLab](https://gitlab.com/ldo/harfpy_examples),
[GitHub](https://github.com/ldo/harfpy_examples)) repo.


More Info About HarfBuzz
========================

The API documentation seems to be rather lacking. A good starting point for finding out
more is the [HarfBuzz Wiki](https://github.com/behdad/harfbuzz/wiki).

Lawrence D'Oliveiro <ldo@geek-central.gen.nz>
2017 April 7
