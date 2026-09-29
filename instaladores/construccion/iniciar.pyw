"""Arranque de la Servitotal en Windows.

Se abre el programa como módulo (no como script): así Python usa su versión ya compilada (carpeta __pycache__) y el
programa abre más rápido; ejecutar agencia.py directamente lo recompilaría entero cada vez."""
import agencia

agencia.main()
