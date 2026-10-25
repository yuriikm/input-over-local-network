import socket
import ctypes
import sys

# --- PORT CONFIGURATION ---
LISTEN_IP = "0.0.0.0"  
LISTEN_PORT = 5005

# --- WIN32 API STRUCTURES & CONSTANTS ---
INPUT_MOUSE    = 0
INPUT_KEYBOARD = 1

MOUSEEVENTF_MOVE     = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP   = 0x0004
MOUSEEVENTF_RIGHTDOWN= 0x0008
MOUSEEVENTF_RIGHTUP  = 0x0010
MOUSEEVENTF_MIDDLEDOWN=0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_WHEEL    = 0x0800

KEYEVENTF_KEYUP       = 0x0002
KEYEVENTF_SCANCODE    = 0x0008
KEYEVENTF_EXTENDEDKEY = 0x0001  

LONG = ctypes.c_long
DWORD = ctypes.c_ulong
ULONG_PTR = ctypes.c_ulonglong if sys.maxsize > 2**32 else ctypes.c_ulong

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", LONG), ("dy", LONG), ("mouseData", DWORD), 
                ("dwFlags", DWORD), ("time", DWORD), ("dwExtraInfo", ULONG_PTR)]

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort), ("wScan", ctypes.c_ushort), 
                ("dwFlags", DWORD), ("time", DWORD), ("dwExtraInfo", ULONG_PTR)]

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [("uMsg", DWORD), ("wParamL", ctypes.c_ushort), ("wParamH", ctypes.c_ushort)]

class INPUT_UNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT)]

class INPUT(ctypes.Structure):
    _fields_ = [("type", DWORD), ("u", INPUT_UNION)]

# --- LINUX KERNEL CODE TO WINDOWS SCANCODE MAPPING ---
LINUX_TO_WIN_SCANCODE = {
    1: (0x01, False),   # ESC
    2: (0x02, False), 3: (0x03, False), 4: (0x04, False), 5: (0x05, False), 
    6: (0x06, False), 7: (0x07, False), 8: (0x08, False), 9: (0x09, False), 
    10: (0x0A, False), 11: (0x0B, False), 
    12: (0x0C, False),  # MINUS
    13: (0x0D, False),  # EQUAL
    14: (0x0E, False),  # BACKSPACE
    15: (0x0F, False),  # TAB
    16: (0x10, False), 17: (0x11, False), 18: (0x12, False), 19: (0x13, False), 
    20: (0x14, False), 21: (0x15, False), 22: (0x16, False), 23: (0x17, False), 
    24: (0x18, False), 25: (0x19, False), 
    26: (0x1A, False),  # LEFTBRACE
    27: (0x1B, False),  # RIGHTBRACE
    28: (0x1C, False),  # ENTER
    29: (0x1D, False),  # LEFTCTRL
    30: (0x1E, False), 31: (0x1F, False), 32: (0x20, False), 33: (0x21, False), 
    34: (0x22, False), 35: (0x23, False), 36: (0x24, False), 37: (0x25, False), 
    38: (0x26, False), # A-L
    39: (0x27, False),  # SEMICOLON
    40: (0x28, False),  # APOSTROPHE
    41: (0x29, False),  # GRAVE/TILDE
    42: (0x2A, False),  # LEFTSHIFT
    43: (0x2B, False),  # BACKSLASH
    44: (0x2C, False), 45: (0x2D, False), 46: (0x2E, False), 47: (0x2F, False), 
    48: (0x30, False), 49: (0x31, False), 50: (0x32, False), # Z-M
    51: (0x33, False),  # COMMA
    52: (0x34, False),  # DOT
    53: (0x35, False),  # SLASH
    54: (0x36, False),  # RIGHTSHIFT
    55: (0x37, False),  # KPASTERISK
    56: (0x38, False),  # LEFTALT
    57: (0x39, False),  # SPACE
    58: (0x3A, False),  # CAPSLOCK
    59: (0x3B, False), 60: (0x3C, False), 61: (0x3D, False), 62: (0x3E, False), 
    63: (0x3F, False), 64: (0x40, False), 65: (0x41, False), 66: (0x42, False), 
    67: (0x43, False), 68: (0x44, False), # F1-F10
    87: (0x57, False), 88: (0x58, False), # F11, F12
    
    # Extended keys definitions
    97: (0x1D, True),   # RIGHTCTRL
    100: (0x38, True),  # RIGHTALT
    102: (0x47, True),  # HOME
    103: (0x48, True),  # UP ARROW
    104: (0x49, True),  # PAGE UP
    105: (0x4B, True),  # LEFT ARROW
    106: (0x4D, True),  # RIGHT ARROW
    107: (0x4F, True),  # END
    108: (0x50, True),  # DOWN ARROW
    109: (0x51, True),  # PAGE DOWN
    111: (0x53, True),  # DELETE
    125: (0x5B, True),  # LEFT WINDOWS KEY
}

