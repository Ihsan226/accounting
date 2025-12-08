from django import template
from django.contrib.humanize.templatetags.humanize import intcomma
import locale

register = template.Library()

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
