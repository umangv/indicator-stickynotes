#!/usr/bin/python3
# 
# Copyright © 2012-2015 Umang Varma <umang.me@gmail.com>
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
from stickynotes.gui import *
import stickynotes.info
from stickynotes.info import MO_DIR, LOCALE_DOMAIN

from gi.repository import Gtk, GLib
from gi.repository import AppIndicator3 as appindicator

import os.path
import locale
import argparse
from locale import gettext as _
from functools import wraps
from shutil import copyfile, SameFileError
import signal #needed to send signal if another process is running

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
        self.data_file = stickynotes.info.DEBUG_SETTINGS_FILE if isdev \
                else stickynotes.info.SETTINGS_FILE
        # Initialize NoteSet
        self.nset = NoteSet(StickyNote, self.data_file, self)
        try:
            self.nset.open()
        except FileNotFoundError:
            self.nset.load_fresh()
        except Exception as e:
            err = _("Error reading data file. Do you want to "
                "backup the current data?")
            winError = Gtk.MessageDialog(None, None, Gtk.MessageType.ERROR,
                    Gtk.ButtonsType.NONE, err)
            winError.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,
                    _("Backup"), Gtk.ResponseType.ACCEPT)
            resp = winError.run()
            winError.hide()
            if resp == Gtk.ResponseType.ACCEPT:
                self.backup_datafile()
            winError.destroy()
            self.nset.load_fresh()

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

        self.mExport = Gtk.MenuItem(_("Export Data"))
        self.menu.append(self.mExport)
        self.mExport.connect("activate", self.export_datafile, None)
        self.mExport.show()

        self.mImport = Gtk.MenuItem(_("Import Data"))
        self.menu.append(self.mImport)
        self.mImport.connect("activate", self.import_datafile, None)
        self.mImport.show()

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

    def backup_datafile(self):
        winChoose = Gtk.FileChooserDialog(_("Export Data"), None,
                Gtk.FileChooserAction.SAVE, (Gtk.STOCK_CANCEL,
                    Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE,
                    Gtk.ResponseType.ACCEPT))
        winChoose.set_do_overwrite_confirmation(True)
        response = winChoose.run()
        backupfile = None
        if response == Gtk.ResponseType.ACCEPT:
            backupfile =  winChoose.get_filename()
        winChoose.destroy()
        if backupfile:
            try:
                copyfile(os.path.expanduser(self.data_file), backupfile)
            except SameFileError:
                err = _("Please choose a different "
                    "destination for the backup file.")
                winError = Gtk.MessageDialog(None, None,
                        Gtk.MessageType.ERROR, Gtk.ButtonsType.CLOSE, err)
                winError.run()
                winError.destroy()
                self.backup_datafile()

    def export_datafile(self, *args):
        self.backup_datafile()

    def import_datafile(self, *args):
        winChoose = Gtk.FileChooserDialog(_("Import Data"), None,
                Gtk.FileChooserAction.OPEN, (Gtk.STOCK_CANCEL,
                    Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN,
                    Gtk.ResponseType.ACCEPT))
        response = winChoose.run()
        backupfile = None
        if response == Gtk.ResponseType.ACCEPT:
            backupfile =  winChoose.get_filename()
        winChoose.destroy()
        if backupfile:
            try:
                with open(backupfile, encoding="utf-8") as fsock:
                    self.nset.merge(fsock.read())
            except Exception as e:
                err = _("Error importing data.")
                winError = Gtk.MessageDialog(None, None,
                        Gtk.MessageType.ERROR, Gtk.ButtonsType.CLOSE, err)
                winError.run()
                winError.destroy()

    def show_about(self, *args):
        show_about_dialog()

    def show_settings(self, *args):
        SettingsDialog(self.nset)

    def save(self):
        self.nset.save()

def handler(indicator):
    indicator.showall() 
    # really don't know why there's a need to do this
    install_glib_handler(indicator, signal.SIGUSR1)

    # this will be a way to switch between notes using the same shortcut...
    #nnote = len(indicator.nset.notes)
    #current_note = (indicator.nset.current_note+1)%nnote
    #indicator.nset.notes[current_note].show()
    #indicator.nset.current_note = current_note

def reload_handler(indicator):
    # reload from data file on SIGUSR2
    with open(os.path.expanduser(indicator.data_file), encoding="utf-8") as fsock:
        indicator.nset.merge(fsock.read())
    install_glib_handler(indicator, signal.SIGUSR2)

def install_glib_handler(indicator, sig=None):
    unix_signal_add = None
    if hasattr(GLib, "unix_signal_add"):
        unix_signal_add = GLib.unix_signal_add
    elif hasattr(GLib, "unix_signal_add_full"):
        unix_signal_add = GLib.unix_signal_add_full

    if unix_signal_add:
        if not sig or sig==signal.SIGUSR1:
            unix_signal_add(GLib.PRIORITY_HIGH, signal.SIGUSR1, handler, indicator)
        if not sig or sig==signal.SIGUSR2:
            unix_signal_add(GLib.PRIORITY_HIGH, signal.SIGUSR2, reload_handler, indicator)



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

    parser = argparse.ArgumentParser(description=_("Sticky Notes"),
            usage = "%(prog)s [-k | -r | [[-c CATEGORY] " +
                    "(-i INPUTFILE | -n STRING ...)] | -d]")

    parser.add_argument("-k","--kill", action="store_true",
            help="kill background proccess")
    parser.add_argument("-r","--refresh", action="store_true",
            help="refresh data")
    parser.add_argument("-c","--category", nargs=1, default=[''],
            help="using with [-n|-i ...], set categeory", type=str)
    parser.add_argument("-i","--infile", type=argparse.FileType('r'),
            help="new sticky note with content from a file")
    parser.add_argument("-n","--new", metavar='NEW_NOTE', nargs='+',
            help="create a new note")
    parser.add_argument("--no-daemon", action="store_true",
            help="do not daemonize")
    parser.add_argument("-d", action='store_true',
            help="use the development data file")
    args = parser.parse_args()

    if args.new or args.infile: # create a new note if required
        args.refresh=True
        noteset=NoteSet(indicator=None, gui_class=None,
            data_file=stickynotes.info.DEBUG_SETTINGS_FILE if args.d        \
                else stickynotes.info.SETTINGS_FILE)
        try: noteset.open()
        except Exception as e:
            print('failed to load config file')
            sys.exit(1)
        notebody = ' '.join(args.new).encode().decode('unicode-escape')     \
            .encode('latin1').decode('utf-8') if args.new                   \
            else args.infile.read().rstrip()
        noteset.new(notebody=notebody, category=args.category[0])
        noteset.save()

    pid = is_running()
    if pid:
        if   args.kill:     sig = signal.SIGKILL
        elif args.refresh:  sig = signal.SIGUSR2
        else:               sig = signal.SIGUSR1
        # send signal to the existing process accordingly
        os.kill(pid, sig)
    elif not (args.kill or args.refresh):
        main()   # run

    sys.exit(0)
