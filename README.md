Canaveral: Quickly find and open applications and files
================================================================

![Canaveral logo](https://raw.githubusercontent.com/joshburnett/canaveral/main/resources/rocket_with_shadow_blue_256px.png "Canaveral")

* Blazing fast search: Indexes folders you specify, cataloging files and subdirectories matching your specified filters
* Globally available via a user-configurable hotkey
* Learns your preferences, bringing previously-opened files and applications to the top of search results

Getting started
---------------

### Installation & configuration

1. Install via `pip install canaveral`. Installing in a virtual environment is recommended.
2. Run from the command line: `canaveral`
3. Canaveral looks in %APPDATA%\Canaveral for a file called paths.py that defines the locations and extensions it should index. An example is provided, called paths-example.py. Modify this file to suit your needs and save it as paths.py, in the canaveral source directory. (In future releases, this file will be moved to a more appropriate user-specific location.)

### Running Canaveral
1. Activate your virtual environment, and run Canaveral from the command line via `python main.py`. **Tip:** You can also launch Canaveral from a Windows shortcut if you put the full path to the virtual environment's python location and to main.py as the Target, and the Canaveral directory as the working directory (the 'Start In' location). If you put this shortcut in your Startup directory, it will launch Canaveral on Windows startup.
2. Bring up the Canaveral window with the Ctrl+Alt+Space hotkey.
3. Start typing your search.
4. Select your desired entry from the drop-down list (via keyboard or mouse) and press enter. If no entry is selected, the first item in the list will be launched (so there's no need to select it).

Releases
--------
### 0.1: 2021-09-xx

- First public release
