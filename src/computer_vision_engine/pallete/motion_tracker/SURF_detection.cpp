#include <opencv2/opencv.hpp>
#include <opencv2/nonfree/nonfree.hpp>
#include <opencv2/core/core.hpp>
#include <opencv2/highgui/highgui.hpp>
#include <string>
#include <iostream>

using namespace cv;
using namespace std;

const int NUM_IMAGES = 6;
const string IMG_NAMES[] = {"/workbox/Design Project/Event_Detection/resources/image_samples/javan1.png",
                            "/workbox/Design Project/Event_Detection/resources/image_samples/javan2.png",
                            "/workbox/Design Project/Event_Detection/resources/image_samples/javan3.png",
                            "/workbox/Design Project/Event_Detection/resources/image_samples/javan4.png", 
                            "/workbox/Design Project/Event_Detection/resources/image_samples/javan5.png",
                            "/workbox/Design Project/Event_Detection/resources/image_samples/javan6.png"};

String detected;
vector<double> timestamps;
double fps;
VideoWriter writer;
// Descriptor Objects
const string algorithm = "SURF";
Ptr<FeatureDetector> feature_detector = FeatureDetector::create(algorithm);
Ptr<DescriptorExtractor> descriptor_extractor = DescriptorExtractor::create(algorithm);
BFMatcher matcher(NORM_L2, false);

void read_images(vector<Mat> &);
void display_images(vector<Mat>);
void compute_keyPoints(vector<Mat>);
Mat determine_mask(Mat, Rect);
void compute_roi_features(Mat, Mat, vector<KeyPoint> &, Mat &);
void compute_features(Mat, vector<KeyPoint> &, Mat &);
void compare_matches(Mat, Mat, vector<DMatch> &);
int display_matches(Mat, vector<KeyPoint>, Mat, vector<KeyPoint>, vector<DMatch>);

int main(int argc, char **argv){

    double xx1 = stod(argv[1]);
    double yy1 = stod(argv[2]);
    double xx2 = stod(argv[3]);
    double yy2 = stod(argv[4]);
    double time = stod(argv[5]);
    string output_video_id = argv[6];


    // Initialize OpenCV nonfree module
    initModule_nonfree();

    // Load the video
    VideoCapture capture(0);
    if(!capture.isOpened())
        throw "Error reading video";

    // Process the ROI
    capture.set(CV_CAP_PROP_POS_MSEC, time);
    Mat roi;
    capture >> roi;

    //Mat roi = imread("/workbox/Design Project/Event_Detection/resources/image_samples/roi_book.png");
    
    // Initialize the video writer
    fps = capture.get(CV_CAP_PROP_FPS);
    stringstream video_path;
    int fourcc = CV_FOURCC('M','J','P','G');
    video_path << "output" << output_video_id << ".avi";
    writer = VideoWriter(video_path.str(), fourcc, fps, roi.size(), true);

    
    // Determine region of interest
    int x1=126, y1=51;
    int x2=435, y2=444;
    //Mat mask = determine_mask(roi, Rect(x1, y1, x2-x1, y2-y1));
    Mat mask = determine_mask(roi, Rect(xx1, yy1, xx2-xx1, yy2-yy1));
    Mat masked_image;
    roi.copyTo(masked_image, mask);

    stringstream roi_image;
    roi_image << "roi_image" << output_video_id << ".png";

    imwrite(roi_image, roi);

    capture.set(CV_CAP_PROP_POS_MSEC, 0);

    // Compute features of the masked region
    vector<KeyPoint> roi_keyPoints; 
    Mat roi_descriptor;
    compute_roi_features(roi, mask, roi_keyPoints, roi_descriptor);
    
    Mat frame;
    for(capture>>frame;!frame.empty();capture>>frame){
        vector<KeyPoint> keyPoints;
        Mat descriptor;
        compute_features(frame, keyPoints, descriptor);
        Mat keyPoints_frame;
        drawKeypoints(frame, keyPoints, keyPoints_frame);
        vector<DMatch> matches;
        compare_matches(roi_descriptor, descriptor, matches);
        if(display_matches(masked_image, roi_keyPoints, frame, keyPoints, matches))
            timestamps.push_back(capture.get(CV_CAP_PROP_POS_MSEC)/1000);

        waitKey(1);
    }
    for (int i = 0; i < timestamps.size(); i++) {
	cout << timestamps[i] << endl;
    }
}


void compute_roi_features(Mat image, Mat mask, vector<KeyPoint> &roi_keyPoints, Mat &roi_descriptor){
    feature_detector->detect(image, roi_keyPoints, mask);
    descriptor_extractor->compute(image, roi_keyPoints, roi_descriptor); 

    // draw keyPoints
    Mat roi_features;
    drawKeypoints(image, roi_keyPoints, roi_features);
    imshow("ROI features", roi_features);
    waitKey(0);
}

void compute_features(Mat image, vector<KeyPoint> &keyPoints, Mat &descriptor){
    feature_detector->detect(image, keyPoints);
    descriptor_extractor->compute(image, keyPoints, descriptor); 
}


// returns a binarized mask the same size of the input image, with the pixels inside the rectangle 
// denoted as Rect(x, y, w, h) set to 1;
Mat determine_mask(Mat image, Rect rect){
    Mat mask = Mat::zeros(image.size(), CV_8U);
    Mat roi(mask, rect);
    roi = Scalar(255, 255, 255);
    return mask;
}

void compare_matches(Mat roi_descriptor, Mat descriptor, vector<DMatch> &matches){
    matcher.match(roi_descriptor, descriptor, matches);
}

int display_matches(Mat image1, vector<KeyPoint> keyPoints1, Mat image2, vector<KeyPoint> keyPoints2, vector<DMatch> matches){
    Mat drawn_matches;
    vector<DMatch> filtered_matches;
    vector<Point2f> inliners;

    for(int i=0;i<matches.size();i++){
        if(matches[i].distance < 0.06){
            filtered_matches.push_back(matches[i]);

            inliners.push_back(keyPoints2[matches[i].queryIdx].pt); 
        }
    }
    
    stringstream convert;
    convert << filtered_matches.size();
    String num_matches = convert.str(); 


    if(filtered_matches.size() > 5)
        detected = "Object Detected";
    else
        detected = "No Object Detected";

    putText(image2, detected, Point(50, 50), FONT_HERSHEY_SIMPLEX, 1, Scalar(255, 255, 255));
    //Rect bounding_box = cv::boundingRect(inliners);
    
    image2.copyTo(drawn_matches);
    //rectangle(drawn_matches, bounding_box.tl(), bounding_box.br(), Scalar(255, 255, 255));
    
    drawMatches(image1, keyPoints1, image2, keyPoints2, filtered_matches, drawn_matches);
    imshow("matches", drawn_matches);
    writer << drawn_matches;
    
    return detected == "Object Detected"? 1 : 0;
}

void read_images(vector<Mat> &images){
    for(int i=0;i<NUM_IMAGES;i++){
        images.push_back(imread(IMG_NAMES[i]));
    }
}

void display_images(vector<Mat> images){
    for(int i=0;i<NUM_IMAGES;i++){
        imshow("image ", images[i]);
        waitKey(0);
    }
}