def win32_mouse_move(dx, dy):
    extra = ULONG_PTR(0)
    mi = MOUSEINPUT(dx, dy, 0, MOUSEEVENTF_MOVE, 0, extra)
    ii = INPUT(INPUT_MOUSE, INPUT_UNION(mi=mi))
    ctypes.windll.user32.SendInput(1, ctypes.byref(ii), ctypes.sizeof(ii))

def win32_mouse_click(button, state):
    flags = 0
    if button == "LEFT":
        flags = MOUSEEVENTF_LEFTDOWN if state == "PRESSED" else MOUSEEVENTF_LEFTUP
    elif button == "RIGHT":
        flags = MOUSEEVENTF_RIGHTDOWN if state == "PRESSED" else MOUSEEVENTF_RIGHTUP
    elif button == "MIDDLE":
        flags = MOUSEEVENTF_MIDDLEDOWN if state == "PRESSED" else MOUSEEVENTF_MIDDLEUP
        
    if flags:
        extra = ULONG_PTR(0)
        mi = MOUSEINPUT(0, 0, 0, flags, 0, extra)
        ii = INPUT(INPUT_MOUSE, INPUT_UNION(mi=mi))
        ctypes.windll.user32.SendInput(1, ctypes.byref(ii), ctypes.sizeof(ii))

def win32_mouse_scroll(value):
    clicks = 120 if value > 0 else -120
    extra = ULONG_PTR(0)
    mi = MOUSEINPUT(0, 0, clicks, MOUSEEVENTF_WHEEL, 0, extra)
    ii = INPUT(INPUT_MOUSE, INPUT_UNION(mi=mi))
    ctypes.windll.user32.SendInput(1, ctypes.byref(ii), ctypes.sizeof(ii))

def win32_keyboard_event(linux_code, state):
    mapping = LINUX_TO_WIN_SCANCODE.get(linux_code, None)
    if not mapping:
        return  

    win_scancode, is_extended = mapping
    flags = KEYEVENTF_SCANCODE
    if is_extended:
        flags |= KEYEVENTF_EXTENDEDKEY
    if state == "RELEASED":
        flags |= KEYEVENTF_KEYUP
        
    extra = ULONG_PTR(0)
    ki = KEYBDINPUT(0, win_scancode, flags, 0, extra)
    ii = INPUT(INPUT_KEYBOARD, INPUT_UNION(ki=ki))
    ctypes.windll.user32.SendInput(1, ctypes.byref(ii), ctypes.sizeof(ii))

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind((LISTEN_IP, LISTEN_PORT))
    except Exception as e:
        print(f"Failed to bind socket on port {LISTEN_PORT}: {e}")
        return

    print(f"Windows receiver listening on port {LISTEN_PORT}... Close terminal to stop.")
    
    try:
        while True:
            data, addr = sock.recvfrom(1024)
            message = data.decode('utf-8')
            parts = message.split('|')
            
            # FIXED: Properly extract the first element as the type identifier
            msg_type = parts[0]
            
            if msg_type == "MOVE":
                axis, val = parts[1], int(parts[2])
                if axis == "X":
                    win32_mouse_move(val, 0)
                elif axis == "Y":
                    win32_mouse_move(0, val)
            elif msg_type == "CLICK":
                btn, state = parts[1], parts[2]
                win32_mouse_click(btn, state)
            elif msg_type == "SCROLL":
                val = int(parts[1])
                win32_mouse_scroll(val)
            elif msg_type == "KEY":
                code, state = int(parts[1]), parts[2]
                win32_keyboard_event(code, state)
                
    except KeyboardInterrupt:
        print("\nStopping network listener.")
    finally:
        sock.close()

if __name__ == '__main__':
    main()
