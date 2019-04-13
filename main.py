import errno
import os
import shutil
import threading
import time

import jinja2
import markdown
from flask import Flask, send_from_directory
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

mark = markdown.Markdown(extensions=['mdx_math'])

scripts = []


def recursive_copy(src, dst, rm=True):
    """recursive_copy
    Recursive copy files in directory.
    :param src: source location
    :param dst: destanation.
    :param rm: will delete Resource before copying if exists.
    """
    try:
        if os.path.exists(dst) and rm:
            shutil.rmtree(dst)
        print(f"Copying {src}")
        shutil.copytree(src, dst)
    except FileExistsError:
        if rm:
            raise
    except OSError as exc:
        if exc.errno == errno.ENOTDIR:
            shutil.copy(src, dst)
        else:
            raise


def create_structure():
    """create_structure
    Create file structure for generated pages
    and resources.
    """

    def create_folder(path):
        if not os.path.exists(path):
            os.makedirs(path)

    create_folder("generated")
    create_folder("generated/pages")
    create_folder("generated/js")
    create_folder("generated/loaded")
    recursive_copy("templates/js", "generated/js/static", False)


def load_plugin_from_github(plugin_link):
    raise Exception("Unimplemeted")


def register_plugin(directory: str, pluginname: str):
    if not os.path.exists(f"{directory}/{pluginname}/main.py"):
        raise Exception("No main.py entry was found in plugin.")
    mark.registerExtensions([f"{directory}.{pluginname}.main:Plugin"], {})
    script_dir = f"{directory}/{pluginname}/scripts"
    if os.path.exists(script_dir):
        recursive_copy(script_dir, f"generated/js/{pluginname}")
        for script in os.listdir(script_dir):
            if f"/js/{pluginname}/{script}" not in scripts:
                scripts.append(f"/js/{pluginname}/{script}")
    print(f"[  OK  ] Registring {pluginname}")


def load_plugins(md: str):
    """load_plugins
    Function to load all imported plugins from page.
    And return page text without "@import".
    :param md:
    :type md: str
    """
    global scripts
    scripts = []
    new_lines = []
    for line in md.splitlines():
        if line.strip().startswith("@import"):
            plugin = line.replace("@import", "").split()
            if not plugin:
                raise Exception("Empty plugin nothing to load.")
            if plugin[0].lower() == "from":
                if not plugin[1:]:
                    raise Exception("Empty plugin. Nothing to load.")
                url = plugin[1]
                load_plugin_from_github(url)
                register_plugin("loaded", url.split("/")[-1])
            else:
                extension = plugin[0]
                register_plugin("plugins", extension)
        else:
            new_lines.append(line)
    return "\n".join(new_lines)


def generate_page(filename: str):
    """generate_page
    Generate page from markdown to html
    and place it in "generated/pages/".
    :param filename:
    :type filename: str
    """
    global scripts
    print('{:-^100}'.format(f'Generating {filename}'))
    with open(filename, 'r') as page:
        text = page.read()
        text = load_plugins(text)
        content = mark.convert(text)
        print(f"[  OK  ] Converting {filename}")
        mark.reset()
        name = filename.replace(".md", "").split("/")[-1]
        with open(f"generated/pages/{name}.html", 'w') as out:
            template = jinja2.Template(open("templates/page.html").read())
            rendered = template.render(
                page_title=name, content=content, scripts=scripts)
            out.write(rendered)
        print(f"[  OK  ] Generating page for {name}")


def generate_book():
    print("Parsing pages")
    for file in os.listdir("book"):
        if os.path.isfile(f"book/{file}"):
            generate_page(f"book/{file}")
    print('{:-^100}'.format(f'Starting server'))


def init_app() -> Flask:
    """init_app
    Initialize scribes app.
    Create file structure,
    load and generate all pages,
    return Flask object.
    :rtype: Flask
    """
    app = Flask(__name__)
    create_structure()
    generate_book()
    return app


app = init_app()


@app.route('/js/<path:path>')
def find_js(path):
    return send_from_directory(f"generated/js", path)


@app.route('/page/<path:path>')
def find_page(path):
    return send_from_directory(f"generated/pages", path)


@app.route("/")
def hello():
    return "Table of contents."


class FileWatcher(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith(".md"):
            try:
                generate_page(event.src_path)
            except Exception as ex:
                print(
                    f"Cannot render page {event.src_path}\n\nReason: {str(ex)}"
                )


def start_listen(directory: str):
    event_handler = FileWatcher()
    observer = Observer()
    observer.schedule(event_handler, path=directory, recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    #  thread.start_new_thread(start_listen("book/"))
    t = threading.Thread(
        target=start_listen, name="File watcher", args=("book/", ))
    t.daemon = True
    t.start()
    app.run()
