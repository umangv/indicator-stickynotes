#!/usr/bin/python3

from backend import Note, NoteSet
from gui import StickyNote
from gi.repository import Gtk, Gdk

def main():
    nset = NoteSet(StickyNote)
    nset.open()
    nset.showall()
    Gtk.main()
    nset.save()

if __name__ == "__main__":
    main()
