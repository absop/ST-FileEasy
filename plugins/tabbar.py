import os
import re
import shutil
import functools

import sublime
import sublime_plugin


class TabBarCopyFileNameCommand(sublime_plugin.WindowCommand):
    def run(self, group, index):
        branch, leaf = os.path.split(self.path)
        sublime.set_clipboard(leaf)

    def is_visible(self, group, index):
        view = self.window.views_in_group(group)[index]
        self.path = view.file_name()
        return self.path is not None


class TabBarFileCommand(sublime_plugin.WindowCommand):
    def is_visible(self, group, index):
        self.view = self.window.views_in_group(group)[index]
        self.path = self.view.file_name()
        return self.path is not None and os.path.exists(self.path)

    def is_enabled(self, group, index):
        return self.is_visible(group, index)


class TabBarNewFileCommand(TabBarFileCommand):
    def run(self, group, index):
        branch, leaf = os.path.split(self.path)
        v = self.window.show_input_panel(
            "File Name",
            leaf,
            functools.partial(self.on_done, branch),
            None, None)
        v.sel().clear()
        v.sel().add(sublime.Region(0, len(os.path.splitext(leaf)[0])))

    def on_done(self, dir, name):
        open(os.path.join(dir, name), "a").close()
        self.window.open_file(os.path.join(dir, name))


class TabBarCopyFilePathCommand(TabBarFileCommand):
    def is_visible(self, group, index):
        self.view = self.window.views_in_group(group)[index]
        self.path = self.view.file_name()
        return self.path is not None

    def run(self, group, index):
        sublime.set_clipboard(self.path)


class TabBarOpenContainedFolderCommand(TabBarFileCommand):
    def run(self, group, index):
        branch, leaf = os.path.split(self.path)
        self.window.run_command("open_dir", {"dir": branch, "file": leaf})


class TabBarSaveFileCommand(TabBarFileCommand):
    def run(self, group, index):
        dir = os.path.dirname(self.path)
        if not os.path.exists(dir):
            os.makedirs(dir)
        self.view.run_command("save")

    def is_visible(self, group, index):
        self.view = self.window.views_in_group(group)[index]
        self.path = self.view.file_name()
        if self.path is None:
            return False
        return not os.path.exists(self.path) or self.view.is_dirty()


class TabBarRenameFileCommand(TabBarFileCommand):
    def run(self, group, index):
        self.window.run_command("rename_path", {"paths": [self.path]})


class TabBarDeleteFileCommand(TabBarFileCommand):
    def run(self, group, index):
        name = os.path.basename(self.path).center(64)
        delete = sublime.ok_cancel_dialog(
            "Are you sure you want to delete?\n\n" + name,
            "Delete")

        if delete and self.view.close():
            import Default.send2trash as send2trash
            try:
                send2trash.send2trash(self.path)
            except:
                msg = "Unable to delete file: " + self.path
                sublime.status_message(msg)


class TabBarCopyFileCommand(TabBarFileCommand):
    def run(self, group, index):
        self.window.run_command("side_bar_copy_files", {"paths": [self.path]})


class TabBarMoveFileCommand(TabBarFileCommand):
    def run(self, group, index):
        self.window.run_command("side_bar_move_files", {"paths": [self.path]})


class TabBarCloneFileCommand(TabBarFileCommand):
    number_format = "{}"

    def run(self, group, index):
        new_path = self.get_new_path(self.path, self.number_format)
        shutil.copy(self.path, new_path)
        self.window.open_file(new_path)

    def get_new_path(self, path, format):
        dirname, filename = os.path.split(path)
        base_name, extension = os.path.splitext(filename)
        if extension:
            formal, number = self.split_suffixal_number(base_name, format)
            prefix = os.path.join(dirname, formal)
            strnum = format.format
            while os.path.exists(prefix + strnum(number) + extension):
                number += 1
            return prefix + strnum(number) + extension
        # For files with no extension, such as `.vimrc`, `.bashrc`,
        # we simply return the filename itself with the `.bk` suffix
        else:
            return path + '.bk'

    def split_suffixal_number(self, base_name, format):
        # If no matching number is found, then return 1
        number = 1
        formal = base_name
        regexp = r'(?P<number>\d+)'.join(map(re.escape, format.split('{}')))
        for match in re.finditer(regexp, base_name):
            groups = match.groupdict()
            number = int(groups['number'])
            formal = base_name[:match.span()[0]]
        return formal, number

