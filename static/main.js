let documentImageBlob;
let selfieImageBlob;

let videoElement;
let videoStream;

async function createCameraFeed(useSelfieCamera)
{
	const video = document.getElementById('video');

	const stream = await navigator.mediaDevices.getUserMedia
	({
		video:
		{
			facingMode: useSelfieCamera ? 'user' : 'environment',
			resizeMode: 'crop-and-scale'
		},
		audio: false
	});

	videoStream = stream;
	video.srcObject = stream;
	video.play();
	return video;
}

async function getCameraFeed()
{
	if(videoElement === undefined) videoElement = await createCameraFeed();
	return videoElement;
}

function stopCameras()
{
	if(videoStream === undefined) throw new Error("Theres not a video stream to stop");
	videoStream.getTracks().forEach(function(track)
	{
		track.stop();
	});
}

async function changeCameraDirection(selfie)
{
	if(videoStream === undefined) throw new Error("Theres not a video stream available to change direction to");
	stopCameras();

	videoElement = await createCameraFeed(selfie);
	return videoElement;
}

document.getElementById('document-btn').addEventListener('click', async function()
{
	const canvas = document.getElementById('document-canvas');
	const ctx = canvas.getContext('2d');
	const overlayImg = new Image();
	overlayImg.src = "overlay_document.svg";

	let video = await getCameraFeed();

	function drawFrame()
	{
		let aspect = video.videoHeight / video.videoWidth;
		let wantedWidth = window.innerWidth * 0.75;
		let height = Math.round(wantedWidth * aspect);

		//console.log(video.videoWidth, video.videoHeight, aspect, wantedWidth, height);
	
		canvas.width = wantedWidth;
		canvas.height = height;

		ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
		ctx.drawImage(overlayImg, 0, 0, canvas.width, canvas.height);

		requestAnimationFrame(drawFrame);
	}
	
	document.getElementById('document-section').hidden = true;
	document.getElementById('document-canvas-container').hidden = false;

	document.getElementById('document-shutter').addEventListener('click', async function()
	{
		documentImageBlob = await captureImage(video);
		
		let urlCreator = window.URL || window.webkitURL;
		let imageUrl = urlCreator.createObjectURL(documentImageBlob);
		document.getElementById('document-result').src = imageUrl;

		document.getElementById('document-canvas-container').hidden = true;
		document.getElementById('selfie-section').hidden = false;
	});
	//resize();
	drawFrame();
});

document.getElementById('selfie-btn').addEventListener('click', async function()
{
	useSelfieCamera = true;

	const canvas = document.getElementById('selfie-canvas');
	const ctx = canvas.getContext('2d');

	let video = await changeCameraDirection(true);

	function drawFrame()
	{
		let aspect = video.videoHeight / video.videoWidth;
		let wantedWidth = window.innerWidth * 0.75;
		let height = Math.round(wantedWidth * aspect);
	
		//console.log(video.videoWidth, video.videoHeight, aspect, wantedWidth, height);
	
		canvas.width = wantedWidth;
		canvas.height = height;

		ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
		//ctx.drawImage(overlayImg, 0, 0, canvas.width, canvas.height);

		requestAnimationFrame(drawFrame);
	}
	
	document.getElementById('selfie-section').hidden = true;
	document.getElementById('selfie-canvas-container').hidden = false;

	document.getElementById('selfie-shutter').addEventListener('click', async function()
	{
		selfieImageBlob = await captureImage(video);
		
		let urlCreator = window.URL || window.webkitURL;
		let imageUrl = urlCreator.createObjectURL(selfieImageBlob);
		document.getElementById('selfie-result').src = imageUrl;

		document.getElementById('selfie-canvas-container').hidden = true;
		document.getElementById('results').hidden = false;
		stopCameras();
		sendImages();
	});
	//resize();
	drawFrame();
});


async function captureImage(video)
{
	const canvas = document.createElement('canvas');
	canvas.width = video.videoWidth;
	canvas.height = video.videoHeight;

	canvas.getContext("2d").drawImage(video, 0, 0);

	return await new Promise(function(resolve)
	{
		canvas.toBlob(resolve, "image/jpeg", 0.9);
	});
}

async function sendImages()
{
	if(documentImageBlob === undefined || selfieImageBlob === undefined)
	{
		console.error('Some blobs are undefined');
		return;
	}

	try
	{
		let formData = new FormData();
		formData.append("image-document", documentImageBlob, "document.jpg");
		formData.append("image-selfie", selfieImageBlob, "selfie.jpg");
	
		let response = await fetch('/api/facial_auth',
		{
			method: 'POST',
			body: formData
		});
	
		let responseText = await response.text();
		let responseJson;
		try
		{
			responseJson = JSON.parse(responseText);
		}
		catch
		{
			console.error("Failed to parse json");
			alert(responseText);
		}
		console.log(responseJson);
		document.getElementById('log-result').innerText = responseText;
		alert(responseJson);
	}
	catch(error)
	{
		alert(JSON.stringify(error));
	}
}
