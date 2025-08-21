from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CallbackContext
from PIL import Image
import os
import logging

# تفعيل التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# التوكن
TOKEN = "8311304428:AAFueJYGva0phMmQKs2lTa2fH4eF75aG3BU"

# التحقق من وجود الشعار
WATERMARK_PATH = "speder.jpg"
if not os.path.exists(WATERMARK_PATH):
    raise FileNotFoundError(f"لم يتم العثور على ملف الشعار: {WATERMARK_PATH}")

def add_watermark(input_path, output_path, watermark_logo_path=WATERMARK_PATH):
    try:
        # فتح الصورة الأصلية والشعار
        image = Image.open(input_path).convert("RGB")
        watermark = Image.open(watermark_logo_path).convert("RGBA")
        
        # زيادة حجم الشعار بمقدار 10 مرات
        watermark = watermark.resize((1000, 1000), Image.Resampling.LANCZOS)

        # تعديل الشفافية إلى 10% (التقليل إلى 25 من 255)
        watermark_with_opacity = watermark.copy()
        watermark_with_opacity.putalpha(25)  # 10% شفافية

        # تحويل الصورة إلى RGBA للتعامل مع الشفافية
        image_rgba = image.convert("RGBA")
        background = Image.new("RGBA", image_rgba.size)
        background.paste(image_rgba, (0, 0))

        # وضع الشعار في منتصف الصورة
        pos = ((image.width - watermark_with_opacity.width) // 2, (image.height - watermark_with_opacity.height) // 2)
        background.paste(watermark_with_opacity, pos, watermark_with_opacity)

        # حفظ الصورة الناتجة
        background.convert("RGB").save(output_path, "JPEG", quality=95)
        return True
    except Exception as e:
        logger.error(f"خطأ في add_watermark: {e}")
        return False

async def handle_photo(update: Update, context: CallbackContext):
    if not update.message.photo:
        return

    input_path = "input.jpg"
    output_path = "output.jpg"

    try:
        file = await update.message.photo[-1].get_file()
        await file.download_to_drive(input_path)

        if not add_watermark(input_path, output_path):
            await update.message.reply_text("❌ فشل في معالجة الصورة.")
            return

        with open(output_path, "rb") as f:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=f
            )
    except Exception as e:
        logger.error(f"خطأ في معالجة الصورة: {e}")
        await update.message.reply_text("⚠️ حدث خطأ أثناء معالجة الصورة.")
    finally:
        for path in [input_path, output_path]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception as e:
                    logger.warning(f"تعذر حذف {path}: {e}")

async def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    logger.info("البوت يعمل الآن... ✅")
    # ❌ لا نستخدم asyncio.run() هنا
    # ✅ نستخدم الـ loop يدويًا
    await application.run_polling(close_loop=False)  # مهم: close_loop=False

# —————————————————————————————
# ✅ الحل المضمون لـ Python 3.13
# —————————————————————————————
if __name__ == '__main__':
    import asyncio
    import sys

    # ✅ تغيير policy للـ event loop
    if sys.version_info >= (3, 12):
        try:
            import asyncio.windows_events
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        except Exception:
            pass

    # ✅ استخدام nest_asyncio لحل مشكلة "loop already running"
    try:
        import nest_asyncio
        nest_asyncio.apply()
        print("✅ تم تطبيق nest_asyncio")
    except ImportError:
        print("❌ يرجى تثبيت: pip install nest-asyncio")
        exit(1)

    # ✅ بدء تشغيل البوت بدون asyncio.run()
    loop = asyncio.get_event_loop()
    try:
        loop.create_task(main())
        loop.run_forever()  # ⚠️ هذا هو المفتاح!
    except KeyboardInterrupt:
        print("\n🛑 تم إيقاف البوت")
    finally:
        loop.close()
