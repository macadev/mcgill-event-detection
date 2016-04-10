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
stringstream video_path;
vector<double> timestamps;
double fps;
int drawn_matches_rows, drawn_matches_cols;
VideoWriter writer;
// Descriptor Objects
const string algorithm = "SURF";
Ptr<FeatureDetector> feature_detector = FeatureDetector::create(algorithm);
//Ptr<FeatureDetector> fast_detector;
//fast_detector = new DynamicAdaptedFeatureDetector(new FastAdjuster(10, true), 5000, 10000, 10);
Ptr<DescriptorExtractor> descriptor_extractor = DescriptorExtractor::create(algorithm);
// Matcher Objecsts
BFMatcher matcher(NORM_L2, false);
FlannBasedMatcher flann_matcher;



void read_images(vector<Mat> &);
void display_images(vector<Mat>);
void compute_keyPoints(vector<Mat>);
Mat determine_mask(Mat, Rect);
void compute_roi_features(Mat, Mat, vector<KeyPoint> &, Mat &);
void compute_features(Mat, vector<KeyPoint> &, Mat &);
void compare_matches(Mat, Mat, vector<DMatch> &);
int display_matches(Mat, vector<KeyPoint>, Mat, vector<KeyPoint>, vector<DMatch>);
void printParams(Algorithm *algorithm);

int main(int argc, char **argv){

        // PRE-PROCESSING

    printParams(feature_detector); 
    double xx1 = stod(argv[1]);
    double yy1 = stod(argv[2]);
    double xx2 = stod(argv[3]);
    double yy2 = stod(argv[4]);
    double time = stod(argv[5]);
    string output_video_id = argv[6];
    double start_time = stod(argv[7]);
    double end_time = stod(argv[8]);
    double sampling_rate = stod(argv[9]);
 
    // Initialize OpenCV nonfree module
    initModule_nonfree();

    // Load the video
    stringstream input_video;
    input_video <<  "/home/ubuntu/projects/Event_Detection/src/EventDetectionWebServer/dled_video" << output_video_id << ".mp4";
    VideoCapture capture(input_video.str());
    if(!capture.isOpened())
        throw "Error reading video";

    // Process the ROI
    //cout << "TIME!: " << time << endl;
    capture.set(CV_CAP_PROP_POS_MSEC, time);
    Mat roi;
    capture >> roi;
	
    // Process video dimensions
    int video_height = roi.rows;
    int video_width = roi.cols;
    //cout << "Video Width: " << video_width << endl;
    //cout << "Video Height: " << video_height << endl;

    // Initialize the video writer
    fps = capture.get(CV_CAP_PROP_FPS);
    int number_of_frames = capture.get(CV_CAP_PROP_FRAME_COUNT);

    // Determine region of interest (scaled against youtube dimensions)
    int scaled_x1 = xx1 / 640 * video_width;
    int scaled_y1 = yy1 / 360 * video_height;
    int scaled_x2 = xx2 / 640 * video_width;
    int scaled_y2 = yy2 / 360 * video_height;	
    Mat mask = determine_mask(roi, Rect(scaled_x1, scaled_y1, scaled_x2 - scaled_x1, scaled_y2 - scaled_y1));
    Mat masked_image;
    roi.copyTo(masked_image, mask);

    // Write ROI image

    stringstream roi_path; 
    roi_path << "/home/ubuntu/projects/Event_Detection/src/EventDetectionWebServer/roi_image" << output_video_id << ".png";
    imwrite(roi_path.str(), masked_image);

    // TODO: Reset position to Options.START
    capture.set(CV_CAP_PROP_POS_MSEC, (int)(start_time));
    video_path << "/home/ubuntu/projects/Event_Detection/src/EventDetectionWebServer/output" << output_video_id << ".avi";

    // Compute features of the masked region
    vector<KeyPoint> roi_keyPoints; 
    Mat roi_descriptor;
    compute_roi_features(roi, mask, roi_keyPoints, roi_descriptor);

    int counter = 0;
    int prev_percent_complete = 0;
    int current_percent_complete = 0;
    Mat frame;
    // TODO: unil Options.END
    //cout << "about to enter for" << endl;
    for(capture>>frame;!frame.empty() && capture.get(CV_CAP_PROP_POS_MSEC) < (int)(end_time);capture>>frame){
        // TODO: skip by Options.SAMPLE_RATE
	    if (counter++ % (int)(sampling_rate) != 0) {
	        writer << frame;
	        continue;
	    }
        // Display percentage complete
	    current_percent_complete = int ((counter / number_of_frames) * 100);
	    if (current_percent_complete != prev_percent_complete) {
	        //cout << current_percent_complete << "%" << endl;
	    }	
	    prev_percent_complete = current_percent_complete;

        vector<KeyPoint> keyPoints;
        Mat descriptor;
        compute_features(frame, keyPoints, descriptor);
        Mat keyPoints_frame;
        drawKeypoints(frame, keyPoints, keyPoints_frame);
        vector<DMatch> matches;
        compare_matches(roi_descriptor, descriptor, matches);
        if(display_matches(masked_image, roi_keyPoints, frame, keyPoints, matches)){
            //cout << "object detected" << endl;
            timestamps.push_back(capture.get(CV_CAP_PROP_POS_MSEC)/1000);
        }

        // TODO: is the object in the scene? Track.time.push_back(timestamp)
        
        waitKey(1);
	    counter++;
    }
    writer.release();
    
    stringstream times;

    for (int i = 0; i < timestamps.size(); i++) {
        times << to_string(timestamps[i]) << ", ";
    }
    cout << times.str() << endl;
}


