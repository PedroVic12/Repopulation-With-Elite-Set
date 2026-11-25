import cv2
import numpy as np

# import autopy
import pyautogui
import hand_tracking_module as htm
import time

wCam, hCam = 640, 480
wScr, hScr = pyautogui.size()


def setup():

    ##########################
    frameR = 100  # Frame Reduction
    smoothening = 7
    #########################

    pTime = 0
    plocX, plocY = 0, 0
    clocX, clocY = 0, 0

    cap = cv2.VideoCapture(1)
    cap.set(3, wCam)
    cap.set(4, hCam)
    detector = htm.handDetector(maxHands=1)
    print(wScr, hScr)
    return (
        cap,
        detector,
    )


def showCV(img):
    cv2.imshow("Tela", img)
    cv2.waitKey(1)


def displayText(text):
    cv2.putText(text, (20, 50), cv2.FONT_HERSHEY_PLAIN, 3, 255, 0, 0, 3)


def desenhaCirculo(img, x1, y1):
    cv2.circle(img, (x1, y1), 15, (255, 0, 255), cv2.FILLED)


def movingMode(fingers, x1, y1, WCam, h):
    if fingers[1] == 1 and fingers[2] == 0:
        # 5. converter em coordenadas
        x3 = np.interp(x1, (0, wCam), (0, wScr))
        y3 = np.interp(y1, (0, wCam), (0, hScr))

        # 6 smothen values

        # 7 move mouse
        pyautogui.move(x3, y3)


def main_ia_virtualMouse():
    cap, detector = setup()

    while True:
        # 1. Find hand Landmarks
        success, img = cap.read()
        img = detector.findHands(img)
        lmList, bbox = detector.findPosition(img)
        # 2. Get the tip of the index and middle fingers
        if len(lmList) != 0:
            x1, y1 = lmList[8][1:]
            x2, y2 = lmList[12][1:]
            # print(x1, y1, x2, y2)

            # Check witch fingers
            dedos = detector.fingersUp()
            print(dedos)

            # only finger index - moving mode
            # movingMode(dedos)
            if dedos[1] == 1 and dedos[2] == 0:
                # 5. converter em coordenadas
                x3 = np.interp(x1, (0, wCam), (0, wScr))
                y3 = np.interp(y1, (0, wCam), (0, hScr))

                # 6 smothen values

                # 7 move mouse
                pyautogui.move(x3, y3)

            # frame rate
            cTime = time.time()
            fps = 1 / (cTime - pTime)
            pTime = cTime
            cv2.putText(
                img, str(int(fps)), (20, 50), cv2.FONT_HERSHEY_PLAIN, 3, 255, 0, 0, 3
            )

        # 12 display
        showCV(img)


main_ia_virtualMouse()
