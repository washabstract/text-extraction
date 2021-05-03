import re

class DoNotUse(NotImplementedError):
    pass

# ---------------------- Used in all bills ------------------------

class Layer:
    def __init__(self, order, text):
        self.order = order
        self.gen = self.counter()
        self.sublayers = None
        self.text = [text]
        self.readable_text = text
    
    def counter(self):
        raise NotImplementedError

    def split(self):
        self.current = next(self.gen)
        div = re.split(self.expr[cls_].format(self.current), self.text[-1], maxsplit=1)
        while len(div) == 2:
            self.text = self.text[:-1] + div
            self.current = next(self.gen)
            self.sublayers = [self.subcls(i, text) for i, text in enumerate(self.text)]
            div = re.split(self.expr[cls_].format(self.current), self.text[-1], maxsplit=1)

class Section(Layer):
    def __init__(self, order, text):
        super().__init__(order, text)
        self.subcls = Subsection
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

class Subsection(Layer):
    def __init__(self, order, text):
        super().__init__(order, text)
        self.subcls = Paragraph
    def counter(self):
        self.i = 1
        while True:
            yield self.i
            self.i += 1

class Paragraph(Layer):
    def __init__(self, order, text):
        super().__init__(order, text)
        self.subcls = Subparagraph
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

class Subparagraph(Layer):
    def __init__(self, order, text):
        super().__init__(order, text)
        self.subcls = Clause
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
        return "".join(result).lower()

class Clause(Layer):
    def __init__(self, order, text):
        super().__init__(order, text)
        self.subcls = Subclause
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

class Subclause(Layer):
    def counter(self):
        raise DoNotUse

# ---------------- Used in large bills only ------------------

class Title(Layer):
    pass 
class Subtitle(Layer):
    pass
class Chapter(Layer):
    pass
class Subchapter(Layer):
    pass
class Part(Layer):
    pass
class Subpart(Layer):
    pass

# ------------------------------------------------------------

class BillText:
    """
    """
    def __init__(self, text):
        # self.name = name
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

    def format_text(self):
        for layer in [Section, Subsection, Paragraph, Subparagraph, Clause, Subclause]:
            print(layer)

# DUMP
# # Split bill by sections
#         if self.titles is None:
#             self.current = next(self.generator)
#             div = re.split(self.expr[Section].format(self.current), self.text[-1], maxsplit=1)
#             while len(div) == 2:
#                 div = re.split(self.expr[Section].format(self.current), self.text[-1], maxsplit=1)
#                 self.text = self.text[:-1] + div 
#                 self.current = next(self.generator)
#             self.sections = [Section(i, text) for i, text in enumerate(self.text)]

#             # Now for printing, convert back to string
#             self.text = self.text[0]
        
#         # Split each section by subsection
#         for sec in self.sections:
#             sec.current = next(sec.generator)
#             div = re.split(self.expr[Subsection].format(sec.current), sec.text[-1], maxsplit=1)
#             while len(div) == 2:
#                 div = re.split(self.expr[Subsection].format(sec.current), sec.text[-1], maxsplit=1)
#                 sec.text = sec.text[:-1] + div
#                 sec.current = next(sec.generator)
#             sec.subsections = [Subsection(i, text) for i, text in enumerate(sec.text)]

#             # Split each subsection by paragraph
#             for subsection in sec.subsections:
#                 subsection.current = next(subsection.generator)
#                 div = re.split(self.expr[Paragraph].format(subsection.current), subsection.text[-1], maxsplit=1)
#                 while len(div) == 2:
#                     div = re.split(self.expr[Paragraph].format(subsection.current), subsection.text[-1], maxsplit=1)
#                     subsection.text = subsection.text[:-1] + div
#                     subsection.current = next(subsection.generator)
#                 subsection.paragraphs = [Paragraph(i, text) for i, text in enumerate(subsection.text)]

#                 # Split each paragraph by subparagraph
#                 for paragraph in subsection.paragraphs:
#                     paragraph.current = next(paragraph.generator)
#                     div = re.split(self.expr[Subparagraph].format(paragraph.current), paragraph.text[-1], maxsplit=1)
#                     while len(div) == 2:
#                         div = re.split(self.expr[Subparagraph].format(paragraph.current), paragraph.text[-1], maxsplit=1)
#                         paragraph.text = paragraph.text[:-1] + div
#                         paragraph.current = next(paragraph.generator)
#                     paragraph.subparagraphs = [Subparagraph(i, text) for i, text in enumerate(paragraph.text)]

#                     # Split each subparagraph by clause
#                     for subparagraph in paragraph.subparagraphs:
#                         subparagraph.current = next(subparagraph.generator)
#                         div = re.split(self.expr[Clause].format(subparagraph.current), subparagraph.text[-1], maxsplit=1)
#                         while len(div) == 2:
#                             div = re.split(self.expr[Clause].format(subparagraph.current), subparagraph.text[-1], maxsplit=1)
#                             subparagraph.text = paragraph.text[:-1] + div
#                             subparagraph.current = next(subparagraph.generator)
#                         subparagraph.clauses = [Clause(i, text) for i, text in enumerate(subparagraph.text)]

#                         # Split each clause by subclause
#                         for clause in subparagraph.clauses:
#                             clause.current = next(clause.generator)
#                             div = re.split(self.expr[Subclause].format(clause.current), clause.text[-1], maxsplit=1)
#                             while len(div) == 2:
#                                 div = re.split(self.expr[Subclause].format(clause.current), clause.text[-1], maxsplit=1)
#                                 clause.text = clause.text[:-1] + div
#                                 clause.current = next(clause.generator)
#                             clause.subclauses = [Subclause(i, text) for i, text in enumerate(clause.text)]
 