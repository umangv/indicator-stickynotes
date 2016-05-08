#!/usr/bin/python3
# -*- coding: utf-8 -*-
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

from distutils.core import setup
from distutils.cmd import Command
import distutils.command.build, distutils.command.install_data, \
    distutils.command.clean

from subprocess import call

import glob
import os
import sys
import shutil

sys.dont_write_bytecode = True
from stickynotes.info import PO_DIR, MO_DIR, LOCALE_DOMAIN
sys.dont_write_bytecode = False

class BuildPo(Command):
    """Builds translation files
    
    This is useful for testing translations that haven't been installed"""
    user_options = []
    def initialize_options(self):
        pass
    def finalize_options(self):
        pass
    def run(self):
        """Compiles .po files in PO_DIR to .mo files in MO_DIR"""
        for file in glob.glob(os.path.join(PO_DIR, "*.po")):
            locale = os.path.splitext(os.path.basename(file))[0]
            dest = os.path.join(MO_DIR, locale, "LC_MESSAGES",
                    LOCALE_DOMAIN + ".mo")
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            try:
                ret = call(["msgfmt", "-o", dest, file])
            except OSError:
                raise Exception("Error: Unable to run msgfmt")
            if ret:
                raise Exception("Error: msgfmt returned error code {0}" \
                        .format(ret))

class Build(distutils.command.build.build):
    # build should depend on build_po
    sub_commands = distutils.command.build.build.sub_commands + \
            [('build_po', None)]

class Clean(distutils.command.clean.clean):
    def run(self):
        # delete MO_DIR files before cleaning everything else
        print("Deleting {0}/ and contents".format(MO_DIR))
        shutil.rmtree(MO_DIR, ignore_errors=True)
        return super().run()

class InstallData(distutils.command.install_data.install_data):
    """Find icon and translation files before continuing install process"""

    def run(self):
        self.data_files.extend([(os.path.join("/usr/share/", dir),
            [os.path.join(dir, file) for file in files]) for dir, subdirs,
            files in os.walk("locale") if files])
        return super().run()

def main():
    # Default data files
    data_files = [('', ('COPYING', 'style.css', 'StickyNotes.glade',
                    'style_global.css', 'GlobalDialogs.glade',
                    'SettingsCategory.glade')),
                ('/usr/share/applications', ('indicator-stickynotes.desktop',)),
                ('Icons', glob.glob("Icons/*.png"))]
    # Icon themes
    icon_themes = ["hicolor", "ubuntu-mono-dark", "ubuntu-mono-light"]
    for theme in icon_themes:
        data_files.extend([(os.path.join("/usr/share/icons/", theme,
            os.path.relpath(dir, "Icons/" + theme)), [os.path.join(
                dir, file) for file in files])
            for dir, subdirs, files in os.walk("Icons/" + theme) if files])

    setup(name='indicator-stickynotes',
            version='0.5.4',
            description='Sticky Notes Indicator',
            author='Umang Varma',
            author_email='umang.me@gmail.com',
            url='https://www.launchpad.net/indicator-stickynotes/',
            packages=['stickynotes',],
            scripts=['indicator-stickynotes.py',],
            data_files=data_files,
            cmdclass={'build': Build, 'install_data': InstallData,
                'build_po': BuildPo, 'clean':Clean},
            long_description="Write reminders on notes with Indicator "
                "Stickynotes")

if __name__ == "__main__":
    main()
