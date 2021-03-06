import errno
import math
import os
import shutil
import threading
import time
import zipfile

import jinja2
import markdown
import requests
import tqdm
from flask import Flask, send_from_directory
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from typing import List

mark = markdown.Markdown(extensions=['mdx_math', 'toc', 'attr_list'])

scripts = []
styles = []


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
        shutil.copytree(src, dst)
        print(f"[  OK  ] Copying {src}")
    except FileExistsError:
        if rm:
            raise
    except OSError as exc:
        if exc.errno == errno.ENOTDIR:
            shutil.copy(src, dst)
        else:
            raise


def create_folder(path):
    """create_folder
    Create folder if not exists
    :param path:
    """
    if not os.path.exists(path):
        os.makedirs(path)


def create_structure():
    """create_structure
    Create file structure for generated pages
    and resources.
    """

    create_folder("generated")
    create_folder("generated/pages")
    create_folder("generated/js")
    create_folder("generated/loaded")
    recursive_copy("templates/js", "generated/js/static", False)


def download_repo(repo):
    request = requests.get(
        f"https://github.com/{repo}/archive/master.zip", stream=True)
    total_size = int(request.headers.get('content-length', 0))
    block_size = 1024
    wrote = 0
    with open("tmp/plugin.zip", 'wb') as out:
        for data in tqdm.tqdm(
                request.iter_content(block_size),
                total=math.ceil(total_size // block_size),
                unit="KB",
                desc=f"Loading {repo}"):
            wrote += len(data)
            out.write(data)
    if total_size != 0 and wrote != total_size:
        raise Exception("Can't load plugin. Aborting")


def load_plugin_from_github(plugin_link):
    url_path = plugin_link.split(":")
    local_path = ""
    if len(url_path) > 1:
        local_path = url_path[1]
    url = url_path[0]
    if os.path.exists(f"plugins/loaded/{url}/{local_path}"):
        print(f"Found cached plugin {url}")
        return f"plugins/loaded/{url}/{local_path}"
    create_folder("tmp")
    try:
        download_repo(url)
    except Exception:
        shutil.rmtree("tmp")
        raise
    plugin_zip = zipfile.ZipFile("tmp/plugin.zip")
    print("[  OK  ] Download Plugin.")
    if local_path == "":
        plugin_zip.extractall(f"plugins/loaded/{url}")
        shutil.rmtree("tmp")
        return f"plugins/loaded/{url}"
    plugin_zip.extractall("tmp")
    load_location = f"plugins/loaded/{url}/{local_path}"
    recursive_copy(f"tmp/{url.split('/')[-1]}-master/{local_path}",
                   load_location, True)
    shutil.rmtree("tmp")
    return load_location


def copy_and_link(src: str, pluginname: str, dst: str, links: List[str]):
    if os.path.exists(src):
        recursive_copy(src, f"generated/{dst}/{pluginname}")
        for element in os.listdir(src):
            if element not in links:
                links.append(f"/{dst}/{pluginname}/{element}")
                print(f"[  OK  ] Linking {pluginname}/{element}")


def register_plugin(directory: str, pluginname: str):
    if not os.path.exists(f"{directory}/{pluginname}/main.py"):
        raise Exception("No main.py entry was found in plugin.")
    import_path = directory.replace("/", ".")
    mark.registerExtensions([f"{import_path}.{pluginname}.main:Plugin"], {})
    global scripts
    script_dir = f"{directory}/{pluginname}/scripts"
    copy_and_link(script_dir, pluginname, "js", scripts)
    print("[  OK  ] Linking scripts")

    global styles
    style_dir = f"{directory}/{pluginname}/styles"
    copy_and_link(style_dir, pluginname, "css", styles)
    print("[  OK  ] Linking styles")
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
    global styles
    styles = []
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
                plugin_path = load_plugin_from_github(url)
                plugin_dir = "/".join(plugin_path.split("/")[:-1])
                register_plugin(plugin_dir, plugin_path.split("/")[-1])
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
    global styles
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
                page_title=name,
                content=content,
                scripts=scripts,
                styles=styles)
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


@app.route('/css/<path:path>')
def find_css(path):
    return send_from_directory(f"generated/css", path)


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
    t = threading.Thread(
        target=start_listen, name="File watcher", args=("book/", ))
    t.daemon = True
    t.start()
    app.run()
