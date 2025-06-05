class IMCCalculator:
    def __init__(self, dados):
        self.window_title = "Calculadora de IMC"
        self.nome = dados["nome"]
        self.idade = dados["idade"]
        self.altura = dados["altura"]
        self.peso = dados["peso"]

    def get_input(self):
        try:
            msg = "Insira seus dados abaixo:"
            title = self.window_title
            fieldNames = ["nome", "idade", "altura (m)", "peso (kg)"]
            fieldNames_defs = [self.nome, self.idade, self.altura, self.peso]
            fieldValues = easygui.multenterbox(msg, title, fieldNames, fieldNames_defs)

            while 1:
                if fieldValues == None:
                    break
                errmsg = ""
                for i in range(len(fieldNames)):
                    if fieldValues[i].strip() == "":
                        errmsg = errmsg + (
                            '"%s" is a required field.\n\n' % fieldNames[i]
                        )
                if errmsg == "":
                    break  # no problems found
                fieldValues = easygui.multenterbox(
                    errmsg, title, fieldNames, fieldValues
                )
            return fieldValues
        except:
            print("erro ao carregar tela")

    def calculate_imc(self, weight, height):
        if weight <= 0 or height <= 0:
            raise ValueError("Valores negativos não são aceitos.")
        imc = weight / (height * height)
        return imc

    def display_result(self, imc, age, name):
        message = f"Voce com {age} anos, {name}, tem seu IMC é: {imc:.2f}"
        # easygui.msgbox(
        #     message,
        #     self.window_title,
        #     title="Resultado",
        #     ok_button="OK",
        #     image=None,
        #     root=None,
        # )
        print(message)


def main():
    dados = {"nome": "Pedro", "idade": 26, "altura": 1.72, "peso": 70}

    calculator = IMCCalculator(dados)
    try:
        name, age, height, weight = calculator.get_input()
        imc = calculator.calculate_imc(float(weight), float(height))
        calculator.display_result(imc, age, name)
    except ValueError as e:
        easygui.msgbox(str(e), "Erro", title="Erro", ok_button="OK")


main()
