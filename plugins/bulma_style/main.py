from markdown import Markdown
from markdown.extensions import Extension


class Plugin(Extension):
    def extendMarkdown(self, md: Markdown, md_globals):
        pass
