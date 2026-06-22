def clean_and_format_row(row: list, headers: list) -> list:
    """Limpia y formatea una fila completa basándose en sus encabezados."""
    cleaned_row = []

    for i, value in enumerate(row):
        if i >= len(headers):
            cleaned_row.append(value)
            continue

        header = headers[i]

        # Remover comillas del inicio
        if isinstance(value, str) and value.startswith("'"):
            value = value[1:]

        # Convertir montos a números
        numeric_keywords = [
            'cantidad', 'qty', 'monto', 'amount', 'precio', 'price',
            'bruto', 'neto', 'impuesto', 'tax', 'descuento', 'discount', 'total'
        ]

        if any(keyword in header.lower() for keyword in numeric_keywords):
            try:
                if value and str(value).strip():
                    num_value = float(str(value))
                    # Convertir a int si no tiene decimales
                    value = int(num_value) if num_value == int(num_value) else round(num_value, 2)
            except (ValueError, TypeError):
                pass

        cleaned_row.append(value)

    return cleaned_row
