#!/usr/bin/python3
#
# Copyright © 2012-2013 Umang Varma <umang.me@gmail.com>
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

from stickynotes.backend import NoteSet
from stickynotes.gui import StickyNote, show_about_dialog, \
    SettingsDialog, load_global_css
import stickynotes.info
from stickynotes.info import MO_DIR, LOCALE_DOMAIN

from gi.repository import Gtk, GLib
from gi.repository import AppIndicator3 as appindicator

import os.path
import locale
import argparse
from locale import gettext as _
from functools import wraps
import signal



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
        self.nset = NoteSet(StickyNote, data_file, self)
        self.nset.open()
        # If all notes were visible previously, show them now
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

        # Define secondary action (middle click)
        self.connect_secondary_activate()

    def new_note(self, *args):
        self.nset.new()

    def showall(self, *args):
        self.nset.showall(*args)
        self.connect_secondary_activate()

    def hideall(self, *args):
        self.nset.hideall()
        self.connect_secondary_activate()

    def connect_secondary_activate(self):
        """Define action of secondary action (middle click) depending
        on visibility state of notes."""
        if self.nset.properties["all_visible"] == True:
            self.ind.set_secondary_activate_target(self.mHideAll)
        else:
            self.ind.set_secondary_activate_target(self.mShowAll)


    @save_required
    def lockall(self, *args):
        for note in self.nset.notes:
            note.set_locked_state(True)

    @save_required
    def unlockall(self, *args):
        for note in self.nset.notes:
            note.set_locked_state(False)

    def show_about(self, *args):
        show_about_dialog()

    def show_settings(self, *args):
        SettingsDialog(self.nset)

    def save(self):
        self.nset.save()

def handler(indicator):
    indicator.showall() 
    # really don't know why there's a need to do this
    install_glib_handler(indicator)

    # this will be a way to switch between notes using the same shortcut...
    #nnote = len(indicator.nset.notes)
    #current_note = (indicator.nset.current_note+1)%nnote
    #indicator.nset.notes[current_note].show()
    #indicator.nset.current_note = current_note


def install_glib_handler(indicator):
    unix_signal_add = None
    if hasattr(GLib, "unix_signal_add"):
        unix_signal_add = GLib.unix_signal_add
    elif hasattr(GLib, "unix_signal_add_full"):
        unix_signal_add = GLib.unix_signal_add_full

    if unix_signal_add:
        unix_signal_add(GLib.PRIORITY_HIGH, signal.SIGUSR1, handler, indicator)



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

    parser = argparse.ArgumentParser(description=_("Sticky Notes"))
    parser.add_argument("-d", action='store_true', help="use the development"
            " data file")
    args = parser.parse_args()

    indicator = IndicatorStickyNotes(args)

    # Load global css for the first time.
    load_global_css()

    GLib.idle_add(install_glib_handler, indicator, priority=GLib.PRIORITY_HIGH)

    Gtk.main()
    indicator.save()


def is_running():
    """ Check if indicator-stickynotes is already running
        and return PID in case, False elsewhere """
    from fcntl import flock, LOCK_EX, LOCK_NB
    global pid_fd #we need the pid_fd global to keep flock on it

    # open PID/LOCK file
    pid_fd = os.fdopen(os.open('/tmp/indicator-stickynotes.pid', os.O_CREAT|os.O_RDWR), "r+")
    try:
        flock( pid_fd, LOCK_EX|LOCK_NB )
        pid_fd.truncate()
        pid_fd.write("%d" % os.getpid())
        pid_fd.flush()
        return False
    except:
        pid_fd.seek(0)
        pid = pid_fd.readline()
        pid = int(pid)
        pid_fd.close()
        return pid


if __name__ == "__main__":
    import sys

    # if already running send signal 
    # to make stickynotes appears on top
    # and exit
    pid = is_running()
    if pid:
        os.kill(pid,signal.SIGUSR1)
        sys.exit(0)

    main()
