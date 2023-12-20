@echo off
timeout /t 1
echo Copying files..
xcopy /E /Y ".\self-updater" ".\"
timeout /t 1
echo Deleting update copy..
rmdir /s /q self-updater
timeout /t 1
.\GDFetch.exe