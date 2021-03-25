@call rm -r bin\windows
@call rm -r build
@call rm resume.spec
@call pyinstaller --distpath bin\windows --hidden-import PySimpleGUI -wF resume.py
