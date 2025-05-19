@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo    大型文本处理工具 - 使用阿里千问模型
echo ===================================================
echo.

REM 检查Python是否安装
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo 错误: 未找到Python。请安装Python并确保它在PATH中。
    goto :end
)

REM 检查Ollama是否运行
curl -s http://localhost:11434/api/version >nul 2>nul
if %errorlevel% neq 0 (
    echo 错误: 无法连接到Ollama服务。请确保Ollama正在运行。
    goto :end
)

REM 检查依赖包
echo 检查依赖包...
python -c "import requests" >nul 2>nul
if %errorlevel% neq 0 (
    echo 安装必要的Python包...
    pip install requests
)

REM 列出可用模型
echo 正在获取可用的Ollama模型...
python process_text_cli.py --list-models
echo.

:menu
echo 请选择操作:
echo 1. 处理文本文件
echo 2. 查看使用说明
echo 3. 退出
echo.
set /p choice=请输入选项 (1-3): 

if "%choice%"=="1" goto process_text
if "%choice%"=="2" goto show_help
if "%choice%"=="3" goto end
echo 无效的选项，请重试。
goto menu

:process_text
echo.
echo === 处理文本文件 ===
echo.

REM 输入文件
set /p input_file=输入文件路径 (默认: example_input.txt): 
if "!input_file!"=="" set input_file=example_input.txt

REM 检查输入文件是否存在
if not exist "!input_file!" (
    echo 错误: 输入文件 '!input_file!' 不存在。
    goto menu
)

REM 输出文件
set /p output_file=输出文件路径 (默认: output.txt): 
if "!output_file!"=="" set output_file=output.txt

REM 模型选择
set /p model=模型名称 (默认: qwen:14b): 
if "!model!"=="" set model=qwen:14b

REM 块大小
set /p chunk_size=文本块大小 (默认: 4000): 
if "!chunk_size!"=="" set chunk_size=4000

REM 任务描述
set /p task=处理任务描述 (默认: 总结这段内容的要点): 
if "!task!"=="" set task=总结这段内容的要点

echo.
echo 开始处理文本...
echo.

python process_text_cli.py -i "!input_file!" -o "!output_file!" -m "!model!" -c !chunk_size! -t "!task!"

echo.
echo 处理完成！结果已保存到 !output_file!
echo.
pause
goto menu

:show_help
echo.
echo === 使用说明 ===
echo.
type README.md | more
echo.
pause
goto menu

:end
echo.
echo 感谢使用大型文本处理工具！
echo.
pause
endlocal