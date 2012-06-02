#!/usr/bin/python3

from backend import Note, NoteSet
from gui import StickyNote
from gi.repository import Gtk, Gdk
from gi.repository import AppIndicator3 as appindicator

class IndicatorStickyNotes:
    def __init__(self):
        # Initialize NoteSet
        self.nset = NoteSet(StickyNote)
        self.nset.open()
        self.nset.showall()
        # Create App Indicator
        self.ind = appindicator.Indicator.new(
                "Sticky Notes", "accessories-text-editor",
                appindicator.IndicatorCategory.APPLICATION_STATUS)
        self.ind.set_status(appindicator.IndicatorStatus.ACTIVE)
        self.ind.set_title("Sticky Notes")
        #self.ind.set_attention_icon("pynagram")
        # Create Menu
        self.menu = Gtk.Menu()
        self.mNewNote = Gtk.MenuItem("New Note")
        self.menu.append(self.mNewNote)
        self.mNewNote.connect("activate", self.new_note, None)
        self.mNewNote.show()

        s = Gtk.SeparatorMenuItem.new()
        self.menu.append(s)
        s.show()

        self.mShowAll = Gtk.MenuItem("Show All")
        self.menu.append(self.mShowAll)
        self.mShowAll.connect("activate", self.showall, None)
        self.mShowAll.show()

        self.mHideAll = Gtk.MenuItem("Hide All")
        self.menu.append(self.mHideAll)
        self.mHideAll.connect("activate", self.hideall, None)
        self.mHideAll.show()

        s = Gtk.SeparatorMenuItem.new()
        self.menu.append(s)
        s.show()

        self.mQuit = Gtk.MenuItem("Quit")
        self.menu.append(self.mQuit)
        self.mQuit.connect("activate", Gtk.main_quit, None)
        self.mQuit.show()
        # Connect Indicator to menu
        self.ind.set_menu(self.menu)

    def new_note(self, *args):
        self.nset.new()

    def showall(self, *args):
        self.nset.showall(*args)

    def hideall(self, *args):
        self.nset.hideall()

    def save(self):
        self.nset.save()


def main():
    indicator = IndicatorStickyNotes()
    Gtk.main()
    indicator.save()

if __name__ == "__main__":
    main()
