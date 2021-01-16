import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt
import os
# import commonfunctions
from skimage import io, color
from skimage.feature import local_binary_pattern
from sklearn.preprocessing import minmax_scale
# from commonfunctions import show_images, showHist
from sklearn import svm
from sklearn import metrics

def get_paragraph(gray_img, bin_img):

    height, width = gray_img.shape

    contours, hierarchy = cv.findContours(bin_img, cv.RETR_LIST, cv.CHAIN_APPROX_SIMPLE)

    threshold_width = 1500


    up, down, left, right = 0, height - 1, 0, width - 1

    for cnt in contours:
        x, y, w, h = cv.boundingRect(cnt)

        if w < threshold_width:
            continue

        if y < height / 2:
            if y > up:
                up = y
        else:
            down = y

    th = 0
    bin_img = bin_img[up:down + 1, left:right + 1]
    gray_img = gray_img[up:down + 1, left:right + 1]
    # Apply erosion to remove noise and dots.
    kernel = np.ones((3, 3), np.uint8)
    bin_img = cv.erode(bin_img, kernel, iterations=3)
    pts = np.nonzero(bin_img)
    x_min, y_min, x_max, y_max = min(pts[0]), min(pts[1]), max(pts[0]), max(pts[1])
    bin_img = bin_img[x_min-th:x_max+th, y_min-th:y_max+th]
    gray_img = gray_img[x_min-th:x_max+th, y_min-th:y_max+th]
    # Return the handwritten paragraph
    return gray_img, bin_img

def preprocessing(gray_img):
    gray_img = cv.GaussianBlur(gray_img, (5, 5), 0)
    ## (2) threshold
    thresh, bin_img = cv.threshold(gray_img, 0, 255, cv.THRESH_BINARY_INV|cv.THRESH_OTSU)
    gray_img, bin_img = get_paragraph(gray_img, bin_img)
    thresh, bin_img = cv.threshold(gray_img, 0, 255, cv.THRESH_BINARY_INV|cv.THRESH_OTSU)
#     plt.imshow(bin_img)
    hist = cv.reduce(bin_img,1, cv.REDUCE_AVG).reshape(-1)
#     for i in range(len(hist)):
#         print(i, hist[i])
    th = 2
    H,W = bin_img.shape[:2]
    uppers = []
    lowers = []
    if hist[0] > th:
        uppers.append(0)
    
     
    for y in range(H-1):
        if hist[y]<=th and hist[y+1]>th:
            uppers.append(y)
     
    for y in range(H-1):
        if hist[y]>th and hist[y+1]<=th:
            lowers.append(y)
            
    if hist[len(hist)-1] > th:
        lowers.append(len(hist)-1)

#     img = cv.cvtColor(gray_img, cv.COLOR_GRAY2BGR)
    
    lines = []
    bin_lines = []
    temp_uppers = uppers.copy()
    temp_lowers = lowers.copy()
    for i in range(len(uppers)):
        if lowers[i] - uppers[i] > 50:
            lines.append(gray_img[uppers[i]:lowers[i], :])
            bin_lines.append(bin_img[uppers[i]:lowers[i], :])
        else:
            temp_uppers.remove(uppers[i])
            temp_lowers.remove(lowers[i])
#     print(temp_uppers)
#     print(temp_lowers)

    count = 1
#     for l in bin_lines:
#         cv.imwrite("line" + str(count) + ".png", l)
#         count+=1
    
    return lines, bin_lines

def LBP_feature_extraction(lines,bin_lines, features, labels, label):
    R = 3
    P = 8
    featureVectors = []
    for i in range(len(lines)):
        #rgb to grat scale
        grayImage = cv.cvtColor(lines[i], cv.COLOR_BGR2GRAY)
        #calc PBL
        LBPImage = local_binary_pattern(grayImage, P, R)
        #change format for histogram function
        LBPImage = np.uint8(LBPImage)     
        #calculate the histogram
        LBPHist = cv.calcHist([LBPImage],[0],bin_lines[i],[256],[0,256])
        #normalize the histogram 0-1
        normalizedHist = minmax_scale(LBPHist)
        #normalizedHist = LBPHist/np.mean(LBPHist)
        #print(normalizedHist[:,0])
        featureVectors.append(normalizedHist)
        features.append(normalizedHist[:,0])
        labels.append(label)
        #plot histogram
        #plt.hist(normalizedHist, bins=256)
        #plt.show()
    return featureVectors

def get_features(pics,features,labels,ids):
    for i in range(len(pics)):
        gray_img = cv.cvtColor(pics[i], cv.COLOR_BGR2GRAY)
        lines,bin_lines = preprocessing(gray_img)
        LBP_feature_extraction(lines,bin_lines, features, labels, ids[i])

def train_using_svm(features,labels):
    clf = svm.SVC(kernel='linear') # Linear Kernel
    clf.fit(features, labels)
    return clf

def testing(clf,testImage,ids):
    trainF = []
    trainLabels = []
    testPic = [testImage]
    get_features(testPic,trainF,trainLabels,ids)
    trainF = np.array(trainF)
    trainLabels = np.array(trainLabels)
    y_pred = clf.predict(trainF)
    print(y_pred)
    print("Most frequent value in the above array:") 
    print(np.bincount(y_pred).argmax())
    print("Accuracy:",metrics.accuracy_score(trainLabels, y_pred),"\n")
    return 1 if np.bincount(y_pred).argmax() == ids[0] else 0

def runTests(num):

    features = []
    labels = []
    rootDir = "TestCases"
    testCase = num
    testDir = os.path.join(rootDir,testCase)
    picsPath = []
    testPath = []
    for dirpath, dirnames, files in os.walk(testDir):
        if dirpath == testDir:
            testPath.append(os.path.join(dirpath,files[-1]))
            continue
        for file in files:
            picsPath.append(os.path.join(dirpath,file))

    # print(picsPath)
    # print(testPath)
    testId = []
    with open(os.path.join(rootDir,"results.txt")) as fp: 
        Lines = fp.readlines() 
        for line in Lines: 
            if "TestCase " + testCase in line:
                testId.append(int(line[len(line)-2]))
                break

    print(testId)

    ids = [1,1,2,2,3,3]
    #read all images
    pics = []
    for i in range(len(picsPath)):
        img = cv.imread(picsPath[i])
        pics.append(img)
    testImage =  cv.imread(testPath)
    #create data and train model
    get_features(pics,features,labels,ids)
    features = np.array(features)
    labels = np.array(labels)
    clf = train_using_svm(features,labels)
    
    #test model
    return testing(clf,testImage,testId)

testCasesNum = 5
totalAcc = 0
for i in range(1,testCasesNum + 1):
    totalAcc += runTests(str(i))

print("total accuracy ... = ",totalAcc/testCasesNum)