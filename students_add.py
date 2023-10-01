import io
from PIL import Image as PILImage
import pandas as pd
import secrets
import os
from shutil import copyfile
from models.models import Student
from app import db, create_app
import openpyxl
import xlrd
from PIL import Image
from io import BytesIO


data = pd.read_excel('assets\students.xlsx', engine='openpyxl')
app = create_app()

IMAGES_FOLDER = 'assets/images'


def generate_password(length=8):
    alphabet = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password


def save_image(image, folder, filename):
    image_path = os.path.join(folder, filename)
    with open(image_path, "wb") as img_file:
        img_file.write(image.image.blob)
    return image_path


def transliterate_ukr_to_eng(text):
    ukr_characters = ['а', 'б', 'в', 'г', 'ґ', 'д', 'е', 'є', 'ж', 'з', 'и', 'і', 'ї', 'й', 'к',
                      'л', 'м', 'н', 'о', 'п', 'р', 'с', 'т', 'у', 'ф', 'х', 'ц', 'ч', 'ш', 'щ', 'ь', 'ю', 'я']
    eng_transliteration = ['a', 'b', 'v', 'g', 'g', 'd', 'e', 'ye', 'zh', 'z', 'y', 'i', 'yi', 'y', 'k',
                           'l', 'm', 'n', 'o', 'p', 'r', 's', 't', 'u', 'f', 'h', 'ts', 'ch', 'sh', 'shch', '', 'yu', 'ya']

    translation_dict = {
        ukr_characters[i]: eng_transliteration[i] for i in range(len(ukr_characters))}
    translation_dict.update({char.upper(): trans.upper()
                            for char, trans in translation_dict.items()})

    translated_text = ''.join(
        [translation_dict[char] if char in translation_dict else char for char in text])
    return translated_text


def generate_login(fullname):
    names = fullname.split()
    if len(names) >= 2:
        first_name, last_name = names[0], names[1]
    else:
        first_name, last_name = names[0], ''

    translated_first_name = transliterate_ukr_to_eng(first_name)
    translated_last_name = transliterate_ukr_to_eng(last_name)

    login = f"{translated_first_name.lower()}_{translated_last_name.lower()}"
    return login


def extract_image_from_excel(sheet, row, col):
    cell_obj = sheet.cell(row, col)
    xfx = cell_obj.xf_index
    xf = sheet.book.xf_list[xfx]
    bgx = xf.background.pattern_colour_index
    pattern_record = sheet.book.colour_map[bgx]

    image_data = pattern_record[1]
    image = Image.open(BytesIO(image_data))

    return image


def get_value_or_default(value, default="Не вказано"):
    if pd.isnull(value) or value == '':
        return default
    return value


wb = openpyxl.load_workbook('assets\students.xlsx')
sheet = wb.active

with app.app_context():
    for index, row in data.iterrows():

        password = generate_password()
        login = generate_login(row["fullname"])

        found_image = None
        for img_obj in sheet._images:
            if img_obj.anchor._from.col == 5 and img_obj.anchor._from.row == index + 1:
                found_image = img_obj  # Берем найденное изображение
                break

        if found_image:
            image_data = found_image._data()
            image_stream = io.BytesIO(image_data)
            pil_image = PILImage.open(image_stream)

            if pil_image.mode == "RGBA":
                pil_image = pil_image.convert("RGB")

            image_path = os.path.join(IMAGES_FOLDER, f"{login}.jpg")
            pil_image.save(image_path, "JPEG")

        else:
            print(f"No image found for student {login}")
            image_path = f"{login}.jpg"

        # Используем функцию проверки для полей
        faculty_value = get_value_or_default(row["faculty"])
        room_value = get_value_or_default(
            row["room"], default="Не указанная комната")

        new_student = Student(
            fullname=row["fullname"],
            room=room_value,
            faculty=faculty_value,
            login=login,
            photo=f"{login}.jpg"
        )
        new_student.set_password(password)

        db.session.add(new_student)

    db.session.commit()
