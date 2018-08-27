import datetime
import financespy.time_factory as time_factory

_current_year = datetime.datetime.now().year

class Account:
    def __init__( self, backend ):
        self.timef = time_factory.TimeFactory( backend )
        
    def day(self, day, month, year = _current_year ):
        return self.timef.month(month,year).day(day)

    def month(self,month,year = _current_year):
        return self.timef.month(month, year)
