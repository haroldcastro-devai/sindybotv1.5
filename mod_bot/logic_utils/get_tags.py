# logica para el extraer las partes de un nombre de archivo de audio

def obtener_gasera_seguro(nombre_archivo: str) -> tuple:
    """
    Extrae el nombre de la gasera y los seguros a partir del nombre del archivo.
    """
    gaseras = {
        "01": "GASES DEL CARIBE",
        "02": "SURTIGAS",
        "03": "GASES DE LA GUAJIRA",
        "04": "GASES DE OCCIDENTE",
        "05": "EFIGAS",
        "06": "CEO",
        "07": "GRUPO VANTI",
        "08": "GASES DE ORIENTE",
        "09": "GASES CUNDIBOYACENSE",
        "10": "GASES DE CESAR"
    }

    seguros = {
        "FUN": "FUNERARIO",
        "SALVA": "SALVAFACTURA",
        "PRACTI": "PRACTISEGURO",
        "FACTURA-P": "FACTURA PROTEGIDA",
        "FUTURO-P-P": "FUTURO PROTEGIDO PLUS",
        "MSCT": "SEGURO MASCOTAS",
        "A": "Parte A del audio",
        "B": "Parte B del audio",
        "C": "Parte C del audio",
        "D": "Parte D del audio",
        "E": "Parte E del audio",
        "F": "Parte F del audio",
        "G": "Parte G del audio",
        "H": "Parte H del audio"
    }

    partes_nombre = nombre_archivo.split("_")

    if len(partes_nombre) >= 6:
        codigo_gasera = partes_nombre[0]
        numero_contrato = partes_nombre[1]
        fecha_contrato = partes_nombre[2]
        nombre_seguro_1 = partes_nombre[3].split(".")[0]
        nombre_seguro_2 = partes_nombre[4].split(".")[0]
        nombre_seguro_3 = partes_nombre[5].split(".")[0]

        gasera = gaseras.get(codigo_gasera, "Gasera desconocida")
        seguro_1 = seguros.get(nombre_seguro_1, "Seguro 1 desconocido")
        seguro_2 = seguros.get(nombre_seguro_2, "Seguro 2 desconocido")
        seguro_3 = seguros.get(nombre_seguro_3, "Seguro 3 desconocido")

        return gasera, numero_contrato, fecha_contrato, seguro_1, seguro_2, seguro_3

    elif len(partes_nombre) == 5:
        codigo_gasera = partes_nombre[0]
        numero_contrato = partes_nombre[1]
        fecha_contrato = partes_nombre[2]
        nombre_seguro_1 = partes_nombre[3].split(".")[0]
        nombre_seguro_2 = partes_nombre[4].split(".")[0]

        gasera = gaseras.get(codigo_gasera, "Gasera desconocida")
        seguro_1 = seguros.get(nombre_seguro_1, "Seguro 1 desconocido")
        seguro_2 = seguros.get(nombre_seguro_2, "Seguro 2 desconocido")

        return gasera, numero_contrato, fecha_contrato, seguro_1, seguro_2, None

    elif len(partes_nombre) == 4:
        codigo_gasera = partes_nombre[0]
        numero_contrato = partes_nombre[1]
        fecha_contrato = partes_nombre[2]
        nombre_seguro_1 = partes_nombre[3].split(".")[0]

        gasera = gaseras.get(codigo_gasera, "Gasera desconocida")
        seguro_1 = seguros.get(nombre_seguro_1, "Seguro 1 desconocido")

        return gasera, numero_contrato, fecha_contrato, seguro_1, None, None

    else:
        return None, None, None, None, None, None