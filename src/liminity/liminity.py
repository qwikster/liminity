# liminity_todo.py
import sys
import time
import random
import importlib.resources as resources
from luciditycli import Theme, Listener, print, print_buffer, actual_print

def get_theme(path: str | None = None) -> Theme:
    if path is not None:
        return Theme(path)
    # Get liminity/example.cfg inside the installed package
    cfg_path = resources.files("liminity").joinpath("example.cfg")
    return Theme(str(cfg_path))

# Initialize theme + listener
theme = get_theme()
listener = Listener()

tasks = []
colors = []  # stores random color indices for each task

def get_random_color():
    return random.randint(1, 6)

def draw_box(idx, task, color_idx):
    """Render one task inside a box with given color index."""
    col = getattr(theme, f"col_color_{color_idx}")
    reset = theme.col_reset

    status = "[ ]" if not task["done"] else "[✓]"
    content = f"{idx}. {status} {task['title']}"
    width = len(content) + 2

    top = f"{col}╔{'═' * width}╗{reset}"
    mid = f"{col}║ {content} ║{reset}"
    bot = f"{col}╚{'═' * width}╝{reset}"

    return f"{top}\n{mid}\n{bot}"

def show_tasks():
    print_buffer()
    print(f"{theme.col_title}{theme.col_background}Your To-Do List:\n")

    if not tasks:
        print(f"{theme.col_error}{theme.col_background}[empty]\n")
        return

    for idx, (task, color_idx) in enumerate(zip(tasks, colors), start=1):
        print(draw_box(idx, task, color_idx))
    print_buffer()

def add_task():
    title = listener.safe_input(f"{theme.col_prompt}Enter new task: ")
    if title.strip():
        tasks.append({"title": title.strip(), "done": False})
        colors.append(get_random_color())

def toggle_task():
    if not tasks:
        return
    index = listener.safe_input(f"{theme.col_prompt}Enter task number to toggle: ")
    try:
        idx = int(index) - 1
        if 0 <= idx < len(tasks):
            tasks[idx]["done"] = not tasks[idx]["done"]
    except ValueError:
        actual_print("Not a valid number.")

def delete_task():
    if not tasks:
        return
    index = listener.safe_input(f"{theme.col_prompt}Enter task number to delete: ")
    try:
        idx = int(index) - 1
        if 0 <= idx < len(tasks):
            tasks.pop(idx)
            colors.pop(idx)
    except ValueError:
        actual_print("Not a valid number.")

def draw_theme_menu(themes):
    """Render theme selection menu inside a box."""
    reset = theme.col_reset
    col = theme.col_title

    # Build menu content lines
    lines = [f"{idx+1}. {t}" for idx, t in enumerate(themes)]
    width = max(len(line) for line in lines) + 2

    top = f"{col}╔{'═' * width}╗{reset}"
    body = "\n".join(f"{col}║ {line.ljust(width-1)}║{reset}" for line in lines)
    bot = f"{col}╚{'═' * width}╝{reset}"

    return f"{top}\n{body}\n{bot}"

def switch_theme():
    available = list(theme.storage.sections())
    if not available:
        actual_print(f"{theme.col_error}No themes available.")
        return

    print_buffer()
    print(f"{theme.col_title}{theme.col_background}Available Themes:\n")
    print(draw_theme_menu(available))
    print_buffer()

    choice = listener.safe_input(f"{theme.col_prompt}Enter theme number: ")
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(available):
            new_name = available[idx]
            theme.load_theme(new_name)
            actual_print(f"Switched to theme: {new_name}")
        else:
            actual_print(f"{theme.col_error}Invalid selection.")
    except ValueError:
        actual_print(f"{theme.col_error}Not a valid number.")

def _read_color_input(prompt_text: str):
    """Prompt until a valid RGB list [r,g,b] is returned.
       Accepts '#RRGGBB' or 'r,g,b'."""
    while True:
        raw = listener.safe_input(prompt_text).strip()
        if not raw:
            actual_print("Input required; please enter #RRGGBB or r, g, b.")
            continue
        try:
            if raw.startswith("#"):
                rgb = list(theme.hex_to_rgb(raw))
            else:
                rgb = theme.rgb_str_to_list(raw)
            if any((c < 0 or c > 255) for c in rgb):
                actual_print("Each channel must be between 0 and 255.")
                continue
            return rgb
        except Exception as e:
            actual_print(f"Invalid color format: {e}. Try again.")

def create_theme():
    # Get a non-empty theme name
    while True:
        name = listener.safe_input(f"{theme.col_prompt}Enter new theme name: ").strip()
        if not name:
            actual_print("Theme name cannot be empty.")
            continue
        # warn if overwriting existing theme
        if name in theme.storage.sections():
            resp = listener.safe_input(f"Theme '{name}' exists — overwrite? (y/N): ").strip().lower()
            if resp not in ("y", "yes"):
                actual_print("Choose a different name.")
                continue
        break

    # fields we require
    fields = [
        ("background", "Background color (#RRGGBB or r,g,b): "),
        ("title",      "Title color (#RRGGBB or r,g,b): "),
        ("text",       "Text color (#RRGGBB or r,g,b): "),
        ("error",      "Error color (#RRGGBB or r,g,b): "),
        ("prompt",     "Prompt color (#RRGGBB or r,g,b): "),
    ]

    theme_data = {}

    # prompt for the semantic fields
    for key, prompt_text in fields:
        rgb = _read_color_input(f"{theme.col_prompt}{prompt_text}")
        theme_data[key] = rgb

    # prompt for the six generic colors
    for n in range(1, 7):
        key = f"color_{n}"
        prompt_text = f"Color slot {n} (#RRGGBB or r,g,b): "
        rgb = _read_color_input(f"{theme.col_prompt}{prompt_text}")
        theme_data[key] = rgb

    # Build the dict exactly as Theme.new_theme expects
    new_theme_dict = {name: theme_data}

    try:
        theme.new_theme(new_theme_dict)
        theme.load_theme(name)
        actual_print(f"Created and loaded theme: {name}")
    except Exception as e:
        actual_print(f"Failed to create theme: {e}")

def main():
    while True:
        print(f"{theme.col_background}{theme.col_clear}{theme.col_background}")
        print(f"{theme.col_title}{theme.col_background}liminity | AI-generated lucidity demo")
        print(f"{theme.col_text}{theme.col_background}todo: [a]dd, [t]oggle, [d]elete, [s]witch / [n]ew theme, [q]uit\n")

        show_tasks()
        print(f"\n{theme.col_prompt}{theme.col_background}Press a key...")
        print_buffer()

        key = listener.pop()
        if key:
            if key == "a":
                listener.done()
                add_task()
            elif key == "t":
                listener.done()
                toggle_task()
            elif key == "d":
                listener.done()
                delete_task()
            elif key == "s":
                listener.done()
                switch_theme()
            elif key == "n":
                listener.done()
                create_theme()
            elif key == "q":
                listener.done()
                actual_print("Goodbye!\n")
                sys.exit(0)
            else:
                listener.done()
                actual_print(f"{theme.col_error}{theme.col_background}Unknown key: {key}\n")
        time.sleep(0.2)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
