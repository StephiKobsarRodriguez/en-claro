"""Taxonomía de ministerios vigentes y comunidades autónomas.

Los departamentos son los del Real Decreto 829/2023, de 20 de noviembre,
en su texto consolidado (incluye Transportes y Movilidad Sostenible).
El léxico solo elige pasajes. No redacta fichas.
"""

MINISTRIES = [
    {
        "id": "exteriores",
        "name": "Asuntos Exteriores, Unión Europea y Cooperación",
        "short": "Exteriores",
        "keywords": [
            "asuntos exteriores", "politica exterior", "union europea", "unio europea",
            "cooperacion internacional", "servicio exterior", "diplomacia", "diplomatic",
            "geopolit", "embajada", "relaciones internacionales", "politica exterior",
            "palestina", "ucrania", "marruecos", "otan", "frontera exterior",
        ],
    },
    {
        "id": "presidencia",
        "name": "Presidencia, Justicia y Relaciones con las Cortes",
        "short": "Presidencia y Justicia",
        "keywords": [
            "justicia", "justicia", "xustiza", "justicia", "poder judicial",
            "fiscalia", "cortes generales", "congreso de los diputados",
            "calidad democratica", "separacion de poderes", "indulto",
            "consejo general del poder judicial", "turno de oficio",
            "administracion de justicia", "justicia gratuita",
        ],
    },
    {
        "id": "defensa",
        "name": "Defensa",
        "short": "Defensa",
        "keywords": [
            "defensa nacional", "fuerzas armadas", "ejercito", "exercit",
            "gasto militar", "ministerio de defensa", "misiones internacionales",
            "industria de defensa", "militares",
        ],
    },
    {
        "id": "hacienda",
        "name": "Hacienda",
        "short": "Hacienda",
        "keywords": [
            "hacienda", "hisenda", "irpf", "impuesto", "impost", "fiscalidad",
            "fiscalitat", "tribut", "iva", "sociedades", "fraude fiscal",
            "agencia tributaria", "presion fiscal", "tipo impositivo",
        ],
    },
    {
        "id": "interior",
        "name": "Interior",
        "short": "Interior",
        "keywords": [
            "interior", "guardia civil", "policia nacional", "policia", "policia",
            "seguridad ciudadana", "seguretat ciutadana", "seguridade cidadá",
            "prision", "preso", "terroris", "okupa", "okupacio", "proteccion civil",
        ],
    },
    {
        "id": "transportes",
        "name": "Transportes y Movilidad Sostenible",
        "short": "Transportes",
        "keywords": [
            "transporte", "transport", "movilidad", "mobilitat", "ferrocarril",
            "autovia", "autovias", "cercania",
            "cercanias", "rodalies", "renfe", "carretera", "autopista",
            "aeropuerto", "aeroport", "puerto", "portu", "rodaxe",
        ],
    },
    {
        "id": "educacion",
        "name": "Educación, Formación Profesional y Deportes",
        "short": "Educación",
        "keywords": [
            "educacion", "educacio", "ensino", "hezkuntza", "escuela", "escola",
            "alumnado", "formacion profesional", "formacio professional",
            "deporte", "esport", "kirol", "beca", "infantil", "eso",
        ],
    },
    {
        "id": "trabajo",
        "name": "Trabajo y Economía Social",
        "short": "Trabajo",
        "keywords": [
            "empleo", "trabajo", "treball", "traballo", "salario", "salari",
            "jornada", "convenio colectivo", "desempleo", "paro", "autonomo",
            "autonom", "salario minimo", "smi", "economia social", "erte",
        ],
    },
    {
        "id": "industria",
        "name": "Industria y Turismo",
        "short": "Industria y Turismo",
        "keywords": [
            "industria", "industria", "turismo", "turisme", "turismo",
            "reindustrial", "pyme", "pime", "hosteleria", "destino turistico",
        ],
    },
    {
        "id": "agricultura",
        "name": "Agricultura, Pesca y Alimentación",
        "short": "Agricultura",
        "keywords": [
            "agricultura", "agricultura", "pesca", "ganaderia", "gandaria",
            "alimentacion", "alimentacio", "regadio", "pac ", "sector primario",
            "agricultor", "pescador", "pages",
        ],
    },
    {
        "id": "territorial",
        "name": "Política Territorial y Memoria Democrática",
        "short": "Política territorial",
        "keywords": [
            "financiacion autonomica", "financament autonomic", "estatuto de autonomia",
            "estatut", "autogobierno", "autogovern", "autogoberno", "memoria democratica",
            "memoria democratica", "concierto economico", "cupo", "politica territorial",
            "modelo territorial", "foral", "reparto competencial",
        ],
    },
    {
        "id": "transicion",
        "name": "Transición Ecológica y Reto Demográfico",
        "short": "Transición ecológica",
        "keywords": [
            "transicion ecologica", "transicio ecologica", "cambio climatico",
            "emergencia climatica", "energia renovable", "renovable", "biodiversidad",
            "biodiversitat", "sequia", "aigua", "agua", "reto demografico",
            "despoblacion", "despoblament", "nuclear", "emisiones",
        ],
    },
    {
        "id": "vivienda",
        "name": "Vivienda y Agenda Urbana",
        "short": "Vivienda",
        "keywords": [
            "vivienda", "vivenda", "habitatge", "etxebizitza", "alquiler",
            "lloguer", "alokairu", "hipoteca", "desahucio", "desnonament",
            "parque publico", "agenda urbana", "okupacion de viviendas",
        ],
    },
    {
        "id": "cultura",
        "name": "Cultura",
        "short": "Cultura",
        "keywords": [
            "cultura", "kultura", "patrimonio cultural", "patrimoni cultural",
            "cine", "museo", "museu", "industrias culturales", "creacion cultural",
        ],
    },
    {
        "id": "economia",
        "name": "Economía, Comercio y Empresa",
        "short": "Economía",
        "keywords": [
            "modelo economico", "modelo economic", "comercio", "comerc",
            "competitividad", "inflacion", "producto interior", "pib",
            "empresa", "emprended", "politica economica",
        ],
    },
    {
        "id": "sanidad",
        "name": "Sanidad",
        "short": "Sanidad",
        "keywords": [
            "sanidad", "sanitat", "sanidade", "osasun", "salud publica",
            "salut publica", "atencion primaria", "atencio primaria",
            "hospital", "lista de espera", "sistema nacional de salud",
        ],
    },
    {
        "id": "derechos",
        "name": "Derechos Sociales, Consumo y Agenda 2030",
        "short": "Derechos sociales",
        "keywords": [
            "dependencia", "dependencia", "servicios sociales", "serveis socials",
            "cuidados", "cures", "consumo", "consum", "agenda 2030",
            "personas consumidoras", "discapacidad", "discapacitat",
        ],
    },
    {
        "id": "ciencia",
        "name": "Ciencia, Innovación y Universidades",
        "short": "Ciencia",
        "keywords": [
            "ciencia", "ciencia", "investigacion", "recerca", "investigacion",
            "universidad", "universitat", "unibertsitate", "innovacion", "innovacio",
            "i+d", "beca universitaria",
        ],
    },
    {
        "id": "igualdad",
        "name": "Igualdad",
        "short": "Igualdad",
        "keywords": [
            "igualdad", "igualtat", "igualdade", "berdintasun", "feminis",
            "violencia machista", "violencia masclista", "lgtbi", "brecha salarial",
            "permiso parental", "conciliacion",
        ],
    },
    {
        "id": "inclusion",
        "name": "Inclusión, Seguridad Social y Migraciones",
        "short": "Inclusión y migraciones",
        "keywords": [
            "inmigracion", "immigracio", "migracion", "migracio", "asilo",
            "refugiad", "seguridad social", "seguretat social", "pension",
            "pensio", "pentsio", "inclusion social", "inclusion social",
        ],
    },
    {
        "id": "digital",
        "name": "Transformación Digital y Función Pública",
        "short": "Transformación digital",
        "keywords": [
            "transformacion digital", "digitalizacion", "digitalitzacio",
            "inteligencia artificial", "intelligencia artificial",
            "funcion publica", "funcio publica", "administracion electronica",
            "ciberseguridad", "dato publico",
        ],
    },
    {
        "id": "juventud",
        "name": "Juventud e Infancia",
        "short": "Juventud e infancia",
        "keywords": [
            "juventud", "joventut", "juventude", "gazteria", "infancia",
            "infancia", "infancia", "menores", "emancipacion juvenil",
            "derechos de la infancia", "ninez",
        ],
    },
]

