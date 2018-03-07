#!/usr/bin/env python

"""
Autoreloader using watchdog
"""

import sys
import os
import time
import logging
import importlib
import os.path
import py
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


log = logging.getLogger(__name__)


def in_directory(file, directory):
    #make both absolute
    directory = os.path.join(os.path.realpath(directory), '')
    file = os.path.realpath(file)

    #return true, if the common prefix of both is equal to directory
    #e.g. /a/b/c/d.rst and directory is /a/b, the common prefix is /a/b
    return os.path.commonprefix([file, directory]) == directory


def load_module_or_path(module_or_path):
    module = None
    module_path = None

    if hasattr(module_or_path, '__file__'):
        module = module_or_path
        module_path = module.__file__
    else:
        try:
            module = importlib.import_module(module_or_path)
            module_path = os.path.abspath(os.path.dirname(module.__file__))
        except:
            local_path = py.path.local(module_or_path)
            if local_path.exists():
                module = None
                try:
                    module = local_path.pyimport()
                except AttributeError:
                    pass
                module_path = module_or_path

    return module, module_path


def execute_reload(module, *callbacks):
    if module:
        try:
            importlib.reload(module)
            log.info('reloading %s', module.__name__)
        except Exception as e:
            log.error(e)

        reload_function = module.__dict__.get('__reload__')
        if reload_function:
            reload_function()

    for cb in callbacks:
        try:
            cb()
        except Exception as e:
            log.error(e)


_enable_self_reload = False
observer = Observer()


class EventHandler(FileSystemEventHandler):
    def __init__(self, path, *callbacks):
        self.module, self.module_path = load_module_or_path(path)
        print(self.module, self.module_path)
        self.callbacks = callbacks

    def on_modified(self, event):
        # only handle event if it's a file
        # ignore directories
        if py.path.local(event.src_path).isfile():
            execute_reload(self.module, *self.callbacks)


def add(path, *callbacks):
    module, module_path = load_module_or_path(path)
    handler = EventHandler(module_path, *callbacks)

    # we listen on the directory, even if it's a file
    observer.schedule(handler, py.path.local(module_path).dirname, recursive=True)


def start(enable_self_reload=False):
    global _enable_self_reload
    _enable_self_reload = enable_self_reload

    observer.start()
    if enable_self_reload:
        add(py.path.local(__file__).dirname, reload)


def stop():
    observer.stop()


def reload(callback=None):
    log.info('reload autoreload')
    stop()
    global observer
    observer = Observer()
    if callback: callback()
    start(_enable_self_reload)


def main():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    paths = sys.argv[1:]

    def reload_with_params():
        [add(path, lambda: (print('event'), reload(reload_with_params))) for path in paths]

    reload_with_params()
    # add events

    print('==> Start monitoring (type c^c to exit) <==')
    start(enable_self_reload=True)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print('exception')
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
