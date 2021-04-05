import re


class Section:
    def __init__(self, order, text=None):
        self.order = order
        self.generator = self.counter()
        self.subsections = None
        self.text = [text]
    
    def counter(self):
        return (char for char in "abcdefghijklmnopqrstuvwxyz")

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
        return (char for char in "abcdefghijklmnopqrstuvwxyz".upper())

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
    """Class representing the text of a bill.
    Attributes:
        Sections   
        Titles 

    Each attribute is a class itself, with attributes:
        text : the text between that heading and the next heading of the same type 
        order : ordinal number of that heading (relative to others of its type)
        the next highest organizational structure in a bill (except for Subclause).
    """
    def __init__(self, name, text):
        self.name = name
        self.raw_text = text
        self.text = [str(text)]
        self.titles = None
        self.sections = None
        self.generator = self.counter()
        self.expr = {
            Title :         r"\({}\)",
            Subtitle :      r"\({}\)",
            Chapter :       r"\({}\)",
            Subchapter :    r"\({}\)",
            Part :          r"\({}\)",
            Subpart :       r"\({}\)",
            Section :       r"[(?:SEC(?:TION|\.)?)§] *{}",
            Subsection :    r"^[\d\.\t ]*\({}\)",
            Paragraph :     r"^[\t ]*\({}\)",
            Subparagraph :  r"\({}\)",
            Clause :        r"\({}\)",
            Subclause :     r"\({}\)"
        }

    def counter(self):
        self.i = 1
        while True:
            yield self.i
            self.i += 1

    def format_text(self):
        """Formats text accordering to bill headings for readability."""
        #TODO: Check for title headings (large bills)

        # Split bill by sections
        if self.titles is None:
            self.current = next(self.generator)
            div = ["",""]
            while len(div) == 2:
                div = re.split(self.expr[Section].format(self.current), self.text[-1], maxsplit=1)
                self.text = self.text[:-1] + div 
                self.current = next(self.generator)
            self.sections = [Section(i+1, text) for i, text in enumerate(self.text)]
        
        # Split each section by subsection
        for sec in self.sections:
            sec.current = next(sec.generator)
            div = ["",""]
            while len(div) == 2:
                div = re.split(self.expr[Subsection].format(sec.current), sec.text[-1], maxsplit=1)
                sec.text = sec.text[:-1] + div
                sec.current = next(sec.generator)
            sec.subsections = [Subsection(i+1, text) for i, text in enumerate(sec.text)]

            # Split each subsection by paragraph
            for subsection in sec.subsections:
                subsection.current = next(subsection.generator)
                div = ["",""]
                while len(div) == 2:
                    div = re.split(self.expr[Paragraph].format(subsection.current), subsection.text[-1], maxsplit=1)
                    subsection.text = subsection.text[:-1] + div
                    subsection.current = next(subsection.generator)
                subsection.paragraphs = [Paragraph(i+1, text) for i, text in enumerate(subsection.text)]

                # Split each paragraph by subparagraph
                for paragraph in subsection.paragraphs:
                    paragraph.current = next(paragraph.generator)
                    div = ["",""]
                    while len(div) == 2:
                        div = re.split(self.expr[Subparagraph].format(paragraph.current), paragraph.text[-1], maxsplit=1)
                        paragraph.text = paragraph.text[:-1] + div
                        paragraph.current = next(paragraph.generator)
                    paragraph.subparagraphs = [Subparagraph(i+1, text) for i, text in enumerate(paragraph.text)]

                    # Split each subparagraph by clause
                    for subparagraph in paragraph.subparagraphs:
                        subparagraph.current = next(subparagraph.generator)
                        div = ["",""]
                        while len(div) == 2:
                            div = re.split(self.expr[Clause].format(subparagraph.current), subparagraph.text[-1], maxsplit=1)
                            subparagraph.text = paragraph.text[:-1] + div
                            subparagraph.current = next(subparagraph.generator)
                        subparagraph.clauses = [Clause(i+1, text) for i, text in enumerate(subparagraph.text)]

                        # Split each clause by subclause
                        for clause in subparagraph.clauses:
                            clause.current = next(clause.generator)
                            div = ["",""]
                            while len(div) == 2:
                                div = re.split(self.expr[Subclause].format(clause.current), clause.text[-1], maxsplit=1)
                                clause.text = clause.text[:-1] + div
                                clause.current = next(clause.generator)
                            clause.subclauses = [Subclause(i+1, text) for i, text in enumerate(clause.text)]
 