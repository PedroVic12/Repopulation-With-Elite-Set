# Pyside6 para Python com Qt desginer

1. [Docs Qt for Python](https://doc.qt.io/qtforpython-6/index.html)

2. [Tauri Rust Desktop](https://v2.tauri.app/develop/calling-rust/)

## Rust

O que é: Uma linguagem de programação de sistemas focada em segurança, velocidade e concorrência.

No contexto Web: Rust é compilado para WebAssembly (Wasm), o que permite que ele execute no navegador com desempenho próximo ao nativo, muitas vezes mais rápido que estruturas JavaScript como React ou Vue.

## Leptos

O que é: Um framework web Rust de última geração, focado na construção de interfaces declarativas e rápidas.
Principais características:

- Reatividade de Grão Fino (Fine-grained Reactivity): Diferente do React, que re-renderiza componentes inteiros, o Leptos atualiza apenas o pequeno pedaço do DOM que mudou, resultando em performance superior.
- Full-stack: Pode ser usado para renderização no cliente (CSR), renderização no servidor (SSR) ou hidratação, permitindo que Rust seja usado tanto no front-end quanto no back-end.
- Sem Virtual DOM: O Leptos interage diretamente com o DOM, o que aumenta a eficiência.

## Trunk

O que é: Uma ferramenta de build e "bundler" (empacotador) para aplicações Rust WebAssembly.
O que ele faz:

- Compilação Automática: Monitora seu código Rust, compila para Wasm, e recarrega o navegador automaticamente quando há mudanças (live-reloading).
- Gerenciamento de Assets: Processa HTML, CSS, Sass e imagens, facilitando o empacotamento para produção.

Ideal para CSR: É a ferramenta recomendada para desenvolver aplicações Leptos renderizadas no cliente (Client-Side Rendering).
