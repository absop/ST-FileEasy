from .log import *
from .sidebar import *
from .tabbar import *
from .open_context_path import *


def plugin_loaded():
    def reload_settings():
        TabBarCloneFileCommand.number_format = settings.get(
            'TabBarCloneFileCommand.number_format', '{}')

        SideBarOpenFolderInTerminalCommand.command = settings.get(
            'SideBarOpenFolderInTerminalCommand.commands', {}).get(
                sublime.platform(), "")

    settings = sublime.load_settings('FileEasy.sublime-settings')
    settings.clear_on_change('tabbar_clone_file.number_format')
    settings.add_on_change('tabbar_clone_file.number_format', reload_settings)
    reload_settings()
