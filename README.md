Canaveral: Quickly find and open applications and files
================================================================

![Canaveral logo](resources/rocket_with_shadow_blue.png "Canaveral")

* Indexes folders you specify, cataloging files and subdirectories matching your specified filters
* Globally available via a user-configurable hotkey
* Blazing fast search
* Learns your preferences, bringing previously-opened files and applications to the top of search results

Getting started
---------------

### Installation

1. In future releases, we will be adding an entry point to the canaveral package, allowing you to start Canaveral by simply running `canaveral` on the command line, and to easily install it with the [`pipx`](https://pypa.github.io/pipx/installation/) package. This is not ready yet. So, on to step 2 for now.
2. Create a virtual environment for canaveral.
3. Clone or copy the Canaveral source code directory locally.
4. Install Canaveral's dependencies by running `pip install -r requirements.txt` in your local copy of Canaveral's source directory.

### Configuration
1. Canaveral looks for a file called paths.py that defines the locations and extensions it should index. An example is provided, called paths-example.py. Modify this file to suit your needs and save it as paths.py, in the canaveral source directory. (In future releases, this file will be moved to a more appropriate user-specific location.)

### Running Canaveral
1. Activate your virtual environment, and run Canaveral from the command line via `python main.py`. **Tip:** You can also launch Canaveral from a Windows shortcut if you put the full path to the virtual environment's python location and to main.py as the Target, and the Canaveral directory as the working directory (the 'Start In' location). If you put this shortcut in your Startup directory, it will launch Canaveral on Windows startup.
2. Bring up the Canaveral window with the Ctrl+Alt+Space hotkey.
3. Start typing your search.
4. Select your desired entry from the drop-down list (via keyboard or mouse) and press enter. If no entry is selected, the first item in the list will be launched (so there's no need to select it).

Releases
--------
### 0.1: 2021-09-xx

- First public release
