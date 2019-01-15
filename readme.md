## Whats this all about

Quick and dirty sample to use Azure cognitive services on the edge with a webcam to observe human emotions and characteristics and report the statistics up to IoT Central or an IoT Hub for further analysis.

The scenario we did this demo for was a retail store that wanted to monitor user emotions within the store with an eye to optimizing the store merchandise and/or placement for better emotional response from customers. 

The code uses the Cognitive services Docker container that interfaces with Azure Cognitive services to do the heavy lifting.  Azure Cognitive Services can get expensive for processing frames of video so to prevent sending frames with no faces in it to the service a Haas facial recognition algorithm is run against each frame to look for human faces.  Only if a positive hit for a face occures is the frame then sent for further processing on Azure.

Details on how to obtain the Azure Cognitive Service Docker container can be found here https://docs.microsoft.com/en-us/azure/cognitive-services/face/face-how-to-install-containers

This code was run on a small Intel NUC computer with an Atom class processor and 8GB of RAM.  The video frames were obtained from a Logitech USB webcam using Open CV2.  The OS was Ubuntu 18.04.1 LTS server with the latest version of Docker installed.

If using this with Azure IoT Central you will need to create a device template that has all the telemetry counts in it.  You will also need to derive a connection string from the Device Provisioning Service connection information using the DPS_Keygen tool found here https://github.com/Azure/dps-keygen.

If you run into issues post an issue and I'll try and help as I have time.

