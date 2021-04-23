import os

import sublime
import sublime_plugin
try:
    from log import Loger
except:
    from .log import Loger


class OpenContextPathCommand(sublime_plugin.TextCommand):
    def run(self, edit, event=None):
        # key pressed
        if event is None:
            paths = set()
            for sel in self.view.sel():
                if self.find_path(sel):
                    paths.add(self.path)
            for path in list(paths)[:5]:
                self.open_path(path)
        # menu selected
        else:
            self.open_path(self.path)

    def open_path(self, path):
        if os.path.isfile(path):
            Loger.print("open file: " + path)
            self.view.window().open_file(path)
        elif os.path.isdir(path):
            Loger.print("open folder: " + path)
            self.view.window().run_command("open_dir", {"dir": path})

    def is_visible(self, event):
        return self.path is not None

    def find_path(self, region):
        if isinstance(region, sublime.Region) and region.empty():
            region = region.a
        if isinstance(region, int):
            region = self.view.extract_scope(region)

        selected_content = self.view.substr(region)
        path = selected_content.strip('\'"')
        if os.path.exists(path):
            self.path = path
            return path

        # Maybe consider addind settings to config searching diractories.
        file = path.lstrip('\\/')
        dirs = [sublime.packages_path()]
        if self.view.file_name():
            dirs.insert(0, os.path.dirname(self.view.file_name()))

        for d in dirs:
            path = os.path.join(d, file).replace('\\', '/')
            if file and os.path.exists(path):
                self.path = path
                return file
        return None

    def description(self, event):
        self.path = None
        if self.view.has_non_empty_selection_region():
            region = self.view.sel()[0]
        else:
            region = self.view.window_to_text((event["x"], event["y"]))
        file = self.find_path(region)
        if file is not None:
            if os.path.isfile(self.path):
                open_cmd = "Open File: "
            elif os.path.isdir(self.path):
                open_cmd = "Open Folder: "
            if len(file) > 56:
                file = file[0:56] + "..."
            return open_cmd + file
        return ""

    def want_event(self):
        return True
