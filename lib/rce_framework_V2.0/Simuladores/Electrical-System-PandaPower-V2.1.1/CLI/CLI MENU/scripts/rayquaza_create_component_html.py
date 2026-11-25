import sys
import os

def create_component(name):
    template = f"""<!DOCTYPE html>
<html>
<head>
    <!-- React and ReactDOM via unpkg CDN -->
    <script crossorigin src="https://unpkg.com/react@18/umd/react.development.js"></script>
    <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
    <!-- Babel for JSX transformation -->
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100">
    <div id="root"></div>
    <script type="text/babel">
        class {name} extends React.Component {{
            render() {{
                return (
                    <div className="p-8 text-center">
                        <p>Componente {name}</p>
                        <h1 className="text-3xl font-bold text-blue-600">Componente {name}</h1>
                        <button
                            className="mt-4 px-4 py-2 bg-black text-white rounded"
                            onClick={{() => alert('Você clicou no botão!')}}
                        >
                            Clique Aqui
                        </button>
                    </div>
                );
            }}
        }}
        const root = ReactDOM.createRoot(document.getElementById('root'));
        root.render(<{name} />);
        console.log("Componente {name} renderizado");
    </script>
</body>
</html>"""

    # Cria a pasta components se não existir
    components_dir = "components"
    os.makedirs(components_dir, exist_ok=True)

    component_path = os.path.join(components_dir, f"{name}.html")
    with open(component_path, "w", encoding="utf-8") as f:
        f.write(template)
    print(f"✅ Componente {component_path} criado com sucesso!")


if __name__ == "__main__":
    # Uso no terminal: python rayquaza_create_component_html.py create JanelaPrincipal
    if len(sys.argv) > 2 and sys.argv[1] == "create":
        create_component(sys.argv[2])
