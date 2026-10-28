"""
Источники RSS и правила фильтрации для автомобилей.
Только крупные мировые издания с надёжными RSS-лентами.
"""

RSS_FEEDS = [
    # --- Англоязычные ---
    "https://insideevs.com/rss/category/artificial-intelligence/",
    "https://www.carscoops.com/feed/",
    "https://www.motor1.com/rss/",
    "https://jalopnik.com/rss",
    "https://www.caranddriver.com/rss/all.xml",
    "https://www.autoblog.com/rss.xml",
    "https://electrek.co/feed/",
    # --- Русскоязычные ---
    "https://motor.ru/exports/rss",
    "https://www.drive.ru/rss",
    "https://www.autonews.ru/rss",
    "https://www.kolesa.ru/rss",
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
    "лада", "lada", "москвич", "газ", "уаз", "камаз", "yangwang",
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
    # МОТОТЕХНИКА
    "motorcycle", "motorbike", "scooter", "bike", "atv", "quad",
    "мотоцикл", "мопед", "скутер", "квадроцикл", "снегоход",
    # ЗАПЧАСТИ / АКСЕССУАРЫ
    "tire", "tires", "wheel", "wheels", "brake pad", "oil filter",
    "spark plug", "accessory",
    "шины", "колеса", "тормозные колодки", "масляный фильтр", "аксессуары",
    # ЩЁТКИ / ДВОРНИКИ
    "щетк", "щётк", "стеклоочистител", "дворник",
    "wiper", "wipers", "windshield washer",
    "омывател", "антифриз", "моторное масло", "тосол",
    # СОВЕТЫ / ИНСТРУКЦИИ
    "как выбрать", "как заменить", "как проверить", "как ухаживать",
    "совет", "советы", "инструкция", "лайфхак", "how to", "tips", "advice",
    # РЕЙТИНГИ
    "топ-", "топ ", "top-", "top 10", "top 5",
    "рейтинг", "rating", "лучших", "лучшие",
    "худших", "худшие", "worse", "worst",
    # СТРАХОВКИ / ЗАКОНЫ
    "insurance", "tariff", "tax", "fine", "toll", "driving license",
    "страховка", "тариф", "налог", "штраф", "платная дорога", "права",
    # ГОНКИ
    "f1 race result", "nascar race", "motogp race", "formula 1 race",
    "результаты гонки", "формула-1 гонка",
    # НЕ АВТО
    "smartphone", "смартфон", "планшет", "tablet", "наушники",
    "бытовая техника", "холодильник", "стиральная машина",
]
