# عامل AI فروش برای وردپرس (FastAPI + LangChain)

یک API مبتنی بر FastAPI برای کسب‌وکارهای تجارت الکترونیکی با ویژگی‌های زیر:
- چت پشتیبانی مشتریان دارای هوش مصنوعی
- پاسخ به سوالات محصول (موجودی، تعداد موجود، توضیحات)
- جریان فروش (افزودن به سبد خرید و تغییر مسیر به صفحه پرداخت)
- خط لوله RAG از داده‌های MySQL وردپرس/ووکامرس
- پشتیبانی از Gemini LLM از طریق Google AI Studio

## معماری

- `app/main.py`: نقطه ورود API
- `app/core/config.py`: پیکربندی مبتنی بر متغیرهای محیط
- `app/core/database.py`: موتور و جلسه SQLAlchemy async
- `app/services/wordpress/repository.py`: دسترسی به محصولات و موجودی از پایگاه داده WP
- `app/services/rag/retriever.py`: سازنده متن RAG از داده‌های محصول WP
- `app/services/llm/providers.py`: کارخانه ارائه‌دهنده LLM قابل توسعه
- `app/services/agent/customer_agent.py`: هماهنگی عامل LangChain
- `app/services/wordpress/cart_service.py`: منطق سبد خرید و پرداخت
- `app/routers/*.py`: نقاط پایانی REST

## شروع سریع

### پیش‌نیازها

- Python 3.10+
- MySQL Server (یا استفاده از Docker Compose)
- API Key برای Google Gemini (یا OpenAI/DeepSeek)

### نصب و راه‌اندازی

#### 1. کپی کردن فایل محیط:

```bash
cp .env.example .env
```

#### 2. تنظیم متغیرهای محیط (.env):

فایل `.env` را باز کنید و موارد زیر را تنظیم کنید:

```env
# اطلاعات اتصال MySQL/وردپرس
MYSQL_HOST=your_mysql_host
MYSQL_PORT=3306
MYSQL_USER=your_wordpress_db_user
MYSQL_PASSWORD=your_secure_password
MYSQL_DB=wordpress

# انتخاب ارائه‌دهنده LLM و کلید API
LLM_PROVIDER=gemini  # یا: openai, deepseek, openai_compatible
GEMINI_API_KEY=your_google_api_key_here

# URL پرداخت وردپرس شما
WP_CHECKOUT_BASE_URL=https://your-domain.com/checkout
```

#### 3. نصب وابستگی‌ها:

```bash
pip install -r requirements.txt
```

#### 4. اجرای API:

```bash
uvicorn app.main:app --reload
```

API در `http://127.0.0.1:8000` اجرا خواهد شد

#### 5. مشاهده مستندات تعاملی:

`http://127.0.0.1:8000/docs`

### استفاده از Docker

```bash
# ساخت و اجرای کانتینرها
docker-compose up --build

# API در http://localhost:8000 در دسترس خواهد بود
```

## نکات در خصوص وردپرس/ووکامرس

- سرویس از جداول کلاسیک ووکامرس (`wp_posts`, `wp_postmeta`) استفاده می‌کند
- برای پرداخت‌های بزرگ، نهایی کردن سفارش را در خود وردپرس انجام دهید
- این سرویس یک جریان سبد خرید headless فراهم می‌کند و یک `payment_url` برمی‌گرداند که می‌توانید به صفحه پرداخت وردپرس نقل دهید

## نقاط پایانی API

### سلامت سرویس
```
GET /api/v1/health
```

### محصولات
```
GET /api/v1/products - دریافت تمام محصولات
GET /api/v1/products/{product_id} - جزئیات محصول
```

### چت
```
POST /api/v1/chat - ارسال پیام برای عامل AI
```

### سبد خرید
```
POST /api/v1/cart - افزودن محصول به سبد
GET /api/v1/cart/{session_id} - دریافت سبد خرید
POST /api/v1/checkout - شروع فرآیند پرداخت
```

## مشکل‌یابی

### خطای اتصال MySQL
- تأیید کنید که MySQL در حال اجرا است
- اطلاعات اتصال را در `.env` بررسی کنید
- اگر از Docker استفاده می‌کنید، مطمئن شوید که کانتینر MySQL اجرا می‌شود

### خطای API Key
- اطمینان حاصل کنید که API key صحیح وارد شده است
- تازه‌گی کردن و دوباره امتحان کنید

### مشکل CORS
- اگر از فرانت‌اند متفاوت دسترسی می‌داشتید، CORS را در `main.py` فعال کنید

## مساهمه

برای مساهمه در این پروژه:
1. Fork کنید
2. یک branch جدید ایجاد کنید
3. تغییرات خود را commit کنید
4. Push کنید و یک Pull Request ایجاد کنید

## لایسنس

این پروژه تحت لایسنس MIT منتشر شده است.
#cyrusai