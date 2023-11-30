import boto3
from PIL import Image, ImageDraw, ImageEnhance
import io

# Function to draw bounding box on an image
def ShowBoundingBox(draw, box, width, height, boxColor):
    left = width * box['Left']
    top = height * box['Top']
    draw.rectangle([left, top, left + (width * box['Width']), top + (height * box['Height'])], outline=boxColor)

# Function to preprocess an image by enhancing contrast and brightness
def preprocess_image(image, contrast_factor=1.5, brightness_factor=1.0):
    image = image.convert('L')  # Convert to grayscale
    
    # Enhance contrast
    enhancer_contrast = ImageEnhance.Contrast(image)
    image = enhancer_contrast.enhance(contrast_factor)
    
    # Enhance brightness
    enhancer_brightness = ImageEnhance.Brightness(image)
    image = enhancer_brightness.enhance(brightness_factor)
    
    return image

# Function to process text detection on an image using Amazon Textract
def process_text_detection(client, img_bytes, output_file_path):
    image = Image.open(io.BytesIO(img_bytes))
    preprocessed_image = preprocess_image(image, contrast_factor=1.5, brightness_factor=1.2)
    response = client.detect_document_text(Document={'Bytes': img_bytes})
    blocks = response['Blocks']
    width, height = preprocessed_image.size
    detected_code = ['']  # Initialize with an empty string
    prev_distance = None
    indentation_level = 0

    draw = ImageDraw.Draw(preprocessed_image)

    for index, block in enumerate(blocks):
        if block['BlockType'] == "LINE":
            box = block['Geometry']['BoundingBox']
            distance = box['Left'] * width  # Calculate distance from left edge to margin
            current_line = block['Text'].strip()

            if prev_distance is not None and distance > prev_distance:
                if detected_code[-1].strip().endswith(':'):
                    indentation_level += 1
                detected_code.append(' ' * indentation_level + current_line + '\n')
            elif detected_code[-1].strip().endswith(('break', 'continue')) or detected_code[-1].strip().startswith('return') or current_line.strip().startswith(('elif', 'else')):
                indentation_level -= 1
                detected_code.append(' ' * indentation_level + current_line + '\n')
            elif current_line.strip().startswith('def'):
                indentation_level = 0
                detected_code.append(' ' * indentation_level + current_line + '\n')
            elif index == 1 or indentation_level == 0:
                detected_code[-1] += '' + current_line + '\n'
            else:
                detected_code[-1] += ' ' + current_line + '\n'

            ShowBoundingBox(draw, box, width, height, 'red')
            prev_distance = distance

    for line in detected_code:
        print(line)
    with open(output_file_path, 'w') as output_file:
        for line in detected_code:
            output_file.write(line)


    return preprocessed_image, len(blocks)

def main():
    session = boto3.Session(profile_name='riya')  # Connect to AWS using the 'riya' profile
    client = session.client('textract', region_name='us-east-1')  # Create a Textract client

    # Load image bytes from file
    with open("C:\\Users\\riyap\\OneDrive\\Desktop\\code\\image\\hw22.png", 'rb') as img_file:
        img_bytes = img_file.read()
    output_text_file_path = "C:\\Users\\riyap\\OneDrive\\Desktop\\code\\image\\out\\output1.txt"

    processed_image, block_count = process_text_detection(client, img_bytes, output_text_file_path)
    processed_image.show()

    processed_image, block_count = process_text_detection(client, img_bytes)
    processed_image.show()  # Display the preprocessed image with bounding boxes
    print("Blocks detected: " + str(block_count))

if __name__ == "__main__":
    main()
