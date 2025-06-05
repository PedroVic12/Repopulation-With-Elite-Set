import cv2

caputa = cv2.VideoCapture(0)
while True:
    ret, frame = caputa.read()
    cv2.imshow("frame", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

caputa.release()
cv2.destroyAllWindows()
print("Camera released")  # print a message to let us know the camera has been released
