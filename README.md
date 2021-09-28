Canaveral: Quickly find and open applications and files
================================================================

![Canaveral logo](https://raw.githubusercontent.com/joshburnett/canaveral/main/canaveral/resources/rocket_with_shadow_blue_256px.png "Canaveral")

* Blazing fast search: Indexes folders you specify, cataloging files and subdirectories matching your specified filters
* Globally available via a user-configurable hotkey
* Learns your preferences, bringing previously-opened files and applications to the top of search results

Installation
---------------

You can install Canaveral in (at least) two different ways, depending on your needs:

1. Install in an isolated virtual environment from PyPI via [`pipx`](https://pypa.github.io/pipx/). This path is generally recommended for normal usage.
2. Create your own virtual environment, clone the Canaveral git repo, and install Canaveral in 'dev mode' with `pip install -e` (also known as 'editable' mode). This path is recommended for development.

### Installation via `pipx`

1. Install pipx first, if you don't already have pipx installed. Simply run the following commands at the terminal:

```shell
python -m pip install --user pipx
python -m pipx ensurepath
```

2. After installing `pipx`, you'll need to log out and log back in so that it will be added to your path.

3. Use `pipx` to install Canaveral from PyPI. `pipx` will automatically create an isolated virtual environment and install Canaveral into it from PyPI:

```shell
pipx install canaveral
```

### Installation via `pip` from a local copy of the repo, in 'editable' mode

1. Create a virtual environment and activate it. If you're choosing this path, we'll assume you already know how to do this.
2. Install Canaveral into the virtual environment in 'editable' mode by running the following command from the canaveral source directory (where setup.py is located):

```shell
pip install -e .
```

Running Canaveral
-----------------

1. If you've installed Canaveral into your own virtual environment, you'll need to activate it first. You can skip this step if you installed Canaveral via `pipx`.
2. Run from the command line: `canaveral`.
3. Canaveral looks in %APPDATA%\Canaveral for a file called paths.py that defines the locations and extensions it should index. The first time you run Canaveral, this directory is created and a paths.py with the default search locations will be placed there. Modify this file to suit your needs and save it in place, as paths.py.
4. Bring up the Canaveral window with the Ctrl+Alt+Space hotkey.
5. Start typing your search.
6. Select your desired entry from the drop-down list (via keyboard or mouse) and press enter. If no entry is selected, the first item in the list will be launched (so there's no need to select it).
7. As you search for items and launch them, Canaveral will remember your choices and place the launched items at the top of the results for relevant searches.

### Alternate ways to launch Canaveral
1. If you are interested in developing Canaveral and have installed it via the `pip install -e .` method above, you can directly launch Canaveral from its source directory by activating the virtual environment and then running the `main.py` file directly:

```shell
python main.py
```

2. You can also launch Canaveral from a Windows shortcut if you put the full path to the virtual environment's python location and to main.py as the Target, and the Canaveral directory as the working directory (the 'Start In' location). If you put this shortcut in your Startup directory, it will launch Canaveral on Windows startup.

Releases
--------
### 0.0.1: 2021-09-xx

- First public release
