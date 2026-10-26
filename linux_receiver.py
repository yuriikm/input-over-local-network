import socket
import os
import struct
import fcntl
import sys

# --- PORT CONFIGURATION ---
LISTEN_IP = "0.0.0.0"
LISTEN_PORT = 5005

# --- LINUX UINPUT CONSTANTS ---
UI_SET_EVBIT   = 0x40045564
UI_SET_KEYBIT  = 0x40045565
UI_SET_RELBIT  = 0x40045566
UI_DEV_SETUP   = 0x405c5503 # Modern setup ioctl
UI_DEV_CREATE  = 0x00005501
UI_DEV_DESTROY = 0x00005502

EV_SYN = 0x00
EV_KEY = 0x01
EV_REL = 0x02

REL_X = 0x00
REL_Y = 0x01
REL_WHEEL = 0x08

BTN_LEFT   = 0x110
BTN_RIGHT  = 0x111
BTN_MIDDLE = 0x112

BTN_MAPPING = {
    "LEFT": BTN_LEFT,
    "RIGHT": BTN_RIGHT,
    "MIDDLE": BTN_MIDDLE
}

uinput_fd = None

def setup_virtual_device():
    """Creates a virtual hybrid mouse and keyboard device via /dev/uinput."""
    global uinput_fd
    try:
        uinput_fd = os.open("/dev/uinput", os.O_WRONLY | os.O_NONBLOCK)
    except Exception as e:
        print(f"Error opening /dev/uinput: {e}")
        print("Make sure you run this script as root (sudo) and 'sudo modprobe uinput' is loaded.")
        sys.exit(1)

    # 1. Enable Event Types
    fcntl.ioctl(uinput_fd, UI_SET_EVBIT, EV_SYN)
    fcntl.ioctl(uinput_fd, UI_SET_EVBIT, EV_KEY)
    fcntl.ioctl(uinput_fd, UI_SET_EVBIT, EV_REL)

    # 2. Enable Relative Axes (Mouse movements & scroll wheel)
    fcntl.ioctl(uinput_fd, UI_SET_RELBIT, REL_X)
    fcntl.ioctl(uinput_fd, UI_SET_RELBIT, REL_Y)
    fcntl.ioctl(uinput_fd, UI_SET_RELBIT, REL_WHEEL)

    # 3. Enable Mouse Buttons
    fcntl.ioctl(uinput_fd, UI_SET_KEYBIT, BTN_LEFT)
    fcntl.ioctl(uinput_fd, UI_SET_KEYBIT, BTN_RIGHT)
    fcntl.ioctl(uinput_fd, UI_SET_KEYBIT, BTN_MIDDLE)

    # 4. Enable All Standard Keyboard Keys
    for key_code in range(256):
        fcntl.ioctl(uinput_fd, UI_SET_KEYBIT, key_code)

    # 5. Build and Create the Device using modern UI_DEV_SETUP
    # struct uinput_setup layout: struct input_id (4H: bustype, vendor, product, version), name (80s), ff_effects_max (I)
    uinput_setup_format = "HHHH 80s I"
    setup_data = struct.pack(
        uinput_setup_format,
        0x0001, 0x0001, 0x0001, 0x0000,   # bustype, vendor, product, version
        b"Virtual Network Input Device", # Name (padded up to 80 bytes automatically)
        0                                # ff_effects_max
    )
    
    fcntl.ioctl(uinput_fd, UI_DEV_SETUP, setup_data)
    fcntl.ioctl(uinput_fd, UI_DEV_CREATE)
    print("Virtual Input Device initialized successfully.")

def emit_event(ev_type, code, value):
    """Writes a structural low-level event packet into the virtual device."""
    event_packet = struct.pack("llHHi", 0, 0, ev_type, code, value)
    os.write(uinput_fd, event_packet)

def sync_events():
    """Forces the system to instantly process the events batch."""
    emit_event(EV_SYN, 0, 0)

def linux_mouse_move(dx, dy):
    if dx != 0:
        emit_event(EV_REL, REL_X, dx)
    if dy != 0:
        emit_event(EV_REL, REL_Y, dy)
    sync_events()

def linux_mouse_click(button_str, state_str):
    code = BTN_MAPPING.get(button_str)
    if code is not None:
        value = 1 if state_str == "PRESSED" else 0
        emit_event(EV_KEY, code, value)
        sync_events()

def linux_mouse_scroll(value):
    emit_event(EV_REL, REL_WHEEL, value)
    sync_events()

def linux_keyboard_event(linux_code, state_str):
    value = 1 if state_str == "PRESSED" else (0 if state_str == "RELEASED" else 2) # 2 = HELD
    emit_event(EV_KEY, linux_code, value)
    sync_events()

def main():
    if os.geteuid() != 0:
        print("Error: Must run as root (sudo python3 script.py) to manage virtual input nodes.")
        sys.exit(1)

    setup_virtual_device()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind((LISTEN_IP, LISTEN_PORT))
    except Exception as e:
        print(f"Failed to bind socket on port {LISTEN_PORT}: {e}")
        return

    print(f"Linux receiver listening on port {LISTEN_PORT}... Close terminal to stop.")

    try:
        while True:
            data, addr = sock.recvfrom(1024)
            message = data.decode("utf-8")
            parts = message.split("|")
            msg_type = parts[0]

            if msg_type == "MOVE":
                axis, val = parts[1], int(parts[2])
                if axis == "X":
                    linux_mouse_move(val, 0)
                elif axis == "Y":
                    linux_mouse_move(0, val)

            elif msg_type == "CLICK":
                btn, state = parts[1], parts[2]
                linux_mouse_click(btn, state)

            elif msg_type == "SCROLL":
                val = int(parts[1])
                linux_mouse_scroll(val)

            elif msg_type == "KEY":
                code, state = int(parts[1]), parts[2]
                linux_keyboard_event(code, state)

    except KeyboardInterrupt:
        print("\nStopping network listener.")
    finally:
        sock.close()
        if uinput_fd is not None:
            try:
                fcntl.ioctl(uinput_fd, UI_DEV_DESTROY)
                os.close(uinput_fd)
            except Exception:
                pass

if __name__ == "__main__":
    main()
