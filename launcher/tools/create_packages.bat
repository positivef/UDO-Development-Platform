@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo.
echo ============================================================
echo   UDO Portable Package Creator
echo ============================================================
echo.

set "PROJECT_ROOT=%~dp0..\.."
set "OUTPUT_DIR=%PROJECT_ROOT%\..\UDO-Packages"

:: 출력 폴더 생성
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

echo [1/2] 옵션 1: UDO 전체 패키지 생성 중...
echo       (UDO 대시보드 실행용)

:: 임시 폴더 생성
set "TEMP_FULL=%TEMP%\UDO-Full-Package"
if exist "%TEMP_FULL%" rmdir /s /q "%TEMP_FULL%"
mkdir "%TEMP_FULL%"

:: 필요한 파일 복사 (불필요한 것 제외)
xcopy "%PROJECT_ROOT%\*" "%TEMP_FULL%\" /E /I /Q /EXCLUDE:%~dp0exclude_full.txt 2>nul

:: 압축 (PowerShell 사용)
powershell -Command "Compress-Archive -Path '%TEMP_FULL%\*' -DestinationPath '%OUTPUT_DIR%\UDO-Full-Package.zip' -Force"

echo       완료: %OUTPUT_DIR%\UDO-Full-Package.zip

echo.
echo [2/2] 옵션 2: 규칙 템플릿 패키지 생성 중...
echo       (새 프로젝트에 규칙 적용용)

set "TEMP_RULES=%TEMP%\UDO-Rules-Template"
if exist "%TEMP_RULES%" rmdir /s /q "%TEMP_RULES%"
mkdir "%TEMP_RULES%"

:: 규칙 파일만 복사
copy "%PROJECT_ROOT%\CLAUDE.md" "%TEMP_RULES%\" >nul
copy "%PROJECT_ROOT%\AGENTS.md" "%TEMP_RULES%\" >nul
copy "%PROJECT_ROOT%\.governance.yaml" "%TEMP_RULES%\" >nul
copy "%PROJECT_ROOT%\.pre-commit-config.yaml" "%TEMP_RULES%\" >nul
copy "%PROJECT_ROOT%\.env.example" "%TEMP_RULES%\" >nul
copy "%PROJECT_ROOT%\requirements.txt" "%TEMP_RULES%\" >nul

:: launcher 폴더 복사
xcopy "%PROJECT_ROOT%\launcher\*" "%TEMP_RULES%\launcher\" /E /I /Q >nul

:: scripts 유틸리티 복사
mkdir "%TEMP_RULES%\scripts"
copy "%PROJECT_ROOT%\scripts\session_start.py" "%TEMP_RULES%\scripts\" 2>nul
copy "%PROJECT_ROOT%\scripts\validate_system_rules.py" "%TEMP_RULES%\scripts\" 2>nul
copy "%PROJECT_ROOT%\scripts\check_korean_preservation.py" "%TEMP_RULES%\scripts\" 2>nul
copy "%PROJECT_ROOT%\scripts\validate_documentation_consistency.py" "%TEMP_RULES%\scripts\" 2>nul

:: templates 폴더 복사 (있다면)
if exist "%PROJECT_ROOT%\templates" (
    xcopy "%PROJECT_ROOT%\templates\*" "%TEMP_RULES%\templates\" /E /I /Q >nul
)

:: 압축
powershell -Command "Compress-Archive -Path '%TEMP_RULES%\*' -DestinationPath '%OUTPUT_DIR%\UDO-Rules-Template.zip' -Force"

echo       완료: %OUTPUT_DIR%\UDO-Rules-Template.zip

:: 정리
rmdir /s /q "%TEMP_FULL%" 2>nul
rmdir /s /q "%TEMP_RULES%" 2>nul

echo.
echo ============================================================
echo   패키지 생성 완료!
echo ============================================================
echo.
echo   저장 위치: %OUTPUT_DIR%
echo.
echo   [옵션 1] UDO-Full-Package.zip
echo            - UDO 대시보드 전체 실행용
echo            - launcher\install\install_windows.bat 실행
echo.
echo   [옵션 2] UDO-Rules-Template.zip
echo            - 새 프로젝트에 규칙만 적용
echo            - 압축 해제 후 새 프로젝트 폴더에 복사
echo.

:: 폴더 열기
explorer "%OUTPUT_DIR%"

pause
