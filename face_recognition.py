import boto3
from PIL import Image
import io
import json
import numbers
import traceback

SIMILARITY_THRESHOLD = 70

def create_aws_client():
	json_data = None
	with open("config.json") as json_file:
		json_data = json.load(json_file)

	print("Creating AWS Client...")
	
	aws_client = boto3.client(
		'rekognition',
		aws_access_key_id=json_data["access_key"],
		aws_secret_access_key=json_data["secret_access_key"],
		region_name="us-east-1"
	)

	print("AWS Client created!")
	return aws_client


def detect_and_crop_face(image_blob, image_file_extension, aws_client):
	try:
		if image_file_extension == 'jpg':
			image_file_extension = 'jpeg' # Pillow is stupid

		# Resize image
		full_image = Image.open(io.BytesIO(image_blob))
		full_width, full_height = full_image.size
		print("full image size: " + str(full_width) + "x" + str(full_height))

		resized_image = full_image.resize((int(full_width/1.5), int(full_height/1.5)), Image.Resampling.LANCZOS)

		resized_blob = None
		with io.BytesIO() as f:
			resized_image.save(f, format=image_file_extension, optimize=True, quality=90)
			resized_blob = f.getvalue()

		# Send image to aws to get face bounding box
		print("Asking AWS to detect a face...")
		response = aws_client.detect_faces(Image={'Bytes': resized_blob}, Attributes=['DEFAULT'])
		print("AWS finished!")

		if len(response["FaceDetails"]) == 0:
			print("There are no faces :c")
			return None

		bounding_box = response["FaceDetails"][0]["BoundingBox"]

		# Crop the face and return it
		w, h = resized_image.size
		print("resized image: " + str(w) + "x" + str(h))
		left = int(bounding_box['Left'] * w)
		top = int(bounding_box['Top'] * h)
		width = int(bounding_box['Width'] * w)
		height = int(bounding_box['Height'] * h)

		cropped = resized_image.crop((left, top, left+width, top+height))

		with io.BytesIO() as f:
			cropped.save(f, format=image_file_extension)
			return f.getvalue()
	except Exception as e:
		print("Error: (" + str(type(e).__name__) + ") " + str(e))
		traceback.print_exc()
		return None


def are_faces_the_same(document_blob, selfie_blob, aws_client):
	print("Asking AWS to compare the faces...")
	response = aws_client.compare_faces(
		SourceImage={'Bytes': document_blob},
		TargetImage={'Bytes': selfie_blob},
		SimilarityThreshold=SIMILARITY_THRESHOLD
	)
	print("Are these faces the same? " + str(response))

	if response["FaceMatches"] is None \
	or response["FaceMatches"][0] is None \
	or response["FaceMatches"][0]["Similarity"] is None:
		print("Failed to get Similarity value")
		return None
	
	similarity = response["FaceMatches"][0]["Similarity"]
	if not isinstance(similarity, numbers.Number) or isinstance(similarity, bool):
		print("Similarity value is not a number")
		return None

	print("Similarity: ", str(similarity) + "/" + str(SIMILARITY_THRESHOLD))
	return similarity >= SIMILARITY_THRESHOLD

def compare_two_faces(document_object, selfie_object, aws_client):
	cropped_document_face_blob = detect_and_crop_face(document_object["blob"], document_object["fileext"], aws_client)
	if cropped_document_face_blob is None:
		print("Failed to get cropped document face :C")
		return None

	cropped_selfie_face_blob = detect_and_crop_face(selfie_object["blob"], selfie_object["fileext"], aws_client)
	if cropped_selfie_face_blob is None:
		print("Failed to get cropped selfie face :C")
		return None

	are_the_same = are_faces_the_same(cropped_document_face_blob, cropped_selfie_face_blob, aws_client)
	return are_the_same