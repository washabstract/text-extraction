import re



# Large bills only
class Title:
    def __init__(self, order, text=None):
        self.order = order
        self.subtitles = None
        self.text = [text]

class Subtitle:
    def __init__(self, order, text=None):
        self.order = order
        self.chapters = None
        self.text = [text]

class Chapter:
    def __init__(self, order, text=None):
        self.order = order
        self.subchapters = None
        self.text = [text]

class Subchapter:
    def __init__(self, order, text=None):
        self.order = order
        self.parts = None
        self.text = [text]

class Part:
    def __init__(self, order, text=None):
        self.order = order
        self.subparts = None
        self.text = [text]

class Subpart:
    def __init__(self, order, text=None):
        self.order = order
        self.sections = None
        self.text = [text]

# All bills
class Section:
    def __init__(self, order, text=None):
        self.order = order
        self.generator = self.counter()
        self.subsections = None
        self.text = [text]

    def __str__(self):
        return (f"Section {self.order}" if self.order > 0 else "Heading")
    
    def counter(self):
        self.alphabet = "abcdefghijklmnopqrstuvwxyz"
        self.j = 1
        self.i = [0]
        while True:
            yield "".join(self.alphabet[char] for char in self.i)
            self.i[-1] += 1
            if self.i[-1] % 26 == 0:
                self.j += 1
                self.i = [0]*self.j

class Subsection:
    def __init__(self, order, text=None):
        self.order = order
        self.generator = self.counter()
        self.paragraphs = None
        self.text = [text]

    def counter(self):
        self.i = 1
        while True:
            yield self.i
            self.i += 1

class Paragraph:
    def __init__(self, order, text=None):
        self.order = order
        self.generator = self.counter()
        self.subparagraphs = None
        self.text = [text]

    def counter(self):
        self.alphabet = "abcdefghijklmnopqrstuvwxyz"
        self.j = 1
        self.i = [0]
        while True:
            yield "".join(self.alphabet[char].upper() for char in self.i)
            self.i[-1] += 1
            if self.i[-1] % 26 == 0:
                self.j += 1
                self.i = [0]*self.j

class Subparagraph:
    def __init__(self, order, text=None):
        self.order = order
        self.generator = self.counter()
        self.clauses = None
        self.text = [text]
        self.ROMAN = [
            (1000, "M"),
            ( 900, "CM"),
            ( 500, "D"),
            ( 400, "CD"),
            ( 100, "C"),
            (  90, "XC"),
            (  50, "L"),
            (  40, "XL"),
            (  10, "X"),
            (   9, "IX"),
            (   5, "V"),
            (   4, "IV"),
            (   1, "I"),
        ]

    def counter(self):
        self.i = 1
        while True:
            yield self._counter(self.i)
            self.i += 1

    def _counter(self, number):
        result = []
        for (arabic, roman) in self.ROMAN:
            (factor, number) = divmod(number, arabic)
            result.append(roman * factor)
            if number == 0:
                break
        return "".join(result)

class Clause:
    def __init__(self, order, text=None):
        self.order = order
        self.generator = self.counter()
        self.subclauses = None
        self.text = [text]
        self.ROMAN = [
            (1000, "M"),
            ( 900, "CM"),
            ( 500, "D"),
            ( 400, "CD"),
            ( 100, "C"),
            (  90, "XC"),
            (  50, "L"),
            (  40, "XL"),
            (  10, "X"),
            (   9, "IX"),
            (   5, "V"),
            (   4, "IV"),
            (   1, "I"),
        ]

    def counter(self):
        self.i = 1
        while True:
            yield self._counter(self.i)
            self.i += 1

    def _counter(self, number):
        result = []
        for (arabic, roman) in self.ROMAN:
            (factor, number) = divmod(number, arabic)
            result.append(roman * factor)
            if number == 0:
                break
        return "".join(result)

class Subclause:
    def __init__(self, order, text=None):
        self.order = order
        self.text = [text]

class BillText:
    """
    """
    def __init__(self, text):
        # self.name = name
        self.raw_text = text
        self.text = [str(text)]
        self.titles = None
        self.sublayers = []
        self.generator = self.counter()
        self.expr = {
            Title :         r"\({}\)",
            Subtitle :      r"\({}\)",
            Chapter :       r"\({}\)",
            Subchapter :    r"\({}\)",
            Part :          r"\({}\)",
            Subpart :       r"\({}\)",
            Section :       r"\s*SECTION *{}\.?\s*",
            Subsection :    r"\({}\)",
            Paragraph :     r"\({}\)",
            Subparagraph :  r"\({}\)",
            Clause :        r"\({}\)",
            Subclause :     r"\({}\)"
        }

    def counter(self):
        self.i = 1
        while True:
            yield self.i
            self.i += 1

    def lsplit(self, outer, inner):
        """Splits a layer (outer), giving it sublayer attributes (inner).
        """
        # If text attribute has been changed to str, enclose it in a list for splitting
        if type(outer.text) is str:
            outer.text = [outer.text]

        outer.current = next(outer.generator)
        div = re.split(self.expr[inner].format(outer.current), outer.text[-1], maxsplit=1)
        while len(div) == 2:
            outer.text = outer.text[:-1] + div 
            outer.current = next(outer.generator)
            div = re.split(self.expr[inner].format(outer.current), outer.text[-1], maxsplit=1)
        outer.sublayers = [inner(i, text) for i, text in enumerate(self.text)]

        # Now for printing, convert back to string
        outer.text_full = ''.join(outer.text)

    def format_text(self):
        """Formats text accordering to bill headings for readability."""
        #TODO: Check for title headings (large bills)

        # Split bill by section
        self.lsplit(self, Section)

        # Split each section by subsection
        for sec in self.sublayers:
            self.lsplit(sec, Subsection)

            # Split each subsection by paragraph
            for subsection in sec.sublayers:
                self.lsplit(subsection, Paragraph)

                # Split each paragraph by subparagraph
                for par in subsection.sublayers:
                    self.lsplit(par, Subparagraph)

                    # Split each subparagraph by clause
                    for subpar in par.sublayers:
                        self.lsplit(subpar, Clause)

                        # Split each clause by subclause
                        # for clause in subpar.sublayers:
                        #     self.lsplit(clause, Subclause)