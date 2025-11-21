import boto3
from textractor import Textractor
from PIL import Image
import io
import os
import json
import traceback

SIMILARITY_THRESHOLD = 70



def _get_config():
	with open("config.json") as json_file:
		return json.load(json_file)


def _create_rekognition_client():
	config = _get_config()

	print("Creating AWS Rekognition Client...")
	
	rekognition_client = boto3.client(
		'rekognition',
		aws_access_key_id=config["access_key"],
		aws_secret_access_key=config["secret_access_key"],
		region_name="us-east-1"
	)

	print("AWS Rekognition Client created!")
	return rekognition_client



def _create_textract_client():
	config = _get_config()

	print("Creating AWS Textract Client...")

	os.environ["AWS_ACCESS_KEY_ID"] = config["access_key"]
	os.environ["AWS_SECRET_ACCESS_KEY"] = config["secret_access_key"]

	textractor = Textractor(region_name="us-east-1")

	print("AWS Textract Client created!")
	return textractor



def _resize_image(image_blob, image_file_extension):
	try:
		if image_file_extension == 'jpg':
			image_file_extension = 'jpeg' # Pillow is stupid

		# Resize image
		full_image = Image.open(io.BytesIO(image_blob))
		full_width, full_height = full_image.size
		print("full image size: " + str(full_width) + "x" + str(full_height))

		target_width = full_width
		target_height = full_height
		if full_width > 2000 or full_height > 2000:
			target_width = int(full_width / 2)
			target_height = int(full_height / 2)
		elif full_width > 1000 or full_height > 1000:
			target_width = int(full_width / 1.5)
			target_height = int(full_height / 1.5)

		resized_image = full_image.resize((target_width, target_height), Image.Resampling.LANCZOS)

		w, h = resized_image.size
		print("resized image: " + str(w) + "x" + str(h))

		resized_blob = None
		with io.BytesIO() as f:
			resized_image.save(f, format=image_file_extension, optimize=True, quality=90)
			resized_blob = f.getvalue()

		return {"width": w, "height": h, "blob": resized_blob}
	except Exception as e:
		print("Error: (" + str(type(e).__name__) + ") " + str(e))
		traceback.print_exc()
		return None



def _detect_and_crop_face(image_blob, image_file_extension, aws_client):
	try:
		if image_file_extension == 'jpg':
			image_file_extension = 'jpeg' # Pillow is stupid

		resized_obj = _resize_image(image_blob, image_file_extension)
		resized_blob = resized_obj["blob"]
		# Send image to aws to get face bounding box
		print("Asking AWS to detect a face...")
		response = aws_client.detect_faces(Image={'Bytes': resized_blob}, Attributes=['DEFAULT'])
		print("AWS finished!")

		if len(response["FaceDetails"]) == 0:
			print("There are no faces :c")
			return None

		bounding_box = response["FaceDetails"][0]["BoundingBox"]

		# Crop the face and return it
		w = resized_obj["width"]
		h = resized_obj["height"]
		left = int(bounding_box['Left'] * w)
		top = int(bounding_box['Top'] * h)
		width = int(bounding_box['Width'] * w)
		height = int(bounding_box['Height'] * h)

		cropped = Image.open(io.BytesIO(resized_blob)).crop((left, top, left+width, top+height))

		with io.BytesIO() as f:
			cropped.save(f, format=image_file_extension)
			return f.getvalue()
	except Exception as e:
		print("Error: (" + str(type(e).__name__) + ") " + str(e))
		traceback.print_exc()
		return None



def _are_faces_the_same(document_blob, selfie_blob, aws_client):
	print("Asking AWS to compare the faces...")
	response = aws_client.compare_faces(
		SourceImage={'Bytes': document_blob},
		TargetImage={'Bytes': selfie_blob},
		SimilarityThreshold=SIMILARITY_THRESHOLD
	)
	print("Are these faces the same? " + json.dumps(response))

	if response["FaceMatches"] is not None \
	and response["UnmatchedFaces"] is not None:
		if len(response["FaceMatches"]) > 0:
			return True
		elif len(response["UnmatchedFaces"]) > 0:
			return False
		else:
			print("Neither FaceMatched nor UnmatchedFaces have content in them, weird")
			return None
	else:
		print("FaceMatches or UnmatchedFaces is not present")
		return None



def compare_two_faces(document_object, selfie_object):
	rekognition_client = _create_rekognition_client()

	cropped_document_face_blob = _detect_and_crop_face(document_object["blob"], document_object["fileext"], rekognition_client)
	if cropped_document_face_blob is None:
		print("Failed to get cropped document face :C")
		return None

	cropped_selfie_face_blob = _detect_and_crop_face(selfie_object["blob"], selfie_object["fileext"], rekognition_client)
	if cropped_selfie_face_blob is None:
		print("Failed to get cropped selfie face :C")
		return None

	are_the_same = _are_faces_the_same(cropped_document_face_blob, cropped_selfie_face_blob, rekognition_client)
	return are_the_same



def _obtain_document_data(textractor_result):
	result = {
		"name" : textractor_result["FIRST_NAME"].title() + " " + textractor_result["MIDDLE_NAME"].title(),
		"lastname": textractor_result["LAST_NAME"].title(),
		"cin": textractor_result["DOCUMENT_NUMBER"],
		"date_of_birth": textractor_result["DATE_OF_BIRTH"]
	}

	return result




def get_document_details(document_object):
	textract_client = _create_textract_client()

	document_image_blob = _resize_image(document_object["blob"], document_object["fileext"])["blob"]

	document = textract_client.analyze_id(
		file_source=Image.open(io.BytesIO(document_image_blob))
	)

	print(document.identity_documents[0])

	return _obtain_document_data(document.identity_documents[0])
