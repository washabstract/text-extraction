import re


class Layer:
    def __init__(self, order, text=None):
        self.order = order
        self.generator = self.counter()
        self.sublayers = []
        self.text = [text]
        self.full_text = "error: not set" + self.text[0]
        self.label = self.make_label()

    def __str__(self):
        if self.sublayers == []:
            return self.label + "\n\n" + self.full_text
        else:
            return self.label + "\t" + "\n\n".join([sl.__str__() for sl in self.sublayers])

    def make_label(self):
        tempgen = self.counter()
        k = 0
        for _ in range(self.order):
            k = next(tempgen)
        return k

    def counter(self): # Virtual
        raise NotImplementedError


# Large bills only
# End large bills only

# All bills
class Section(Layer):
    def __repr__(self):
        return (f"Section {self.order}" if self.order > 0 else "Heading")
    
    def __str__(self):
        pass

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
    def counter(self):
        self.i = 1
        while True:
            yield self.i
            self.i += 1

class Paragraph(Layer):
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
    def __init__(self, order, text=None):
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
        super().__init__(order, text)

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

class Clause(Layer):
    def __init__(self, order, text=None):
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
        super().__init__(order, text)

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
    def __init__(self, order, text=None):
        self.order = order
        self.text = [text]
        self.sublayers = []
        # self.label = self.make_label()
        self.label = "no label"

class BillText(Layer):
    """
    """
    def __init__(self, text):
        # self.name = name
        self.raw_text = text
        self.text = [str(text)]
        self.titles = None
        self.sublayers = []
        self.generator = self.counter()
        self.label = ""
        self.expr = {
            # Title :         r"\({}\)",
            # Subtitle :      r"\({}\)",
            # Chapter :       r"\({}\)",
            # Subchapter :    r"\({}\)",
            # Part :          r"\({}\)",
            # Subpart :       r"\({}\)",
            Section :       r"\s*SECTION *{}\.?\s*",
            Subsection :    r"\({}\)",
            Paragraph :     r"\({}\)",
            Subparagraph :  r"\({}\)",
            Clause :        r"\({}\)",
            Subclause :     r"\({}\)"
        }

    def __str__(self):
        self.format_text()
        if len(self.sublayers) < 2:
            return self.label + "\n\n" + self.full_text
        else:
            # try:
            #     return self.label + "\t" + "\n\n".join([sl.__str__() for sl in self.sublayers])
            # except:
            #     return f"Self is {self}, with sublayers {self.sublayers}"
            return f"self is {self} with sublayers {self.sublayers}"

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
        outer.full_text = ''.join(outer.text)

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
                        for clause in subpar.sublayers:
                            self.lsplit(clause, Subclause)

    def write(self, fname):
        with open(fname, 'w') as fout:
            fout.write(self.__str__())
                                    
