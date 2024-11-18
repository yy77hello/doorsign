import sys
import os
import cv2
import numpy as np
import re
import fitz
import math
from pdf2image import convert_from_path

CURRENT_ROOM = "224"
PDF_DIR = "maps"
ROUTE_PREFIX = "route"
BLUE = (255, 0, 0)
LINE_THICKNESS = 6

def extract_text_from_pdf(pdf_path):
    room_coordinates = {}
    staircases = {}
    doc = fitz.open(pdf_path)
    pdf_name = os.path.basename(pdf_path)
    
    for page in doc:
        for inst in page.get_text("words"):
            text = inst[4]
            if re.match(r'^(?:[A-Z]\d{3}|\d{3}[A-Z]?)$', text):
                center_x, center_y = (inst[0] + inst[2]) / 2, (inst[1] + inst[3]) / 2
                room_info = (center_x, center_y, pdf_name)
                room_coordinates[text] = room_info
                if text.startswith('Z'):
                    staircases[text] = room_info
                print(f"Detected room: {text} at coordinates: ({center_x}, {center_y}) in PDF: {pdf_name}")
    
    return room_coordinates, staircases

def find_rooms_in_pdfs():
    room_coordinates = {}
    all_staircases = {}
    
    for pdf_file in os.listdir(PDF_DIR):
        if pdf_file.endswith(".pdf"):
            pdf_rooms, pdf_staircases = extract_text_from_pdf(os.path.join(PDF_DIR, pdf_file))
            room_coordinates.update(pdf_rooms)
            all_staircases.update(pdf_staircases)

    return room_coordinates, all_staircases

def get_image_from_pdf(pdf_file):
    pdf_path = os.path.join("maps", pdf_file)
    images = convert_from_path(pdf_path)
    return np.array(images[0])

def calculate_distance(point1, point2):
    return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

def find_closest_staircase(room, staircases):
    closest_staircase = None
    min_distance = float('inf')
    for staircase, staircase_info in staircases.items():
        if staircase_info[2] == room[2]:  # Check if they're in the same PDF
            distance = calculate_distance(room[:2], staircase_info[:2])
            if distance < min_distance:
                min_distance = distance
                closest_staircase = staircase
    return closest_staircase

def find_corresponding_staircase(original_staircase, staircases, destination_pdf):
    last_digit = original_staircase[-1]
    return next((staircase for staircase, info in staircases.items() 
                 if staircase.endswith(last_digit) and info[2] == destination_pdf), None)

def draw_route(image, start_room, end_room, room_coordinates):
    start_info, end_info = room_coordinates.get(start_room), room_coordinates.get(end_room)
    if not (start_info and end_info):
        print(f"Could not find coordinates for: {start_room} or {end_room}.")
        return False

    pdf_doc = fitz.open(os.path.join(PDF_DIR, start_info[2]))
    pdf_width, pdf_height = pdf_doc[0].rect.width, pdf_doc[0].rect.height
    img_height, img_width = image.shape[:2]
    scale_x, scale_y = img_width / pdf_width, img_height / pdf_height

    start_point = tuple(int(coord * scale) for coord, scale in zip(start_info[:2], (scale_x, scale_y)))
    end_point = tuple(int(coord * scale) for coord, scale in zip(end_info[:2], (scale_x, scale_y)))
    
    print(f"Drawing line from {start_point} to {end_point}")
    cv2.line(image, start_point, end_point, BLUE, LINE_THICKNESS)
    return True

def main(destination):
    # Clear old drawn route pdfs
    for filename in os.listdir():
        if filename.lower().startswith(ROUTE_PREFIX) and filename.lower().endswith(".jpg"):
            try:
                os.remove(filename)
                print(f"Deleted: {filename}")
            except Exception as e:
                print(f"Error deleting {filename}: {e}")
    
    room_coordinates, staircases = find_rooms_in_pdfs()

    current_info = room_coordinates.get(CURRENT_ROOM)
    destination_info = room_coordinates.get(destination)

    if not (current_info and destination_info):
        print("Current room or destination room not found.")
        return

    current_pdf_file = current_info[2]
    destination_pdf_file = destination_info[2]

    current_image = get_image_from_pdf(current_pdf_file)
    
    if current_pdf_file != destination_pdf_file:
        closest_staircase_current = find_closest_staircase(current_info, staircases)
        corresponding_staircase_dest = find_corresponding_staircase(closest_staircase_current, staircases, destination_pdf_file)

        if not corresponding_staircase_dest:
            print(f"Could not find a corresponding staircase on the destination floor.")
            return

        if draw_route(current_image, CURRENT_ROOM, closest_staircase_current, room_coordinates):
            cv2.imwrite(f"{ROUTE_PREFIX}.jpg", current_image)
            print(f"Route created from {CURRENT_ROOM} to staircase {closest_staircase_current} in {current_pdf_file}.")

        destination_image = get_image_from_pdf(destination_pdf_file)
        if draw_route(destination_image, corresponding_staircase_dest, destination, room_coordinates):
            cv2.imwrite(f"{ROUTE_PREFIX}-2.jpg", destination_image)
            print(f"Route created from staircase {corresponding_staircase_dest} to {destination} in {destination_pdf_file}.")
    else:
        if draw_route(current_image, CURRENT_ROOM, destination, room_coordinates):
            cv2.imwrite(f"{ROUTE_PREFIX}.jpg", current_image)
            print(f"Route created from {CURRENT_ROOM} to {destination} in {current_pdf_file}.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python process_navigation.py <destination_room>")
    else:
        main(sys.argv[1])