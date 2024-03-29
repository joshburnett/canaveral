# -*- coding: utf-8 -*-

import ctypes
from ctypes import windll
from PySide6.QtGui import QKeySequence
from PySide6.QtCore import Qt

from .keycodes import KeyTbl, ModsTbl


def keys_from_string(keys):
    keysequence = QKeySequence(keys)
    ks = keysequence[0]

    mods = ModsTbl.index(ks.keyboardModifiers())

    return mods, ks.key().value

    # Old method that works for PySide 6 6.0-6.3
    # # Calculate the modifiers
    # mods = Qt.NoModifier
    # qtmods = Qt.NoModifier
    # if ks & Qt.ShiftModifier == Qt.ShiftModifier:
    #     mods |= ModsTbl.index(Qt.ShiftModifier)
    #     qtmods |= int(Qt.ShiftModifier)  # PySide
    # if ks & Qt.AltModifier == Qt.AltModifier:
    #     mods |= ModsTbl.index(Qt.AltModifier)
    #     qtmods |= int(Qt.AltModifier)
    # if ks & Qt.ControlModifier == Qt.ControlModifier:
    #     mods |= ModsTbl.index(Qt.ControlModifier)
    #     qtmods |= int(Qt.ControlModifier)
    #
    # # import ipdb
    # # ipdb.set_trace()
    #
    # # Calculate the keys
    # qtkeys = ks ^ int(qtmods)
    # try:
    #     keys = KeyTbl[qtkeys]
    #     if keys == 0:
    #         keys = _get_virtual_key(qtkeys)
    # except ValueError:
    #     keys = _get_virtual_key(qtkeys)
    # except IndexError:
    #     keys = KeyTbl.index(qtkeys)
    #     if keys == 0:
    #         keys = _get_virtual_key(qtkeys)
    #
    # return mods, keys


def _get_virtual_key(qtkeys):
    """Use the system keyboard layout to retrieve the virtual key.

    Fallback when we're unable to find a keycode in the mappings table.
    """
    user32 = ctypes.WinDLL('user32', use_last_error=True)
    thread_id = 0

    # Key table doesn't have an entry for this keycode
    # Attempt to retrieve the VK code from system
    keyboard_layout = user32.GetKeyboardLayout(thread_id)
    virtual_key = windll.user32.VkKeyScanExW(qtkeys, keyboard_layout)
    if virtual_key == -1:
        keyboard_layout = user32.GetKeyboardLayout(0x409)
        virtual_key = windll.user32.VkKeyScanExW(qtkeys, keyboard_layout)
    # Key code is the low order byte
    keys = virtual_key & 0xff

    return keys
