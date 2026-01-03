from django import template
from django.contrib.humanize.templatetags.humanize import intcomma
import locale
import re

register = template.Library()


def _to_float(value):
    if value is None or value == '':
        return None

    if isinstance(value, (int, float)):
        return float(value)

    try:
        return float(value)
    except Exception:
        pass

    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return None

        raw = raw.replace('Rp', '').replace('rp', '')
        raw = raw.replace(' ', '')

        # Normalize Indonesian separators safely
        if '.' in raw and ',' in raw:
            raw = raw.replace('.', '')
            raw = raw.replace(',', '.')
        else:
            if raw.count('.') > 1:
                raw = raw.replace('.', '')
            if raw.count(',') > 1:
                raw = raw.replace(',', '')

        raw = re.sub(r'[^0-9.\-]', '', raw)
        if raw in {'', '-', '.', '-.'}:
            return None
        return float(raw)

    return None


def _short_juta_parts(value, threshold=100000):
    num = _to_float(value)
    if num is None:
        return ('', '0', '')

    try:
        threshold = int(threshold)
    except Exception:
        threshold = 100000

    sign = '-' if num < 0 else ''
    abs_num = abs(num)

    if abs_num >= threshold:
        juta = abs_num / 1_000_000
        formatted = f"{juta:.1f}"
        if formatted.endswith('.0'):
            formatted = formatted[:-2]
        return (sign, formatted, 'juta')

    formatted = f"{int(abs_num):,}".replace(',', '.')
    return (sign, formatted, '')


@register.filter
def short_juta_value(value, threshold=100000):
    sign, formatted, _unit = _short_juta_parts(value, threshold=threshold)
    return f"{sign}{formatted}"


@register.filter
def short_juta_unit(value, threshold=100000):
    _sign, _formatted, unit = _short_juta_parts(value, threshold=threshold)
    return unit

@register.filter
def currency_format(value):
    """
    Format angka menjadi format mata uang Indonesia yang mudah dibaca
    Contoh: 1000000 -> Rp 1.000.000
    """
    if value is None or value == '':
        return 'Rp 0'
    
    try:
        # Konversi ke integer jika string
        if isinstance(value, str):
            value = float(value.replace(',', ''))
        
        # Format dengan pemisah ribuan
        formatted = f"{int(value):,}".replace(',', '.')
        return f"Rp {formatted}"
    except (ValueError, TypeError):
        return 'Rp 0'

@register.filter
def number_format(value):
    """
    Format angka dengan pemisah ribuan
    Contoh: 1000000 -> 1.000.000
    """
    if value is None or value == '':
        return '0'
    
    try:
        if isinstance(value, str):
            value = float(value.replace(',', ''))
        
        formatted = f"{int(value):,}".replace(',', '.')
        return formatted
    except (ValueError, TypeError):
        return '0'

@register.filter
def compact_currency(value):
    """
    Format angka dalam bentuk compact untuk tampilan yang lebih bersih
    Contoh: 1000000 -> Rp 1,0 Jt
    """
    if value is None or value == '':
        return 'Rp 0'
    
    try:
        if isinstance(value, str):
            value = float(value.replace(',', ''))
        
        value = int(value)
        
        if value >= 1000000000:  # Milyar
            formatted = f"{value/1000000000:.1f} M"
        elif value >= 1000000:  # Juta
            formatted = f"{value/1000000:.1f} Jt"
        elif value >= 1000:  # Ribu
            formatted = f"{value/1000:.0f} Rb"
        else:
            formatted = str(value)
        
        return f"Rp {formatted}"
    except (ValueError, TypeError):
        return 'Rp 0'

@register.filter
def format_decimal(value, decimal_places=0):
    """
    Format angka dengan jumlah desimal tertentu
    """
    if value is None or value == '':
        return '0'
    
    try:
        if isinstance(value, str):
            value = float(value.replace(',', ''))
        
        if decimal_places == 0:
            return f"{int(value):,}".replace(',', '.')
        else:
            return f"{float(value):,.{decimal_places}f}".replace(',', '.')
    except (ValueError, TypeError):
        return '0'
