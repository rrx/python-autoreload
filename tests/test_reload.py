import pytest
import autoreload
import os
import sys
import time
from autoreload import load_module_or_path
import threading
import py


def touch_file(fn):
    open(fn, 'a').close()


def set_variable_in_python_file(filename, value):
    with open(filename, 'w') as fp:
        fp.write("X=%s" % value)


@pytest.fixture(scope='session')
def setup(tmpdir):
    print(tmpdir)
    os.chdir(tmpdir)
    os.makedirs(tmpdir.join("testmodule/directorymodule/"), exist_ok=True)
    os.makedirs(tmpdir.join("testmodule/directorymodule/"), exist_ok=True)
    touch_file(os.path.join(tmpdir, "testmodule/directorymodule/__init__.py"))
    touch_file(os.path.join(tmpdir, "testmodule/__init__.py"))
    touch_file(os.path.join(tmpdir, "testmodule/directorymodule/filemodule.py"))
    touch_file(os.path.join(tmpdir, "testmodule/filemodule.py"))
    touch_file(os.path.join(tmpdir, "testmodule/directorymodule/test.html"))

    sys.path.insert(0, "%s" % tmpdir)
    autoreload.start()


def teardown_module(module):
    autoreload.stop()


def test_import(tmpdir):
    setup(tmpdir)
    print(sys.path)
    os.chdir(tmpdir)
    m = tmpdir.join("testmodule").pyimport()

    # import and make sure we have a valid path in the right place
    import testmodule
    assert(testmodule.__file__ == tmpdir.join("testmodule/__init__.py").strpath)

    import testmodule.directorymodule
    from testmodule import filemodule
    import testmodule.directorymodule.filemodule

    m, mp = load_module_or_path(testmodule)
    # make sure file returned
    assert(py.path.local(mp).exists())

    event = threading.Event()

    def set_and_check(module, value):
        event.clear()
        set_variable_in_python_file(module.__file__, value)
        time.sleep(1)
        assert(event.wait(10))
        event.clear()

        current_value = getattr(module, 'X', None)
        assert (current_value == value)

    def callback():
        print('set')
        event.set()

    autoreload.add(testmodule, callback)
    set_and_check(testmodule, 0)

    autoreload.add("testmodule", callback)
    set_and_check(testmodule, 1)

    autoreload.add(testmodule.directorymodule, callback)
    set_and_check(testmodule.directorymodule, 2)

    autoreload.add(filemodule, callback)
    set_and_check(filemodule, 3)
