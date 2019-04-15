from markdown import Markdown
from markdown.extensions import Extension

from utils.extensions import AttrTagPattern


class Plugin(Extension):
    def extendMarkdown(self, md: Markdown, md_globals):
        import_tag = AttrTagPattern(
            r"^(@draw_func) (\d*) (\d*) (.*)", attrs={
                "class": "func_plugin",
                "width": "$3",
                "height": "$4",
                "function": "$5"
            })
        md.inlinePatterns.add('draw_func', import_tag, "_begin")
