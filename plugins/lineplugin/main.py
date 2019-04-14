from markdown import Markdown
from utils.extensions import AttrTagPattern
from markdown.extensions import Extension


class Plugin(Extension):
    def extendMarkdown(self, md: Markdown, md_globals):
        import_tag = AttrTagPattern(
            "(@line) ([a-zA-Z/]*)",
            attrs={
                "width": "100",
                "height": "150",
                "class": "testplugin"
            })
        md.inlinePatterns.add('testplugin', import_tag, "_begin")
