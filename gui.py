#!/usr/bin/python3

from gi.repository import Gtk, Gdk, Gio, GObject, GtkSource

class StickyNote(object):

    def __init__(self, note):
        self.note = note
        self.builder = Gtk.Builder()
        GObject.type_register(GtkSource.View)
        self.builder.add_from_file("StickyNotes.glade")
        self.builder.connect_signals(self)
        self.txtNote = self.builder.get_object("txtNote")
        self.winMain = self.builder.get_object("MainWindow")
        self.bAdd = self.builder.get_object("bAdd")
        self.imgAdd = self.builder.get_object("imgAdd")
        self.imgResizeR = self.builder.get_object("imgResizeR")
        self.eResizeR = self.builder.get_object("eResizeR")
        self.run()

    def run(self, *args):
        # (Maybe?) Remove this eventually
        settings = Gtk.Settings.get_default()
        settings.props.gtk_button_images = True
        # Load and set CSS
        css = Gtk.CssProvider()
        css.load_from_file(Gio.File.new_for_path("style.css"))
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
        return {"position":self.winMain.get_position(),
                "size":self.winMain.get_size()}

    def save(self, *args):
        self.note.noteset.save()
        return False

    def add(self, *args):
        self.note.noteset.new()
        return False

    def delete(self, *args):
        self.note.delete()
        self.winMain.hide()
        return False

    def quit(self, *args):
        Gtk.main_quit()

    def focus_out(self, *args):
        self.save(*args)

