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
import uuid
import json
from os.path import expanduser

class Note:
    def __init__(self, content=None, gui_class=None, noteset=None):
        content = content or {}
        self.uuid = content.get('uuid')
        self.body = content.get('body','')
        self.properties = content.get("properties", {})
        last_modified = content.get('last_modified')
        if last_modified:
            self.last_modified = datetime.strptime(last_modified,
                    "%Y-%m-%dT%H:%M:%S")
        else:
            self.last_modified = datetime.now()
        self.gui_class = gui_class
        self.noteset = noteset
        self.gui = self.gui_class(note=self)

    def extract(self):
        self.gui.update_note()
        if not self.uuid:
            self.uuid = str(uuid.uuid4())
        self.properties = self.gui.properties()
        return {"uuid":self.uuid, "body":self.body,
                "last_modified":self.last_modified.strftime(
                    "%Y-%m-%dT%H:%M:%S"), "properties":self.properties}

    def update(self,body=None):
        if not body == None:
            self.body = body
            self.last_modified = datetime.now()

    def delete(self):
        self.noteset.notes.remove(self)
        self.noteset.save()
        del self

    def show(self, *args):
        self.gui.show(*args)

    def hide(self):
        self.gui.hide()


class NoteSet:
    def __init__(self, gui_class, data_file):
        self.notes = []
        self.properties = {}
        self.gui_class = gui_class
        self.data_file = data_file

    def _loads_updater(self, dnoteset):
        """Parses old versions of the Notes structure and updates them"""
        return dnoteset

    def loads(self, snoteset):
        """Loads notes into their respective objects"""
        try:
            notes = self._loads_updater(json.loads(snoteset))
        except ValueError:
            notes = {}
        self.properties = notes.get("properties", {})
        self.notes = [Note(note, gui_class=self.gui_class, noteset=self)
                for note in notes.get("notes",[])]

    def dumps(self):
        return json.dumps({"notes":[x.extract() for x in self.notes],
            "properties": self.properties})

    def save(self, path=''):
        output = self.dumps()
        with open(path or expanduser(self.data_file),
                mode='w', encoding='utf-8') as fsock:
            fsock.write(output)

    def open(self, path=''):
        try:
            with open(path or expanduser(self.data_file), 
                    encoding='utf-8') as fsock:
                self.loads(fsock.read())
        except IOError:
            self.loads('{}')
            self.new()

    def new(self):
        """Creates a new note and adds it to the note set"""
        note = Note(gui_class=self.gui_class, noteset=self)
        self.notes.append(note)
        note.show()
        return note

    def showall(self, *args):
        for note in self.notes:
            note.show(*args)
        self.properties["all_visible"] = True

    def hideall(self, *args):
        self.save()
        for note in self.notes:
            note.hide(*args)
        self.properties["all_visible"] = False

class dGUI:
    def __init__(self, *args, **kwargs):
        pass
    """Dummy GUI"""
    def show(self):
        pass
    def hide(self):
        pass
    def update_note(self):
        pass
    def properties(self):
        return None

