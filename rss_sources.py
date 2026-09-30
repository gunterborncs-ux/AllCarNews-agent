# rss_sources.py
"""
Источники RSS и правила фильтрации для тематики:
только автомобили, концепткары, электромобили.
"""

RSS_FEEDS = [
    # --- Англоязычные ---
    "https://insideevs.com/rss/category/artificial-intelligence/", # InsideEVs (AI & EV)
    "https://www.carscoops.com/feed/",                             # Carscoops
    "https://www.motor1.com/rss/",                                 # Motor1
    "https://jalopnik.com/rss",                                    # Jalopnik
    "https://www.caranddriver.com/rss/all.xml",                    # Car and Driver
    "https://www.autoblog.com/rss.xml",                            # Autoblog
    "https://electrek.co/feed/",                                   # Electrek (EV)
    # --- Русскоязычные ---
    "https://motor.ru/exports/rss",                                # Motor.ru
    "https://www.drive.ru/rss",                                    # Drive.ru
    "https://www.autonews.ru/rss",                                 # Autonews.ru (РБК)
    "https://www.kolesa.ru/rss",                                   # Kolesa.ru
]

# ---------------------------------------------------------------------------
# Правило фильтрации:
#   статья проходит, если содержит >= 1 маркер из CAR_BRANDS
#   ИЛИ >= 1 маркер из AUTO_KEYWORDS,
#   И НЕ содержит ни одного стоп-слова из STOP_WORDS.
# ---------------------------------------------------------------------------

# Марки автомобилей (в нижнем регистре)
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
]

# Общие слова про автомобили, новинки и концепты
AUTO_KEYWORDS = [
    # Английские
    "car", "vehicle", "automobile", "auto", "ev", "electric vehicle",
    "concept car", "concept", "prototype", "premiere", "unveil", "debut",
    "launch", "leak", "rumor", "spy shot", "production model", "roadster",
    "coupe", "sedan", "suv", "crossover", "hatchback", "pickup", "truck",
    "engine", "motor", "horsepower", "hp", "torque", "battery", "range",
    "charging", "autonomous", "self-driving",
    # Русские
    "автомобиль", "машина", "авто", "электромобиль", "электрокар",
    "концепт", "концепткар", "прототип", "премьера", "дебют", "новинка",
    "утечка", "слух", "шпионские фото", "серийная модель", "родстер",
    "купе", "седан", "кроссовер", "внедорожник", "хэтчбек", "пикап", "грузовик",
    "двигатель", "мотор", "лошадиные силы", "крутящий момент", "батарея",
    "запас хода", "зарядка", "автономный", "беспилотный",
]

# Стоп-слова: если статья содержит хотя бы одно — отбрасываем
STOP_WORDS = [
    # Мотоциклы
    "motorcycle", "motorbike", "scooter", "bike", "atv", "quad",
    "мотоцикл", "мопед", "скутер", "квадроцикл",
    # Запчасти и аксессуары (не про сами авто)
    "tire", "wheel", "brake pad", "oil filter", "spark plug", "accessory",
    "шины", "колеса", "тормозные колодки", "масляный фильтр", "аксессуары",
    # Тарифы, страховки, законы
    "insurance", "tariff", "tax", "fine", "toll", "driving license",
    "страховка", "тариф", "налог", "штраф", "платная дорога", "права",
    # Гоночные серии (если это не про новую модель)
    "f1 race result", "nascar race", "motogp race", "formula 1 race",
    "результаты гонки", "формула-1 гонка",
]
