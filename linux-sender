import os
import struct
import select
import sys
import fcntl
import socket

# --- NETWORK CONFIGURATION ---
TARGET_WINDOWS_IP = "0.0.0.0"  # <-- Change this to your Windows laptop's IP address
TARGET_PORT = 5005

# Setup lightweight UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def send_event(payload):
    """Sends the input event metadata over the local network immediately."""
    try:
        sock.sendto(payload.encode('utf-8'), (TARGET_WINDOWS_IP, TARGET_PORT))
    except Exception:
        pass

# --- LINUX HARDWARE CAPTURE ---
EV_KEY = 0x01
EV_REL = 0x02
KEY_PRESS = 1
KEY_CALC = 140
REL_X = 0x00
REL_Y = 0x01
REL_WHEEL = 0x08
BTN_MAPPING = {272: "LEFT", 273: "RIGHT", 274: "MIDDLE"}

EVENT_FORMAT = "QQHHi"
EVENT_SIZE = struct.calcsize(EVENT_FORMAT)
EVIOCGRAB = 0x40044590

def find_devices():
    kb_devs, mouse_devs = [], []
    is_keyboard, is_mouse = False, False
    current_handlers = ""
    with open("/proc/bus/input/devices", "r") as f:
        for line in f:
            if line.startswith("H: Handlers="):
                current_handlers = line
            elif line.startswith("B: EV="):
                parts = line.split("=")
                if len(parts) > 1:
                    ev_val = int(parts[1].strip(), 16)
                    if (ev_val & 0x12) == 0x12: is_keyboard = True
                    elif (ev_val & 0x06) == 0x06: is_mouse = True
            elif line.strip() == "":
                for token in current_handlers.split():
                    if token.startswith("event"):
                        path = f"/dev/input/{token}"
                        if is_keyboard: kb_devs.append(path)
                        if is_mouse: mouse_devs.append(path)
                is_keyboard = False; is_mouse = False; current_handlers = ""
    return list(set(kb_devs)), list(set(mouse_devs))

def handle_device_data(fd):
    try:
        data = os.read(fd, EVENT_SIZE)
        if not data or len(data) < EVENT_SIZE:
            return True
            
        _, _, ev_type, code, value = struct.unpack(EVENT_FORMAT, data)
        
        if ev_type == EV_KEY:
            if code == KEY_CALC and value == KEY_PRESS:
                print("\n[EXIT] XF86 Calculator key detected. Restoring local control...")
                return False
                
            state = "PRESSED" if value == KEY_PRESS else ("RELEASED" if value == 0 else "HELD")
            if code in BTN_MAPPING:
                send_event(f"CLICK|{BTN_MAPPING[code]}|{state}")
            else:
                send_event(f"KEY|{code}|{state}")

        elif ev_type == EV_REL:
            if code == REL_X:
                send_event(f"MOVE|X|{value}")
            elif code == REL_Y:
                send_event(f"MOVE|Y|{value}")
            elif code == REL_WHEEL:
                send_event(f"SCROLL|{value}")
                
    except Exception:
        pass
    return True

def main():
    if os.geteuid() != 0:
        print("Error: Must run as root (sudo python3 script.py)")
        sys.exit(1)

    kb_paths, mouse_paths = find_devices()
    all_paths = kb_paths + mouse_paths
    
    poller = select.poll()
    opened_fds = []

    print(f"Locking local system inputs and streaming to {TARGET_WINDOWS_IP}:{TARGET_PORT}...")
    for path in all_paths:
        try:
            fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
            fcntl.ioctl(fd, EVIOCGRAB, 1)
            poller.register(fd, select.POLLIN)
            opened_fds.append(fd)
        except Exception:
            continue
    
    running = True
    try:
        while running:
            events = poller.poll(50)
            for fd, mask in events:
                if mask & select.POLLIN:
                    if not handle_device_data(fd):
                        running = False
                        break
    finally:
        for fd in opened_fds:
            try:
                fcntl.ioctl(fd, EVIOCGRAB, 0)
                os.close(fd)
            except Exception: pass
        sock.close()
        print("Local system interaction restored safely.")

if __name__ == '__main__':
    main()
