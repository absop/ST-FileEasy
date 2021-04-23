import webbrowser
import sublime_plugin

from .plugins import *


class FileEasyEventListener(sublime_plugin.EventListener):
    def on_load(self, view):
        file_path = view.file_name()
        extensions = ['.pdf']
        for ext in extensions:
            if file_path and file_path.endswith(ext):
                webbrowser.open_new_tab(file_path)
                # view.close()
                return
