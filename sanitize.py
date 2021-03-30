import re 
from extract.utils import jid_to_abbr


class Sanitizer:
    """Abstract base class for sanitizing extracted text with pre-compiled regular expressions."""
    def __init__(self):
        self.re = None
    def sanitize(self, text):
        return self.re.sub('', text)

class LineNumCleaner(Sanitizer):
    """Removes line numbers from extracted text."""
    def __init__(self):
        self.re = re.compile(r"^ *line *\d+", flags=re.MULTILINE) 

class NewlineCleaner(Sanitizer):
    """Removes excessive newlines from extracted text."""
    def __init__(self):
        self.re = re.compile(r"\n(?=\n)")

class TexasCSSCleaner(Sanitizer):
    """Removes the line of CSS from extracted TX text."""
    def __init__(self):
        self.re = re.compile(r"td { font-family: Courier, Arial, sans-serif; font-size: 10pt; }.*")

class FontDefCleaner(Sanitizer):
    """Removes HTML font definitions from extracted TX text."""
    def __init__(self):
        self.re = re.compile(r"<!?--.+>", flags=re.DOTALL)

class NbspCleaner(Sanitizer):
    """Replaces NBSP with SP"""
    def __init__(self):
        self.re = re.compile(r"\xa0")
    def sanitize(self, text):
        return self.re.sub(' ', text)

class CarriageReturnCleaner(Sanitizer):
    """Removes carriage returns from extracted text."""
    def __init__(self):
        self.re = re.compile(r"\r(?=\n)", flags=re.DOTALL)

class SpaceCleaner(Sanitizer):
    """Collapses spaces in extracted text."""
    def __init__(self):
        self.re = re.compile(r"\t(?<= )")


def get_sanitizers(state, is_jid=False):
    """Determines which sanitizers to use on text based on jurisdiction id.
        Returns: a list of instances of each appropriate sanitizer.
    """
    sanitizers_by_state = {
        'ca' : [LineNumCleaner],
        'tx' : [FontDefCleaner, TX_CSS_Cleaner]
    }

    sanitizers_all = [
        NewlineCleaner,
        NBSP_Cleaner,
        CarriageReturnCleaner,
        SpaceCleaner
    ]

    if is_jid == True:
        state = jid_to_abbr(state)
    try:
        sanitizers_spec = sanitizers_by_state[state]
    except KeyError:
        sanitizers_spec = []
    return [s() for s in sanitizers_all + sanitizers_spec]

def clean(sanitizers, text):
    """Sanitizes text using each of the given sanitizers, input as a list 
        of instantiated objects (like output of get_sanitizers()).
    """
    for sanitizer in sanitizers:
        text = sanitizer.sanitize(text)  
    return text  