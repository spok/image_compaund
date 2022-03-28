from PyQt5 import QtWidgets
from PIL import Image
import sys
import exifread
import os
import pathlib


PAPER_WIDTH_MM = 180
PAPER_HEIGHT_MM = 280
RESOLUTION = 600
base_path = r'f:\Nextcloud\!!!Работа\0_Текущие проекты\Заключение по подстанции\Фото опор'


class MyWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)



class Element:
    def __init__(self, name: str = '', h_or: bool = True, desc: str = ''):
        self.name = name
        self.h_orient = h_or
        self.width = 0
        self.height = 0
        self.ratio = 0
        self.description = desc
        self.image = Image.new('RGB', (self.width, self.height), color='white')


class Mozaic:
    def __init__(self, p: str):
        self.list_fotos = []
        self.list_nods = []
        self.path = p

    def abs_path(self, name: str):
        return os.path.join(self.path, name)

    def get_paper_image(self):
        paper_width = int(PAPER_WIDTH_MM * RESOLUTION / 25.4)
        paper_height = int(PAPER_HEIGHT_MM * RESOLUTION / 25.4)
        im = Image.new('RGB', (paper_width, paper_height), color='white')
        return im

    def scale_image(self, foto: object, typ: int):
        im = foto.image
        paper_width = int(PAPER_WIDTH_MM * RESOLUTION / 25.4)
        paper_height = int(PAPER_HEIGHT_MM * RESOLUTION / 25.4)
        border = 40
        im_out = Image.new('RGB', (foto.width + border * 2, foto.height + border * 2), color='white')
        im_out.paste(foto.image, (border, border))
        x, y = im_out.size
        if typ == 1:
            scale = (paper_width / 1.8888) / paper_width
        elif typ == 2:
            scale = (paper_width - paper_width / 1.8888) / paper_width
        else:
            scale = 0.5
        foto.width = int(paper_width * scale)
        foto.height = int(foto.width * y / x)
        new_image = im_out.resize((foto.width, foto.height))
        foto.image = new_image

    def _read_img_and_correct_exif_orientation(self, foto: object):
        """
        Поворот фотографии с учетом с учетом ориентации снимка по exif
        :param foto: объект класс Element
        :return:
        """
        im = Image.open(self.abs_path(foto.name))
        tags = {}
        with open(self.abs_path(foto.name), 'rb') as f:
            tags = exifread.process_file(f, details=False)
        if "Image Orientation" in tags.keys():
            orientation = tags["Image Orientation"]
            val = orientation.values
            if 5 in val:
                val += [4, 8]
            if 7 in val:
                val += [4, 6]
            if 3 in val:
                im = im.transpose(Image.ROTATE_180)
            if 4 in val:
                im = im.transpose(Image.FLIP_TOP_BOTTOM)
            if 6 in val:
                im = im.transpose(Image.ROTATE_270)
                foto.h_orient = False
            if 8 in val:
                im = im.transpose(Image.ROTATE_90)
                foto.h_orient = False
        x, y = im.size
        foto.width = x
        foto.height = y
        if foto.width > foto.height:
            foto.ratio = foto.width / foto.height
        else:
            foto.ratio = foto.height / foto.width
        foto.image = im

    def scan_photo(self):
        """
        Поиск фотографий в каталоге и размещение на листе
        :return:
        """
        for address, dirs, files in os.walk(self.path):
            break
        self.list_fotos = []
        self.list_nods = []
        nod = []
        if len(files) > 0:
            # Создание списка фотографий
            for f in files:
                if '.jpg' in f.lower():
                    foto = Element(name=f)
                    self._read_img_and_correct_exif_orientation(foto)
                    self.list_fotos.append(foto)

            # Разбиение на ноды
            i = 1
            for f in self.list_fotos:
                if f.h_orient == True:
                    nod.append(f)
                    if i == 2 or i == len(self.list_fotos):
                        self.list_nods.append(nod)
                        i = 1
                        nod = []
                    i += 1
                else:
                    self.list_nods.append(f)

            # Вставка фотографий на лист
            paper_im = []
            paper_im.append(self.get_paper_image())
            paper_count = 0
            x_nod = 0
            y_nod = 0
            typ = 1
            for i, nod in enumerate(self.list_nods):
                i += 1
                # Для узла со списком
                if isinstance(nod, list):
                    x = x_nod
                    y = y_nod
                    col = 1
                    for n in nod:
                        if typ == 1 and i % 2 == 0:
                            typ = 2
                        elif i % 2 != 0:
                            if i < len(self.list_nods):
                                if isinstance(self.list_nods[i], list):
                                    typ = 3
                                else:
                                    typ = 2
                            else:
                                typ = 3
                        self.scale_image(n, typ)
                        if i == len(self.list_nods) and i % 2 != 0 and col == 2:
                            y = y_nod
                            x += n.width
                        paper_im[paper_count].paste(n.image, (x, y))
                        y += n.height
                        delta_x = n.width
                        col += 1
                else:
                    # Для узла с одним элементом
                    x = x_nod
                    y = y_nod
                    if typ == 2 and i % 2 == 0:
                        typ = 1
                    elif i % 2 != 0:
                        if i < len(self.list_nods):
                            if isinstance(self.list_nods[i], list):
                                typ = 1
                            else:
                                typ = 3
                        else:
                            typ = 3
                    self.scale_image(nod, typ)
                    paper_im[paper_count].paste(nod.image, (x, y))
                    y += nod.height
                    delta_x = nod.width
                if i % 2 == 0:
                    x_nod = 0
                    y_nod = y
                else:
                    x_nod += delta_x
                paper_height = paper_im[paper_count].size[1]
                if y_nod > paper_height*0.8:
                    y_nod = 0
                    x_nod = 0
                    paper_im.append(self.get_paper_image())
                    paper_count += 1

            for i, im in enumerate(paper_im):
                path_out = pathlib.PureWindowsPath(self.path)
                im.save(os.path.join(base_path, f'Опора {path_out.parts[-1]:>3} - {i+1}.jpg'), quality=90)
                print(f'Опора {path_out.parts[-1]:>3} - {i+1}.jpg')


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MyWindow()
    window.setWindowTitle('Компановка фотографий на листе')
    window.resize(600, 800)
    window.show()
    sys.exit(app.exec_())

    # for address, dirs, files in os.walk(base_path):
    #     if len(dirs) == 0 and len(files) != 0:
    #         macket = Mozaic(address)
    #         macket.scan_photo()
    #         del macket



