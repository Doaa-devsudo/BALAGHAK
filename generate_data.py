"""Generate a synthetic dataset of municipal reports (بلاغات) for the demo.

Output: data/reports.json and data/reports.csv
All data is simulated.
"""
import csv
import json
import random
from datetime import datetime, timedelta

random.seed(42)

N_RANDOM = 80  # random reports, plus the repeated-location clusters below

NEIGHBORHOODS = {
    "حطين": ["طريق الأمير محمد بن سعد", "شارع الأمير مشعل", "شارع رابغ"],
    "النرجس": ["طريق أبو بكر الصديق", "شارع عثمان بن عفان", "شارع الثمامة"],
    "الملقا": ["طريق الملك فهد", "شارع أنس بن مالك", "شارع الأمير سلطان"],
    "الياسمين": ["شارع الملك عبدالعزيز", "شارع الياسمين", "شارع المحمدية"],
    "العليا": ["شارع التحلية", "شارع العليا العام", "شارع موسى بن نصير"],
    "الربوة": ["شارع الأحساء", "شارع الصناعة", "شارع الخليل بن أحمد"],
    "السويدي": ["شارع السويدي العام", "شارع العروبة", "شارع ديراب"],
    "الصحافة": ["شارع الصحافة", "طريق الملك عبدالعزيز", "شارع الخير"],
}

RESTAURANTS = ["مطعم البيك الذهبي", "مطعم شاورما الحي", "بوفية النخيل", "مخبز السنابل",
               "مطعم المندي الملكي", "كافيه الزاوية", "بقالة الأمانة", "سوبرماركت الوفرة"]

# (text template, priority). {street} and {place} are filled in later.
TEMPLATES = {
    "الطرق والأرصفة": [
        ("فيه حفرة كبيرة في {street} والسيارات تنزل فيها، خطيرة مرة", "عاجلة"),
        ("الشارع خربان كله تشققات في {street}، صار له شهور كذا", "متوسطة"),
        ("فيه انخساف في الطريق عند {street} قريب الإشارة", "عاجلة"),
        ("غطاء المنهول مفقود في {street} والفتحة مكشوفة", "عاجلة"),
        ("الرصيف مكسور قدام المسجد في {street} والناس ما تقدر تمشي", "متوسطة"),
        ("البلاط مقلوع في رصيف {street}", "منخفضة"),
        ("فيه مطب عشوائي في {street} يخرب السيارات", "متوسطة"),
        ("المقاول خلص الحفريات في {street} وترك الردم والحفرة بدون سفلتة", "متوسطة"),
        ("كل ما تمطر تتجمع المويه في {street} بسبب الإسفلت", "متوسطة"),
        ("حفرة قريب مدرسة البنات في {street}، الأطفال يمرون جنبها", "عاجلة"),
        ("نبي مطب في {street} السيارات تسرع وفيه أطفال", "منخفضة"),
        ("الإسفلت متشقق شوي في {street}", "منخفضة"),
    ],
    "صحة البيئة والمنشآت الغذائية": [
        ("طلبت من {place} في {street} والأكل كان ريحته خايسة", "عاجلة"),
        ("أكلت من {place} وجاني تسمم أنا وأخوي", "عاجلة"),
        ("شفت صراصير في مطبخ {place} في {street}", "عاجلة"),
        ("{place} يبيع منتجات منتهية الصلاحية، لقيت حليب منتهي", "متوسطة"),
        ("العامل في {place} ما يلبس قفازات ولا غطاء راس", "متوسطة"),
        ("{place} حاطين اللحم برا الثلاجة على الأرض", "متوسطة"),
        ("الأكل اللي جاني من {place} مو مطبوخ زين ولونه غريب", "عاجلة"),
        ("صالة الأكل في {place} وسخة والطاولات ما تنمسح", "منخفضة"),
        ("فيه فار طلع من مطبخ {place} في {street}", "عاجلة"),
        ("{place} يبيع خبز فيه عفن", "متوسطة"),
        ("فيه بياع أكل في الشارع عند {street} بدون ترخيص", "متوسطة"),
        ("أرضية {place} وسخة وريحة المكان مو حلوة", "منخفضة"),
    ],
    "النظافة العامة": [
        ("الحاوية في {street} مليانة ولها ثلاث أيام ما أحد فضاها", "متوسطة"),
        ("فيه قطة ميتة في نص {street}", "عاجلة"),
        ("أحد رامي مخلفات بناء في الأرض الفضاء في {street}", "متوسطة"),
        ("الزبالة متراكمة جنب المدرسة في {street} والريحة قوية", "عاجلة"),
        ("الحاوية مكسورة في {street} والزبالة طايحة على الأرض", "منخفضة"),
        ("فيه كنب وأثاث قديم مرمي في {street}", "متوسطة"),
        ("نبي حاوية زيادة في {street} الموجودة ما تكفي", "منخفضة"),
        ("الكراتين والزبالة سادة الطريق في {street}", "عاجلة"),
        ("ريحة الزبالة في {street} ما تنطاق", "متوسطة"),
        ("الشارع وسخ في {street} ومحد ينظفه", "منخفضة"),
        ("أنقاض وردم مرمية قدام البيوت في {street}", "متوسطة"),
        ("كلب ميت على جنب {street}", "عاجلة"),
    ],
}

