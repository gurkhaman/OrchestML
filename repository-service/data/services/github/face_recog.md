This is a face recognition package for ROS2 (tested on Humble).

It uses Facenet to do the work, and is trained on your own data.  You should supply 
around 20 photos of each person to train it.

The input is a ROS2 topic containing video (produced by any ROS2 camera node).

The output is a ROS2 topic containing the bounding boxes of detected faces and the 
identity of the person in the bounding box.

See BUILD_INSTRUCTIONS and USAGE_INSTRUCTIONS for more info.

## BUILD_INSTRUCTIONS
Install facenet_pytorch - see https://github.com/timesler/facenet-pytorch

#Clone two packages into your ros2 workspace.

cd ~/ros2_ws/src
git clone git@github.com:elpidiovaldez/face_recog.git
git clone git@github.com:elpidiovaldez/vision_interfaces.git

#Build the packages
cd ~/ros2_ws
colcon build --symlink-install

#Now you need to provide your own face data and train the recogniser - see USAGE INSTRUCTIONS

#Start the recogniser:

  source install/setup.bash
  ros2 run face_recog live_face_recog --ros-args -p show_faces:=True

#Start a webcamera video stream in another terminal:

  ros2 run v4l2_camera v4l2_camera_node  --ros-args --remap image_raw:=image -p image_size:=[800,600]
  
  
Or run a complete demo:
 
  cd ~/ros2_ws
  source install/setup.bash
  ros2 launch face_recog face_recog_demo.launch.xml

## USAGE_INSTRUCTIONS
PREPARE A DATA DIRECTORY

Create a folder for each person to be recognised, named with the person's name or id.
Populate the folder for each person with photos of them.  The photos should only contain one face (if there
are multiple faces, then the largest is chosen).

e.g.

face_recog/data
    photos_raw
        person1-name
            person1-photo1.jpg
            person1-photo1.png
            ...
            
        person2-name
            person2-photo1.jpg
            person2-photo2.jpg
            ...
            
        person3-name
            ...

CREATE AND TRAIN A NEURAL NETWORK MODEL

Enter the script directory and run:
./review_training_data.py

This will create a new folder in the data directory called photos_aligned_faces containing sub-folders for each person.
The sub-folders contain cropped, processed faces.  Check that all the faces are of the correct person and of good quality.
If a face is not good, remove the source photo from photos_raw, delete photos_aligned_faces, and re-run review_training_data.py

usage: review_training_data.py [-h] [--data <datapath>] [--no_save_faces] [--show_faces]
optional arguments:
  -h, --help        Show this help message and exit
  --data <datapath> Path to the data folder (which contains the photos_raw folder).  Defaults to '../data'.
  --no_save_faces   Specify that cropped faces should not be saved to photos_aligned_faces folder for review
  --show_faces      Specify that cropped faces should be displayed on-screen as they are extracted

Note: --show_faces will mean user needs to press a key after each face has been viewed.

When all faces are good, run ./make_classifier.  This will create a trained
recognition model called face_classifier.pt in the data folder.  

usage: make_classifier.py [-h] [--data DATA]
optional arguments:
  -h, --help   show this help message and exit
  --data DATA  Path to the data folder (which contains the photos_raw folder)

The final
directory structure will be as shown below.  The photos in photos_aligned_faces
preserve the source file name and extension, for easy cross-reference.

face_recog/data

    face_classifier.pt
    
    photos_raw
        person1-name
            person1-photo1.jpg
            person1-photo1.png
            ...
            
        person2-name
            person2-photo1.jpg
            person2-photo2.jpg
            ...
            
        person3-name
            ...
    photos_aligned_faces
            person1-photo1.jpg
            person1-photo1.png
            ...
            
        person2-name
            person2-photo1.jpg
            person2-photo2.jpg
            ...
            
        person3-name
            ...


RUNNING FACE RECOGNITION ON LIVE VIDEO

The ros node takes input from the topic 'image'.
To launch the node, use:

ros2 run face_recog live_face_recog.py

A full demo using usb_webcam and displaying marked-up video on screen can be run by:

ros2 launch face_recog face_recog_demo.launch.xml