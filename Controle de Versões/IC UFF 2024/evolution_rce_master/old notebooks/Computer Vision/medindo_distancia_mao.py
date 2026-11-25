import cv2
from cvzone.HandTrackingModule import HandDetector

video = cv2.VideoCapture(0)

video.set(3, 1280)
video.set(4, 720)

detector = HandDetector(detectionCon=0.8, maxHands=1)

while True:
    check, img = video.read()

    hands, img = detector.findHands(img, draw=True)

    if hands:
        hand1 = hands[0]
        lmList1 = hand1["lmList"]

        x1, y1, z1 = lmList1[5]
        x2, y2, z2 = lmList1[17]

        distancia = abs(x2 - x1)
        print(distancia, "cm")
        try:
            bbox1 = hand1["bbox"]
            centerPoint1 = hand1["center"]
            handType1 = hand1["type"]

            cv2.circle(img, lmList1[8], 15, (0, 0, 255), cv2.FILLED)
            cv2.circle(img, lmList1[12], 15, (0, 0, 255), cv2.FILLED)

            # Drawing a line between the tip of index and middle finger
            cv2.line(img, lmList1[8], lmList1[12], (255, 0, 255), 3)
        except:
            print("erro")

    cv2.imshow("Image", img)
    cv2.waitKey(1)
