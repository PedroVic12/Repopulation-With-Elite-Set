#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup script para compilar módulos Cython/C++ do Framework RCE
Autor: Pedro Victor Veras
Data: 2025
"""

from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy as np
import os

# Configurações de compilação
extensions = [
    Extension(
        "src.cpp_optimizer",
        ["src/cpp_optimizer.pyx"],
        include_dirs=[np.get_include()],
        extra_compile_args=[
            "-O3",  # Otimização máxima
            "-march=native",  # Otimização para arquitetura específica
            "-ffast-math",  # Matemática otimizada
            "-fopenmp",  # Suporte a OpenMP
        ],
        extra_link_args=["-fopenmp"],
        language="c++",
    )
]

# Configurações do setup
setup(
    name="rce_framework_optimizer",
    version="1.0.0",
    description="Otimizador C++ para Framework RCE",
    author="Pedro Victor Veras",
    author_email="pedro.victor.veras@gmail.com",
    ext_modules=cythonize(
        extensions,
        compiler_directives={
            "language_level": 3,
            "boundscheck": False,
            "wraparound": False,
            "cdivision": True,
        }
    ),
    include_dirs=[np.get_include()],
    install_requires=[
        "numpy>=1.21.0",
        "cython>=0.29.0",
    ],
    python_requires=">=3.8",
)

if __name__ == "__main__":
    print("🔧 Compilando módulos Cython/C++...")
    print("📦 Isso pode levar alguns minutos...")
    setup()
    print("✅ Compilação concluída!") 