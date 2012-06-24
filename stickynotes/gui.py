# 
# Copyright © 2012 Umang Varma <umang.me@gmail.com>
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

from gi.repository import Gtk, Gdk, Gio, GObject, GtkSource
import os.path

class StickyNote(object):

    def __init__(self, note):
        self.path = os.path.abspath(os.path.join(os.path.dirname(__file__),
            '..'))
        self.note = note
        self.locked = self.note.properties.get("locked", False)
        self.builder = Gtk.Builder()
        GObject.type_register(GtkSource.View)
        self.builder.add_from_file(os.path.join(self.path,
            "StickyNotes.glade"))
        self.builder.connect_signals(self)
        # Get necessary objects
        self.txtNote = self.builder.get_object("txtNote")
        self.winMain = self.builder.get_object("MainWindow")
        self.winMain.set_name("main-window")
        self.bAdd = self.builder.get_object("bAdd")
        self.imgAdd = self.builder.get_object("imgAdd")
        self.imgResizeR = self.builder.get_object("imgResizeR")
        self.eResizeR = self.builder.get_object("eResizeR")
        self.bLock = self.builder.get_object("bLock")
        self.imgLock = self.builder.get_object("imgLock")
        self.imgUnlock = self.builder.get_object("imgUnlock")
        self.bClose = self.builder.get_object("bClose")
        self.confirmDelete = self.builder.get_object("confirmDelete")
        # Run
        self.run()

    def run(self, *args):
        # (Maybe?) Remove this eventually
        settings = Gtk.Settings.get_default()
        settings.props.gtk_button_images = True
        # Load and set CSS
        css = Gtk.CssProvider()
        css.load_from_file(Gio.File.new_for_path(os.path.join(self.path,
            "style.css")))
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(),
                css, 800)
        # Set text buffer
        self.bbody = GtkSource.Buffer()
        self.bbody.begin_not_undoable_action()
        self.bbody.set_text(self.note.body)
        self.bbody.set_highlight_matching_brackets(False)
        self.bbody.end_not_undoable_action()
        self.txtNote.set_buffer(self.bbody)
        #Show
        self.winMain.show()
        # Make resize work
        self.winMain.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.eResizeR.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        # Move Window
        self.winMain.move(*self.note.properties.get("position", (10,10)))
        self.winMain.resize(*self.note.properties.get("size", (200,150)))
        # Mouse over
        self.eResizeR.get_window().set_cursor(Gdk.Cursor.new_for_display(
                    self.eResizeR.get_window().get_display(),
                    Gdk.CursorType.BOTTOM_RIGHT_CORNER))
        # Set locked state
        self.set_locked_state(self.locked)

    def show(self, widget=None, event=None):
        self.winMain.present()
        self.winMain.stick()
        self.winMain.move(*self.note.properties.get("position", (10,10)))

    def hide(self, *args):
        self.winMain.hide()

    def update_note(self):
        self.note.update(self.bbody.get_text(self.bbody.get_start_iter(),
            self.bbody.get_end_iter(), True))

    def move(self, widget, event):
        self.winMain.begin_move_drag(event.button, event.x_root,
                event.y_root, event.get_time())
        return False

    def resize(self, widget, event, *args):
        self.winMain.begin_resize_drag(Gdk.WindowEdge.SOUTH_EAST,
                event.button, event.x_root, event.y_root, event.get_time())
        return True

    def properties(self):
        prop = {"position":self.winMain.get_position(),
                "size":self.winMain.get_size(), "locked":self.locked}
        if not self.winMain.get_visible():
            prop["position"] = self.note.properties.get("position", (10, 10))
            prop["size"] = self.note.properties.get("size", (200, 200))
        return prop

    def save(self, *args):
        self.note.noteset.save()
        return False

    def add(self, *args):
        self.note.noteset.new()
        return False

    def delete(self, *args):
        confirm = self.confirmDelete.run()
        self.confirmDelete.hide()
        if confirm == 1:
            self.note.delete()
            self.winMain.hide()
            return False
        else:
            return True

    def set_locked_state(self, locked):
        self.locked = locked
        if not self.bLock.get_active() == self.locked:
            self.bLock.set_active(self.locked)
        self.txtNote.set_editable(not self.locked)
        self.txtNote.set_cursor_visible(not self.locked)
        self.bLock.set_image({True:self.imgLock,
            False:self.imgUnlock}[self.locked])

    def lock_toggled(self, *args):
        self.set_locked_state(self.bLock.get_active())

    def quit(self, *args):
        Gtk.main_quit()

    def focus_out(self, *args):
        self.save(*args)

