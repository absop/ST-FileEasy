from .log import *
from .sidebar import *
from .tabbar import *
from .open_context_path import *


def plugin_loaded():
    def reload_settings():
        format = settings.get('tabbar_clone_file.number_format', '{}')
        TabBarCloneFileCommand.number_format = format

    settings = sublime.load_settings('FileEasy.sublime-settings')
    settings.clear_on_change('tabbar_clone_file.number_format')
    settings.add_on_change('tabbar_clone_file.number_format', reload_settings)
    reload_settings()
