@echo off
REM YouTube Shorts Otomasyon - 7/7 Tam Otomasyon Başlatıcı
REM Haftanın her günü 7 video üretir

echo ============================================================
echo    YouTube Shorts Otomasyon - 7/7 Tam Otomasyon
echo ============================================================
echo.
echo Bu script haftanın her günü otomatik olarak 7 video üretecek.
echo Videolar arası 60 dakika bekleme süresi var.
echo.
echo Başlatılıyor...
echo.

cd /d "%~dp0"
python run.py --continuous

pause