void compute_roi_features(Mat image, Mat mask, vector<KeyPoint> &roi_keyPoints, Mat &roi_descriptor){
    feature_detector->detect(image, roi_keyPoints, mask);
    descriptor_extractor->compute(image, roi_keyPoints, roi_descriptor); 
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
    flann_matcher.match(roi_descriptor, descriptor, matches);
}

int display_matches(Mat image1, vector<KeyPoint> keyPoints1, Mat image2, vector<KeyPoint> keyPoints2, vector<DMatch> matches){
    Mat drawn_matches;
    vector<DMatch> filtered_matches;
    vector<Point2f> inliners;

    // calc min distance
    double min_distance = -1;
    for(int i=0;i<matches.size();i++){
        if(matches[i].distance < min_distance || min_distance < 0)
            min_distance = matches[i].distance;
    } 
    // get good matches based on min distance
    for(int i=0;i<matches.size();i++){
        if(matches[i].distance < 2*min_distance && matches[i].distance < 0.06){
            filtered_matches.push_back(matches[i]);
            inliners.push_back(keyPoints2[matches[i].queryIdx].pt); 
        } 
    }

    vector<Point2f> obj;
    vector<Point2f> scene;
  
    // Get the keypoints from the good matches
    for(int i=0;i<filtered_matches.size();i++){
        obj.push_back(keyPoints1[filtered_matches[i].queryIdx].pt);
        scene.push_back(keyPoints2[filtered_matches[i].trainIdx].pt);
    }
    // ransac
    if(filtered_matches.size() >= 4){
        Mat H = findHomography(obj, scene, CV_RANSAC);
    
        perspectiveTransform(obj, scene, H); 
    }
    
    stringstream convert;
    convert << filtered_matches.size();
    String num_matches = convert.str(); 

    //if(filtered_matches.size() > 5){
    if(scene.size() > 5){
        detected = "Object Detected";
    }else
        detected = "No Object Detected";

    putText(image2, detected, Point(50, 50), FONT_HERSHEY_SIMPLEX, 1, Scalar(255, 255, 255));
    //Rect bounding_box = cv::boundingRect(inliners);
    
    image2.copyTo(drawn_matches);
    //rectangle(drawn_matches, bounding_box.tl(), bounding_box.br(), Scalar(255, 255, 255));
    
    drawMatches(image1, keyPoints1, image2, keyPoints2, filtered_matches, drawn_matches);
    if(!writer.isOpened()){
        int fourcc = CV_FOURCC('M','J','P','G');
        writer = VideoWriter(video_path.str(), fourcc, fps, Size(drawn_matches.cols, drawn_matches.rows), true);
    }

    //imshow("matches", drawn_matches);
    writer << drawn_matches;
    
    return detected.compare("Object Detected") == 0? 1 : 0;
}

void read_images(vector<Mat> &images){
    for(int i=0;i<NUM_IMAGES;i++){
        images.push_back(imread(IMG_NAMES[i]));
    }
}

void display_images(vector<Mat> images){
    for(int i=0;i<NUM_IMAGES;i++){
        //imshow("image ", images[i]);
        //waitKey(0);
    }
}

void printParams( cv::Algorithm* algorithm ) {
    std::vector<std::string> parameters;
    algorithm->getParams(parameters);

    for (int i = 0; i < (int) parameters.size(); i++) {
        std::string param = parameters[i];
        int type = algorithm->paramType(param);
        std::string helpText = algorithm->paramHelp(param);
        std::string typeText;

        switch (type) {
        case cv::Param::BOOLEAN:
            typeText = "bool";
            break;
        case cv::Param::INT:
            typeText = "int";
            break;
        case cv::Param::REAL:
            typeText = "real (double)";
            break;
        case cv::Param::STRING:
            typeText = "string";
            break;
        case cv::Param::MAT:
            typeText = "Mat";
            break;
        case cv::Param::ALGORITHM:
            typeText = "Algorithm";
            break;
        case cv::Param::MAT_VECTOR:
            typeText = "Mat vector";
            break;
        }
        //std::cout << "Parameter '" << param << "' type=" << typeText << " help=" << helpText << std::endl;
    }
}
