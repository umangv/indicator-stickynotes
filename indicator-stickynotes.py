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
from stickynotes.gui import StickyNote, show_about_dialog, \
    SettingsDialog, load_global_css
import stickynotes.info
from stickynotes.info import MO_DIR, LOCALE_DOMAIN

from gi.repository import Gtk, Gdk
from gi.repository import AppIndicator3 as appindicator

import os.path
import locale
import argparse
from locale import gettext as _
from functools import wraps

def save_required(f):
    """Wrapper for functions that require a save after execution"""
    @wraps(f)
    def _wrapper(self, *args, **kwargs):
        ret = f(self, *args, **kwargs)
        self.save()
        return ret
    return _wrapper

class IndicatorStickyNotes:
    def __init__(self, args = None):
        self.args = args
        # use development data file if requested
        isdev = args and args.d
        data_file = stickynotes.info.DEBUG_SETTINGS_FILE if isdev else \
                stickynotes.info.SETTINGS_FILE
        # Initialize NoteSet
        self.nset = NoteSet(StickyNote, data_file)
        self.nset.open()
        if self.nset.properties.get("all_visible", True):
            self.nset.showall()
        # Create App Indicator
        self.ind = appindicator.Indicator.new(
                "Sticky Notes", "indicator-stickynotes",
                appindicator.IndicatorCategory.APPLICATION_STATUS)
        # Delete/modify the following file when distributing as a package
        self.ind.set_icon_theme_path(os.path.abspath(os.path.join(
            os.path.dirname(__file__), 'Icons')))
        self.ind.set_icon("indicator-stickynotes")
        self.ind.set_status(appindicator.IndicatorStatus.ACTIVE)
        self.ind.set_title(_("Sticky Notes"))
        # Create Menu
        self.menu = Gtk.Menu()
        self.mNewNote = Gtk.MenuItem(_("New Note"))
        self.menu.append(self.mNewNote)
        self.mNewNote.connect("activate", self.new_note, None)
        self.mNewNote.show()

        s = Gtk.SeparatorMenuItem.new()
        self.menu.append(s)
        s.show()

        self.mShowAll = Gtk.MenuItem(_("Show All"))
        self.menu.append(self.mShowAll)
        self.mShowAll.connect("activate", self.showall, None)
        self.mShowAll.show()

        self.mHideAll = Gtk.MenuItem(_("Hide All"))
        self.menu.append(self.mHideAll)
        self.mHideAll.connect("activate", self.hideall, None)
        self.mHideAll.show()

        s = Gtk.SeparatorMenuItem.new()
        self.menu.append(s)
        s.show()

        self.mLockAll = Gtk.MenuItem(_("Lock All"))
        self.menu.append(self.mLockAll)
        self.mLockAll.connect("activate", self.lockall, None)
        self.mLockAll.show()

        self.mUnlockAll = Gtk.MenuItem(_("Unlock All"))
        self.menu.append(self.mUnlockAll)
        self.mUnlockAll.connect("activate", self.unlockall, None)
        self.mUnlockAll.show()

        s = Gtk.SeparatorMenuItem.new()
        self.menu.append(s)
        s.show()

        self.mAbout = Gtk.MenuItem(_("About"))
        self.menu.append(self.mAbout)
        self.mAbout.connect("activate", self.show_about, None)
        self.mAbout.show()

        self.mSettings = Gtk.MenuItem(_("Settings"))
        self.menu.append(self.mSettings)
        self.mSettings.connect("activate", self.show_settings, None)
        self.mSettings.show()

        s = Gtk.SeparatorMenuItem.new()
        self.menu.append(s)
        s.show()

        self.mQuit = Gtk.MenuItem(_("Quit"))
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

    @save_required
    def lockall(self, *args):
        for note in self.nset.notes:
            note.gui.set_locked_state(True)
        
    @save_required
    def unlockall(self, *args):
        for note in self.nset.notes:
            note.gui.set_locked_state(False)

    def show_about(self, *args):
        show_about_dialog()

    def show_settings(self, *args):
        wSettings = SettingsDialog(self.nset)

    def save(self):
        self.nset.save()


def main():
    try:
        locale.setlocale(locale.LC_ALL, '')
    except:
        locale.setlocale(locale.LC_ALL, 'C')
    # If we're running from /usr, then .mo files are not in MO_DIR.
    if os.path.abspath(__file__)[:4] == '/usr':
        # Fallback to default
        locale_dir = None
    else:
        locale_dir = os.path.join(os.path.dirname(__file__), MO_DIR)
    locale.bindtextdomain(LOCALE_DOMAIN, locale_dir)
    locale.textdomain(LOCALE_DOMAIN)

    parser = argparse.ArgumentParser(description="Sticky Notes "
            "AppIndicator")
    parser.add_argument("-d", action='store_true', help="use the development"
            " data file")
    args = parser.parse_args()

    indicator = IndicatorStickyNotes(args)
    # Load global css for the first time.
    load_global_css()
    Gtk.main()
    indicator.save()

if __name__ == "__main__":
    main()
