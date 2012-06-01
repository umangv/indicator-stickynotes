from datetime import datetime
import uuid
import json
from os.path import expanduser

SETTINGS_FILE = "stickynotesrc"

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
        self.gui = None
        self.noteset = noteset

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
        if not self.gui:
            self.gui = self.gui_class(note=self)
        self.gui.show(*args)

    def hide(self):
        self.gui.hide()


class NoteSet:
    def __init__(self, gui_class):
        self.notes = []
        self.gui_class = gui_class

    def _loads_updater(self, dnoteset):
        """Parses old versions of the Notes structure and updates them"""
        return dnoteset

    def loads(self, snoteset):
        """Loads notes into their respective objects"""
        notes = self._loads_updater(json.loads(snoteset))
        self.notes = [Note(note, gui_class=self.gui_class, noteset=self)
                for note in notes.get("notes",[])]

    def dumps(self):
        return json.dumps({"notes":[x.extract() for x in self.notes]})

    def save(self, path=''):
        with open(path or expanduser("~/.{0}".format(SETTINGS_FILE)),
                mode='w', encoding='utf-8') as fsock:
            fsock.write(self.dumps())

    def open(self, path=''):
        with open(path or expanduser("~/.{0}".format(SETTINGS_FILE)), 
                encoding='utf-8') as fsock:
            self.loads(fsock.read())

    def new(self):
        """Creates a new note and adds it to the note set"""
        note = Note(gui_class=self.gui_class, noteset=self)
        self.notes.append(note)
        note.show()
        return note

    def showall(self, *args):
        for note in self.notes:
            note.show(*args)

    def hideall(self, *args):
        self.save()
        for note in self.notes:
            note.hide(*args)

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

