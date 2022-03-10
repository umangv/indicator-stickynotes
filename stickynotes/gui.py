# Copyright © 2012-2018 Umang Varma <umang.me@gmail.com>
# 
# This file is part of indicator-stickynotes.
# 
# indicator-stickynotes is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
# 
# indicator-stickynotes is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
# 
# You should have received a copy of the GNU General Public License along with
# indicator-stickynotes.  If not, see <http://www.gnu.org/licenses/>.

from datetime import datetime
from string import Template
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("GtkSource", "3.0")
from gi.repository import Gtk, Gdk, Gio, GObject, GtkSource, Pango
from locale import gettext as _
import os.path
import colorsys
import uuid

def load_global_css():
    """Adds a provider for the global CSS"""
    global_css = Gtk.CssProvider()
    global_css.load_from_path(os.path.join(os.path.dirname(__file__), "..",
        "style_global.css"))
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(),
            global_css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

class StickyNote:
    """Manages the GUI of an individual stickynote"""
    def __init__(self, note):
        """Initializes the stickynotes window"""
        self.path = os.path.abspath(os.path.join(os.path.dirname(__file__),
            '..'))
        self.note = note
        self.noteset = note.noteset
        self.locked = self.note.properties.get("locked", False)

        # Create menu
        self.menu = Gtk.Menu()
        self.populate_menu()

        # Load CSS template and initialize Gtk.CssProvider
        with open(os.path.join(self.path, "style.css"), encoding="utf-8") \
                as css_file:
            self.css_template = Template(css_file.read())
        self.css = Gtk.CssProvider()

        self.build_note()
        
    def build_note(self):
        self.builder = Gtk.Builder()
        GObject.type_register(GtkSource.View)
        self.builder.add_from_file(os.path.join(self.path,
            "StickyNotes.ui"))
        self.builder.connect_signals(self)
        self.winMain = self.builder.get_object("MainWindow")

        # Get necessary objects
        widgets = ["txtNote", "bAdd", "imgAdd", "imgResizeR", "eResizeR",
                "bLock", "imgLock", "imgUnlock", "imgClose", "imgDropdown",
                "bClose", "confirmDelete", "movebox1", "movebox2"]
        for w in widgets:
            setattr(self, w, self.builder.get_object(w))
        self.style_contexts = [self.winMain.get_style_context(),
                self.txtNote.get_style_context()]
        # Update window-specific style. Global styles are loaded initially!
        self.update_style()
        self.update_font()
        # Ensure buttons are displayed with images
        settings = Gtk.Settings.get_default()
        settings.props.gtk_button_images = True
        # Set text buffer
        self.bbody = GtkSource.Buffer()
        self.bbody.begin_not_undoable_action()
        self.bbody.set_text(self.note.body)
        self.bbody.set_highlight_matching_brackets(False)
        self.bbody.end_not_undoable_action()
        self.txtNote.set_buffer(self.bbody)
        # Make resize work
        self.winMain.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.eResizeR.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        # Move Window
        self.winMain.move(*self.note.properties.get("position", (10,10)))
        self.winMain.resize(*self.note.properties.get("size", (200,150)))
        # Show the window
        self.winMain.set_skip_pager_hint(True)
        self.winMain.show_all()
        # Mouse over
        self.eResizeR.get_window().set_cursor(Gdk.Cursor.new_for_display(
                    self.eResizeR.get_window().get_display(),
                    Gdk.CursorType.BOTTOM_RIGHT_CORNER))
        # Set locked state
        self.set_locked_state(self.locked)

        # call set_keep_above just to have the note appearing
        # above everything else.
        # without it, it still won't appear above a window
        # in which a cursor is active
        self.winMain.set_keep_above(True)

        # immediately undo the set keep above after the window
        # is shown, so that windows won't stay up if we switch to
        # a different window
        self.winMain.set_keep_above(False)


    # (re-)show the sticky note after it has been hidden getting a sticky note
    # to show itself was problematic after a "show desktop" command in unity.
    # (see bug lp:1105948).  Reappearance of dialog is problematic for any
    # dialog which has the skip_taskbar_hint=True property in StickyNotes.ui
    # (property necessary to prevent sticky note from showing on the taskbar)

    # workaround which is based on deleting a sticky note and re-initializing
    # it. 
    def show(self, widget=None, event=None, reload_from_backend=False):
        """Shows the stickynotes window"""

        # don't overwrite settings if loading from backend
        if not reload_from_backend:
            # store sticky note's settings
            self.update_note()
        else:
            # Categories may have changed in backend
            self.populate_menu()

        # destroy its main window
        self.winMain.destroy()

        # reinitialize that window
        self.build_note()

    def hide(self, *args):
        """Hides the stickynotes window"""
        self.winMain.hide()

    def update_note(self):
        """Update the underlying note object"""
        self.note.update(self.bbody.get_text(self.bbody.get_start_iter(),
            self.bbody.get_end_iter(), True))

    def move(self, widget, event):
        """Action to begin moving (by dragging) the window"""
        self.winMain.begin_move_drag(event.button, event.x_root,
                event.y_root, event.get_time())
        return False

    def resize(self, widget, event, *args):
        """Action to begin resizing (by dragging) the window"""
        self.winMain.begin_resize_drag(Gdk.WindowEdge.SOUTH_EAST,
                event.button, event.x_root, event.y_root, event.get_time())
        return True

    def properties(self):
        """Get properties of the current note"""
        prop = {"position":self.winMain.get_position(),
                "size":self.winMain.get_size(), "locked":self.locked}
        if not self.winMain.get_visible():
            prop["position"] = self.note.properties.get("position", (10, 10))
            prop["size"] = self.note.properties.get("size", (200, 150))
        return prop

    def update_font(self):
        """Updates the font"""
        # Unset any previously set font
        self.txtNote.override_font(None)
        font = Pango.FontDescription.from_string(
                self.note.cat_prop("font"))
        self.txtNote.override_font(font)

    def update_style(self):
        """Updates the style using CSS template"""
        self.update_button_color()
        css_string = self.css_template.substitute(**self.css_data())\
                .encode("ascii", "replace")
        self.css.load_from_data(css_string)
        for context in self.style_contexts:
            context.add_provider(self.css,
                    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def update_button_color(self):
        """Switches between regular and dark icons appropriately"""
        h,s,v = self.note.cat_prop("bgcolor_hsv")
        # an arbitrary quadratic found by trial and error
        thresh_sat = 1.05 - 1.7*((v-1)**2)
        suffix = "-dark" if s >= thresh_sat else ""
        iconfiles = {"imgAdd":"add", "imgClose":"close", "imgDropdown":"menu",
                "imgLock":"lock", "imgUnlock":"unlock", "imgResizeR":"resizer"}
        for img, filename in iconfiles.items():
            getattr(self, img).set_from_file(
                    os.path.join(os.path.dirname(__file__), "..","Icons/" +
                    filename + suffix + ".png"))

    def css_data(self):
        """Returns data to substitute into the CSS template"""
        data = {}
        # Converts to RGB hex. All RGB/HSV values are scaled to a max of 1
        rgb_to_hex = lambda x: "#" + "".join(["{:02x}".format(int(255*a))
            for a in x])
        hsv_to_hex = lambda x: rgb_to_hex(colorsys.hsv_to_rgb(*x))
        bgcolor_hsv = self.note.cat_prop("bgcolor_hsv")
        data["bgcolor_hex"] = hsv_to_hex(
                self.note.cat_prop("bgcolor_hsv"))
        data["text_color"] = rgb_to_hex(self.note.cat_prop("textcolor"))
        return data

    def populate_menu(self):
        """(Re)populates the note's menu items appropriately"""
        def _delete_menu_item(item, *args):
            self.menu.remove(item)
        self.menu.foreach(_delete_menu_item, None)

        aot = Gtk.CheckMenuItem.new_with_label(_("Always on top"))
        aot.connect("toggled", self.malways_on_top_toggled)
        self.menu.append(aot)
        aot.show()

        mset = Gtk.MenuItem(_("Settings"))
        mset.connect("activate", self.noteset.indicator.show_settings)
        self.menu.append(mset)
        mset.show()

        sep = Gtk.SeparatorMenuItem()
        self.menu.append(sep)
        sep.show()

        catgroup = []
        mcats = Gtk.RadioMenuItem.new_with_label(catgroup,
                _("Categories:"))
        self.menu.append(mcats)
        mcats.set_sensitive(False)
        catgroup = mcats.get_group()
        mcats.show()

        for cid, cdata in self.noteset.categories.items():
            mitem = Gtk.RadioMenuItem.new_with_label(catgroup,
                    cdata.get("name", _("New Category")))
            catgroup = mitem.get_group()
            if cid == self.note.category:
                mitem.set_active(True)
            mitem.connect("activate", self.set_category, cid)
            self.menu.append(mitem)
            mitem.show()

    def malways_on_top_toggled(self, widget, *args):
        self.winMain.set_keep_above(widget.get_active())

    def save(self, *args):
        self.note.noteset.save()
        return False

    def add(self, *args):
        new_note = self.note.noteset.new()

        # Set the new note to the current category
        new_note.gui.set_category(None, self.note.category)
        new_note.gui.populate_menu()  # Fix Category Menu Selected indicator

        # Set the new note position below this note
        w, h = self.note.properties.get("position", (10, 10))
        h += self.winMain.get_allocation().height + 10
        new_note.gui.winMain.move(w, h)

        return False

    def delete(self, *args):
        winConfirm = Gtk.MessageDialog(self.winMain, None,
                Gtk.MessageType.QUESTION, Gtk.ButtonsType.NONE,
                _("Are you sure you want to delete this note?"))
        winConfirm.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,
                Gtk.STOCK_DELETE, Gtk.ResponseType.ACCEPT)
        confirm = winConfirm.run()
        winConfirm.destroy()
        if confirm == Gtk.ResponseType.ACCEPT:
            self.note.delete()
            self.winMain.destroy()
            return False
        else:
            return True

    def popup_menu(self, button, *args):
        """Pops up the note's menu"""
        self.menu.popup(None, None, None, None, Gdk.BUTTON_PRIMARY, 
                Gtk.get_current_event_time())

    def set_category(self, widget, cat):
        """Set the note's category"""
        if not cat in self.noteset.categories:
            raise KeyError("No such category")
        self.note.category = cat
        self.update_style()
        self.update_font()

    def set_locked_state(self, locked):
        """Change the locked state of the stickynote"""
        self.locked = locked
        self.txtNote.set_editable(not self.locked)
        self.txtNote.set_cursor_visible(not self.locked)
        self.bLock.set_image({True:self.imgLock,
            False:self.imgUnlock}[self.locked])
        self.bLock.set_tooltip_text({True: _("Unlock"),
            False: _("Lock")}[self.locked])

    def lock_clicked(self, *args):
        """Toggle the locked state of the note"""
        self.set_locked_state(not self.locked)

    def focus_out(self, *args):
        self.save(*args)

