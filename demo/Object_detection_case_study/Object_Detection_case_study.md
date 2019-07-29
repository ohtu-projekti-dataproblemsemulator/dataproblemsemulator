# Object Detection case study

## Comparison of models from FaceBook's Detectron-project and YOLOv3GPU

We compared the performance of models from FaceBook's Detectron project and YOLOv3 model from Joseph Redmon, when different error sources were added. The models from FaceBook's Detectron project were FasterRCNN, MaskRCNN and RetinaNet.

## Data

We used 118 288 jpg-images (COCO train2017) to train the models. 5000 images (COCO val2017) were used to calculate the mAP-50 scores.

Detectron's model zoo had pretrained weights for FasterRCNN, MaskRCNN and RetinaNet. YOLOv3's weights were trained by us, using the Kale cluster of University of Helsinki. The training took approximately five days when two NVIDIA Tesla V100 GPUs were used. 

## Error types used in the case study

* Gaussian blur

* Rain

* Snow

* JPEG compression

* Resolution change

### Gaussian blur filter

#### Example images using the filter:

##### std 0.0

![std 0.0](https://github.com/dpEmu/dpEmu/blob/object_detection_case_study/demo/Object_detection_case_study/Blur_Gaussian/20190729-150653-727543.jpg)

##### std 1.0

![std 1.0](https://github.com/dpEmu/dpEmu/blob/object_detection_case_study/demo/Object_detection_case_study/Blur_Gaussian/20190729-150700-771777.jpg)

##### std 2.0

![std 0.0](https://github.com/dpEmu/dpEmu/blob/object_detection_case_study/demo/Object_detection_case_study/Blur_Gaussian/20190729-150707-503684.jpg)

##### std 3.0

![std 1.0](https://github.com/dpEmu/dpEmu/blob/object_detection_case_study/demo/Object_detection_case_study/Blur_Gaussian/20190729-150714-401435.jpg)

#### The results of Gaussian Blur filter

![Gaussian Blur](https://github.com/dpEmu/dpEmu/blob/object_detection_case_study/demo/Object_detection_case_study/Blur_Gaussian/20190728-011623-029059.png)

### Rain filter

#### Example images using the filter:

##### probability 0.0001

![probability 10^-4](https://github.com/dpEmu/dpEmu/blob/object_detection_case_study/demo/Object_detection_case_study/Rain/20190729-151307-080828.jpg)

##### probability 0.001

![probability 10^-3](https://github.com/dpEmu/dpEmu/blob/object_detection_case_study/demo/Object_detection_case_study/Rain/20190729-151314-483299.jpg)

##### probability 0.01

![probability 10^-2](https://github.com/dpEmu/dpEmu/blob/object_detection_case_study/demo/Object_detection_case_study/Rain/20190729-151323-269028.jpg)

##### probability 0.1

![probability 10^-1](https://github.com/dpEmu/dpEmu/blob/object_detection_case_study/demo/Object_detection_case_study/Rain/20190729-151330-649152.jpg)

#### The results of Rain filter 

![Rain](https://github.com/dpEmu/dpEmu/blob/object_detection_case_study/demo/Object_detection_case_study/Rain/20190727-103514-755422.png)

### Snow filter

#### Example images using the filter:

##### probability 0.0001

![probability 10^-4]()

##### probability 0.001

![probability 10^-3]()

##### probability 0.01

![probability 10^-2]()

##### probability 0.1

![probability 10^-1]()

#### The results of Snow filter

![Snow](https://github.com/dpEmu/dpEmu/blob/object_detection_case_study/demo/Object_detection_case_study/Snow/20190727-162540-567252.png)

### JPEG Compression

#### Example images using the filter:

##### quality 10

![quality 10]()

##### quality 20

![quality 20]()

##### quality 30

![quality 30]()

##### quality 100

![quality 100]()

#### The results of JPEG Compression filter

![JPEG Compression](https://github.com/dpEmu/dpEmu/blob/object_detection_case_study/demo/Object_detection_case_study/JPEG_Compression/20190727-062156-111953.png)

### Resolution

#### Example images using the filter:

##### Value of k 1

![k 1]()

##### Value of k 2

![k 2]()

##### Value of k 3

![k 3]()

##### Value of k 4

![k 4]()

#### The results of Resolution filter

![Resolution]()