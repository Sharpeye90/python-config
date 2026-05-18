"""python-config installation script."""

from pathlib import Path

from setuptools import setup
from setuptools.command.test import test as Test


class PyTest(Test):
    def finalize_options(self):
        Test.finalize_options(self)
        self.test_args = [ "tests" ]
        self.test_suite = True

    def run_tests(self):
        import pytest
        pytest.main(self.test_args)


if __name__ == "__main__":
    readme = Path("README").read_text()
    version = Path("version.txt").read_text().strip()

    setup(
        name = "python-config",
        version = version,

        description = readme.split("\n", 1)[0],
        long_description = readme,
        url = "https://github.com/KonishchevDmitry/python-config",

        license = "GPL3",
        author = "Dmitry Konishchev",
        author_email = "konishchev@gmail.com",

        classifiers = [
            "Development Status :: 5 - Production/Stable",
            "Intended Audience :: Developers",
            "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
            "Operating System :: MacOS :: MacOS X",
            "Operating System :: POSIX",
            "Operating System :: Unix",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "Programming Language :: Python :: Implementation :: CPython",
        ],
        platforms = [ "unix", "linux", "osx" ],

        packages = [ "python_config" ],

        cmdclass = { "test": PyTest },
        tests_require = [ "pytest" ],
    )
