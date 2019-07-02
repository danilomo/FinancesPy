import pandas as pd

class PieSection:
    
    def __init__( self, label, fn ):
        self.label = label
        self.fn = fn
        self.transactions = []
        self.next = None
        
    def add( self, transaction ):
        if self.fn(transaction):
            self.transactions.append(transaction)
            return
        
        if self.next is not None:
            self.next.add(transaction)
            
    def printLL(self):
        print(self.label + str([ (t.value, t.categories[0].__class__.__name__) for t in self.transactions ]))
        if(self.next):
            self.next.printLL()
            
def section( label, fn = None ):
    if fn is None:
        fn = lambda t: t.is_of_category(categories.get_category(label))
        
    return PieSection( label, fn )

def anything_else( label = "Anything else" ):
    return PieSection(label, lambda _: True)

def transaction_list(trans_list):
    for t in trans_list:
        yield parse_transaction(t)


class PieChart:    
    def __init__(self, sections):
        self.sections = sections
        self._make_linked_list()
        self._head = sections[0]
        
    def add_transaction(self,trans):
        self._head.add(trans)
        
    def _make_linked_list(self):
        sections = self.sections
        sect = sections[0]
        
        for s in sections[1:]:
            sect.next = s
            sect = s
            
    def as_data_frame(self):
        labels = [ sc.label for sc in self.sections ]
        values = [ total(sc.transactions) for sc in self.sections]
        return pd.DataFrame({ "values": values, "labels": labels} , index = labels)
