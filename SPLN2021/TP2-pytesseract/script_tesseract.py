#!/usr/bin/python3
import sys
import re
try:
    from PIL import Image # https://pypi.org/project/Pillow/
except ImportError:
    import Image

import pytesseract
from cv2 import cv2 #pip install opencv-python
import numpy as np
from pdf2image import convert_from_path

# instalar o package sistema tesseract-ocr https://github.com/tesseract-ocr/tesseract
# pip3 install pytesseract
# correr script

# teste com o jornal CONQUISTADOR19280216_002.pdf
# https://www.xpdfreader.com/pdfimages-man.html
# pdfimages -png CONQUISTADOR19280216_002.pdf conquistador    flags = -png -all -list 

# get grayscale image
def get_grayscale(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# noise removal
def remove_noise(image):
    return cv2.medianBlur(image,5)
 
#thresholding
def thresholding(image):
    return cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

#dilation
def dilate(image):
    kernel = np.ones((5,5),np.uint8)
    #image = cv2.dilate(image, kernel_dilate, cv2.BORDER_REFLECT) 
    return cv2.dilate(image, kernel, iterations = 1)
    
#erosion
def erode(image):
    kernel = np.ones((3,3),np.uint8)
    #image = cv2.erode(image, kernel_erode, cv2.BORDER_REFLECT)
    return cv2.erode(image, kernel, iterations = 2)

#opening - erosion followed by dilation
def opening(image):
    kernel = np.ones((5,5),np.uint8)
    return cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)

#inverted BLACK WHITE
def canny(image):
    return cv2.Canny(image, 100, 200)

def image_preprocessing(image):
  print('preprocessing')
  image = get_grayscale(image)
  #image = erode(image)
  image = remove_noise(image)
  image = thresholding(image)
  #image = canny(image)
  return image

def converte_multiple_images(images):
  for i, image in enumerate(images):
    fname = 'image-'+str(i)+'.png'
    image.save(fname, "PNG")

    image = cv2.cvtColor(np.array(image),cv2.COLOR_RGB2BGR)
    image = image_preprocessing(image)

    txt = pytesseract.image_to_string(image, lang='por')
    print('txt: ', txt)
    #image = cv2.resize(image, (960,540))  
    try:
      cv2.imshow(f'Window{i}', image)
    except Exception as err:
      print('cv2.imshow error', err)

  cv2.waitKey(0)
  cv2.destroyAllWindows()


def convert_image(path):
  image = cv2.imread(path)
  image = image_preprocessing(image)
  
  print('a processar ...')
  try:
    #custom_config = r'-l por+eng --psm 6'
    txt = pytesseract.image_to_string(image, config='-l por+eng')
    print('txt: ', txt)
  except Exception as e:
    print('config ', e)
  # Displaying the image
  cv2.imshow('Window', image)
  cv2.waitKey(0)
  cv2.destroyAllWindows()


def main():
  # List of available languages
  print('Linguas disponíveis')
  print(pytesseract.get_languages(config=''))

  if len(sys.argv) == 2:
    path = sys.argv[1]
    if match := re.match(r'(.*).(pdf)', path):
      try:
        print('pdf')
        images = convert_from_path(path, fmt='png')
        print('type images', type(images), images)
        converte_multiple_images(images)
      except:
        print('Erro a ler pdf')
    else:
      try:
        print('png')
        convert_image(path)
      except Exception as e:
        print('Erro a converter imagem para texto', e)
  else:
      print('Argumento inválidos: python script_tesseract.py nome-ficheiro.png')
      exit(0)


if __name__ == "__main__":
    main()
