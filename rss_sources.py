"""
Источники RSS и правила фильтрации для автомобилей.
Только российские сайты.
"""

RSS_FEEDS = [
    # Motor.ru — ведущее автомобильное издание
    "https://motor.ru/rss",
    # Drive.ru — обзоры и тест-драйвы
    "https://www.drive.ru/rss",
    # Kolesa.ru — автомобильный онлайн-журнал
    "https://www.kolesa.ru/rss",
    # Auto.ru — новости и обзоры
    "https://auto.ru/mag/rss/",
    # Автовзгляд
    "https://www.avtovzglyad.ru/rss/",
    # АиФ Авто
    "https://aif.ru/rss/automobile.php",
]

CAR_BRANDS = [
    "tesla", "toyota", "volkswagen", "vw", "ford", "honda", "bmw", "mercedes",
    "audi", "porsche", "lamborghini", "ferrari", "mclaren", "aston martin",
    "bentley", "rolls-royce", "cadillac", "chevrolet", "corvette", "dodge",
    "jeep", "ram", "chrysler", "buick", "gmc", "lincoln", "hyundai", "kia",
    "genesis", "nissan", "infiniti", "mazda", "subaru", "mitsubishi", "lexus",
    "volvo", "polestar", "jaguar", "land rover", "mini", "byd", "nio", "xpeng",
    "li auto", "geely", "chery", "haval", "changan", "great wall", "zeekr",
    "lucid", "rivian", "fisker", "bugatti", "koenigsegg", "pagani", "lotus",
    "alpine", "maserati", "peugeot", "citroen", "renault", "dacia", "skoda",
    "seat", "cupra", "opel", "vauxhall", "fiat", "alfa romeo", "lancia",
    "лада", "lada", "москвич", "газ", "уаз", "камаз",
]

AUTO_KEYWORDS = [
    "car", "vehicle", "automobile", "auto", "ev", "electric vehicle",
    "concept car", "concept", "prototype", "premiere", "unveil", "debut",
    "launch", "leak", "rumor", "spy shot", "production model", "roadster",
    "coupe", "sedan", "suv", "crossover", "hatchback", "pickup", "truck",
    "engine", "motor", "horsepower", "hp", "torque", "battery", "range",
    "charging", "autonomous", "self-driving",
    "автомобиль", "машина", "авто", "электромобиль", "электрокар",
    "концепт", "концепткар", "прототип", "премьера", "дебют", "новинка",
    "утечка", "слух", "шпионские фото", "серийная модель", "родстер",
    "купе", "седан", "кроссовер", "внедорожник", "хэтчбек", "пикап", "грузовик",
    "двигатель", "мотор", "лошадиные силы", "крутящий момент", "батарея",
    "запас хода", "зарядка", "автономный", "беспилотный",
]

STOP_WORDS = [
    # ============ МОТОТЕХНИКА ============
    "motorcycle", "motorbike", "scooter", "bike", "atv", "quad",
    "мотоцикл", "мопед", "скутер", "квадроцикл", "снегоход",

    # ============ ЗАПЧАСТИ / АКСЕССУАРЫ ============
    "tire", "tires", "wheel", "wheels", "brake pad", "oil filter",
    "spark plug", "accessory",
    "шины", "колеса", "тормозные колодки", "масляный фильтр", "аксессуары",

    # ============ СТРАХОВКИ / ЗАКОНЫ ============
    "insurance", "tariff", "tax", "fine", "toll", "driving license",
    "страховка", "тариф", "налог", "штраф", "платная дорога", "права",

    # ============ ГОНОЧНЫЕ СЕРИИ ============
    "f1 race result", "nascar race", "motogp race", "formula 1 race",
    "результаты гонки", "формула-1 гонка",

    # ============ НЕ АВТО ============
    "smartphone", "смартфон", "планшет", "tablet", "наушники",
    "бытовая техника", "холодильник", "стиральная машина",
]