def show_about_dialog():
    glade_file = os.path.abspath(os.path.join(os.path.dirname(__file__),
            '..', "GlobalDialogs.ui"))
    builder = Gtk.Builder()
    builder.add_from_file(glade_file)
    winAbout = builder.get_object("AboutWindow")
    ret =  winAbout.run()
    winAbout.destroy()
    return ret

class SettingsCategory:
    """Widgets that handle properties of a category"""
    def __init__(self, settingsdialog, cat):
        self.settingsdialog = settingsdialog
        self.noteset = settingsdialog.noteset
        self.cat = cat
        self.builder = Gtk.Builder()
        self.path = os.path.abspath(os.path.join(os.path.dirname(__file__),
            '..'))
        self.builder.add_objects_from_file(os.path.join(self.path,
            "SettingsCategory.ui"), ["catExpander"])
        self.builder.connect_signals(self)
        widgets = ["catExpander", "lExp", "cbBG", "cbText", "eName",
                "confirmDelete", "fbFont"]
        for w in widgets:
            setattr(self, w, self.builder.get_object(w))
        name = self.noteset.categories[cat].get("name", _("New Category"))
        self.eName.set_text(name)
        self.refresh_title()
        self.cbBG.set_rgba(Gdk.RGBA(*colorsys.hsv_to_rgb(
            *self.noteset.get_category_property(cat, "bgcolor_hsv")),
            alpha=1))
        self.cbText.set_rgba(Gdk.RGBA(
            *self.noteset.get_category_property(cat, "textcolor"),
            alpha=1))
        fontname = self.noteset.get_category_property(cat, "font")
        if not fontname:
            # Get the system default font, if none is set
            fontname = \
                self.settingsdialog.wSettings.get_style_context()\
                    .get_font(Gtk.StateFlags.NORMAL).to_string()
                #why.is.this.so.long?
        self.fbFont.set_font(fontname)

    def refresh_title(self, *args):
        """Updates the title of the category"""
        name = self.noteset.categories[self.cat].get("name",
                _("New Category"))
        if self.noteset.properties.get("default_cat", "") == self.cat:
            name += " (" + _("Default Category") + ")"
        self.lExp.set_text(name)

    def delete_cat(self, *args):
        """Delete a category"""
        winConfirm = Gtk.MessageDialog(self.settingsdialog.wSettings, None,
                Gtk.MessageType.QUESTION, Gtk.ButtonsType.NONE,
                _("Are you sure you want to delete this category?"))
        winConfirm.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,
                Gtk.STOCK_DELETE, Gtk.ResponseType.ACCEPT)
        confirm = winConfirm.run()
        winConfirm.destroy()
        if confirm == Gtk.ResponseType.ACCEPT:
            self.settingsdialog.delete_category(self.cat)

    def make_default(self, *args):
        """Make this the default category"""
        self.noteset.properties["default_cat"] = self.cat
        self.settingsdialog.refresh_category_titles()
        for note in self.noteset.notes:
            note.gui.update_style()
            note.gui.update_font()

    def eName_changed(self, *args):
        """Update a category name"""
        self.noteset.categories[self.cat]["name"] = self.eName.get_text()
        self.refresh_title()
        for note in self.noteset.notes:
            note.gui.populate_menu()

    def update_bg(self, *args):
        """Action to update the background color"""
        try:
            rgba = self.cbBG.get_rgba()
        except TypeError:
            rgba = Gdk.RGBA()
            self.cbBG.get_rgba(rgba)
            # Some versions of GObjectIntrospection are affected by
            # https://bugzilla.gnome.org/show_bug.cgi?id=687633 
        hsv = colorsys.rgb_to_hsv(rgba.red, rgba.green, rgba.blue)
        self.noteset.categories[self.cat]["bgcolor_hsv"] = hsv
        for note in self.noteset.notes:
            note.gui.update_style()
        # Remind some widgets that they are transparent, etc.
        load_global_css()

    def update_textcolor(self, *args):
        """Action to update the text color"""
        try:
            rgba = self.cbText.get_rgba()
        except TypeError:
            rgba = Gdk.RGBA()
            self.cbText.get_rgba(rgba)
        self.noteset.categories[self.cat]["textcolor"] = \
                [rgba.red, rgba.green, rgba.blue]
        for note in self.noteset.notes:
            note.gui.update_style()

    def update_font(self, *args):
        """Action to update the font size"""
        self.noteset.categories[self.cat]["font"] = \
            self.fbFont.get_font_name()
        for note in self.noteset.notes:
            note.gui.update_font()

