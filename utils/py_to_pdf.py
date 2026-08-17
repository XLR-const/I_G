import os
import re
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def get_system_mono_font():
    """Пытается найти моноширинный шрифт с поддержкой кириллицы в системе"""
    paths_to_try = [
        # Windows
        "C:\\Windows\\Fonts\\consola.ttf",  # Consolas
        "C:\\Windows\\Fonts\\cour.ttf",     # Courier New
        # Linux
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/freefont/FreeMono.ttf",
        # macOS
        "/System/Library/Fonts/Supplemental/Courier New.ttf"
    ]
    for path in paths_to_try:
        if os.path.exists(path):
            return path
    return None

def read_py_file(src_path):
    """Безопасно читает исходный код файла в кодировке utf-8"""
    try:
        with open(src_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"❌ Ошибка чтения файла {src_path}: {e}")
        return None

def append_code_to_story(story, code_content, filename_header, font_name, code_style, title_style):
    """Форматирует и добавляет заголовок и тело кода в общий пулл элементов ReportLab"""
    story.append(Paragraph(filename_header, title_style))
    story.append(Spacer(1, 10))

    lines = code_content.split('\n')
    for line in lines:
        # Экранируем спецсимволы для XML-разметки ReportLab
        escaped_line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        # Сохраняем форматирование табов и пробелов Python
        escaped_line = escaped_line.replace(' ', '&nbsp;').replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;')
        
        if not escaped_line.strip():
            escaped_line = '&nbsp;'
            
        story.append(Paragraph(escaped_line, code_style))

def main():
    # Настройка шрифта с поддержкой русского языка
    font_path = get_system_mono_font()
    font_name = 'Courier'
    
    if font_path:
        try:
            pdfmetrics.registerFont(TTFont('CustomMono', font_path))
            font_name = 'CustomMono'
        except Exception as e:
            print(f"⚠️ Не удалось зарегистрировать шрифт: {e}. Фоллбек на дефолтный Courier.")
    
    source_folder = input("Введите имя папки с .py файлами (в текущей директории): ").strip()
    
    if not os.path.exists(source_folder) or not os.path.isdir(source_folder):
        print(f"❌ Ошибка: Папка '{source_folder}' не найдена.")
        return

    output_folder = f"{source_folder}_pdf"
    os.makedirs(output_folder, exist_ok=True)
    
    # Стили ReportLab
    styles = getSampleStyleSheet()
    
    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=9,
        leading=12,
        keepWithNext=False
    )
    
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading2'],
        fontName=font_name,
        fontSize=11,
        spaceBefore=10,
        spaceAfter=15
    )

    print(f"▶️ Начало конвертации. Результаты сохраняются в: {output_folder}\n")
    
    converted_count = 0
    # Сюда будем собирать элементы для ОДНОГО ОБЩЕГО PDF-файла
    all_code_story = []

    # Обходим все вложенные папки дерева проекта
    for root, dirs, files in os.walk(source_folder):
        for file in files:
            if file.endswith('.py'):
                src_file_path = os.path.join(root, file)
                
                # Вычисляем относительный путь для заголовков (например: core/boss_base.py)
                relative_file_path = os.path.relpath(src_file_path, os.path.dirname(source_folder))
                # Нормализуем слеши под все ОС
                relative_file_path = relative_file_path.replace("\\", "/")
                
                # Строка-заголовок, которую просили в ТЗ
                filename_header = f"=== FILE: {relative_file_path} ==="
                
                # Читаем код
                code_content = read_py_file(src_file_path)
                if code_content is None:
                    continue
                
                # 1. ГЕНЕРИРУЕМ ИЗОЛИРОВАННЫЙ PDF (как в прошлый раз)
                rel_dir_path = os.path.relpath(root, source_folder)
                target_dir = output_folder if rel_dir_path == "." else os.path.join(output_folder, rel_dir_path)
                os.makedirs(target_dir, exist_ok=True)
                
                individual_pdf_path = os.path.join(target_dir, f"{os.path.splitext(file)[0]}.pdf")
                single_story = []
                append_code_to_story(single_story, code_content, filename_header, font_name, code_style, title_style)
                
                doc = SimpleDocTemplate(individual_pdf_path, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
                doc.build(single_story)
                
                # 2. ДОБАВЛЯЕМ В ОБЩУЮ СБОРКУ
                # Если в общем файле уже есть код, переносим следующий файл на новую страницу
                if all_code_story:
                    all_code_story.append(PageBreak())
                
                append_code_to_story(all_code_story, code_content, filename_header, font_name, code_style, title_style)
                
                print(f"📄 Обработан: {relative_file_path}")
                converted_count += 1

    # 3. СОХРАНЯЕМ ОБЩИЙ СКВОЗНОЙ PDF В КОРЕНЬ ПОЛУЧИВШЕЙСЯ ПАПКИ
    if all_code_story:
        combined_pdf_path = os.path.join(output_folder, f"ALL_CODE_COMBINED.pdf")
        print(f"\n📦 Собираю единый файл со всем кодом: {combined_pdf_path}...")
        
        combined_doc = SimpleDocTemplate(combined_pdf_path, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        combined_doc.build(all_code_story)
        print("🎉 Единый PDF-файл успешно скомпилирован!")

    print(f"\n🎉 Скрипт успешно завершил работу. Всего обработано файлов: {converted_count}")

if __name__ == "__main__":
    main()