STATUSES = ["جديد", "قيد المعالجة", "مغلق"]
STATUS_WEIGHTS = [0.4, 0.35, 0.25]

START = datetime(2026, 10, 20)
END = datetime(2026, 11, 18)


def random_date():
    delta = END - START
    return START + timedelta(seconds=random.randint(0, int(delta.total_seconds())))


def make_report(department, template, priority, neighborhood, street, place, created_at):
    text = template.format(street=street, place=place)
    return {
        "department": department,
        "text": text,
        "neighborhood": neighborhood,
        "street": street,
        "facility": place if "{place}" in template else "",
        "priority": priority,
        "status": random.choices(STATUSES, STATUS_WEIGHTS)[0],
        "created_at": created_at.strftime("%Y-%m-%d %H:%M"),
    }


def random_report():
    department = random.choice(list(TEMPLATES))
    template, priority = random.choice(TEMPLATES[department])
    neighborhood = random.choice(list(NEIGHBORHOODS))
    street = random.choice(NEIGHBORHOODS[neighborhood])
    place = random.choice(RESTAURANTS)
    return make_report(department, template, priority, neighborhood, street, place, random_date())


def cluster(department, texts, priority, neighborhood, street, place=""):
    """Several reports about the SAME location, a few hours/days apart."""
    base = random_date() - timedelta(days=3)
    reports = []
    for i, text in enumerate(texts):
        r = make_report(department, text, priority, neighborhood, street, place,
                        base + timedelta(hours=random.randint(2, 20) * (i + 1)))
        r["status"] = "جديد"
        reports.append(r)
    return reports


def main():
    reports = [random_report() for _ in range(N_RANDOM)]

    # Repeated reports about the same place (for the "repeated reports" feature)
    reports += cluster("الطرق والأرصفة", [
        "فيه حفرة كبيرة في طريق الأمير محمد بن سعد والسيارات تنزل فيها",
        "حفرة عند طريق الأمير محمد بن سعد قريب الإشارة، خربت كفر سيارتي",
        "الشارع خربان في طريق الأمير محمد بن سعد في حطين، فيه حفرة خطيرة",
        "تكفون صلحوا الحفرة اللي في طريق الأمير محمد بن سعد",
    ], "عاجلة", "حطين", "طريق الأمير محمد بن سعد")

    reports += cluster("صحة البيئة والمنشآت الغذائية", [
        "أكلت من مطعم شاورما الحي وجاني تسمم",
        "مطعم شاورما الحي في شارع أنس بن مالك الأكل ريحته خايسة",
        "شفت صراصير في مطعم شاورما الحي",
    ], "عاجلة", "الملقا", "شارع أنس بن مالك", "مطعم شاورما الحي")

    reports += cluster("النظافة العامة", [
        "الحاوية في شارع الثمامة مليانة ولها أسبوع",
        "الزبالة طايحة حول الحاوية في شارع الثمامة",
        "ريحة الزبالة في شارع الثمامة في النرجس ما تنطاق",
    ], "متوسطة", "النرجس", "شارع الثمامة")

    reports.sort(key=lambda r: r["created_at"])
    for i, r in enumerate(reports, start=1):
        r["id"] = f"RPT-{1000 + i}"

    fields = ["id", "text", "department", "neighborhood", "street", "facility",
              "priority", "status", "created_at"]
    reports = [{k: r[k] for k in fields} for r in reports]

    with open("data/reports.json", "w", encoding="utf-8") as f:
        json.dump(reports, f, ensure_ascii=False, indent=2)
    with open("data/reports.csv", "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(reports)

    print(f"Generated {len(reports)} reports")


if __name__ == "__main__":
    main()
