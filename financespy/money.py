from __future__ import annotations


class Currency:
    """Represents a currency with an acronym and name.

    Args:
        acronym: The currency acronym (e.g., 'USD', 'EUR')
        name: The full currency name (e.g., 'US Dollar')
    """

    def __init__(self, acronym: str, name: str) -> None:
        self.acronym = acronym
        self.name = name

    def __str__(self) -> str:
        return f"{self.acronym} ({self.name})"

    def __repr__(self) -> str:
        return f"Currency('{self.acronym}', '{self.name}')"


def _currency_list_to_dict(currencies: list[Currency]) -> dict[str, Currency]:
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
    """Manager class for currency collections.

    Provides access to currencies by acronym through both method calls
    and attribute access.
    """

    def __init__(
        self, currencies: list[Currency] | dict[str, Currency] | None = None
    ) -> None:
        if currencies is None:
            currencies = _default_currencies

        if isinstance(currencies, list):
            self._currencies = _currency_list_to_dict(currencies)
        else:
            self._currencies = currencies

    def currency(self, name: str) -> Currency:
        """Get currency by acronym.

        Args:
            name: Currency acronym

        Returns:
            Currency object

        Raises:
            KeyError: If currency not found
        """
        if name not in self._currencies:
            raise KeyError(f"Currency '{name}' not found")
        return self._currencies[name]

    def __getattr__(self, name: str) -> Currency:
        if name in self._currencies:
            return self._currencies[name]
        raise AttributeError(f"Currencies object has no attribute '{name}'")

    def __contains__(self, name: str) -> bool:
        return name in self._currencies


class Money:
    """Represents a monetary amount with currency.

    Supports arithmetic operations and currency conversion.
    Internally stores amounts as cents to avoid floating-point precision issues.

    Args:
        value: The monetary value as int, float, str, or Money
        cents: Alternative way to specify value in cents
        currency: The currency for this amount

    Raises:
        ValueError: If neither value nor cents is provided
    """

    def __init__(
        self,
        value: int | float | str | Money | None = None,
        cents: int | float | None = None,
        currency: Currency | None = None,
    ) -> None:
        if value is None and cents is None:
            raise ValueError("Either value or cents must be provided")

        # Handle currency assignment, with special case for Money values
        if isinstance(value, Money) and currency is None:
            self.currency: Currency = value.currency
        else:
            self.currency = (
                currency if currency is not None else _default_currencies["USD"]
            )

        if cents is not None:
            self._cents = int(cents)
            return

        if isinstance(value, str):
            self._set_float(float(value))
        elif isinstance(value, int):
            self._cents = value * 100
        elif isinstance(value, float):
            self._set_float(value)
        elif isinstance(value, Money):
            self._cents = value._cents

    def is_zero(self) -> bool:
        """Check if the amount is zero."""
        return self._cents == 0

    def _set_float(self, val: float) -> None:
        self._cents = int(round(val * 100, 2))

    def __str__(self) -> str:
        val = round(self._cents / 100.0, 2)
        return f"{val:.2f} {self.currency.acronym}"

    def __float__(self) -> float:
        return round(self._cents / 100.0, 2)

    def __int__(self) -> int:
        return int(self._cents)

    def __repr__(self) -> str:
        return f"Money({float(self)}, currency={self.currency.acronym})"

    def __add__(self, val: Money | int | float) -> Money:
        if not isinstance(val, Money):
            val = Money(value=val, currency=self.currency)
        return Money(cents=self._cents + val._cents, currency=self.currency)

    def __radd__(self, val: int | float) -> Money:
        return Money(val).__add__(self)

    def __sub__(self, val: Money | int | float) -> Money:
        if not isinstance(val, Money):
            val = Money(value=val, currency=self.currency)
        return Money(cents=self._cents - val._cents, currency=self.currency)

    def __rsub__(self, val: int | float) -> Money:
        return Money(val).__sub__(self)

    def __mul__(self, val: int | float) -> Money:
        return Money(cents=self._cents * val, currency=self.currency)

    __rmul__ = __mul__

    def __truediv__(self, val: int | float) -> Money:
        return Money(cents=self._cents / val, currency=self.currency)

    def __rtruediv__(self, val: int | float) -> Money:
        return Money(cents=val / (self._cents / 100.0), currency=self.currency)

    def __eq__(self, obj: object) -> bool:
        return isinstance(obj, Money) and obj._cents == self._cents

    def __ne__(self, obj: object) -> bool:
        return not self.__eq__(obj)

    def __lt__(self, obj: object) -> bool:
        if not isinstance(obj, Money):
            return NotImplemented
        return self._cents < obj._cents

    def __le__(self, obj: object) -> bool:
        if not isinstance(obj, Money):
            return NotImplemented
        return self._cents <= obj._cents

    def __ge__(self, obj: object) -> bool:
        if not isinstance(obj, Money):
            return NotImplemented
        return self._cents >= obj._cents

    def __gt__(self, obj: object) -> bool:
        if not isinstance(obj, Money):
            return NotImplemented
        return self._cents > obj._cents

    def __hash__(self) -> int:
        return hash((self._cents, self.currency.acronym))

    def abs(self) -> Money:
        """Return absolute value of the money amount."""
        return Money(cents=abs(self._cents), currency=self.currency)

    def cents(self) -> int:
        """Return the amount in cents."""
        return int(self._cents)


ZERO = Money(0)
