import markdown
from markdown.inlinepatterns import Pattern
import re
import copy


class AttrTagPattern(Pattern):
    """
    Return element of type `tag` with a text attribute of group(3)
    of a Pattern and with the html attributes defined with the constructor.

    """

    def __init__(self, pattern, tag: str = "canvas", attrs={}, text=""):
        Pattern.__init__(self, pattern)
        self.tag = tag
        self.attrs = attrs
        self.text = text

    def handleMatch(self, m):
        el = markdown.util.etree.Element(self.tag)
        param = re.compile(r".*\$(\d+).*")
        new_attrs = copy.deepcopy(self.attrs)
        for (k, v) in new_attrs.items():
            if param.match(v):
                num = param.match(v).group(1)
                new_attrs[k] = v.replace(f"${num}", m.group(int(num)))
        el.text = self.text
        for (key, val) in new_attrs.items():
            el.set(key, val)
        return el
