<div dir="rtl" align="right">

# راهنمای استفاده

راهنمای گام‌به‌گام، توضیح همهٔ دستورها و کارهایی که باید وقتی چیزی درست پیش نمی‌رود انجام دهید.

> English: [docs/USAGE.md](USAGE.md)

## فهرست

- [۱. قبل از شروع](#۱-قبل-از-شروع)
- [۲. نصب پچ](#۲-نصب-پچ)
- [۳. بررسی درست کار کردن](#۳-بررسی-درست-کار-کردن)
- [۴. حفظ پچ بعد از آپدیت](#۴-حفظ-پچ-بعد-از-آپدیت)
- [۵. حذف پچ](#۵-حذف-پچ)
- [۶. مرجع دستورها](#۶-مرجع-دستورها)
- [۷. رفع اشکال](#۷-رفع-اشکال)
- [۸. حذف کامل](#۸-حذف-کامل)

---

## ۱. قبل از شروع

| نیازمندی | چطور بررسی کنیم |
| --- | --- |
| ویندوز ۱۰ یا ۱۱ | `winver` |
| QwenWork نصب باشد | پوشهٔ `C:\Program Files\QwenWork` وجود داشته باشد |
| پایتون ۳.۸ یا بالاتر | `python --version` (یا `py --version`) |
| حساب مدیر سیستم | کاربر بتواند پنجرهٔ UAC را تأیید کند |

قبل از اجرای اول، QwenWork را ببندید. اسکریپت خودش هم می‌تواند ببندد، ولی اگر خودتان ببندید پاسخی که در
حال نوشتن است از دست نمی‌رود.

## ۲. نصب پچ

### روش اول — فایل bat (ساده‌ترین)

۱. مخزن را دانلود کنید (**Code → Download ZIP**) و هر جایی که خواستید استخراج کنید.
۲. روی **`QwenWork-RTL.bat`** دوبار کلیک کنید.
۳. گزینهٔ **`1`** (نصب/به‌روزرسانی پچ) را بزنید.
۴. پنجرهٔ UAC ویندوز را تأیید کنید.
۵. صبر کنید تا پیام `[OK] QwenWork: patch installed.` بیاید و برنامه دوباره باز شود.

### روش دوم — خط فرمان

```powershell
git clone https://github.com/neeM4c/qwenwork-rtl.git
cd qwenwork-rtl
python qwenwork_rtl.py --install
```

خروجی معمولاً به این شکل است:

```text
QwenWork RTL + Vazir  v1.0.0

[*] QwenWork: injecting RTL patch...
[*] QwenWork: verifying archive integrity...
[OK] QwenWork: patch installed.

Done.
```

## ۳. بررسی درست کار کردن

۱. یک گفتگوی فارسی را باز کنید؛ باید راست‌چین و با فونت وزیر باشد.
۲. یک جملهٔ فارسی در کادر پیام تایپ کنید؛ کادر باید راست‌چین شود.
۳. از مدل یک جدول یا فهرست بخواهید؛ ستون‌ها و بولت‌ها باید از راست شروع شوند.
۴. یک بلوک کد بفرستید؛ باید چپ‌چین و LTR بماند.

همچنین می‌توانید از خود اسکریپت بپرسید:

```powershell
python qwenwork_rtl.py --status
```

```text
QwenWork RTL + Vazir  v1.0.0

  QwenWork
    archive : C:\Program Files\QwenWork\<version>\resources\app.asar
    installed: True
    patched  : True
    current  : True
    running  : True

    guard    : True RTL Patch Guard
    guard log: C:\Users\<you>\AppData\Local\RTL-Patch\guard.log
    font     : embedded Vazirmatn
```

| فیلد | معنی |
| --- | --- |
| `installed` | QwenWork روی این سیستم پیدا شد. |
| `patched` | آرشیو پچ دارد (هر نسخه‌ای). |
| `current` | پچی است که همین نسخهٔ اسکریپت می‌سازد. اگر `False` بود، `--install` را اجرا کنید. |
| `running` | QwenWork الان باز است. |
| `guard` | نگهبان ثبت شده است. |

## ۴. حفظ پچ بعد از آپدیت

هر آپدیت QwenWork فایل `app.asar` را عوض می‌کند و پچ پاک می‌شود. یک بار نگهبان را نصب کنید:

```powershell
python qwenwork_rtl.py --install-guard
```

نگهبان یک تسک زمان‌بندی‌شده به نام **`RTL Patch Guard`** است که:

- هنگام هر ورود به ویندوز با بالاترین دسترسی اجرا می‌شود (بدون پنجرهٔ UAC)،
- هر ۱۵ ثانیه بیدار می‌شود،
- اگر ببیند آرشیو پچ ندارد و QwenWork بسته است، پچ را برمی‌گرداند.

با `--status` (مقدار `guard: True RTL Patch Guard`) یا در *Task Scheduler* می‌توانید بررسی‌اش کنید. لاگ آن در
`%LOCALAPPDATA%\RTL-Patch\guard.log` است:

```text
2026-01-14 19:12:03 guard started (pid 12172)
2026-01-14 20:44:51 qwenwork: unpatched archive detected; applying patch
2026-01-14 20:44:53 qwenwork: patched
```

اگر نمی‌خواهید برنامه‌ای در پس‌زمینه باشد، این مرحله را رد کنید و بعد از هر آپدیت خودتان `--install` را
اجرا کنید.

## ۵. حذف پچ

```powershell
python qwenwork_rtl.py --restore
```

QwenWork بسته می‌شود، تکهٔ اضافه‌شده حذف می‌شود، آرشیو بررسی می‌شود و برنامه با ظاهر اصلی باز می‌شود.
نگهبان می‌تواند نصب بماند: او یادش می‌ماند که شما ظاهر اصلی را خواسته‌اید (در
`%LOCALAPPDATA%\RTL-Patch\restored.json`) و تا وقتی آپدیت بعدی آرشیو را عوض نکند، کاری نمی‌کند.
اگر نگهبان را هم نمی‌خواهید:

```powershell
python qwenwork_rtl.py --remove-guard
```

## ۶. مرجع دستورها

| دستور | نیاز به مدیر | توضیح |
| --- | :---: | --- |
| `python qwenwork_rtl.py` | — | منوی تعاملی (گزینهٔ پیش‌فرض: نصب). |
| `--install` / `-i` | بله | نصب، ارتقا یا تعمیر پچ. اگر QwenWork باز باشد دوباره راه‌اندازی می‌شود. |
| `--restore` / `-r` | بله | حذف پچ. |
| `--status` | خیر | نمایش وضعیت، بدون هیچ تغییری. |
| `--install-guard` | بله | ثبت نگهبان در زمان ورود به ویندوز. |
| `--remove-guard` | بله | حذف نگهبان. |
| `--watch [--silent]` | بله | اجرای حلقهٔ نگهبان در پیش‌زمینه؛ `--silent` فقط در لاگ می‌نویسد. |

با اضافه‌کردن `--silent` به هر دستور، مکث پایانی («Press Enter») حذف می‌شود؛ برای اسکریپت‌نویسی مناسب است.

کد خروج: `0` موفق، `1` ناموفق (هیچ تغییری نوشته نشده).

## ۷. رفع اشکال

### «archive is locked»

QwenWork هنوز باز است یا یک پروسهٔ کمکی فایل را نگه داشته است.

```powershell
taskkill /F /IM QwenWork.exe /T
python qwenwork_rtl.py --install
```

### «No matching app found for target: all»

QwenWork در مسیرهای پشتیبانی‌شده پیدا نشد:

```text
C:\Program Files\QwenWork
C:\Program Files (x86)\QwenWork
%LOCALAPPDATA%\Programs\QwenWork
```

یک Issue با خروجی `dir "C:\Program Files\QwenWork"` و مسیر نصب خودتان باز کنید.

### پچ نصب شد ولی ظاهر عوض نشد

پنجره را با `Ctrl+R` رفرش کنید. اگر هنگام پچ باز بوده، کامل ببندید (آیکون سینی → Quit) و دوباره باز کنید.

### فارسی راست‌چین شد ولی فونت وزیر نیست

در آن پنل یک قاعدهٔ CSS خاص‌تر برنده شده است. یک Issue با اسکرین‌شات باز کنید — فهرست سلکتورها یک بلوک
در `qwenwork_rtl.py` است.

### بعد از آپدیت پچ پاک می‌شود

طبیعی است: آپدیت آرشیو را عوض می‌کند. نگهبان را نصب کنید (بخش ۴).

### آنتی‌ویروس یا Windows Defender هشدار می‌دهد

اسکریپت فایلی داخل `Program Files` را بازنویسی می‌کند و یک تسک زمان‌بندی‌شده می‌سازد؛ بعضی اسکنرها این را
مشکوک می‌دانند. کد کامل یک فایل پایتون ساده است و هیچ چیزی دانلود نمی‌کند.

### پایتون شناخته نمی‌شود

از [python.org](https://www.python.org/downloads/windows/) نصب کنید و تیک **Add python.exe to PATH** را
بزنید. روی بعضی سیستم‌ها `py --version` کار می‌کند ولی `python` نه.

## ۸. حذف کامل

```powershell
python qwenwork_rtl.py --restore
python qwenwork_rtl.py --remove-guard
```

بعد پوشهٔ استخراج‌شده را پاک کنید و اگر خواستید پوشهٔ وضعیت را هم:

```powershell
Remove-Item "$env:LOCALAPPDATA\RTL-Patch" -Recurse -Force
```

چیز دیگری باقی نمی‌ماند: نه سرویسی، نه کلید رجیستری، نه فایلی داخل پوشهٔ QwenWork.

</div>
