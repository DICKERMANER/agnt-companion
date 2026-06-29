@echo off
echo ============================================
echo   AGNT Cyber Companion - 防火牆設定
echo ============================================
echo.
echo 即將開啟 port 5500 (前端) 和 8000 (後端)
echo 讓同 WiFi 的手機可以連線
echo.

netsh advfirewall firewall add rule name="AGNT Frontend 5500" dir=in action=allow protocol=TCP localport=5500
if %ERRORLEVEL% EQU 0 (
    echo [OK] Port 5500 已開啟
) else (
    echo [略過] Port 5500 可能已存在規則
)

netsh advfirewall firewall add rule name="AGNT Backend 8000" dir=in action=allow protocol=TCP localport=8000
if %ERRORLEVEL% EQU 0 (
    echo [OK] Port 8000 已開啟
) else (
    echo [略過] Port 8000 可能已存在規則
)

echo.
echo ============================================
echo   完成！現在手機連同 WiFi，打開瀏覽器：
echo   http://192.168.31.13:5500
echo ============================================
pause