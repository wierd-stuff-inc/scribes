#  from markdown.treeprocessors import Treeprocessor
from markdown.extensions import Extension
from markdown import Markdown
import markdown
from markdown.inlinepatterns import Pattern


class AttrTagPattern(Pattern):
    """
    Return element of type `tag` with a text attribute of group(3)
    of a Pattern and with the html attributes defined with the constructor.

    """

    def __init__(self, pattern, tag: str = "canvas", attrs={}, text=""):
        Pattern.__init__(self, pattern)
        self.tag = tag
        self.attrs = attrs

    def handleMatch(self, m):
        el = markdown.util.etree.Element(self.tag)
        el.text = ""
        el.set("id", m.group(3))
        el.set("class", "testplugin")
        for (key, val) in self.attrs.items():
            el.set(key, val)
        return el


class Plugin(Extension):
    def extendMarkdown(self, md: Markdown, md_globals):
        import_tag = AttrTagPattern(
            "(@line) ([a-zA-Z/]*)", attrs={
                "width": "100",
                "height": "150"
            })
        md.inlinePatterns.add('testplugin', import_tag, "_begin")
