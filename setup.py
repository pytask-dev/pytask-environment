from setuptools import find_packages
from setuptools import setup

import versioneer

setup(
    name="pytask-environment",
    version=versioneer.get_version(),
    cmd_class=versioneer.get_cmdclass(),
    description="Detect changes in your pytask environment and abort a project build.",
    author="Tobias Raabe",
    author_email="raabe@posteo.de",
    python_requires=">=3.6",
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    platforms="any",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    entry_points={"pytask": ["pytask_environment = pytask_environment.plugin"]},
    zip_false=True,
)
