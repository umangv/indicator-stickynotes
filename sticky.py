#!/usr/bin/python3
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

from stickynotes.backend import Note, NoteSet
from stickynotes.gui import StickyNote
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
                "Sticky Notes", "indicator-stickynotes",
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

        self.mLockAll = Gtk.MenuItem("Lock All")
        self.menu.append(self.mLockAll)
        self.mLockAll.connect("activate", self.lockall, None)
        self.mLockAll.show()

        self.mUnlockAll = Gtk.MenuItem("Unlock All")
        self.menu.append(self.mUnlockAll)
        self.mUnlockAll.connect("activate", self.unlockall, None)
        self.mUnlockAll.show()

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

    def lockall(self, *args):
        for note in self.nset.notes:
            note.gui.set_locked_state(True)
        
    def unlockall(self, *args):
        for note in self.nset.notes:
            note.gui.set_locked_state(False)

    def save(self):
        self.nset.save()


def main():
    indicator = IndicatorStickyNotes()
    Gtk.main()
    indicator.save()

if __name__ == "__main__":
    main()
