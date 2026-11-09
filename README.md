
# Matematika olami — 4-sinf matematika platformasi

O‘zbek tilidagi Flask + SQLite boshlang‘ich web-ilova. O‘qituvchi o‘quvchilarni boshqaradi, testlar yaratadi, o‘quvchilar login orqali test topshiradi va natijalar saqlanadi.

## Ishga tushirish (kompyuterda)

1. Python 3.10 yoki yangiroq o‘rnating.
2. Terminalda loyiha papkasiga kiring.
3. Virtual muhit va kutubxonalarni o‘rnating:

   ```bash
   python -m venv .venv
   # Windows: .venv\Scripts\activate
   # macOS/Linux: source .venv/bin/activate
   pip install -r requirements.txt
   ```

4. O‘qituvchi login/parolini muhit o‘zgaruvchisi qilib kiriting. Parolni kodga yozmang:

   **Windows PowerShell**
   ```powershell
   $env:TEACHER_USERNAME="Gulmira To‘raqulova"
   $env:TEACHER_PASSWORD="BU_YERGA_O‘QITUVCHI_PAROLINI_KIRITING"
   $env:SECRET_KEY="uzun-tasodifiy-maxfiy-kalit"
   python app.py
   ```

   **macOS/Linux**
   ```bash
   export TEACHER_USERNAME="Gulmira To‘raqulova"
   export TEACHER_PASSWORD="BU_YERGA_O‘QITUVCHI_PAROLINI_KIRITING"
   export SECRET_KEY="uzun-tasodifiy-maxfiy-kalit"
   python app.py
   ```

5. Brauzerda `http://127.0.0.1:5000` manzilini oching.

Birinchi ishga tushishda o‘qituvchi hisobi yaratiladi. Keyingi ishga tushirishlarda hisob bazada saqlanadi. Parolni o‘zgartirish uchun xavfsiz admin parol-almashtirish funksiyasini keyingi versiyada qo‘shish kerak; hozircha dastlabki parolni xavfsiz saqlang.

## Internetga chiqarish va Google orqali ulashish

Bu loyiha hozircha tayyor manba kodidir; ommaviy internet manzili avtomatik yaratilmagan. Ommaviy URL olish uchun uni Render kabi hostingga joylash, doimiy disk yoki PostgreSQL ulash va maxfiy muhit o‘zgaruvchilarini hosting sozlamalarida kiritish kerak. Shundan keyin chiqqan `https://...` manzilini Google Classroom, Google Sites yoki guruh chatiga yuborish mumkin. Google hisobiga kirish shart emas — o‘quvchilar o‘z login/paroli bilan kiradi.

Render uchun:
- GitHub'ga loyiha fayllarini joylang.
- Render'da **New Web Service** tanlab repozitoriyani ulang.
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`
- `TEACHER_USERNAME`, `TEACHER_PASSWORD`, `SECRET_KEY` muhit o‘zgaruvchilarini kiriting.
- SQLite ishlatilsa Render Persistent Disk kerak bo‘ladi; jiddiy foydalanishda PostgreSQL tavsiya etiladi.

## Hozirgi funksiyalar

- O‘qituvchi va o‘quvchi rollari bilan alohida kirish.
- O‘qituvchi o‘quvchi qo‘shishi va hisobini bloklashi/faollashtirishi.
- Har bir uy ishida 50 ta avtomatik matematika savoli.
- Dars testida 20 ta savol.
- 4 oy va har oy 8 ta uy ishi uchun test yaratish formasi.
- O‘quvchi testni topshirgach natijani ko‘rishi.
- O‘qituvchi so‘nggi test natijalarini ko‘rishi.
- Parollar bazada xeshlangan holda saqlanadi.

## Muhim

Bu — ishga tushadigan MVP/prototip. Ommaviy sinfda ishlatishdan oldin HTTPS, CSRF himoyasi, parolni tiklash/almashtirish, avtomatik zaxira nusxa, o‘qituvchi uchun testni tahrirlash/o‘chirish, savollarni pedagogik tekshirish va PostgreSQL kabi ishlab chiqarish sozlamalarini qo‘shish zarur. Avtomatik savollar arifmetik mashq namunalaridir; ularni o‘qituvchi dars dasturiga moslab tekshirishi kerak.
