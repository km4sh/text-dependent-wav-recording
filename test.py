from pynput import keyboard


def on_press(key):
    print(key)


def on_release(key):
    print(key, "released.")
    if key == keyboard.Key.esc:
        return False


with keyboard.Listener(
    on_press=on_press, on_release=on_release, suppress=False
) as listener:
    print("listening...")
    listener.join()
