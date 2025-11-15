from flask import Flask, Response, request
import uuid

import face_recognition

IMAGES_ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

flask_server = Flask(__name__)

uploaded_files = {}

def get_file_extension(filename):
	return filename.rsplit('.', 1)[1].lower()

def is_file_extension_allowed(filename):
	return '.' in filename and get_file_extension(filename) in IMAGES_ALLOWED_EXTENSIONS


@flask_server.route('/')
def root():
		return flask_server.redirect("/static/index.html")



@flask_server.route('/api/facial_auth', methods=['POST'])
def facial_auth():
	print("Getting something on /api/facial_auth")

	if request.method != 'POST':
		return {"ok": False, "error": "Only POST method supported"}
	
	# Check if the request has the file part
	if 'image-document' not in request.files \
	or 'image-selfie' not in request.files:
		return {"ok": False, "error": "Files were not sent"}

	image_document = request.files['image-document']
	image_selfie = request.files['image-selfie']

	# If no files are sent, the browser sends an empty file with an empty filename
	if image_document.filename == '' \
	or image_selfie.filename == '':
		return {"ok": False, "error": "Images were not sent"}
	
	if not is_file_extension_allowed(image_document.filename) \
	or not is_file_extension_allowed(image_selfie.filename):
		return {"ok": False, "error": "File not allowed"}

	image_document_key = str(uuid.uuid4())
	image_selfie_key = str(uuid.uuid4())

	print("document key: " + image_document_key)
	print("selfie key: " + image_selfie_key)

	image_document_blob = image_document.read()
	image_selfie_blob = image_selfie.read()

	image_document_object = {
		"filename": image_document.filename,
		"fileext": get_file_extension(image_document.filename),
		"blob": image_document_blob
	}
	image_selfie_object = {
		"filename": image_selfie.filename,
		"fileext": get_file_extension(image_selfie.filename),
		"blob": image_selfie_blob
	}

	uploaded_files[image_document_key] = image_document_object
	uploaded_files[image_selfie_key] = image_selfie_object

	aws_client = face_recognition.create_aws_client()
	faces_are_the_same = face_recognition.compare_two_faces(document_object=image_document_object, selfie_object=image_selfie_object, aws_client=aws_client)

	if faces_are_the_same is None:
		return {"ok": False, "error": "Failed to match faces"}
	
	'''
	uploaded_files[image_document_key + "_cropped"] = {
		"filename": str(image_document.filename) + "_cropped",
		"fileext": get_file_extension(image_document.filename),
		"blob": cropped_face
	}

	print("Cropped document: " + image_document_key + "_cropped")
	'''

	return {"ok": True, "faces_match": faces_are_the_same}



@flask_server.route('/api/seeUploads', methods=['GET'])
def see_uploads():
	image_key = request.args.get('key', '')
	image = uploaded_files[image_key]["blob"]
	mimetype = uploaded_files[image_key]["fileext"]
	return Response(response=image, mimetype=mimetype)

if __name__ == "__main__":
	flask_server.run("0.0.0.0", "5000")
