from deepface import DeepFace
import cv2
from PIL import Image
import io
import json
import traceback
import numpy as np

def resize_image(image_object):
	try:
		image_file_extension = image_object["fileext"]
		if image_file_extension == 'jpg':
			image_file_extension = 'jpeg' # Pillow is stupid

		# Resize image
		image_blob = image_object["blob"]
		full_image = Image.open(io.BytesIO(image_blob))
		full_width, full_height = full_image.size
		print("full image size: " + str(full_width) + "x" + str(full_height))

		#return full_image.convert("RGB")

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

		return resized_image.convert("RGB")
	except Exception as e:
		print("Error: (" + str(type(e).__name__) + ") " + str(e))
		traceback.print_exc()
		return None


def compare_two_faces(document_object, selfie_object):
	try:
		document_pil_image = resize_image(document_object)
		selfie_pil_image = resize_image(selfie_object)

		document_nparray_image = cv2.cvtColor(np.array(document_pil_image), cv2.COLOR_RGB2BGR)
		selfie_nparray_image = cv2.cvtColor(np.array(selfie_pil_image), cv2.COLOR_RGB2BGR)

		print("Pidiendo a DeepFace que compare las caras...")
		results = DeepFace.verify(img1_path=document_nparray_image, img2_path=selfie_nparray_image, model_name="Facenet512", detector_backend="retinaface")
		print(results)
		return results["verified"]
	except Exception as e:
		print("Error: (" + str(type(e).__name__) + ") " + str(e))
		traceback.print_exc()
		return None