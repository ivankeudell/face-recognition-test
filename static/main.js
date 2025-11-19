let documentImageBlob;

document.getElementById('document-btn').addEventListener('click', async function()
{
	const video = document.getElementById('document-video');
	const canvas = document.getElementById('document-canvas');
	const ctx = canvas.getContext('2d');
	const overlayImg = new Image();
	overlayImg.src = "overlay_document.svg";
	
	const stream = await navigator.mediaDevices.getUserMedia
	({
		video:
		{
			facingMode: 'environment',
			resizeMode: 'crop-and-scale'
		},
		audio: false
	});

	video.srcObject = stream;

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

	document.getElementById('document-shutter').addEventListener('click', async function()
	{
		documentImageBlob = await captureImage(video);
		
		let urlCreator = window.URL || window.webkitURL;
		let imageUrl = urlCreator.createObjectURL(documentImageBlob);
		document.getElementById('document-result').src = imageUrl;
	});
	//resize();
	video.play();
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

/*
function resize()
{
	let video = document.getElementById('document-video');
	let canvas = document.getElementById('document-canvas');
	video.style.height = window.innerHeight;
	video.style.width = window.innerWidth;
	canvas.height = window.innerHeight;
	canvas.width = window.innerWidth;
}

window.addEventListener('resize', resize);
*/
