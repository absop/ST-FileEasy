import os
import shutil
import traceback

import sublime
import sublime_plugin
from Default import send2trash
try:
    from log import Loger
except:
    from .log import Loger


def contains_or_equals_to(source_path, target_dir):
    target_dir = target_dir.replace('\\', '/')
    source_path = source_path.replace('\\', '/')
    return target_dir.startswith(source_path)


class CopyTask(object):
    __available = True
    during_word = 'Copying'
    ending_word = 'copyed'

    @classmethod
    def is_available(cls):
        return cls.__available

    @classmethod
    def require(cls):
        cls.__available = False

    @classmethod
    def release(cls):
        cls.__available = True

    def __init__(self, origin_paths):
        self.valid = True
        self.origin_paths = origin_paths

    def is_valid_target_dir(self, target_dir):
        for origin_path in self.origin_paths:
            if contains_or_equals_to(origin_path, target_dir):
                return False
        return True

    def start(self, target_dir):
        CopyTask.require()
        self.target_dir = target_dir
        self.origin_paths_iterator = iter(self.origin_paths)
        self.execute_path_by_path()

    def finish(self):
        pass

    def execute_path_by_path(self):
        try:
            origin_path = next(self.origin_paths_iterator)
            if os.path.exists(origin_path):
                self.checked_execute_at(origin_path)
            else:
                Loger.error("No such file or directory:", origin_path)
        except:
            self.finish()
            CopyTask.release()

    def checked_execute_at(self, origin):
        def handle_file_name(file_name):
            target = os.path.join(self.target_dir, file_name)
            skip = replace = False
            if os.path.exists(target):
                msg = "{} already exists in the directory:\n{}\n".format(
                    file_name, self.target_dir)
                skip = sublime.ok_cancel_dialog(msg, ok_title="skip it?")
                if not skip:
                    opt = sublime.yes_no_cancel_dialog(msg,
                        yes_title="Save with new name", no_title="Replace")

                    if opt == sublime.DIALOG_CANCEL:
                        raise "Task Canceled"

                    if opt == sublime.DIALOG_YES:
                        panel = sublime.active_window().show_input_panel(
                            "Input a new file name",
                            file_name, handle_file_name, None, None)
                        panel.sel().clear()
                        panel.sel().add(sublime.Region(0, len(file_name)))
                        return

                    skip = target == origin
                    replace = not skip
            if not skip:
                if replace:
                    self.send2trash(target)
                self.threading_execute(origin, target)
            else:
                self.execute_path_by_path()
        handle_file_name(os.path.basename(origin))

    def send2trash(self, path):
        path_relative_to_project = Loger.relative_path(path)
        try:
            Loger.print('Trying to remove: "%s"' % path_relative_to_project)
            send2trash.send2trash(path)
            Loger.print('succeed in removing: "%s"' % path_relative_to_project)
        except:
            Loger.error('Failed to remove: "%s"' % path_relative_to_project)
            raise "Task Failed"

    def during_message(self, origin, target):
        return '%s "%s" to "%s"' % (self.during_word, origin, target)

    def ending_message(self, origin, target):
        return '"%s" is %s to "%s"' % (origin, self.ending_word, target)

    def threading_execute(self, origin, target):
        _origin = Loger.relative_path(origin)
        _target = Loger.relative_path(target)
        Loger.threading(
            lambda: self._execute(origin, target),
            self.during_message(_origin, _target),
            self.ending_message(_origin, _target),
            self.execute_path_by_path)

    def _execute(self, origin, target):
        try:
            self.execute(origin, target)
        except:
            traceback.print_exc()

    def execute(self, origin, target):
        if os.path.isdir(origin):
            shutil.copytree(origin, target)
        else:
            shutil.copy2(origin, target)


class MoveTask(CopyTask):
    during_word = 'Moving'
    ending_word = 'moved'

    def finish(self):
        self.valid = False

    def execute(self, origin, target):
        def retarget_views(origin, target):
            for window in sublime.windows():
                for view in window.views():
                    path = view.file_name() or ""
                    if path.startswith(origin):
                        view.retarget(target + path[len(origin):])
        shutil.move(origin, target)
        retarget_views(origin, target)


class SideBarPasteFilesCommand(sublime_plugin.WindowCommand):
    task = None

    @classmethod
    def accept(cls, task):
        cls.task = task

    def run(self, paths):
        target_dir = paths[0]
        if os.path.isdir(target_dir):
            self.task.start(target_dir)

    def is_visible(self, paths):
        target_dir = paths[0]
        if self.task and self.task.valid and len(paths) == 1:
            if os.path.exists(target_dir):
                return os.path.isdir(target_dir)
            else:
                msg = "No such file or directory: " + target_dir
                sublime.status_message(msg)
        return False

    def is_enabled(self, paths):
        if self.is_visible(paths):
            return self.task.is_valid_target_dir(paths[0])
        return False


class SideBarCopyFilesCommand(sublime_plugin.WindowCommand):
    Task = CopyTask

    def run(self, paths):
        task = self.Task([p for p in paths if os.path.exists(p)])
        SideBarPasteFilesCommand.accept(task)

    def is_visible(self, paths):
        if CopyTask.is_available():
            return len(paths) > 0 and os.path.exists(paths[0])
        return False

    def is_enabled(self, paths):
        if self.is_visible(paths):
            for i in range(len(paths)):
                for j in range(i + 1, len(paths)):
                    pi, pj = paths[i], paths[j]
                    if (os.path.dirname(pj).startswith(pi) or
                        os.path.dirname(pi).startswith(pj)):
                        return False
            return True
        return False


class SideBarMoveFilesCommand(SideBarCopyFilesCommand):
    Task = MoveTask


class SideBarOpenFilesCommand(sublime_plugin.WindowCommand):
    def run(self, paths):
        for path in paths:
            if os.path.isfile(path):
                self.window.open_file(path)

    def is_visible(self, paths):
        if int(sublime.version()) < 4000 and len(paths) > 1:
            for path in paths:
                if os.path.isfile(path):
                    return True
        return False


class SideBarOpenFolderInExplorerCommand(sublime_plugin.WindowCommand):
    def is_visible(self, paths):
        return len(paths) == 1 and os.path.isdir(paths[0])

    def run(self, paths):
        self.window.run_command("open_dir", {"dir": paths[0]})


class SideBarOpenFolderInNewWindowCommand(sublime_plugin.WindowCommand):
    def is_visible(self, paths):
        return len(paths) == 1 and os.path.isdir(paths[0])

    def run(self, paths):
        self.window.run_command("new_window")
        window = sublime.active_window()
        window.set_project_data({'folders': [{'path': path} for path in paths]})
