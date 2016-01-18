#import the necessary packages
from feature_extractor.SIFT_extractor import RootSIFT
import cv2
 
# load the image we are going to extract descriptors from and convert
# it to grayscale
image = cv2.imread("../../../resources/image_samples/sample-1.jpg")
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
 
# detect Difference of Gaussian keypoints in the image
detector = cv2.FeatureDetector_create("SIFT")
kps = detector.detect(gray)
 
# extract normal SIFT descriptors
extractor = cv2.DescriptorExtractor_create("SIFT")
(kps, descs) = extractor.compute(gray, kps)
print "SIFT: kps=%d, descriptors=%s " % (len(kps), descs.shape)
 
sift = cv2.drawKeypoints(gray, kps)
cv2.imwrite("SIFT1.png", sift)

# extract RootSIFT descriptors
rs = RootSIFT()
(kps, descs) = rs.extract_features(gray, kps)
print "RootSIFT: kps=%d, descriptors=%s " % (len(kps), descs.shape)

sift = cv2.drawKeypoints(gray, kps)
cv2.imwrite("SIFT2.png", sift)
