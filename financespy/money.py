class Currency:
    def __init__(self, acronym, name):
        self.acronym = acronym
        self.name = name


def _currency_list_to_dict(currencies):
    return {currency.acronym: currency for currency in currencies}


_default_currencies = _currency_list_to_dict(
    [
        Currency("AUD", "Australia Dollar"),
        Currency("GBP", "Great Britain Pound"),
        Currency("JPY", "Japan Yen"),
        Currency("CHF", "Switzerland Franc"),
        Currency("USD", "USA Dollar"),
        Currency("AFN", "Afghanistan Afghani"),
        Currency("ALL", "Albania Lek"),
        Currency("DZD", "Algeria Dinar"),
        Currency("AOA", "Angola Kwanza"),
        Currency("ARS", "Argentina Peso"),
        Currency("AMD", "Armenia Dram"),
        Currency("AWG", "Aruba Florin"),
        Currency("AUD", "Australia Dollar"),
        Currency("AZN", "Azerbaijan New Manat"),
        Currency("BSD", "Bahamas Dollar"),
        Currency("BHD", "Bahrain Dinar"),
        Currency("BDT", "Bangladesh Taka"),
        Currency("BBD", "Barbados Dollar"),
        Currency("BYR", "Belarus Ruble"),
        Currency("BZD", "Belize Dollar"),
        Currency("BMD", "Bermuda Dollar"),
        Currency("BTN", "Bhutan Ngultrum"),
        Currency("BOB", "Bolivia Boliviano"),
        Currency("BAM", "Bosnia Mark"),
        Currency("BWP", "Botswana Pula"),
        Currency("BRL", "Brazil Real"),
        Currency("GBP", "Great Britain Pound"),
        Currency("BND", "Brunei Dollar"),
        Currency("BGN", "Bulgaria Lev"),
        Currency("BIF", "Burundi Franc"),
        Currency("XOF", "CFA Franc BCEAO"),
        Currency("XAF", "CFA Franc BEAC"),
        Currency("XPF", "CFP Franc"),
        Currency("KHR", "Cambodia Riel"),
        Currency("CAD", "Canada Dollar"),
        Currency("CVE", "Cape Verde Escudo"),
        Currency("KYD", "Cayman Islands Dollar"),
        Currency("CLP", "Chili Peso"),
        Currency("CNY", "China Yuan/Renminbi"),
        Currency("COP", "Colombia Peso"),
        Currency("KMF", "Comoros Franc"),
        Currency("CDF", "Congo Franc"),
        Currency("CRC", "Costa Rica Colon"),
        Currency("HRK", "Croatia Kuna"),
        Currency("CUC", "Cuba Convertible Peso"),
        Currency("CUP", "Cuba Peso"),
        Currency("CZK", "Czech Koruna"),
        Currency("DKK", "Denmark Krone"),
        Currency("DJF", "Djibouti Franc"),
        Currency("DOP", "Dominican Republich Peso"),
        Currency("XCD", "East Caribbean Dollar"),
        Currency("EGP", "Egypt Pound"),
        Currency("SVC", "El Salvador Colon"),
        Currency("ETB", "Ethiopia Birr"),
        Currency("EUR", "Euro"),
        Currency("FKP", "Falkland Islands Pound"),
        Currency("FJD", "Fiji Dollar"),
        Currency("GMD", "Gambia Dalasi"),
        Currency("GEL", "Georgia Lari"),
        Currency("GHS", "Ghana New Cedi"),
        Currency("GIP", "Gibraltar Pound"),
        Currency("GTQ", "Guatemala Quetzal"),
        Currency("GNF", "Guinea Franc"),
        Currency("GYD", "Guyana Dollar"),
        Currency("HTG", "Haiti Gourde"),
        Currency("HNL", "Honduras Lempira"),
        Currency("HKD", "Hong Kong Dollar"),
        Currency("HUF", "Hungary Forint"),
        Currency("ISK", "Iceland Krona"),
        Currency("INR", "India Rupee"),
        Currency("IDR", "Indonesia Rupiah"),
        Currency("IRR", "Iran Rial"),
        Currency("IQD", "Iraq Dinar"),
        Currency("ILS", "Israel New Shekel"),
        Currency("JMD", "Jamaica Dollar"),
        Currency("JPY", "Japan Yen"),
        Currency("JOD", "Jordan Dinar"),
        Currency("KZT", "Kazakhstan Tenge"),
        Currency("KES", "Kenya Shilling"),
        Currency("KWD", "Kuwait Dinar"),
        Currency("KGS", "Kyrgyzstan Som"),
        Currency("LAK", "Laos Kip"),
        Currency("LBP", "Lebanon Pound"),
        Currency("LSL", "Lesotho Loti"),
        Currency("LRD", "Liberia Dollar"),
        Currency("LYD", "Libya Dinar"),
        Currency("MOP", "Macau Pataca"),
        Currency("MKD", "Macedonia Denar"),
        Currency("MGA", "Malagasy Ariary"),
        Currency("MWK", "Malawi Kwacha"),
        Currency("MYR", "Malaysia Ringgit"),
        Currency("MVR", "Maldives Rufiyaa"),
        Currency("MRO", "Mauritania Ouguiya"),
        Currency("MUR", "Mauritius Rupee"),
        Currency("MXN", "Mexico Peso"),
        Currency("MDL", "Moldova Leu"),
        Currency("MNT", "Mongolia Tugrik"),
        Currency("MAD", "Morocco Dirham"),
        Currency("MZN", "Mozambique New Metical"),
        Currency("MMK", "Myanmar Kyat"),
        Currency("ANG", "NL Antilles Guilder"),
        Currency("NAD", "Namibia Dollar"),
        Currency("NPR", "Nepal Rupee"),
        Currency("NZD", "New Zealand Dollar"),
        Currency("NIO", "Nicaragua Cordoba Oro"),
        Currency("NGN", "Nigeria Naira"),
        Currency("KPW", "North Korea Won"),
        Currency("NOK", "Norway Kroner"),
        Currency("OMR", "Oman Rial"),
        Currency("PKR", "Pakistan Rupee"),
        Currency("PAB", "Panama Balboa"),
        Currency("PGK", "Papua New Guinea Kina"),
        Currency("PYG", "Paraguay Guarani"),
        Currency("PEN", "Peru Nuevo Sol"),
        Currency("PHP", "Philippines Peso"),
        Currency("PLN", "Poland Zloty"),
        Currency("QAR", "Qatar Rial"),
        Currency("RON", "Romania New Lei"),
        Currency("RUB", "Russia Rouble"),
        Currency("RWF", "Rwanda Franc"),
        Currency("WST", "Samoa Tala"),
        Currency("STD", "Sao Tome/Principe Dobra"),
        Currency("SAR", "Saudi Arabia Riyal"),
        Currency("RSD", "Serbia Dinar"),
        Currency("SCR", "Seychelles Rupee"),
        Currency("SLL", "Sierra Leone Leone"),
        Currency("SGD", "Singapore Dollar"),
        Currency("SBD", "Solomon Islands Dollar"),
        Currency("SOS", "Somali Shilling"),
        Currency("ZAR", "South Africa Rand"),
        Currency("KRW", "South Korea Won"),
        Currency("LKR", "Sri Lanka Rupee"),
        Currency("SHP", "St Helena Pound"),
        Currency("SDG", "Sudan Pound"),
        Currency("SRD", "Suriname Dollar"),
        Currency("SZL", "Swaziland Lilangeni"),
        Currency("SEK", "Sweden Krona"),
        Currency("CHF", "Switzerland Franc"),
        Currency("SYP", "Syria Pound"),
        Currency("TWD", "Taiwan Dollar"),
        Currency("TZS", "Tanzania Shilling"),
        Currency("THB", "Thailand Baht"),
        Currency("TOP", "Tonga Pa'anga"),
        Currency("TTD", "Trinidad/Tobago Dollar"),
        Currency("TND", "Tunisia Dinar"),
        Currency("TRY", "Turkish New Lira"),
        Currency("TMM", "Turkmenistan Manat"),
        Currency("USD", "USA Dollar"),
        Currency("UGX", "Uganda Shilling"),
        Currency("UAH", "Ukraine Hryvnia"),
        Currency("UYU", "Uruguay Peso"),
        Currency("AED", "United Arab Emirates Dirham"),
        Currency("VUV", "Vanuatu Vatu"),
        Currency("VEB", "Venezuela Bolivar"),
        Currency("VND", "Vietnam Dong"),
        Currency("YER", "Yemen Rial"),
        Currency("ZMK", "Zambia Kwacha"),
        Currency("ZWD", "Zimbabwe Dollar"),
    ]
)


