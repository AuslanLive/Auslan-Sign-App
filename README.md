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
