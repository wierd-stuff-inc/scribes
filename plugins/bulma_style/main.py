from markdown import Markdown
from markdown.extensions import Extension

from utils.extensions import AttrTagPattern


class Plugin(Extension):
    def extendMarkdown(self, md: Markdown, md_globals):
        import_tag = AttrTagPattern(r"^@style bulma", tag=None)
        md.inlinePatterns.add('bulma_styles', import_tag, "_begin")
