import cv2
import mediapipe as mp

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    model_complexity=0,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Initialize drawing utilities
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# Start webcam capture
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Cannot open camera")
    exit()

def count_raised_fingers(hand_landmarks, handedness, image_width, image_height):
    # Get the hand landmarks
    landmarks = hand_landmarks.landmark
    
    # Finger tip landmarks
    tip_ids = [4, 8, 12, 16, 20]  # thumb, index, middle, ring, pinky
    
    # Count raised fingers
    raised_fingers = 0
    
    # Check if it's left or right hand (for thumb calculation)
    is_right_hand = handedness.classification[0].label == 'Right'
    
    # Check each finger (except thumb)
    for i in range(1, 5):  # index to pinky
        # Compare y-coordinate of tip with y-coordinate of pip (knuckle)
        if landmarks[tip_ids[i]].y < landmarks[tip_ids[i]-2].y:
            raised_fingers += 1
    
    # Special case for thumb (check x-coordinate for right/left hand)
    if is_right_hand:
        if landmarks[4].x < landmarks[3].x:  # Thumb to the left of base
            raised_fingers += 1
    else:
        if landmarks[4].x > landmarks[3].x:  # Thumb to the right of base
            raised_fingers += 1
            
    return raised_fingers

while True:
    # Read a frame from the camera
    success, image = cap.read()
    if not success:
        print("Ignoring empty camera frame.")
        continue

    # Get image dimensions
    image_height, image_width, _ = image.shape

    # To improve performance, optionally mark the image as not writeable to
    # pass by reference.
    image.flags.writeable = False
    # Convert the BGR image to RGB
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Process the image and find hands
    results = hands.process(image_rgb)

    # Draw the hand annotations on the image.
    image.flags.writeable = True
    
    # Check if any hands were detected
    if results.multi_hand_landmarks:
        # Loop through each detected hand
        for hand_landmarks in results.multi_hand_landmarks:
            # Get the coordinates of the index finger tip
            index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
            
            # Convert normalized coordinates to pixel coordinates
            cx, cy = int(index_finger_tip.x * image_width), int(index_finger_tip.y * image_height)
            
            # Print the coordinates
            print(f'Index Finger Tip Coordinates (pixels): x={cx}, y={cy}')

            
            # Draw hand landmarks on the image
            mp_drawing.draw_landmarks(
                image,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style())

            # conta quantos dedos levantados

            

    # Flip the image horizontally for a selfie-view display.
    cv2.imshow('MediaPipe Hands', cv2.flip(image, 1))

    # Exit if 'ESC' is pressed
    if cv2.waitKey(5) & 0xFF == 27:
        break

# Release the capture and destroy all windows
cap.release()
cv2.destroyAllWindows()
hands.close()