class SettingsDialog:
    """Manages the GUI of the settings dialog"""
    def __init__(self, noteset):
        self.noteset = noteset
        self.categories = {}
        self.path = os.path.abspath(os.path.join(os.path.dirname(__file__),
            '..'))
        glade_file = (os.path.join(self.path, "GlobalDialogs.ui"))
        self.builder = Gtk.Builder()
        self.builder.add_from_file(glade_file)
        self.builder.connect_signals(self)
        widgets = ["wSettings", "boxCategories"]
        for w in widgets:
            setattr(self, w, self.builder.get_object(w))
        for c in self.noteset.categories:
            self.add_category_widgets(c)
        ret =  self.wSettings.run()
        self.wSettings.destroy()

    def add_category_widgets(self, cat):
        """Add the widgets for a category"""
        self.categories[cat] = SettingsCategory(self, cat)
        self.boxCategories.pack_start(self.categories[cat].catExpander,
                False, False, 0)

    def new_category(self, *args):
        """Make a new category"""
        cid = str(uuid.uuid4())
        self.noteset.categories[cid] = {}
        self.add_category_widgets(cid)

    def delete_category(self, cat):
        """Delete a category"""
        del self.noteset.categories[cat]
        self.categories[cat].catExpander.destroy()
        del self.categories[cat]
        for note in self.noteset.notes:
            note.gui.populate_menu()
            note.gui.update_style()
            note.gui.update_font()

    def refresh_category_titles(self):
        for cid, catsettings in self.categories.items():
            catsettings.refresh_title()