COMMUNITIES = [
    {"id": "andalucia", "name": "Andalucía", "provinces": ["04", "11", "14", "18", "21", "23", "29", "41"]},
    {"id": "aragon", "name": "Aragón", "provinces": ["22", "44", "50"]},
    {"id": "asturias", "name": "Asturias", "provinces": ["33"]},
    {"id": "balears", "name": "Illes Balears", "provinces": ["07"]},
    {"id": "canarias", "name": "Canarias", "provinces": ["35", "38"]},
    {"id": "cantabria", "name": "Cantabria", "provinces": ["39"]},
    {"id": "castilla-la-mancha", "name": "Castilla-La Mancha", "provinces": ["02", "13", "16", "19", "45"]},
    {"id": "castilla-y-leon", "name": "Castilla y León", "provinces": ["05", "09", "24", "34", "37", "40", "42", "47", "49"]},
    {"id": "cataluna", "name": "Cataluña", "provinces": ["08", "17", "25", "43"]},
    {"id": "valencia", "name": "Comunitat Valenciana", "provinces": ["03", "12", "46"]},
    {"id": "extremadura", "name": "Extremadura", "provinces": ["06", "10"]},
    {"id": "galicia", "name": "Galicia", "provinces": ["15", "27", "32", "36"]},
    {"id": "madrid", "name": "Comunidad de Madrid", "provinces": ["28"]},
    {"id": "murcia", "name": "Región de Murcia", "provinces": ["30"]},
    {"id": "navarra", "name": "Comunidad Foral de Navarra", "provinces": ["31"]},
    {"id": "euskadi", "name": "País Vasco", "provinces": ["01", "20", "48"]},
    {"id": "rioja", "name": "La Rioja", "provinces": ["26"]},
    {"id": "ceuta", "name": "Ceuta", "provinces": ["51"]},
    {"id": "melilla", "name": "Melilla", "provinces": ["52"]},
]

INSTRUMENTS = {
    "financiacion": ["financi", "presupuesto", "inversion", "dotacion", "partida"],
    "oferta-publica": ["parque publico", "vivienda publica", "habitatge public", "alquiler publico"],
    "incentivos": ["deduccion", "bonificacion", "ayuda", "subvencion", "desgrav"],
    "regulacion": ["ley ", "regular", "prohib", "norma"],
    "coordinacion": ["coordin", "cooperacion entre", "conferencia sectorial"],
    "reforma": ["reforma"],
    "energia": ["energia", "renovable", "electric"],
    "servicios-publicos": ["servicio publico", "servei public", "sanidad publica", "educacion publica"],
    "autogobierno": ["competenc", "estatut", "autogobierno", "autogovern", "foral", "concierto"],
    "adaptacion": ["adaptacion", "resilien"],
}
