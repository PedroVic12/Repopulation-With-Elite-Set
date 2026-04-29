import easygui
import json

from Setup_rce import SetupRCE


def load_params(file_path):
    with open(file_path, "r") as file:
        params = json.load(file)
    return params


params = load_params(
    r"/home/pedrov/Documentos/GitHub/Engenharia-Eletrica-UFF/Iniciação Cientifica - Eng Eletrica UFF/evolution_rce_master/src/db/parameters.json"
)


class GUI_RCE:
    def __init__(self) -> None:
        self.window_title = "Calculadora de IMC"

        self.setup = SetupRCE(params=params)

    def MaterialAPP(self):
        msg = "Insira seus dados abaixo:"
        title = self.window_title
        fieldNames = [
            "CROSS",
            "MUTAÇÃO",
            "GERAÇÕES",
            "POPULAÇÃO",
            "TAXA RCE",
            "DELTA",
            "PORCENTAGEM C1",
        ]
        fieldNames_defs = [
            self.setup.CXPB,
            self.setup.MUTPB,
            self.setup.NGEN,
            self.setup.POP_SIZE,
            self.setup.TAXA_GENERATION,
            self.setup.delta,
            self.setup.porcentagem,
        ]
        fieldValues = easygui.multenterbox(msg, title, fieldNames, fieldNames_defs)

        while 1:
            if fieldValues == None:
                break
            errmsg = ""
            for i in range(len(fieldNames)):
                if fieldValues[i].strip() == "":
                    errmsg = errmsg + ('"%s" is a required field.\n\n' % fieldNames[i])
            if errmsg == "":
                break  # no problems found
            fieldValues = easygui.multenterbox(errmsg, title, fieldNames, fieldValues)
        return fieldValues

    def display_result(
        self,
    ):
        message = "Voce com {age} anos, {name}, tem seu IMC é: {imc:.2f}"

        print(message)


def tryfunction():

    gui = GUI_RCE()
    app = gui.MaterialAPP()
    print(app)


#
# tryfunction()
