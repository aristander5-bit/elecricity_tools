import os
import csv
import subprocess
from math import sqrt
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
font_bold_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

if os.path.exists(font_path):
    pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))
    pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', font_bold_path))
    MAIN_FONT = 'DejaVuSans'
    BOLD_FONT = 'DejaVuSans-Bold'
else:
    MAIN_FONT = 'Helvetica'
    BOLD_FONT = 'Helvetica-Bold'


def cable_inspection(name_trace: str, current_a: float, length_m: float, cross_section_mm2: float, cos_phi: float = 0.95) -> dict:
    conductivity_cu = 56.0

    voltage_drop = (sqrt(3) * current_a * length_m * cos_phi) / (conductivity_cu * cross_section_mm2)
    percentage_drop = (voltage_drop / 400.0) * 100.0

    if percentage_drop <= 3.0:
        status = "OK"
    else:
        status = "ВНИМАНИЕ! Голям пад!"

    print(f"-> {name_trace}: Пад {percentage_drop:.2f}% ({voltage_drop:.2f} V) -> {status}")

    return {
        "trace": name_trace,
        "current": f"{current_a} A",
        "length": f"{length_m} m",
        "section": f"{cross_section_mm2} mm²",
        "drop_v": f"{voltage_drop:.2f} V",
        "drop_pct": f"{percentage_drop:.2f}%",
        "status": status
    }


def generate_pdf_report(results: list, filename: str = "Cable_Inspection_Report.pdf"):
    doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontName=BOLD_FONT,
        fontSize=14,
        textColor=colors.HexColor("#003366"),
        spaceAfter=15
    )
    elements.append(Paragraph("Изчисление на кабелни трасета", title_style))

    cell_style = ParagraphStyle('CellStyle', fontName=MAIN_FONT, fontSize=9, alignment=1)
    header_style = ParagraphStyle('HeaderStyle', fontName=BOLD_FONT, fontSize=9, textColor=colors.whitesmoke, alignment=1)

    headers = ["Трасе / Обект", "Ток", "Дължина", "Сечение", "Пад (V)", "Пад (%)", "Статус"]
    table_data = [[Paragraph(h, header_style) for h in headers]]

    for r in results:
        row = [
            Paragraph(r["trace"], ParagraphStyle('LeftCell', parent=cell_style, alignment=0)),
            Paragraph(r["current"], cell_style),
            Paragraph(r["length"], cell_style),
            Paragraph(r["section"], cell_style),
            Paragraph(r["drop_v"], cell_style),
            Paragraph(r["drop_pct"], cell_style),
            Paragraph(r["status"], cell_style)
        ]
        table_data.append(row)

    table = Table(table_data, colWidths=[130, 50, 60, 60, 60, 55, 95])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#003366")),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))

    elements.append(table)
    doc.build(elements)
    print(f"\n[Успех] PDF докладът е записан: {filename}")

def generate_csv_report(results: list, filename: str = "Cable_Report.csv"):
    headers = ["Трасе / Обект", "Ток", "Дължина", "Сечение", "Пад (V)", "Пад (%)", "Статус"]

    with open(filename, mode="w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for r in results:
            writer.writerow([r["trace"], r["current"], r["length"], r["section"], r["drop_v"], r["drop_pct"], r["status"]])

    print(f"\n[Успех] Таблицата за LibreOffice Calc е записана: {filename}")
    return filename


def open_in_libreoffice(filename: str):
    try:
        subprocess.Popen(["libreoffice", "--calc", filename])
        print(f"[Успех] LibreOffice Calc беше стартиран с файла: {filename}")
    except FileNotFoundError:
        print("[ГРЕШКА] LibreOffice не беше намерен на системата.")

if __name__ == "__main__":
    print("=" * 50)
    print("  КАЛКУЛАТОР ЗА КАБЕЛНИ ТРАСЕТА")
    print("=" * 50)

    calculated_results = []

    while True:
        print("\n--- Въвеждане на ново кабелно трасе ---")
        name = input("Име на трасето (или натисни Enter за край): ").strip()
        if not name:
            break

        try:
            current = float(input("Работен ток (A): "))
            length = float(input("Дължина на трасето (m): "))
            section = float(input("Сечение на кабела (mm²): "))

            cos_input = input("cos(phi) [по подразбиране 0.95]: ").strip()
            cos_val = float(cos_input) if cos_input else 0.95

            res = cable_inspection(
                name_trace=name,
                current_a=current,
                length_m=length,
                cross_section_mm2=section,
                cos_phi=cos_val
            )
            calculated_results.append(res)

        except ValueError:
            print("[ГРЕШКА] Моля, въвеждайте само валидни числа!")

    if calculated_results:
        print(f"\nУспешно бяха изчислени {len(calculated_results)} трасета.")

        gen_pdf = input("Желаете ли да генерирате PDF доклад? (y/n): ").strip().lower()
        if gen_pdf in ['y', 'yes', 'да', 'д']:
            pdf_name = input("Име на PDF файла [по подразбиране: Cable_Inspection_Report.pdf]: ").strip()
            pdf_name = pdf_name if pdf_name else "Cable_Inspection_Report.pdf"
            generate_pdf_report(calculated_results, filename=pdf_name)

        gen_calc = input("\nЖелаете ли да отворите данните в LibreOffice Calc? (y/n): ").strip().lower()
        if gen_calc in ['y', 'yes', 'да', 'д']:
            csv_file = generate_csv_report(calculated_results)
            open_in_libreoffice(csv_file)

    else:
        print("\nНяма въведени данни. Скриптът приключи.")