#!/usr/bin/python3
# -*- coding: utf-8 -*-
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

from distutils.core import setup
import glob, os

data_files = [('', ('COPYING', 'style.css', 'StickyNotes.glade')),
    ('/usr/share/applications', ('indicator-stickynotes.desktop',)),
    ('Icons', glob.glob("Icons/*.png"))]

icon_themes = ["hicolor", "ubuntu-mono-dark", "ubuntu-mono-light"]
for theme in icon_themes:
    data_files.extend([(os.path.join("/usr/share/icons/", theme,
        os.path.relpath(dir, "Icons/" + theme)), [os.path.join(dir, file)
        for file in files])
        for dir, subdirs, files in os.walk("Icons/" + theme) if files])

setup(name='indicator-stickynotes',
        version='0.1',
        description='Sticky Notes AppIndicator',
        author='Umang Varma',
        author_email='umang.me@gmail.com',
        url='https://www.launchpad.net/indicator-stickynotes/',
        packages=['stickynotes',],
        scripts=['indicator-stickynotes.py',],
        data_files=data_files)
