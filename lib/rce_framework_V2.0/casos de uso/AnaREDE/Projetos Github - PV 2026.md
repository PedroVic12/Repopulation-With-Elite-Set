# 🚀 Pedro Victor — Projetos GitHub
> Dev Pleno · Engenharia Elétrica & Computação · Rio de Janeiro

---

## 📑 Índice
- [🐍 Python Stack — Pikachu](#python-stack)
- [⚡ JavaScript Stack — Raichu](#javascript-stack)
- [🦋 Flutter Stack — Kyogre](#flutter-stack)
- [🦀 Rust + Tauri Stack — Charizard](#rust-stack)
- [🔬 Simulações de Ciência](#simulacoes)
- [📦 Tabela de Repositórios](#tabela-repos)

---

## 📦 Tabela de Repositórios <a id="tabela-repos"></a>

| Pokémon | Stack | Repositório | Projeto Interno | Status |
|---------|-------|-------------|-----------------|--------|
| 🟡 **Pikachu** | Flask · Python | [Pikachu-Flask-Server][pikachu-repo] | [Batcaverna][batcaverna] · [Astro System][astro-system] · [Quizz Show][quizz] · [Kanban PRO][kanban] | ✅ Ativo |
| ⚡ **Raichu** | FastAPI · Python | [Raichu-FastAPI][raichu-repo] | Pikachu REST API | ✅ Ativo |
| 🔥 **Charizard** | Drogon · C++ | [Charizard-Drogon][charizard-repo] | Backend C++ | ✅ Ativo |
| 🌊 **Kyogre** | Flutter · GetX | [my-flutter-getx-app][kyogre-repo] | SCRUM · Todo · Kyogre | ✅ Ativo |
| 🥦 **Gohan** | React · Web | [Gohan-treinamentos-web-app][gohan-repo] | Treinamentos · Quizz · Habits | ✅ Ativo |
| ⚙️ **GetX Qt6** | Qt6 · Dart | [getx-for-qt6][qt6-repo] | Desktop App Qt6 | 🔧 Dev |
| 🔬 **Mewtwo** | Python · JS · Rust | — | [Circuito RLC][rlc] · [Buraco Negro][blackhole] | 🚧 Planejado |

---

<!-- ===================== VARIÁVEIS DE LINKS ===================== -->
[pikachu-repo]: https://github.com/PedroVic12/Pikachu-Flask-Server
[raichu-repo]: https://github.com/PedroVic12/Raichu-FastAPI
[charizard-repo]: https://github.com/PedroVic12/Charizard-Drogon
[kyogre-repo]: https://github.com/PedroVic12/my-flutter-getx-app
[gohan-repo]: https://github.com/PedroVic12/Gohan-treinamentos-web-app
[qt6-repo]: https://github.com/PedroVic12/getx-for-qt6

<!-- Sub-projetos Pikachu-Flask-Server -->
[batcaverna]: https://github.com/PedroVic12/Pikachu-Flask-Server/tree/main/batcaverna/batcaverna-project
[astro-system]: https://github.com/PedroVic12/Pikachu-Flask-Server/tree/main/pikachu-API/astro-system
[quizz]: https://github.com/PedroVic12/Pikachu-Flask-Server/blob/main/frontend/Quizz_App_For_Studying_With_UI/quizz_show_do_mihao_AI.html
[kanban]: https://github.com/PedroVic12/Pikachu-Flask-Server/tree/main/frontend/project_kanban_pro_2025

<!-- Simulações -->
[rlc]: #simulacoes
[blackhole]: #simulacoes

---

## 🐍 Python Stack — Pikachu <a id="python-stack"></a>
> **Core:** Flask · FastAPI · NumPy · SciPy · Matplotlib · Arduino Serial

```mermaid
graph TD
    PIKACHU(("⚡ PIKACHU\nPython Stack"))

    PIKACHU --> FLASK["🌶️ Flask\nPikachu-Flask-Server"]
    PIKACHU --> FASTAPI["🚀 FastAPI\nRaichu REST API"]
    PIKACHU --> DATA["📊 Data Science\nNumPy · SciPy · Pandas"]
    PIKACHU --> ARDUINO["🔌 Arduino\nSerial · IoT · Sensores"]
    PIKACHU --> SIM["🔬 Simulações\nCircuito RLC"]

    FLASK --> BATCAVERNA["🦇 Batcaverna Project"]
    FLASK --> ASTRO["🌌 Astro System"]
    FLASK --> QUIZZ["🎯 Quizz Show do Milhão"]
    FLASK --> KANBAN["📋 Kanban PRO 2025"]

    FASTAPI --> RAICHU["⚡ Raichu API\nREST Endpoints"]

    DATA --> MATPLOTLIB["📈 Matplotlib\nVisualizações"]
    DATA --> SCIPY["🧪 SciPy\nSimulações"]

    ARDUINO --> SERIAL["🔗 PySerial"]
    ARDUINO --> PYSIDE["🖥️ PySide6 GUI"]

    style PIKACHU fill:#FFD700,stroke:#FF8C00,color:#000,stroke-width:3px
    style FLASK fill:#FF6B6B,stroke:#C0392B,color:#fff
    style FASTAPI fill:#009688,stroke:#00695C,color:#fff
    style DATA fill:#3F51B5,stroke:#283593,color:#fff
    style ARDUINO fill:#00979D,stroke:#006064,color:#fff
    style SIM fill:#9C27B0,stroke:#6A1B9A,color:#fff
```

---

## ⚡ JavaScript Stack — Raichu <a id="javascript-stack"></a>
> **Core:** React · Astro · Next.js · HTML Canvas · Vite

```mermaid
graph TD
    RAICHU(("⚡ RAICHU\nJavaScript Stack"))

    RAICHU --> REACT["⚛️ React\nmeu-react-app-template"]
    RAICHU --> ASTRO_FW["🚀 Astro\nastro-system"]
    RAICHU --> NEXT["▲ Next.js\nKanban PRO"]
    RAICHU --> HTML["🌐 HTML · Canvas\nQuizz Show"]

    REACT --> GOHAN_APP["🥦 Gohan Treinamentos"]
    REACT --> QUIZZ_REACT["🎯 Quizz App"]
    REACT --> HABITS["✅ Habits Tracker"]

    ASTRO_FW --> ASTRO_SYS["🌌 Astro System\n(Pikachu API)"]

    NEXT --> KANBAN_NEXT["📋 Kanban PRO 2025\nNextJS + TypeScript"]

    HTML --> QUIZZ_MIHAO["🏆 Quizz Show do Milhão\nVanilla JS + AI"]

    RAICHU --> STREAMLIT["📊 Streamlit\nPython + JS Dashboards"]

    style RAICHU fill:#F7DF1E,stroke:#F0A500,color:#000,stroke-width:3px
    style REACT fill:#61DAFB,stroke:#21A1C4,color:#000
    style ASTRO_FW fill:#FF5D01,stroke:#C14000,color:#fff
    style NEXT fill:#000,stroke:#444,color:#fff
    style HTML fill:#E44D26,stroke:#C0341A,color:#fff
    style STREAMLIT fill:#FF4B4B,stroke:#C0392B,color:#fff
```

---

## 🦋 Flutter Stack — Kyogre <a id="flutter-stack"></a>
> **Core:** Flutter · Dart · GetX · CustomPainter · Firebase

```mermaid
graph TD
    KYOGRE(("🌊 KYOGRE\nFlutter Stack"))

    KYOGRE --> GETX["📦 GetX\nState Management"]
    KYOGRE --> UI["🎨 Flutter UI\nCustomPainter · Widgets"]
    KYOGRE --> DESKTOP["🖥️ Desktop\ngetx-for-qt6"]
    KYOGRE --> MOBILE["📱 Mobile\nAndroid · iOS"]

    GETX --> SCRUM["🏃 SCRUM App"]
    GETX --> TODO["✅ Todo App"]
    GETX --> KYOGRE_APP["🌊 Kyogre App"]
    GETX --> CALISTENIA["💪 Calistenia App\n+ Goku IA Trainer"]

    UI --> CUSTOM_PAINT["🖌️ CustomPainter\nAnimações"]
    UI --> PYSIDE_ALT["🪟 PySide6\nAlternativa Desktop"]

    DESKTOP --> QT6["⚙️ Qt6 Integration\ngetx-for-qt6"]

    MOBILE --> FIREBASE["🔥 Firebase\nAuth · Firestore"]

    style KYOGRE fill:#1E90FF,stroke:#0060C0,color:#fff,stroke-width:3px
    style GETX fill:#9B59B6,stroke:#6C3483,color:#fff
    style UI fill:#1ABC9C,stroke:#148F77,color:#fff
    style DESKTOP fill:#34495E,stroke:#1A252F,color:#fff
    style MOBILE fill:#E74C3C,stroke:#A93226,color:#fff
```

---

## 🦀 Rust + Tauri Stack — Charizard <a id="rust-stack"></a>
> **Core:** Rust · Tauri V2 · C++ Drogon · WebView · WASM

```mermaid
graph TD
    CHARIZARD(("🔥 CHARIZARD\nRust · Tauri V2"))

    CHARIZARD --> TAURI["🦀 Tauri V2\nDesktop App Framework"]
    CHARIZARD --> DROGON["⚡ Drogon C++\nBackend Server"]
    CHARIZARD --> WASM["🕸️ WASM\nRust → Browser"]
    CHARIZARD --> SIM_RUST["🔬 Simulações\nBuraco Negro"]

    TAURI --> WEBVIEW["🌐 WebView\nFrontend React/HTML"]
    TAURI --> RUST_BACKEND["⚙️ Rust Backend\nSistema de Arquivos · OS"]
    TAURI --> ELECTRON_ALT["🔄 vs Electron\nMenor · Mais Rápido"]

    DROGON --> CHARIZARD_API["🐉 Charizard API\nREST · WebSocket"]
    DROGON --> CPP_CORE["💻 C++ Core\nAlta Performance"]

    WASM --> SIM_WEB["🌌 Simulações Web\nCanvas + Rust"]

    SIM_RUST --> BLACK_HOLE["🕳️ Buraco Negro\nFísica Simulada"]

    style CHARIZARD fill:#FF4500,stroke:#B22222,color:#fff,stroke-width:3px
    style TAURI fill:#FFA500,stroke:#CC7A00,color:#000
    style DROGON fill:#8B0000,stroke:#500000,color:#fff
    style WASM fill:#654FF0,stroke:#3D00CC,color:#fff
    style SIM_RUST fill:#2E4057,stroke:#162030,color:#fff
```

---

## 🔬 Simulações de Ciência — Mewtwo <a id="simulacoes"></a>
> **Core:** Python · JavaScript · Rust · Flutter · Física Computacional

```mermaid
graph LR
    MEWTWO(("🧬 MEWTWO\nSimulações Ciência"))

    MEWTWO --> RLC["⚡ Circuito RLC"]
    MEWTWO --> BH["🕳️ Buraco Negro"]

    RLC --> PY_RLC["🐍 Python\nSciPy · Matplotlib"]
    RLC --> JS_RLC["⚡ JavaScript\nCanvas API · Chart.js"]

    BH --> FL_BH["🦋 Flutter\nCustomPainter · Dart"]
    BH --> RS_BH["🦀 Rust · Tauri V2\nWASM · WebView"]

    PY_RLC --> NUMPY["NumPy · ODE Solver"]
    JS_RLC --> CHARTJS["Animação em tempo real"]
    FL_BH --> PAINTER["Gravitational Lensing"]
    RS_BH --> PHYSICS["Física de Alta Performance"]

    style MEWTWO fill:#6A0572,stroke:#3D0042,color:#fff,stroke-width:3px
    style RLC fill:#E67E22,stroke:#A04000,color:#fff
    style BH fill:#1A1A2E,stroke:#0F0F1A,color:#fff
    style PY_RLC fill:#306998,stroke:#1E4066,color:#fff
    style JS_RLC fill:#F7DF1E,stroke:#C0A800,color:#000
    style FL_BH fill:#1E90FF,stroke:#0060C0,color:#fff
    style RS_BH fill:#FF4500,stroke:#B22222,color:#fff
```

---

## 🗂️ Estrutura de Pastas — Pikachu Flask Server

```
GitHub/Pikachu-Flask-Server/
├── batcaverna/
│   └── batcaverna-project/          ← 🦇 Batcaverna Project
├── pikachu-API/
│   └── astro-system/                ← 🌌 Astro System
└── frontend/
    ├── Quizz_App_For_Studying_With_UI/
    │   └── quizz_show_do_mihao_AI.html  ← 🎯 Quizz Show do Milhão
    └── project_kanban_pro_2025/     ← 📋 Kanban PRO NextJS
```

---

*Gerado em 2026 · Pedro Victor · Engenharia Elétrica & Computação*
