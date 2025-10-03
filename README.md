## AuslanLive

The first publicly available auslan translation app.

## Install requirements/dependencies:

`pip install -r requirements.txt`

## 🚀 Run Locally
Dependencies

1. Install pip (python package manager), then from the root folder, run: pip install -r requirements.txt
2. Install FFMPeg for video conversion. This process is different between Mac and Windows, please consult the documentation online. Go to: https://ffmpeg.org/download.html

In the root folder, run the below two commands in two separate terminals:

1. Start the client:

`npm run dev`

2. Start the server (Flask):

`python -m app.server`

## 🌐 Deployed Live At:
## Currently deployed at:

https://auslan-client-23374783959.australia-southeast1.run.app/

## Committing large files 
Use Git LFS to commit large files. You can see what is currently being tracked by examining the contents of the `.gitattributes` file.

To commit a file using Git LFS using the CLI, please consult the official documentation:

https://github.blog/open-source/git/git-lfs-2-2-0-released/

## Credits:
Sign video animation uses the pose library from Sign MT. Used under the MIT licence outlined on the repository:

https://github.com/sign-language-processing/pose

Auslan signs currently sourced from Auslan Signbank:

https://auslan.org.au/

## Build and Deploy Using Docker and Google Cloud:

Currently using Docker and Google Cloud to build the project. Please follow the below in your CLI to build and deploy the application:

> [!NOTE]
> Please build this using a Windows machine for now. Mac/Linux have different defaults for the docker image build. Workaround still to be found.
> FFMPEG video creation - can only use the libx264 encoder for now, as it uses the CPU. GPU support is not ensured on the gcloud container.

**Install Docker:**

Follow: https://docs.docker.com/desktop/

**Install Google Cloud SDK/CLI:**

Follow: https://cloud.google.com/sdk/docs/install

**Server**

Build the image:

`docker build -t gcr.io/auslan-app-461803/auslan-api -f Dockerfile.api .`

Push the image to Google Cloud:

`docker push gcr.io/auslan-app-461803/auslan-api`

Deploy image to Google Cloud container:

`gcloud run deploy auslan-api --image gcr.io/auslan-app-461803/auslan-api --platform managed --region australia-southeast1 --allow-unauthenticated --port 5173 --memory 4Gi --cpu 2`

**Client**

Build the image:

`docker build -t gcr.io/auslan-app-461803/auslan-client -f Dockerfile.client .`

Push the image to Google Cloud:

`docker push gcr.io/auslan-app-461803/auslan-client`

Deploy image to Google Cloud container:

`gcloud run deploy auslan-client --image gcr.io/auslan-app-461803/auslan-client --platform managed --region australia-southeast1 --allow-unauthenticated --port 80`