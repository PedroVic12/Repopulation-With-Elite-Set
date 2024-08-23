import cv2
import cvzone


class WebCam:
    def __init__(self) -> None:

        pass

    def caixa_texto(self, imagem, msg):

        cvzone.putTextRect(
            imagem,
            msg,
            (200, 300),
            scale=8,
            thickness=3,
            colorT=(255, 255, 255),
            colorR=(255, 0, 255),
            font=cv2.FONT_HERSHEY_PLAIN,
            offset=50,
            border=None,
            colorB=(0, 255, 0),
        )

    def titulo(self, imagem, txt):
        cvzone.putTextRect(imagem, txt, (200, 300), border=5, offset=200)

    def desenha_retangulo(self, imagem):

        cvzone.cornerRect(
            imagem,
            (200, 200, 300, 200),
            l=100,
            t=5,
            rt=1,
            colorR=(255, 0, 255),
            colorC=(255, 0, 0),
        )
        cv2.exibe_imagem("Imagem", imagem)

    def exibe_imagem(self, imagem):
        cv2.imshow("WebCam", imagem)

    def connect(self):
        cap = cv2.VideoCapture(0)

        sucesso, imagem = cap.read()
        return cap, sucesso, imagem

    def achar_contorno(self):
        pass

    def abrir_imagem(self, path_img):
        img = cv2.imread(path_img)
        return img

    #!LOOP
    def main_loop(self):
        cap, sucesso, imagem = self.connect()

        while True:
            if sucesso:

                # todo fazer acontecer
                # coordenadas = [(200, 200), (500, 400), (255, 0, 255), 3]
                # cv2.rectangle(imagem, (200, 200), (500, 400), (255, 0, 255), 3)
                # self.desenha_retangulo(imagem)

                # cvzone.cornerRect(imagem, (200, 200, 300, 200))

                self.caixa_texto(imagem, "Ola pedro")

                self.exibe_imagem(imagem)
                # desliga
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

        cap.release()
        cv2.destroyAllWindows()
        print(
            "Camera released"
        )  # print a message to let us know the camera has been released


def main_webcam():
    cam = WebCam()
    cam.main_loop()


main_webcam()
