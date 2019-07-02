class Money:
    def __init__(self, value = None, cents = None):

        if value is None and cents is None:
            raise AttributeError("Invalid arguments.")

        if cents is not None:
            self._cents = cents
            return

        if( isinstance(value, str) ):
            self._set_float( float(value) )
        elif( isinstance(value, int) ):
            self._cents = value * 100
        elif( isinstance(value, float) ):
            self._set_float( value )
        elif( isinstance(value, Money) ):
            self._cents = value._cents

    def is_zero(self):
        return self._cents == 0

    def _set_float( self, val ):
        self._cents = round( val * 100, 2)

    def __str__( self ):
        val = round(self._cents / 100.0, 2)
        return str( val )

    def __float__(self):
         return round(self._cents / 100.0, 2)

    def __repr__( self ):
        return self.__str__()

    def __add__(self, val):
        other = val
        if not isinstance(val, Money):
            other = Money(val)
        return Money( cents = self._cents + other._cents )

    def __radd__(self, val):
        other = Money(val)
        return other.__add__(self)

    def __sub__(self, val):
        other = val
        if not isinstance(val, Money):
            other = Money(val)
        return Money( cents = self._cents - other._cents )

    def __rsub__(self, val):
        other = Money(val)
        return other.__sub__(self)

    def __mul__(self, val):
        return Money( cents = self._cents * val  )

    __rmul__ = __mul__

    def __truediv__(self, val):
        return Money( cents = self._cents / val  )

    __rtruediv__ = __truediv__

    def __eq__(self, obj):
        return isinstance(obj,Money) and obj._cents == self._cents

    def abs(self):
        return Money( cents = abs(self._cents) )

ZERO = Money(0)