class Currencies:
    def __init__(self, currencies=_default_currencies):
        if type(currencies) is list:
            self._currencies = _currency_list_to_dict(currencies)
        else:
            self._currencies = currencies

    def currency(self, name):
        return self._currencies[name]

    def __getattr__(self, name):
        if name in self._currencies:
            return self._currencies[name]

        raise AttributeError("Transaction object has no atrribute '%s'" % name)


class Money:
    def __init__(self, value=None, cents=None, currency=_default_currencies["USD"]):
        self.currency = currency

        if value is None and cents is None:
            raise AttributeError("Invalid arguments.")

        if cents is not None:
            self._cents = cents
            return

        if isinstance(value, str):
            self._set_float(float(value))
        elif isinstance(value, int):
            self._cents = value * 100
        elif isinstance(value, float):
            self._set_float(value)
        elif isinstance(value, Money):
            self._cents = value._cents

    def is_zero(self):
        return self._cents == 0

    def _set_float(self, val):
        self._cents = round(val * 100, 2)

    def __str__(self):
        val = round(self._cents / 100.0, 2)
        return str(val)

    def __float__(self):
        return round(self._cents / 100.0, 2)

    def __int__(self):
        return int(self._cents)

    def __repr__(self):
        return self.__str__()

    def __add__(self, val):
        other = val
        if not isinstance(val, Money):
            other = Money(value=val, currency=self.currency)
        return Money(cents=self._cents + other._cents)

    def __radd__(self, val):
        other = Money(val)
        return other.__add__(self)

    def __sub__(self, val):
        other = val
        if not isinstance(val, Money):
            other = Money(value=val, currency=self.currency)
        return Money(cents=self._cents - other._cents)

    def __rsub__(self, val):
        other = Money(val)
        return other.__sub__(self)

    def __mul__(self, val):
        return Money(cents=self._cents * val)

    __rmul__ = __mul__

    def __truediv__(self, val):
        return Money(cents=self._cents / val)

    __rtruediv__ = __truediv__

    def __eq__(self, obj):
        return isinstance(obj, Money) and obj._cents == self._cents

    def __ne__(self, obj):
        return not self.__eq__(obj)

    def __lt__(self, obj):
        return self._cents < obj._cents

    def __le__(self, obj):
        return self._cents <= obj._cents

    def __ge__(self, obj):
        return self._cents >= obj._cents

    def __gt__(self, obj):
        return self._cents > obj._cents

    def __hash__(self):
        return self._cents.__hash__()

    def abs(self):
        return Money(cents=abs(self._cents))

    def cents(self):
        return int(self._cents)


ZERO = Money(0)
