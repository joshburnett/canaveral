# Modify this to suit your needs and save it as paths.py.  search_path_entries is loaded
# at startup by main.py and used to populate the search catalog.

from pathlib import Path
import winpath
from canaveral.basemodels import SearchPathEntry

search_path_entries = [
    # Office-type documents and directories in the user's Documents directory
    # (using winpath because the Documents directory's location can change)
    SearchPathEntry(path=Path(winpath.get_my_documents()), search_depth=10,
                    patterns=['.dir', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.pdf',
                              '.txt', '.vsd', '.vsdx']),

    # Subdirectories of the user's home directory
    SearchPathEntry(path=Path(r'~').expanduser(), patterns=['.dir']),

    # User-specific start menu items
    SearchPathEntry(path=Path(winpath.get_programs()), patterns=['*.lnk'], search_depth=3),

    # Start menu items for all users
    SearchPathEntry(path=Path(r'C:\ProgramData\Microsoft\Windows\Start Menu\Programs'), patterns=['*.lnk'],
                    search_depth=3)
]
