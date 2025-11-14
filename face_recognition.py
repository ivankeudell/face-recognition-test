import boto3
from PIL import Image
import io
import json

def create_aws_client():
	json_data = None
	with open("config.json") as json_file:
		json_data = json.load(json_file)

	print("Connecting to AWS...")
	
	aws_client = boto3.client(
		'rekognition',
		aws_access_key_id=json_data["access_key"],
		aws_secret_access_key=json_data["secret_access_key"],
		region_name="us-east-1"
	)

	print("AWS Client created!")
	return aws_client


def detect_and_crop_face(imageBlob, imageFileExtension, aws_client):
	print("Asking AWS to detect a face...")
	response = aws_client.detect_faces(Image={'Bytes': imageBlob}, Attributes=['DEFAULT'])
	print("AWS finished!")

	if len(response["FaceDetails"]) == 0:
		print("There are no faces :c")
		return None

	bounding_box = response["FaceDetails"][0]["BoundingBox"]

	image = Image.open(io.BytesIO(imageBlob))
	w, h = image.size
	print("image size: " + str(w) + "x" + str(h))

	left = int(bounding_box['Left'] * w)
	top = int(bounding_box['Top'] * h)
	width = int(bounding_box['Width'] * w)
	height = int(bounding_box['Height'] * h)

	cropped = image.crop((left, top, left+width, top+height))

	with io.BytesIO() as f:
		cropped.save(f, imageFileExtension)
		return f.getvalue()

	#croppedBlob = io.BytesIO()
	#cropped.save(croppedBlob, format=cropped.format)
	#cropped.save(croppedBlob, format=cropped.format)
	#return croppedBlob.getValue()
	#return None

def compare_two_faces(document_object, selfie_object, aws_client):
	cropped_face = detect_and_crop_face(document_object["blob"], document_object["fileext"], aws_client=aws_client)
	return cropped_face